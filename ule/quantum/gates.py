"""
Quantum Gates Implementation
============================
Comprehensive quantum gate library with security validation.

Includes:
- Single-qubit gates (Pauli, Hadamard, Phase)
- Two-qubit gates (CNOT, CZ, SWAP)
- Multi-qubit gates (Toffoli, Fredkin)
- Custom unitary gates
"""

import numpy as np
import hashlib
from typing import Optional, Dict, Callable, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GateSecurityError(Exception):
    """Exception raised for gate security violations."""
    pass


class GateValidationError(Exception):
    """Exception raised for gate validation errors."""
    pass


@dataclass
class GateDefinition:
    """Gate definition with metadata."""
    name: str
    matrix: np.ndarray
    num_qubits: int
    description: str
    is_parametrized: bool = False
    parameters: Optional[Dict] = None


class QuantumGates:
    """
    Quantum gate library with security features.
    
    All gates are validated for unitarity before use.
    """
    
    EPSILON = 1e-10  # Tolerance for unitarity checks
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize quantum gates library.
        
        Args:
            user_id: Optional user ID for audit logging
        """
        self._user_id = user_id
        self._gate_registry: Dict[str, GateDefinition] = {}
        self._operation_log: List[dict] = []
        
        # Initialize standard gates
        self._init_standard_gates()
    
    def _init_standard_gates(self) -> None:
        """Initialize standard quantum gates."""
        # Single-qubit gates
        self._register_gate(GateDefinition(
            name="I",
            matrix=self.pauli_i(),
            num_qubits=1,
            description="Identity gate"
        ))
        
        self._register_gate(GateDefinition(
            name="X",
            matrix=self.pauli_x(),
            num_qubits=1,
            description="Pauli-X (NOT) gate"
        ))
        
        self._register_gate(GateDefinition(
            name="Y",
            matrix=self.pauli_y(),
            num_qubits=1,
            description="Pauli-Y gate"
        ))
        
        self._register_gate(GateDefinition(
            name="Z",
            matrix=self.pauli_z(),
            num_qubits=1,
            description="Pauli-Z gate"
        ))
        
        self._register_gate(GateDefinition(
            name="HADAMARD",
            matrix=self.hadamard(),
            num_qubits=1,
            description="Hadamard gate"
        ))
        
        self._register_gate(GateDefinition(
            name="S",
            matrix=self.phase_s(),
            num_qubits=1,
            description="Phase (S) gate"
        ))
        
        self._register_gate(GateDefinition(
            name="T",
            matrix=self.phase_t(),
            num_qubits=1,
            description="T gate"
        ))
        
        # Two-qubit gates
        self._register_gate(GateDefinition(
            name="CNOT",
            matrix=self.cnot(),
            num_qubits=2,
            description="Controlled-NOT gate"
        ))
        
        self._register_gate(GateDefinition(
            name="CZ",
            matrix=self.cz(),
            num_qubits=2,
            description="Controlled-Z gate"
        ))
        
        self._register_gate(GateDefinition(
            name="SWAP",
            matrix=self.swap(),
            num_qubits=2,
            description="SWAP gate"
        ))
        
        # Three-qubit gates
        self._register_gate(GateDefinition(
            name="TOFFOLI",
            matrix=self.toffoli(),
            num_qubits=3,
            description="Toffoli (CCNOT) gate"
        ))
        
        self._register_gate(GateDefinition(
            name="FREDKIN",
            matrix=self.fredkin(),
            num_qubits=3,
            description="Fredkin (CSWAP) gate"
        ))
    
    def _register_gate(self, gate: GateDefinition) -> None:
        """
        Register a gate with validation.
        
        Args:
            gate: Gate definition to register
        """
        # Security: Validate unitarity
        self._validate_unitarity(gate.matrix, gate.name)
        
        self._gate_registry[gate.name] = gate
        self._log_operation("REGISTER_GATE", {"name": gate.name})
    
    def _log_operation(self, operation: str, details: dict) -> None:
        """Log gate operation."""
        self._operation_log.append({
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "user_id": self._user_id
        })
    
    @staticmethod
    def _validate_unitarity(matrix: np.ndarray, gate_name: str) -> None:
        """
        Security: Validate that a matrix is unitary (U†U = I).
        
        Args:
            matrix: Matrix to validate
            gate_name: Name of the gate for error messages
        """
        if not isinstance(matrix, np.ndarray):
            raise GateValidationError(
                f"Gate {gate_name}: Matrix must be numpy array"
            )
        
        n = matrix.shape[0]
        if matrix.shape != (n, n):
            raise GateValidationError(
                f"Gate {gate_name}: Matrix must be square, got {matrix.shape}"
            )
        
        # Check U†U = I
        identity = np.eye(n, dtype=complex)
        product = matrix.conj().T @ matrix
        
        if not np.allclose(product, identity, atol=QuantumGates.EPSILON):
            raise GateSecurityError(
                f"Gate {gate_name}: Matrix is not unitary"
            )
    
    @staticmethod
    def _validate_matrix_dimensions(
        matrix: np.ndarray,
        expected_dims: Tuple[int, int],
        gate_name: str
    ) -> None:
        """Security: Validate matrix dimensions."""
        if matrix.shape != expected_dims:
            raise GateValidationError(
                f"Gate {gate_name}: Expected {expected_dims}, got {matrix.shape}"
            )
    
    # ========== Single-Qubit Gates ==========
    
    @staticmethod
    def pauli_i() -> np.ndarray:
        """
        Identity gate (I).
        
        I = [[1, 0],
             [0, 1]]
        """
        return np.array([[1, 0], [0, 1]], dtype=complex)
    
    @staticmethod
    def pauli_x() -> np.ndarray:
        """
        Pauli-X gate (NOT gate).
        
        X = [[0, 1],
             [1, 0]]
        
        Flips |0⟩ ↔ |1⟩
        """
        return np.array([[0, 1], [1, 0]], dtype=complex)
    
    @staticmethod
    def pauli_y() -> np.ndarray:
        """
        Pauli-Y gate.
        
        Y = [[0, -i],
             [i, 0]]
        
        Rotates around Y-axis of Bloch sphere.
        """
        return np.array([[0, -1j], [1j, 0]], dtype=complex)
    
    @staticmethod
    def pauli_z() -> np.ndarray:
        """
        Pauli-Z gate.
        
        Z = [[1, 0],
             [0, -1]]
        
        Flips phase of |1⟩ state.
        """
        return np.array([[1, 0], [0, -1]], dtype=complex)
    
    @staticmethod
    def hadamard() -> np.ndarray:
        """
        Hadamard gate (H).
        
        H = 1/√2 * [[1, 1],
                    [1, -1]]
        
        Creates superposition: |0⟩ → (|0⟩ + |1⟩)/√2
        """
        h = 1 / np.sqrt(2)
        return np.array([[h, h], [h, -h]], dtype=complex)
    
    @staticmethod
    def phase_s() -> np.ndarray:
        """
        Phase gate (S).
        
        S = [[1, 0],
             [0, i]]
        
        S = √Z gate
        """
        return np.array([[1, 0], [0, 1j]], dtype=complex)
    
    @staticmethod
    def phase_t() -> np.ndarray:
        """
        T gate.
        
        T = [[1, 0],
             [0, e^(iπ/4)]]
        
        T = √S gate
        """
        return np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
    
    def phase_p(self, phi: float) -> np.ndarray:
        """
        Parametrized phase gate (P).
        
        P(φ) = [[1, 0],
                [0, e^(iφ)]]
        
        Args:
            phi: Phase angle in radians
            
        Returns:
            Phase gate matrix
        """
        # Security: Validate parameter
        if not isinstance(phi, (int, float)):
            raise GateValidationError(f"Phase must be numeric, got {type(phi)}")
        if np.isnan(phi) or np.isinf(phi):
            raise GateValidationError(f"Phase must be finite, got {phi}")
        
        return np.array([[1, 0], [0, np.exp(1j * phi)]], dtype=complex)
    
    def rotation_x(self, theta: float) -> np.ndarray:
        """
        Rotation around X-axis (Rx).
        
        Rx(θ) = [[cos(θ/2), -i·sin(θ/2)],
                 [-i·sin(θ/2), cos(θ/2)]]
        
        Args:
            theta: Rotation angle in radians
        """
        # Security: Validate parameter
        if not isinstance(theta, (int, float)):
            raise GateValidationError(f"Theta must be numeric, got {type(theta)}")
        
        c = np.cos(theta / 2)
        s = np.sin(theta / 2)
        return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)
    
    def rotation_y(self, theta: float) -> np.ndarray:
        """
        Rotation around Y-axis (Ry).
        
        Ry(θ) = [[cos(θ/2), -sin(θ/2)],
                 [sin(θ/2), cos(θ/2)]]
        
        Args:
            theta: Rotation angle in radians
        """
        if not isinstance(theta, (int, float)):
            raise GateValidationError(f"Theta must be numeric, got {type(theta)}")
        
        c = np.cos(theta / 2)
        s = np.sin(theta / 2)
        return np.array([[c, -s], [s, c]], dtype=complex)
    
    def rotation_z(self, theta: float) -> np.ndarray:
        """
        Rotation around Z-axis (Rz).
        
        Rz(θ) = [[e^(-iθ/2), 0],
                 [0, e^(iθ/2)]]
        
        Args:
            theta: Rotation angle in radians
        """
        if not isinstance(theta, (int, float)):
            raise GateValidationError(f"Theta must be numeric, got {type(theta)}")
        
        return np.array([
            [np.exp(-1j * theta / 2), 0],
            [0, np.exp(1j * theta / 2)]
        ], dtype=complex)
    
    # ========== Two-Qubit Gates ==========
    
    @staticmethod
    def cnot() -> np.ndarray:
        """
        Controlled-NOT gate (CNOT, CX).
        
        CNOT = [[1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]]
        
        Flips target qubit if control is |1⟩
        """
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=complex)
    
    @staticmethod
    def cz() -> np.ndarray:
        """
        Controlled-Z gate (CZ).
        
        CZ = [[1, 0, 0, 0],
              [0, 1, 0, 0],
              [0, 0, 1, 0],
              [0, 0, 0, -1]]
        
        Applies Z to target if control is |1⟩
        """
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, -1]
        ], dtype=complex)
    
    @staticmethod
    def swap() -> np.ndarray:
        """
        SWAP gate.
        
        SWAP = [[1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1]]
        
        Swaps two qubit states
        """
        return np.array([
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
        ], dtype=complex)
    
    # ========== Three-Qubit Gates ==========
    
    @staticmethod
    def toffoli() -> np.ndarray:
        """
        Toffoli gate (CCNOT, Controlled-Controlled-NOT).
        
        8x8 matrix that flips third qubit if first two are |1⟩
        """
        matrix = np.eye(8, dtype=complex)
        # Swap |110⟩ and |111⟩ (indices 6 and 7)
        matrix[6, 6] = 0
        matrix[7, 7] = 0
        matrix[6, 7] = 1
        matrix[7, 6] = 1
        return matrix
    
    @staticmethod
    def fredkin() -> np.ndarray:
        """
        Fredkin gate (CSWAP, Controlled-SWAP).
        
        8x8 matrix that swaps second and third qubits if first is |1⟩
        """
        matrix = np.eye(8, dtype=complex)
        # Swap |101⟩ and |110⟩ (indices 5 and 6)
        matrix[5, 5] = 0
        matrix[6, 6] = 0
        matrix[5, 6] = 1
        matrix[6, 5] = 1
        return matrix
    
    # ========== Gate Operations ==========
    
    def get_gate(self, name: str) -> GateDefinition:
        """
        Get a registered gate by name.
        
        Args:
            name: Gate name (case-insensitive)
            
        Returns:
            Gate definition
        """
        name_upper = name.upper()
        if name_upper not in self._gate_registry:
            raise GateValidationError(f"Unknown gate: {name}")
        
        self._log_operation("GET_GATE", {"name": name_upper})
        return self._gate_registry[name_upper]
    
    def register_custom_gate(
        self,
        name: str,
        matrix: np.ndarray,
        description: str = "Custom gate"
    ) -> None:
        """
        Register a custom gate with validation.
        
        Args:
            name: Gate name
            matrix: Unitary matrix
            description: Gate description
        """
        # Security: Validate name
        if not name or not isinstance(name, str):
            raise GateValidationError("Gate name must be non-empty string")
        if not name.isalnum():
            raise GateValidationError("Gate name must be alphanumeric")
        
        # Security: Validate matrix
        self._validate_unitarity(matrix, name)
        
        # Determine number of qubits from matrix size
        dim = matrix.shape[0]
        if dim not in [2, 4, 8, 16, 32, 64]:
            raise GateValidationError(
                f"Matrix dimension {dim} not power of 2"
            )
        num_qubits = int(np.log2(dim))
        
        gate = GateDefinition(
            name=name.upper(),
            matrix=matrix,
            num_qubits=num_qubits,
            description=description
        )
        
        self._register_gate(gate)
    
    def create_controlled_gate(
        self,
        base_gate: np.ndarray,
        num_controls: int = 1
    ) -> np.ndarray:
        """
        Create a controlled version of a gate.
        
        Args:
            base_gate: Base gate to control (2x2)
            num_controls: Number of control qubits
            
        Returns:
            Controlled gate matrix
        """
        # Security: Validate base gate
        if base_gate.shape != (2, 2):
            raise GateValidationError(
                f"Base gate must be 2x2, got {base_gate.shape}"
            )
        
        self._validate_unitarity(base_gate, "base_gate")
        
        if num_controls < 1:
            raise GateValidationError(
                f"Must have at least 1 control, got {num_controls}"
            )
        
        # Build controlled gate
        dim = 2 ** (num_controls + 1)
        identity = np.eye(dim // 2, dtype=complex)
        
        # Controlled gate: |0⟩⟨0| ⊗ I + |1⟩⟨1| ⊗ U
        controlled = np.zeros((dim, dim), dtype=complex)
        
        # Identity block for |0⟩ control states
        controlled[:dim // 2, :dim // 2] = identity
        
        # Base gate block for |1⟩ control states
        controlled[dim // 2:, dim // 2:] = base_gate
        
        return controlled
    
    def tensor_product(self, gates: List[np.ndarray]) -> np.ndarray:
        """
        Compute tensor product of multiple gates.
        
        Args:
            gates: List of gate matrices
            
        Returns:
            Tensor product of all gates
        """
        if not gates:
            raise GateValidationError("Gates list cannot be empty")
        
        result = gates[0]
        for gate in gates[1:]:
            result = np.kron(result, gate)
        
        return result
    
    def list_gates(self) -> List[str]:
        """List all registered gate names."""
        return list(self._gate_registry.keys())
    
    def get_operation_log(self) -> List[dict]:
        """Get operation log."""
        return self._operation_log.copy()
    
    def __repr__(self) -> str:
        return f"QuantumGates(registered={len(self._gate_registry)})"
