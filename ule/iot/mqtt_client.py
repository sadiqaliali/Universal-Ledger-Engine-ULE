"""
ULE MQTT Client - IoT Message Broker Integration

Provides MQTT publish/subscribe capabilities for ULE databases.
Enables real-time data streaming from IoT devices to ULE.
"""

import json
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class QoS(Enum):
    """Quality of Service levels for MQTT."""
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


@dataclass
class MQTTMessage:
    """Represents an MQTT message."""
    topic: str
    payload: Any
    qos: QoS = QoS.AT_LEAST_ONCE
    retain: bool = False
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'topic': self.topic,
            'payload': self.payload,
            'qos': self.qos.value,
            'retain': self.retain,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MQTTMessage':
        return cls(
            topic=data['topic'],
            payload=data['payload'],
            qos=QoS(data.get('qos', 1)),
            retain=data.get('retain', False),
            timestamp=data.get('timestamp', time.time())
        )


class MQTTClient:
    """
    MQTT Client for ULE.
    
    Provides MQTT publish/subscribe functionality with automatic
    message routing to ULE tables.
    
    Usage:
        client = MQTTClient(broker='localhost', port=1883)
        client.connect()
        client.subscribe('sensors/temperature', callback=handle_temp)
        client.publish('sensors/humidity', {'value': 65.2})
        client.disconnect()
    """
    
    def __init__(self, broker: str = 'localhost', port: int = 1883,
                 client_id: Optional[str] = None, username: Optional[str] = None,
                 password: Optional[str] = None, db_connection=None):
        self.broker = broker
        self.port = port
        self.client_id = client_id or f'ule_client_{int(time.time())}'
        self.username = username
        self.password = password
        self.db = db_connection
        
        self._connected = False
        self._subscriptions: Dict[str, Callable] = {}
        self._message_queue: List[MQTTMessage] = []
        self._lock = threading.Lock()
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None
        
        # Try to import paho-mqtt if available
        try:
            import paho.mqtt.client as mqtt
            self._mqtt_client = mqtt.Client(client_id=self.client_id)
            if username:
                self._mqtt_client.username_pw_set(username, password)
            self._mqtt_client.on_message = self._on_mqtt_message
            self._mqtt_client.on_connect = self._on_connect
            self._has_paho = True
        except ImportError:
            self._mqtt_client = None
            self._has_paho = False
    
    def connect(self) -> bool:
        """Connect to MQTT broker."""
        if self._has_paho and self._mqtt_client:
            try:
                self._mqtt_client.connect(self.broker, self.port, 60)
                self._mqtt_client.loop_start()
                self._connected = True
                return True
            except Exception as e:
                print(f"MQTT connection error: {e}")
                self._connected = False
                return False
        else:
            # Simulated mode for testing without broker
            self._connected = True
            return True
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._has_paho and self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
        self._connected = False
        self._running = False
    
    def publish(self, topic: str, payload: Any, qos: QoS = QoS.AT_LEAST_ONCE,
                retain: bool = False) -> bool:
        """
        Publish a message to an MQTT topic.
        
        Args:
            topic: MQTT topic (e.g., 'sensors/temperature')
            payload: Message payload (will be JSON serialized if dict/list)
            qos: Quality of Service level
            retain: Whether to retain the message
            
        Returns:
            True if published successfully
        """
        if not self._connected:
            raise ConnectionError("Not connected to MQTT broker")
        
        message = MQTTMessage(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain
        )
        
        if self._has_paho and self._mqtt_client:
            payload_str = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload)
            result = self._mqtt_client.publish(
                topic, 
                payload_str, 
                qos=qos.value, 
                retain=retain
            )
            return result.rc == 0
        else:
            # Simulated mode
            with self._lock:
                self._message_queue.append(message)
            
            # Store in database if connected
            if self.db:
                self._store_message(message)
            
            return True
    
    def subscribe(self, topic: str, callback: Optional[Callable] = None,
                  qos: QoS = QoS.AT_LEAST_ONCE) -> bool:
        """
        Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic pattern (supports wildcards +, #)
            callback: Function to call when message received
            qos: Quality of Service level
            
        Returns:
            True if subscribed successfully
        """
        if not self._connected:
            raise ConnectionError("Not connected to MQTT broker")
        
        self._subscriptions[topic] = callback or self._default_callback
        
        if self._has_paho and self._mqtt_client:
            result = self._mqtt_client.subscribe(topic, qos=qos.value)
            return result[0] == 0
        else:
            return True
    
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from a topic."""
        if topic in self._subscriptions:
            del self._subscriptions[topic]
            if self._has_paho and self._mqtt_client:
                self._mqtt_client.unsubscribe(topic)
            return True
        return False
    
    def get_queued_messages(self) -> List[MQTTMessage]:
        """Get all queued messages (for simulated mode)."""
        with self._lock:
            messages = list(self._message_queue)
            self._message_queue.clear()
            return messages
    
    def route_to_table(self, topic_pattern: str, table: str,
                       column_mapping: Optional[Dict[str, str]] = None) -> bool:
        """
        Route MQTT messages matching a topic pattern to a database table.
        
        Args:
            topic_pattern: MQTT topic pattern to match
            table: Target database table
            column_mapping: Map payload keys to table columns
            
        Returns:
            True if route created successfully
        """
        def route_callback(client, userdata, msg):
            try:
                payload = json.loads(msg.payload) if isinstance(msg.payload, bytes) else msg.payload
                
                if isinstance(payload, dict):
                    columns = list(payload.keys())
                    values = list(payload.values())
                    
                    if column_mapping:
                        columns = [column_mapping.get(c, c) for c in columns]
                    
                    placeholders = ', '.join(['?' for _ in values])
                    col_names = ', '.join(columns)
                    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                    
                    if self.db:
                        conn = self.db.get_connection()
                        conn.execute(sql, values)
                        conn.commit()
            except Exception as e:
                print(f"Error routing message: {e}")
        
        return self.subscribe(topic_pattern, route_callback)
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        topic = msg.topic
        
        # Find matching subscriptions
        for pattern, callback in self._subscriptions.items():
            if self._match_topic(pattern, topic):
                callback(client, userdata, msg)
                break
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self._connected = True
            # Resubscribe to all topics
            for topic in self._subscriptions:
                client.subscribe(topic)
    
    def _default_callback(self, client, userdata, msg):
        """Default message handler."""
        print(f"Received message on {msg.topic}: {msg.payload}")
    
    def _store_message(self, message: MQTTMessage):
        """Store message in database."""
        try:
            conn = self.db.get_connection()
            conn.execute(
                "INSERT INTO mqtt_messages (topic, payload, timestamp) VALUES (?, ?, ?)",
                (message.topic, json.dumps(message.payload), message.timestamp)
            )
            conn.commit()
        except Exception:
            pass  # Table may not exist
    
    def _match_topic(self, pattern: str, topic: str) -> bool:
        """Simple MQTT topic matching with wildcard support."""
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if len(pattern_parts) < len(topic_parts) and not pattern_parts[-1] == '#':
            return False
        
        for i, p in enumerate(pattern_parts):
            if p == '#':
                return True
            if i >= len(topic_parts):
                return False
            if p != '+' and p != topic_parts[i]:
                return False
        
        return len(pattern_parts) >= len(topic_parts)
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    @property
    def subscription_count(self) -> int:
        return len(self._subscriptions)
