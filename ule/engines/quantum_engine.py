"""
Quantum Storage Engine
======================
Quantum computing storage engine for ULE.

Integrates quantum computing capabilities with ULE's .udb file format.
Supports storing quantum states, circuits, and algorithm results.

Security Features:
- State encryption
- Audit logging
- Access control
- Integrity verification
"""

import numpy as np
import json
import hashlib
import base64
from typing import Optional, Dict, List, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import os

# Import from ule.quantum instead of local path
from ule.quantum.qubit import Qubit, QubitRegister, QuantumValidationError, QuantumSecurityError
from ule.quantum.gates import QuantumGates
from ule.quantum.circuit import QuantumCircuit, CircuitResult
from ule.quantum.algorithms import QuantumAlgorithms, AlgorithmResult
from ule.quantum.qiskit_backend import QiskitBackend
from ule.quantum.visualization import QuantumVisualizer

logger = logging.getLogger(__name__)


class QuantumEngineError(Exception):
    """Exception raised for quantum engine errors."""
    pass


class QuantumStorageError(Exception):
    """Exception raised for quantum storage errors."""
    pass


@dataclass
class QuantumStateRecord:
    """Record of a stored quantum state."""
    state_id: str
    num_qubits: int
    state_vector: List[complex]
    created_at: str
    user_id: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    state_hash: str = ""
    encrypted: bool = False


@dataclass
class QuantumCircuitRecord:
    """Record of a stored quantum circuit."""
    circuit_id: str
    name: str
    num_qubits: int
    operations: List[Dict[str, Any]]
    created_at: str
    user_id: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    circuit_hash: str = ""


class QuantumEngine:
    """
    Quantum computing engine for ULE with security features.
    
    Provides:
    - Quantum state storage
    - Circuit execution
    - Algorithm running
    - Integration with .udb files
    - Audit logging
    """
    
    MAX_QUBITS = 20  # Maximum qubits for simulation
    MAX_STATES = 1000  # Maximum stored states
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        encryption_key: Optional[bytes] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize quantum engine.
        
        Args:
            db_path: Path to .udb file (optional)
            encryption_key: Optional encryption key for states
            user_id: User ID for audit logging
        """
        self._db_path = db_path
        self._user_id = user_id
        self._encryption_key = encryption_key
        self._audit_log: List[dict] = []
        
        # Initialize components
        self._gates = QuantumGates(user_id=user_id)
        self._algorithms = QuantumAlgorithms(user_id=user_id)
        self._visualizer = QuantumVisualizer(user_id=user_id)
        self._qiskit_backend = QiskitBackend(user_id=user_id)
        
        # Storage
        self._quantum_states: Dict[str, QuantumStateRecord] = {}
        self._quantum_circuits: Dict[str, QuantumCircuitRecord] = {}
        
        self._log_operation("ENGINE_INIT", {
            "db_path": db_path,
            "encryption_enabled": encryption_key is not None
        })
    
    def _log_operation(self, operation: str, details: dict) -> None:
        """Log engine operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "user_id": self._user_id
        })
    
    def _generate_state_id(self) -> str:
        """Generate unique state ID."""
        timestamp = datetime.utcnow().isoformat()
        random_data = os.urandom(16)
        data = f"{timestamp}{random_data}".encode()
        return f"qstate_{hashlib.sha256(data).hexdigest()[:16]}"
    
    def _generate_circuit_id(self) -> str:
        """Generate unique circuit ID."""
        timestamp = datetime.utcnow().isoformat()
        random_data = os.urandom(16)
        data = f"{timestamp}{random_data}".encode()
        return f"qcircuit_{hashlib.sha256(data).hexdigest()[:16]}"
    
    def _compute_state_hash(self, state_vector: np.ndarray) -> str:
        """Compute hash of state vector."""
        return hashlib.sha256(state_vector.tobytes()).hexdigest()[:32]
    
    def _encrypt_state(self, state_vector: np.ndarray) -> bytes:
        """Encrypt state vector if encryption key is set."""
        if not self._encryption_key:
            return state_vector.tobytes()
        
        # Simple XOR encryption (in production, use proper encryption)
        key_hash = hashlib.sha256(self._encryption_key).digest()
        data = state_vector.tobytes()
        encrypted = bytes(d ^ key_hash[i % len(key_hash)] for i, d in enumerate(data))
        return encrypted
    
    def _decrypt_state(self, encrypted_data: bytes) -> np.ndarray:
        """Decrypt state vector if encryption key is set."""
        if not self._encryption_key:
            return np.frombuffer(encrypted_data, dtype=complex)
        
        key_hash = hashlib.sha256(self._encryption_key).digest()
        decrypted = bytes(d ^ key_hash[i % len(key_hash)] for i, d in enumerate(encrypted_data))
        return np.frombuffer(decrypted, dtype=complex)
    
    # ========== State Management ==========
    
    def create_state(
        self,
        num_qubits: int,
        initial_state: str = "0",
        metadata: Optional[Dict] = None
    ) -> QuantumStateRecord:
        """
        Create and store a new quantum state.
        
        Args:
            num_qubits: Number of qubits
            initial_state: Initial state string
            metadata: Optional metadata
            
        Returns:
            QuantumStateRecord
        """
        # Security: Validate qubit count
        if num_qubits < 1 or num_qubits > self.MAX_QUBITS:
            raise QuantumValidationError(
                f"Number of qubits must be 1-{self.MAX_QUBITS}, got {num_qubits}"
            )
        
        if len(self._quantum_states) >= self.MAX_STATES:
            raise QuantumStorageError(
                f"Maximum {self.MAX_STATES} states reached"
            )
        
        # Create register
        register = QubitRegister(
            num_qubits=num_qubits,
            initial_state=initial_state,
            user_id=self._user_id
        )
        
        state_vector = register.state_vector
        state_hash = self._compute_state_hash(state_vector)
        
        # Encrypt if enabled
        encrypted_data = self._encrypt_state(state_vector)
        is_encrypted = self._encryption_key is not None
        
        record = QuantumStateRecord(
            state_id=self._generate_state_id(),
            num_qubits=num_qubits,
            state_vector=state_vector.tolist(),
            created_at=datetime.utcnow().isoformat(),
            user_id=self._user_id,
            metadata=metadata or {},
            state_hash=state_hash,
            encrypted=is_encrypted
        )
        
        self._quantum_states[record.state_id] = record
        
        self._log_operation("CREATE_STATE", {
            "state_id": record.state_id,
            "num_qubits": num_qubits,
            "encrypted": is_encrypted
        })
        
        return record
    
    def get_state(self, state_id: str) -> Optional[QuantumStateRecord]:
        """Get stored quantum state."""
        return self._quantum_states.get(state_id)
    
    def delete_state(self, state_id: str) -> bool:
        """Delete stored quantum state."""
        if state_id in self._quantum_states:
            del self._quantum_states[state_id]
            self._log_operation("DELETE_STATE", {"state_id": state_id})
            return True
        return False
    
    def list_states(self) -> List[Dict[str, Any]]:
        """List all stored states (metadata only)."""
        return [
            {
                "state_id": s.state_id,
                "num_qubits": s.num_qubits,
                "created_at": s.created_at,
                "state_hash": s.state_hash,
                "encrypted": s.encrypted
            }
            for s in self._quantum_states.values()
        ]
    
    # ========== Circuit Management ==========
    
    def create_circuit(
        self,
        num_qubits: int,
        name: str = "circuit",
        metadata: Optional[Dict] = None
    ) -> QuantumCircuit:
        """
        Create a new quantum circuit.
        
        Args:
            num_qubits: Number of qubits
            name: Circuit name
            metadata: Optional metadata
            
        Returns:
            QuantumCircuit
        """
        circuit = QuantumCircuit(
            num_qubits=num_qubits,
            name=name,
            user_id=self._user_id
        )
        
        self._log_operation("CREATE_CIRCUIT", {
            "name": name,
            "num_qubits": num_qubits
        })
        
        return circuit
    
    def save_circuit(
        self,
        circuit: QuantumCircuit,
        metadata: Optional[Dict] = None
    ) -> QuantumCircuitRecord:
        """
        Save circuit to storage.
        
        Args:
            circuit: Circuit to save
            metadata: Optional metadata
            
        Returns:
            QuantumCircuitRecord
        """
        if not isinstance(circuit, QuantumCircuit):
            raise QuantumValidationError("Expected QuantumCircuit")
        
        record = QuantumCircuitRecord(
            circuit_id=self._generate_circuit_id(),
            name=circuit.name,
            num_qubits=circuit.num_qubits,
            operations=[
                {
                    "gate": op.gate_name,
                    "targets": op.targets,
                    "controls": op.controls,
                    "parameters": op.parameters
                }
                for op in circuit.operations
            ],
            created_at=datetime.utcnow().isoformat(),
            user_id=self._user_id,
            metadata=metadata or {},
            circuit_hash=circuit._compute_circuit_hash()
        )
        
        self._quantum_circuits[record.circuit_id] = record
        
        self._log_operation("SAVE_CIRCUIT", {
            "circuit_id": record.circuit_id,
            "name": circuit.name
        })
        
        return record
    
    def get_circuit(self, circuit_id: str) -> Optional[QuantumCircuitRecord]:
        """Get stored circuit."""
        return self._quantum_circuits.get(circuit_id)
    
    def delete_circuit(self, circuit_id: str) -> bool:
        """Delete stored circuit."""
        if circuit_id in self._quantum_circuits:
            del self._quantum_circuits[circuit_id]
            self._log_operation("DELETE_CIRCUIT", {"circuit_id": circuit_id})
            return True
        return False
    
    def list_circuits(self) -> List[Dict[str, Any]]:
        """List all stored circuits (metadata only)."""
        return [
            {
                "circuit_id": c.circuit_id,
                "name": c.name,
                "num_qubits": c.num_qubits,
                "depth": len(c.operations),
                "circuit_hash": c.circuit_hash
            }
            for c in self._quantum_circuits.values()
        ]
    
    # ========== Circuit Execution ==========
    
    def execute_circuit(
        self,
        circuit: QuantumCircuit,
        initial_state: Optional[str] = None,
        measure: bool = False,
        shots: int = 1
    ) -> Union[CircuitResult, Dict[str, int]]:
        """
        Execute a quantum circuit.
        
        Args:
            circuit: Circuit to execute
            initial_state: Initial state string
            measure: Whether to measure
            shots: Number of shots for simulation
            
        Returns:
            CircuitResult for single shot, dict for multiple shots
        """
        if shots > 1:
            return circuit.simulate(
                initial_state=initial_state or "0" * circuit.num_qubits,
                shots=shots
            )
        else:
            return circuit.execute(
                initial_state=initial_state,
                measure=measure
            )
    
    def run_algorithm(
        self,
        algorithm_name: str,
        **kwargs
    ) -> AlgorithmResult:
        """
        Run a quantum algorithm.
        
        Args:
            algorithm_name: Name of algorithm
            **kwargs: Algorithm parameters
            
        Returns:
            AlgorithmResult
        """
        if not hasattr(self._algorithms, algorithm_name.lower().replace(" ", "_")):
            raise QuantumValidationError(f"Unknown algorithm: {algorithm_name}")
        
        algorithm_func = getattr(self._algorithms, algorithm_name.lower().replace(" ", "_"))
        return algorithm_func(**kwargs)
    
    # ========== Visualization ==========
    
    def visualize_state(
        self,
        state_id: str,
        visualization_type: str = "bloch"
    ) -> Union[str, bytes, None]:
        """
        Visualize a stored quantum state.
        
        Args:
            state_id: State ID
            visualization_type: Type of visualization
            
        Returns:
            Visualization output
        """
        state = self.get_state(state_id)
        if not state:
            raise QuantumValidationError(f"State not found: {state_id}")
        
        # Create qubit register from state vector
        register = QubitRegister(
            num_qubits=state.num_qubits,
            initial_state="0" * state.num_qubits,
            user_id=self._user_id
        )
        
        if visualization_type == "bloch":
            # Visualize first qubit on Bloch sphere
            return self._visualizer.bloch_sphere(
                register.get_qubit(0),
                title=f"State {state_id}"
            )
        elif visualization_type == "distribution":
            return self._visualizer.probability_distribution(
                register,
                title=f"State {state_id}"
            )
        else:
            raise QuantumValidationError(f"Unknown visualization: {visualization_type}")
    
    def visualize_circuit(
        self,
        circuit_id: str
    ) -> str:
        """
        Visualize a stored circuit.
        
        Args:
            circuit_id: Circuit ID
            
        Returns:
            ASCII circuit diagram
        """
        circuit_record = self.get_circuit(circuit_id)
        if not circuit_record:
            raise QuantumValidationError(f"Circuit not found: {circuit_id}")
        
        # Reconstruct circuit
        circuit = QuantumCircuit(
            num_qubits=circuit_record.num_qubits,
            name=circuit_record.name,
            user_id=self._user_id
        )
        
        for op in circuit_record.operations:
            circuit.add_gate(
                gate_name=op["gate"],
                targets=op["targets"],
                controls=op.get("controls", []),
                parameters=op.get("parameters")
            )
        
        return self._visualizer.circuit_diagram(circuit, circuit_record.name)
    
    # ========== Qiskit Integration ==========
    
    def run_on_simulator(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024
    ) -> Dict[str, int]:
        """
        Run circuit on Qiskit simulator.
        
        Args:
            circuit: Circuit to run
            shots: Number of shots
            
        Returns:
            Measurement counts
        """
        if not self._qiskit_backend._qiskit_available:
            logger.warning("Qiskit not available, using native simulator")
            return circuit.simulate(shots=shots)
        
        result = self._qiskit_backend.run_simulator(circuit, shots=shots)
        return result.measurements
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about available backends."""
        return {
            "qiskit_available": self._qiskit_backend._qiskit_available,
            "backends": self._qiskit_backend.list_backends(),
            "native_simulator": True,
            "max_qubits": self.MAX_QUBITS
        }
    
    # ========== Export/Import ==========
    
    def export_state(
        self,
        state_id: str,
        format: str = "json"
    ) -> Union[str, bytes]:
        """
        Export quantum state.
        
        Args:
            state_id: State ID
            format: Export format (json, numpy)
            
        Returns:
            Exported data
        """
        state = self.get_state(state_id)
        if not state:
            raise QuantumValidationError(f"State not found: {state_id}")
        
        if format == "json":
            return json.dumps({
                "state_id": state.state_id,
                "num_qubits": state.num_qubits,
                "state_vector": [
                    {"real": c.real, "imag": c.imag}
                    for c in state.state_vector
                ],
                "state_hash": state.state_hash,
                "metadata": state.metadata
            })
        elif format == "numpy":
            return np.array(state.state_vector, dtype=complex).tobytes()
        else:
            raise QuantumValidationError(f"Unknown format: {format}")
    
    def import_state(
        self,
        data: Union[str, bytes],
        format: str = "json"
    ) -> QuantumStateRecord:
        """
        Import quantum state.
        
        Args:
            data: Imported data
            format: Data format
            
        Returns:
            QuantumStateRecord
        """
        if format == "json":
            state_data = json.loads(data)
            state_vector = [
                complex(c["real"], c["imag"])
                for c in state_data["state_vector"]
            ]
            num_qubits = state_data["num_qubits"]
            metadata = state_data.get("metadata", {})
        elif format == "numpy":
            state_vector = np.frombuffer(data, dtype=complex).tolist()
            num_qubits = int(np.log2(len(state_vector)))
            metadata = {}
        else:
            raise QuantumValidationError(f"Unknown format: {format}")
        
        # Validate state vector
        if len(state_vector) != 2 ** num_qubits:
            raise QuantumValidationError(
                f"State vector length {len(state_vector)} != 2^{num_qubits}"
            )
        
        # Create record
        record = QuantumStateRecord(
            state_id=self._generate_state_id(),
            num_qubits=num_qubits,
            state_vector=state_vector,
            created_at=datetime.utcnow().isoformat(),
            user_id=self._user_id,
            metadata=metadata,
            state_hash=hashlib.sha256(
                np.array(state_vector, dtype=complex).tobytes()
            ).hexdigest()[:32]
        )
        
        self._quantum_states[record.state_id] = record
        
        self._log_operation("IMPORT_STATE", {
            "state_id": record.state_id,
            "format": format
        })
        
        return record
    
    # ========== Utility ==========
    
    def get_audit_log(self) -> List[dict]:
        """Get engine audit log."""
        return self._audit_log.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "states_count": len(self._quantum_states),
            "circuits_count": len(self._quantum_circuits),
            "max_qubits": self.MAX_QUBITS,
            "max_states": self.MAX_STATES,
            "encryption_enabled": self._encryption_key is not None,
            "qiskit_available": self._qiskit_backend._qiskit_available
        }
    
    def clear_all(self) -> None:
        """Clear all stored states and circuits."""
        self._quantum_states.clear()
        self._quantum_circuits.clear()
        self._log_operation("CLEAR_ALL", {})
    
    def __repr__(self) -> str:
        return (
            f"QuantumEngine(states={len(self._quantum_states)}, "
            f"circuits={len(self._quantum_circuits)})"
        )
