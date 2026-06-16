"""
Qubit Representation and Management
===================================
Core quantum bit (qubit) implementation with security features.

A qubit is the fundamental unit of quantum information:
|ψ⟩ = α|0⟩ + β|1⟩
where α and β are complex amplitudes with |α|² + |β|² = 1
"""

import numpy as np
import hashlib
import json
import logging
from typing import Optional, Tuple, List, Union
from dataclasses import dataclass, field
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class QuantumSecurityError(Exception):
    """Exception raised for quantum security violations."""
    pass


class QuantumValidationError(Exception):
    """Exception raised for quantum state validation errors."""
    pass


@dataclass
class QuantumStateAudit:
    """Audit record for quantum state operations."""
    operation: str
    timestamp: str
    state_hash: str
    parameters: dict = field(default_factory=dict)
    user_id: Optional[str] = None


class Qubit:
    """
    Single qubit representation with security features.
    
    Attributes:
        alpha: Complex amplitude for |0⟩ state
        beta: Complex amplitude for |1⟩ state
        qubit_id: Unique identifier for the qubit
        created_at: Creation timestamp
        audit_log: List of operations performed
    """
    
    EPSILON = 1e-10  # Tolerance for normalization checks
    
    def __init__(
        self,
        alpha: complex = 1.0,
        beta: complex = 0.0,
        qubit_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize a qubit with security validation.
        
        Args:
            alpha: Complex amplitude for |0⟩ (default: 1.0, pure |0⟩ state)
            beta: Complex amplitude for |1⟩ (default: 0.0)
            qubit_id: Optional unique identifier
            user_id: Optional user ID for audit logging
        """
        # Security: Validate inputs
        self._validate_complex(alpha, "alpha")
        self._validate_complex(beta, "beta")
        
        # Security: Check normalization
        self._validate_normalization(alpha, beta)
        
        self._alpha = complex(alpha)
        self._beta = complex(beta)
        self._qubit_id = qubit_id or self._generate_qubit_id()
        self._created_at = datetime.utcnow().isoformat()
        self._user_id = user_id
        self._audit_log: List[QuantumStateAudit] = []
        
        # Record creation
        self._log_operation("INIT", {"alpha": str(alpha), "beta": str(beta)})
    
    @staticmethod
    def _validate_complex(value: complex, param_name: str) -> None:
        """Security: Validate complex number input."""
        if not isinstance(value, (complex, int, float)):
            raise QuantumValidationError(
                f"{param_name} must be a complex number, got {type(value)}"
            )
        # Check for NaN or Inf
        real_val = value.real if isinstance(value, complex) else value
        imag_val = value.imag if isinstance(value, complex) else 0.0
        
        if np.isnan(real_val) or np.isnan(imag_val):
            raise QuantumValidationError(
                f"{param_name} contains NaN values"
            )
        if np.isinf(real_val) or np.isinf(imag_val):
            raise QuantumValidationError(
                f"{param_name} contains Inf values"
            )
    
    @staticmethod
    def _validate_normalization(alpha: complex, beta: complex) -> None:
        """Security: Validate qubit state normalization (|α|² + |β|² = 1)."""
        norm = abs(alpha) ** 2 + abs(beta) ** 2
        if abs(norm - 1.0) > Qubit.EPSILON:
            raise QuantumValidationError(
                f"Qubit state not normalized: |α|² + |β|² = {norm}, expected 1.0"
            )
    
    @staticmethod
    def _generate_qubit_id() -> str:
        """Generate a unique qubit identifier."""
        timestamp = datetime.utcnow().isoformat()
        random_data = np.random.random(16).tobytes()
        data = f"{timestamp}{random_data}".encode()
        return f"qubit_{hashlib.sha256(data).hexdigest()[:16]}"
    
    def _compute_state_hash(self) -> str:
        """Compute hash of current quantum state for integrity verification."""
        state_data = f"{self._alpha}{self._beta}".encode()
        return hashlib.sha256(state_data).hexdigest()[:32]
    
    def _log_operation(
        self,
        operation: str,
        parameters: Optional[dict] = None
    ) -> None:
        """Log quantum operation for audit trail."""
        audit = QuantumStateAudit(
            operation=operation,
            timestamp=datetime.utcnow().isoformat(),
            state_hash=self._compute_state_hash(),
            parameters=parameters or {},
            user_id=self._user_id
        )
        self._audit_log.append(audit)
    
    @property
    def alpha(self) -> complex:
        """Get amplitude for |0⟩ state."""
        return self._alpha
    
    @property
    def beta(self) -> complex:
        """Get amplitude for |1⟩ state."""
        return self._beta
    
    @property
    def qubit_id(self) -> str:
        """Get qubit unique identifier."""
        return self._qubit_id
    
    @property
    def state_vector(self) -> np.ndarray:
        """Get state vector as numpy array."""
        return np.array([self._alpha, self._beta], dtype=complex)
    
    @property
    def audit_log(self) -> List[QuantumStateAudit]:
        """Get audit log of operations."""
        return self._audit_log.copy()
    
    def get_probabilities(self) -> Tuple[float, float]:
        """
        Get measurement probabilities for |0⟩ and |1⟩.
        
        Returns:
            Tuple of (prob_0, prob_1) where prob_0 + prob_1 = 1
        """
        prob_0 = abs(self._alpha) ** 2
        prob_1 = abs(self._beta) ** 2
        return (prob_0, prob_1)
    
    def measure(self, seed: Optional[int] = None) -> int:
        """
        Measure the qubit (collapses to |0⟩ or |1⟩).
        
        Args:
            seed: Optional random seed for reproducibility
            
        Returns:
            0 or 1 based on measurement outcome
        """
        if seed is not None:
            np.random.seed(seed)
        
        prob_0, prob_1 = self.get_probabilities()
        
        # Security: Validate probabilities sum to 1
        if abs(prob_0 + prob_1 - 1.0) > self.EPSILON:
            raise QuantumSecurityError(
                f"Invalid probability distribution: {prob_0} + {prob_1} != 1"
            )
        
        # Perform measurement
        outcome = 0 if np.random.random() < prob_0 else 1
        
        # Collapse state
        if outcome == 0:
            self._alpha = 1.0
            self._beta = 0.0
        else:
            self._alpha = 0.0
            self._beta = 1.0
        
        self._log_operation("MEASURE", {"outcome": outcome, "seed": seed})
        return outcome
    
    def apply_gate(self, matrix: np.ndarray, gate_name: str = "UNKNOWN") -> "Qubit":
        """
        Apply a unitary gate to the qubit.
        
        Args:
            matrix: 2x2 unitary matrix
            gate_name: Name of the gate for audit logging
            
        Returns:
            Self for method chaining
        """
        # Security: Validate matrix
        if not isinstance(matrix, np.ndarray):
            raise QuantumValidationError("Gate matrix must be numpy array")
        if matrix.shape != (2, 2):
            raise QuantumValidationError(f"Gate matrix must be 2x2, got {matrix.shape}")
        
        # Security: Validate unitarity (U†U = I)
        identity = np.eye(2, dtype=complex)
        product = matrix.conj().T @ matrix
        if not np.allclose(product, identity, atol=self.EPSILON):
            raise QuantumSecurityError(
                f"Gate matrix is not unitary: {gate_name}"
            )
        
        # Apply gate
        new_state = matrix @ self.state_vector
        
        # Security: Validate result is normalized
        new_alpha, new_beta = new_state[0], new_state[1]
        self._validate_normalization(new_alpha, new_beta)
        
        self._alpha = new_alpha
        self._beta = new_beta
        
        self._log_operation(f"GATE_{gate_name}", {"matrix_shape": str(matrix.shape)})
        return self
    
    def reset(self) -> "Qubit":
        """Reset qubit to |0⟩ state."""
        self._alpha = 1.0
        self._beta = 0.0
        self._log_operation("RESET", {})
        return self
    
    def to_dict(self) -> dict:
        """Serialize qubit state to dictionary."""
        return {
            "qubit_id": self._qubit_id,
            "alpha": {"real": self._alpha.real, "imag": self._alpha.imag},
            "beta": {"real": self._beta.real, "imag": self._beta.imag},
            "created_at": self._created_at,
            "user_id": self._user_id,
            "probabilities": self.get_probabilities()
        }
    
    def __repr__(self) -> str:
        return (
            f"Qubit(id={self._qubit_id}, "
            f"α={self._alpha:.4f}, β={self._beta:.4f}, "
            f"P(0)={self.get_probabilities()[0]:.4f})"
        )


class QubitRegister:
    """
    Multi-qubit register with security features.
    
    Supports tensor product states for multiple qubits.
    """
    
    def __init__(
        self,
        num_qubits: int,
        initial_state: str = "0",
        user_id: Optional[str] = None
    ):
        """
        Initialize a multi-qubit register.
        
        Args:
            num_qubits: Number of qubits in the register
            initial_state: Initial state string (e.g., "00", "01", "110")
            user_id: Optional user ID for audit logging
        """
        # Security: Validate number of qubits
        if not isinstance(num_qubits, int) or num_qubits < 1:
            raise QuantumValidationError(
                f"Number of qubits must be positive integer, got {num_qubits}"
            )
        if num_qubits > 20:
            raise QuantumValidationError(
                f"Maximum 20 qubits supported, got {num_qubits}"
            )
        
        # Security: Validate initial state
        if not all(c in "01" for c in initial_state):
            raise QuantumValidationError(
                f"Initial state must contain only 0s and 1s, got {initial_state}"
            )
        if len(initial_state) != num_qubits:
            raise QuantumValidationError(
                f"Initial state length ({len(initial_state)}) != num_qubits ({num_qubits})"
            )
        
        self._num_qubits = num_qubits
        self._user_id = user_id
        self._qubits: List[Qubit] = []
        self._audit_log: List[QuantumStateAudit] = []
        self._state_vector: Optional[np.ndarray] = None  # Store full state for entanglement
        self._is_entangled = False

        # Initialize qubits based on initial state
        for i, bit in enumerate(initial_state):
            if bit == "0":
                qubit = Qubit(alpha=1.0, beta=0.0, user_id=user_id)
            else:
                qubit = Qubit(alpha=0.0, beta=1.0, user_id=user_id)
            self._qubits.append(qubit)
        
        # Initialize state vector
        self._initialize_state_vector(initial_state)

        self._log_operation("REGISTER_INIT", {
            "num_qubits": num_qubits,
            "initial_state": initial_state
        })
    
    def _log_operation(
        self,
        operation: str,
        parameters: Optional[dict] = None
    ) -> None:
        """Log register operation."""
        audit = QuantumStateAudit(
            operation=operation,
            timestamp=datetime.utcnow().isoformat(),
            state_hash=self._compute_state_hash(),
            parameters=parameters or {},
            user_id=self._user_id
        )
        self._audit_log.append(audit)
    
    def _compute_state_hash(self) -> str:
        """Compute hash of register state."""
        if self._is_entangled and self._state_vector is not None:
            state_data = self._state_vector.tobytes()
            return hashlib.sha256(state_data).hexdigest()[:32]
        else:
            state_data = "".join(str(q.to_dict()) for q in self._qubits)
            return hashlib.sha256(state_data.encode()).hexdigest()[:32]

    def _initialize_state_vector(self, initial_state: str) -> None:
        """Initialize the state vector from initial state string."""
        n = self._num_qubits
        dim = 2 ** n
        self._state_vector = np.zeros(dim, dtype=complex)
        
        # Set the amplitude for the initial state to 1
        initial_index = int(initial_state, 2)
        self._state_vector[initial_index] = 1.0

    @property
    def num_qubits(self) -> int:
        """Get number of qubits."""
        return self._num_qubits

    @property
    def qubits(self) -> List[Qubit]:
        """Get list of qubits."""
        return self._qubits.copy()

    @property
    def state_vector(self) -> np.ndarray:
        """
        Get full state vector (tensor product of all qubits).

        Returns:
            2^n dimensional state vector
        """
        if self._is_entangled and self._state_vector is not None:
            return self._state_vector.copy()
        
        # Compute from individual qubits (product state)
        state = self._qubits[0].state_vector
        for qubit in self._qubits[1:]:
            state = np.kron(state, qubit.state_vector)
        return state
    
    def get_qubit(self, index: int) -> Qubit:
        """
        Get qubit at specified index with bounds checking.
        
        Args:
            index: Qubit index (0-based)
            
        Returns:
            Qubit at specified index
        """
        # Security: Validate index
        if not isinstance(index, int):
            raise QuantumValidationError(f"Index must be integer, got {type(index)}")
        if index < 0 or index >= self._num_qubits:
            raise QuantumValidationError(
                f"Qubit index {index} out of range [0, {self._num_qubits - 1}]"
            )
        return self._qubits[index]
    
    def apply_gate(
        self,
        matrix: np.ndarray,
        target: int,
        gate_name: str = "UNKNOWN"
    ) -> "QubitRegister":
        """
        Apply single-qubit gate to specified qubit.

        Args:
            matrix: 2x2 unitary matrix
            target: Target qubit index
            gate_name: Name of the gate

        Returns:
            Self for method chaining
        """
        # If entangled, update state vector directly
        if self._is_entangled and self._state_vector is not None:
            self._apply_single_qubit_gate_to_state_vector(matrix, target, gate_name)
        else:
            qubit = self.get_qubit(target)
            qubit.apply_gate(matrix, gate_name)
            # Update state vector
            self._state_vector = self.state_vector
        
        self._log_operation(f"GATE_{gate_name}", {"target": target})
        return self

    def _apply_single_qubit_gate_to_state_vector(
        self,
        matrix: np.ndarray,
        target: int,
        gate_name: str
    ) -> None:
        """Apply single-qubit gate to the full state vector."""
        n = self._num_qubits
        dim = 2 ** n
        
        # Build the full operator: I ⊗ I ⊗ ... ⊗ U ⊗ ... ⊗ I
        # where U is at position target
        
        # For efficiency, we'll apply the gate directly to the state vector
        new_state = np.zeros(dim, dtype=complex)
        
        for i in range(dim):
            # Extract the target qubit's value from the index
            target_bit = (i >> (n - 1 - target)) & 1
            other_bits = i & ~(1 << (n - 1 - target))
            
            # Apply the gate
            for new_bit in range(2):
                new_i = other_bits | (new_bit << (n - 1 - target))
                new_state[new_i] += matrix[new_bit, target_bit] * self._state_vector[i]
        
        self._state_vector = new_state
    
    def apply_two_qubit_gate(
        self,
        matrix: np.ndarray,
        control: int,
        target: int,
        gate_name: str = "UNKNOWN"
    ) -> "QubitRegister":
        """
        Apply two-qubit gate (entangling operation).

        Args:
            matrix: 4x4 unitary matrix
            control: Control qubit index
            target: Target qubit index
            gate_name: Name of the gate

        Returns:
            Self for method chaining
        """
        # Security: Validate indices
        if control == target:
            raise QuantumValidationError(
                f"Control and target must be different, got {control}"
            )

        self.get_qubit(control)
        self.get_qubit(target)

        # Security: Validate matrix
        if not isinstance(matrix, np.ndarray):
            raise QuantumValidationError("Gate matrix must be numpy array")
        if matrix.shape != (4, 4):
            raise QuantumValidationError(f"Matrix must be 4x4, got {matrix.shape}")

        # Apply the gate to the state vector
        self._apply_two_qubit_gate_to_state_vector(matrix, control, target, gate_name)
        
        # Mark as entangled
        self._is_entangled = True
        
        self._log_operation(f"GATE_{gate_name}", {
            "control": control,
            "target": target
        })
        return self

    def _apply_two_qubit_gate_to_state_vector(
        self,
        matrix: np.ndarray,
        control: int,
        target: int,
        gate_name: str
    ) -> None:
        """Apply two-qubit gate to the full state vector."""
        n = self._num_qubits
        dim = 2 ** n
        
        new_state = np.zeros(dim, dtype=complex)
        
        for i in range(dim):
            # Extract control and target bits
            ctrl_bit = (i >> (n - 1 - control)) & 1
            tgt_bit = (i >> (n - 1 - target)) & 1
            
            # Get the combined index for the 2-qubit subspace
            combined = (ctrl_bit << 1) | tgt_bit
            
            # Get other bits (not control or target)
            other_mask = ~((1 << (n - 1 - control)) | (1 << (n - 1 - target)))
            other_bits = i & other_mask
            
            # Apply the 4x4 matrix to the 2-qubit subspace
            for new_combined in range(4):
                new_ctrl = (new_combined >> 1) & 1
                new_tgt = new_combined & 1
                
                new_i = other_bits | (new_ctrl << (n - 1 - control)) | (new_tgt << (n - 1 - target))
                new_state[new_i] += matrix[new_combined, combined] * self._state_vector[i]
        
        self._state_vector = new_state
    
    def measure_all(
        self,
        seed: Optional[int] = None
    ) -> str:
        """
        Measure all qubits in the register.

        Args:
            seed: Optional random seed

        Returns:
            Measurement result as bit string
        """
        if seed is not None:
            np.random.seed(seed)

        # If entangled, sample from the full state vector
        if self._is_entangled and self._state_vector is not None:
            # Calculate probabilities for each basis state
            probs = np.abs(self._state_vector) ** 2
            
            # Sample from the distribution
            n = self._num_qubits
            dim = 2 ** n
            outcome_index = np.random.choice(dim, p=probs)
            
            # Convert index to bit string
            result = format(outcome_index, f'0{n}b')
            
            # Collapse the state to the measured state
            self._state_vector = np.zeros(dim, dtype=complex)
            self._state_vector[outcome_index] = 1.0
            
            # Also update individual qubits to match
            for i, bit in enumerate(result):
                if bit == '0':
                    self._qubits[i]._alpha = 1.0
                    self._qubits[i]._beta = 0.0
                else:
                    self._qubits[i]._alpha = 0.0
                    self._qubits[i]._beta = 1.0
        else:
            # Measure individual qubits (product state)
            result = ""
            for i, qubit in enumerate(self._qubits):
                bit = qubit.measure()
                result += str(bit)

        self._log_operation("MEASURE_ALL", {"result": result, "seed": seed})
        return result
    
    def reset_all(self) -> "QubitRegister":
        """Reset all qubits to |0⟩ state."""
        for qubit in self._qubits:
            qubit.reset()
        self._log_operation("RESET_ALL", {})
        return self
    
    def to_dict(self) -> dict:
        """Serialize register to dictionary."""
        return {
            "num_qubits": self._num_qubits,
            "qubits": [q.to_dict() for q in self._qubits],
            "state_vector_shape": self.state_vector.shape,
            "audit_count": len(self._audit_log)
        }
    
    def __repr__(self) -> str:
        probs = [q.get_probabilities()[0] for q in self._qubits]
        return f"QubitRegister(n={self._num_qubits}, P(0)={probs})"
