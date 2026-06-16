"""
Universal Ledger Engine (ULE) - The People's Database
One File, Every Model, Absolute Trust, Quantum Ready
"""

__version__ = "0.1.0"
__author__ = "ULE Contributors"

from ule.core.database import ULEDatabase
from ule.core.connection import connect

# Security
from ule.security.column_encryption import ColumnEncryption
from ule.security.signatures import DigitalSignature
from ule.security.access_control import AccessControlManager
from ule.security.pqc import MLKEM_Simulation as MLKEM, Dilithium_Simulation as Dilithium, HybridCrypto

# Engines
from ule.engines.sql_engine import SQLEngine
from ule.engines.nosql_engine import NoSQL_Engine
from ule.engines.graph_engine import GraphEngine
from ule.engines.vector_engine import VectorEngine
from ule.engines.timeseries_engine import TimeSeriesEngine
from ule.engines.fulltext_engine import FullTextEngine
from ule.engines.geospatial_engine import GeospatialEngine
from ule.engines.pqc_engine import PQCEngine

# Quantum
try:
    from ule.quantum import (
        Qubit,
        QubitRegister,
        QuantumGates,
        QuantumCircuit,
        QuantumAlgorithms,
        QiskitBackend,
        QuantumVisualizer,
    )
    _quantum_available = True
except ImportError:
    _quantum_available = False

# IoT
try:
    from ule.iot.mqtt_client import MQTTClient, MQTTMessage, QoS
except ImportError:
    _iot_available = False

__all__ = [
    "ULEDatabase",
    "connect",
    "ColumnEncryption",
    "DigitalSignature",
    "AccessControlManager",
    "MLKEM",
    "Dilithium",
    "HybridCrypto",
    "SQLEngine",
    "NoSQL_Engine",
    "GraphEngine",
    "VectorEngine",
    "TimeSeriesEngine",
    "FullTextEngine",
    "GeospatialEngine",
    "PQCEngine",
    "__version__",
]
