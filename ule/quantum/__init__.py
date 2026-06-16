"""
ULE Quantum Computing Module
============================
Quantum computing support for Universal Lite DB.

Features:
- Qubit representation and manipulation
- Quantum gates (single and multi-qubit)
- Quantum circuit builder
- Quantum algorithms (Grover, Deutsch-Jozsa, QFT, etc.)
- IBM Qiskit integration
- Bloch sphere visualization

Security:
- Input validation for all quantum operations
- State integrity verification
- Audit logging for quantum operations
"""

from .qubit import Qubit, QubitRegister
from .gates import QuantumGates
from .circuit import QuantumCircuit
from .algorithms import QuantumAlgorithms
from .qiskit_backend import QiskitBackend
from .visualization import QuantumVisualizer

__all__ = [
    "Qubit",
    "QubitRegister",
    "QuantumGates",
    "QuantumCircuit",
    "QuantumAlgorithms",
    "QiskitBackend",
    "QuantumVisualizer",
]

__version__ = "0.2.0"
