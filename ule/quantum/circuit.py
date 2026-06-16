"""
Quantum Circuit Builder
=======================
Build, optimize, and execute quantum circuits with security validation.

Features:
- Circuit construction with gate sequencing
- Circuit optimization
- Circuit visualization (text-based)
- State vector simulation
- Audit logging for all operations
"""

import numpy as np
import hashlib
import json
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .qubit import Qubit, QubitRegister, QuantumSecurityError, QuantumValidationError
from .gates import QuantumGates, GateDefinition

logger = logging.getLogger(__name__)


@dataclass
class CircuitOperation:
    """Represents a single operation in a quantum circuit."""
    gate_name: str
    gate_matrix: np.ndarray
    targets: List[int]
    controls: List[int] = field(default_factory=list)
    parameters: Optional[Dict] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class CircuitResult:
    """Result of circuit execution."""
    final_state: np.ndarray
    measurements: Optional[str] = None
    num_operations: int = 0
    execution_time_ms: float = 0.0
    state_hash: str = ""


class CircuitSecurityError(Exception):
    """Exception raised for circuit security violations."""
    pass


class CircuitValidationError(Exception):
    """Exception raised for circuit validation errors."""
    pass


class QuantumCircuit:
    """
    Quantum circuit builder and executor with security features.
    
    Attributes:
        num_qubits: Number of qubits in the circuit
        operations: List of gate operations
        name: Circuit name
    """
    
    MAX_QUBITS = 20  # Maximum qubits for simulation
    MAX_OPERATIONS = 10000  # Maximum operations per circuit
    
    def __init__(
        self,
        num_qubits: int,
        name: str = "circuit",
        user_id: Optional[str] = None
    ):
        """
        Initialize quantum circuit.
        
        Args:
            num_qubits: Number of qubits
            name: Circuit name
            user_id: User ID for audit logging
        """
        # Security: Validate qubit count
        if not isinstance(num_qubits, int) or num_qubits < 1:
            raise CircuitValidationError(
                f"Number of qubits must be positive integer, got {num_qubits}"
            )
        if num_qubits > self.MAX_QUBITS:
            raise CircuitValidationError(
                f"Maximum {self.MAX_QUBITS} qubits supported, got {num_qubits}"
            )
        
        # Security: Validate name
        if not name or not isinstance(name, str):
            raise CircuitValidationError("Circuit name must be non-empty string")
        if len(name) > 100:
            raise CircuitValidationError("Circuit name must be < 100 characters")
        
        self._num_qubits = num_qubits
        self._name = name
        self._user_id = user_id
        self._operations: List[CircuitOperation] = []
        self._audit_log: List[dict] = []
        self._gates = QuantumGates(user_id=user_id)
        
        self._log_operation("CIRCUIT_INIT", {
            "num_qubits": num_qubits,
            "name": name
        })
    
    def _log_operation(self, operation: str, details: dict) -> None:
        """Log circuit operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "user_id": self._user_id
        })
    
    def _compute_circuit_hash(self) -> str:
        """Compute hash of circuit for integrity verification."""
        circuit_data = json.dumps([
            {
                "gate": op.gate_name,
                "targets": op.targets,
                "controls": op.controls
            }
            for op in self._operations
        ], sort_keys=True)
        return hashlib.sha256(circuit_data.encode()).hexdigest()[:32]
    
    @property
    def num_qubits(self) -> int:
        """Get number of qubits."""
        return self._num_qubits
    
    @property
    def operations(self) -> List[CircuitOperation]:
        """Get list of operations."""
        return self._operations.copy()
    
    @property
    def name(self) -> str:
        """Get circuit name."""
        return self._name
    
    @property
    def depth(self) -> int:
        """Get circuit depth (number of operations)."""
        return len(self._operations)
    
    def _validate_qubit_indices(self, indices: List[int]) -> None:
        """Security: Validate qubit indices are within bounds."""
        for idx in indices:
            if not isinstance(idx, int):
                raise CircuitValidationError(
                    f"Qubit index must be integer, got {type(idx)}"
                )
            if idx < 0 or idx >= self._num_qubits:
                raise CircuitValidationError(
                    f"Qubit index {idx} out of range [0, {self._num_qubits - 1}]"
                )
    
    def _validate_no_duplicate_targets(
        self,
        targets: List[int],
        controls: List[int]
    ) -> None:
        """Security: Ensure no qubit is both target and control."""
        all_indices = set(targets) | set(controls)
        if len(all_indices) != len(targets) + len(controls):
            raise CircuitValidationError(
                "Qubit cannot be both target and control"
            )
    
    def _check_operation_limit(self) -> None:
        """Security: Check operation limit not exceeded."""
        if len(self._operations) >= self.MAX_OPERATIONS:
            raise CircuitSecurityError(
                f"Maximum {self.MAX_OPERATIONS} operations exceeded"
            )
    
    # ========== Gate Operations ==========
    
    def add_gate(
        self,
        gate_name: str,
        targets: Union[int, List[int]],
        controls: Optional[Union[int, List[int]]] = None,
        parameters: Optional[Dict] = None
    ) -> "QuantumCircuit":
        """
        Add a gate operation to the circuit.
        
        Args:
            gate_name: Name of the gate
            targets: Target qubit(s)
            controls: Control qubit(s) for controlled gates
            parameters: Gate parameters (for parametrized gates)
            
        Returns:
            Self for method chaining
        """
        self._check_operation_limit()
        
        # Normalize to lists
        if isinstance(targets, int):
            targets = [targets]
        if isinstance(controls, int):
            controls = [controls]
        elif controls is None:
            controls = []
        
        # Security: Validate indices
        self._validate_qubit_indices(targets + controls)
        self._validate_no_duplicate_targets(targets, controls)
        
        # Get gate definition
        gate_def = self._gates.get_gate(gate_name)
        
        # Security: Validate gate matches expected qubits
        expected_qubits = gate_def.num_qubits
        actual_qubits = len(targets) + len(controls)
        if expected_qubits != actual_qubits:
            raise CircuitValidationError(
                f"Gate {gate_name} expects {expected_qubits} qubits, "
                f"got {actual_qubits} ({len(targets)} targets, {len(controls)} controls)"
            )
        
        # Create operation
        operation = CircuitOperation(
            gate_name=gate_name.upper(),
            gate_matrix=gate_def.matrix.copy(),
            targets=targets,
            controls=controls,
            parameters=parameters
        )
        
        self._operations.append(operation)
        self._log_operation("ADD_GATE", {
            "gate": gate_name.upper(),
            "targets": targets,
            "controls": controls
        })
        
        return self
    
    def add_parametrized_gate(
        self,
        gate_func: callable,
        target: int,
        param: float,
        gate_name: str
    ) -> "QuantumCircuit":
        """
        Add a parametrized gate to the circuit.
        
        Args:
            gate_func: Function that returns gate matrix given parameter
            target: Target qubit
            param: Gate parameter (e.g., rotation angle)
            gate_name: Name for the gate
            
        Returns:
            Self for method chaining
        """
        self._check_operation_limit()
        
        # Security: Validate target
        self._validate_qubit_indices([target])
        
        # Security: Validate parameter
        if not isinstance(param, (int, float)):
            raise CircuitValidationError(
                f"Gate parameter must be numeric, got {type(param)}"
            )
        if np.isnan(param) or np.isinf(param):
            raise CircuitValidationError(
                f"Gate parameter must be finite, got {param}"
            )
        
        # Get gate matrix
        matrix = gate_func(param)
        
        # Security: Validate unitarity
        self._gates._validate_unitarity(matrix, gate_name)
        
        operation = CircuitOperation(
            gate_name=gate_name.upper(),
            gate_matrix=matrix,
            targets=[target],
            controls=[],
            parameters={"param": param}
        )
        
        self._operations.append(operation)
        self._log_operation("ADD_PARAMETRIZED_GATE", {
            "gate": gate_name,
            "target": target,
            "param": param
        })
        
        return self
    
    # ========== Convenience Methods ==========

    def h(self, target: int) -> "QuantumCircuit":
        """Apply Hadamard gate."""
        return self.add_gate("HADAMARD", target)

    def x(self, target: int) -> "QuantumCircuit":
        """Apply Pauli-X gate."""
        return self.add_gate("X", target)

    def y(self, target: int) -> "QuantumCircuit":
        """Apply Pauli-Y gate."""
        return self.add_gate("Y", target)

    def z(self, target: int) -> "QuantumCircuit":
        """Apply Pauli-Z gate."""
        return self.add_gate("Z", target)

    def s(self, target: int) -> "QuantumCircuit":
        """Apply S gate."""
        return self.add_gate("S", target)

    def t(self, target: int) -> "QuantumCircuit":
        """Apply T gate."""
        return self.add_gate("T", target)
    
    def rx(self, target: int, theta: float) -> "QuantumCircuit":
        """Apply Rx rotation gate."""
        return self.add_parametrized_gate(
            self._gates.rotation_x, target, theta, f"RX({theta})"
        )
    
    def ry(self, target: int, theta: float) -> "QuantumCircuit":
        """Apply Ry rotation gate."""
        return self.add_parametrized_gate(
            self._gates.rotation_y, target, theta, f"RY({theta})"
        )
    
    def rz(self, target: int, theta: float) -> "QuantumCircuit":
        """Apply Rz rotation gate."""
        return self.add_parametrized_gate(
            self._gates.rotation_z, target, theta, f"RZ({theta})"
        )
    
    def cnot(self, control: int, target: int) -> "QuantumCircuit":
        """Apply CNOT gate."""
        return self.add_gate("CNOT", target, control)
    
    def cx(self, control: int, target: int) -> "QuantumCircuit":
        """Apply CNOT gate (alias)."""
        return self.cnot(control, target)
    
    def cz(self, control: int, target: int) -> "QuantumCircuit":
        """Apply CZ gate."""
        return self.add_gate("CZ", target, control)
    
    def swap(self, qubit1: int, qubit2: int) -> "QuantumCircuit":
        """Apply SWAP gate."""
        return self.add_gate("SWAP", [qubit1, qubit2])
    
    def toffoli(
        self,
        control1: int,
        control2: int,
        target: int
    ) -> "QuantumCircuit":
        """Apply Toffoli (CCNOT) gate."""
        return self.add_gate("TOFFOLI", target, [control1, control2])
    
    def barrier(self) -> "QuantumCircuit":
        """Add a barrier (visual separator, no operation)."""
        self._log_operation("BARRIER", {})
        return self
    
    def measure(self, qubits: Optional[Union[int, List[int]]] = None) -> "QuantumCircuit":
        """
        Add measurement operation.
        
        Args:
            qubits: Qubits to measure (default: all)
        """
        if qubits is None:
            qubits = list(range(self._num_qubits))
        elif isinstance(qubits, int):
            qubits = [qubits]
        
        self._validate_qubit_indices(qubits)
        self._log_operation("MEASURE", {"qubits": qubits})
        return self
    
    # ========== Circuit Execution ==========
    
    def execute(
        self,
        initial_state: Optional[str] = None,
        measure: bool = False,
        seed: Optional[int] = None
    ) -> CircuitResult:
        """
        Execute the circuit.
        
        Args:
            initial_state: Initial state string (e.g., "00", "01")
            measure: Whether to measure at the end
            seed: Random seed for measurement
            
        Returns:
            CircuitResult with final state and measurements
        """
        import time
        start_time = time.time()
        
        # Initialize register
        if initial_state is None:
            initial_state = "0" * self._num_qubits
        
        register = QubitRegister(
            num_qubits=self._num_qubits,
            initial_state=initial_state,
            user_id=self._user_id
        )
        
        # Execute operations
        for op in self._operations:
            if op.gate_name == "MEASURE":
                continue  # Handle measurement separately
            
            if len(op.controls) == 0:
                # Single-qubit gate
                for target in op.targets:
                    register.apply_gate(op.gate_matrix, target, op.gate_name)
            elif len(op.controls) == 1:
                # Two-qubit controlled gate
                register.apply_two_qubit_gate(
                    op.gate_matrix,
                    op.controls[0],
                    op.targets[0],
                    op.gate_name
                )
            else:
                # Multi-qubit gate (simplified handling)
                logger.warning(
                    f"Multi-control gate {op.gate_name} not fully supported"
                )
        
        # Measurement
        measurements = None
        if measure:
            measurements = register.measure_all(seed=seed)
        
        execution_time = (time.time() - start_time) * 1000
        
        result = CircuitResult(
            final_state=register.state_vector,
            measurements=measurements,
            num_operations=len(self._operations),
            execution_time_ms=execution_time,
            state_hash=hashlib.sha256(
                register.state_vector.tobytes()
            ).hexdigest()[:32]
        )
        
        self._log_operation("EXECUTE", {
            "initial_state": initial_state,
            "measure": measure,
            "result_hash": result.state_hash
        })
        
        return result
    
    def get_state_vector(
        self,
        initial_state: Optional[str] = None
    ) -> np.ndarray:
        """
        Get the state vector after executing the circuit.
        
        Args:
            initial_state: Initial state string
            
        Returns:
            Final state vector
        """
        result = self.execute(initial_state=initial_state)
        return result.final_state
    
    def simulate(
        self,
        initial_state: Optional[str] = None,
        shots: int = 1024,
        seed: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Simulate the circuit with multiple shots.

        Args:
            initial_state: Initial state (default: all zeros)
            shots: Number of simulation runs
            seed: Random seed

        Returns:
            Dictionary of measurement outcomes and counts
        """
        # Default to all zeros if not specified
        if initial_state is None:
            initial_state = "0" * self._num_qubits
            
        # Security: Validate shots
        if not isinstance(shots, int) or shots < 1:
            raise CircuitValidationError(
                f"Shots must be positive integer, got {shots}"
            )
        if shots > 100000:
            raise CircuitValidationError(
                f"Maximum 100000 shots supported, got {shots}"
            )
        
        counts: Dict[str, int] = {}
        
        for i in range(shots):
            result = self.execute(
                initial_state=initial_state,
                measure=True,
                seed=seed + i if seed else None
            )
            outcome = result.measurements or "0" * self._num_qubits
            counts[outcome] = counts.get(outcome, 0) + 1
        
        self._log_operation("SIMULATE", {
            "shots": shots,
            "outcomes": len(counts)
        })
        
        return counts
    
    # ========== Circuit Visualization ==========
    
    def draw(self, max_width: int = 80) -> str:
        """
        Draw circuit as ASCII art.
        
        Args:
            max_width: Maximum line width
            
        Returns:
            ASCII representation of circuit
        """
        lines = []
        lines.append(f"Circuit: {self._name}")
        lines.append(f"Qubits: {self._num_qubits}")
        lines.append(f"Depth: {self.depth}")
        lines.append("-" * min(50, max_width))
        
        # Draw each qubit line
        for q in range(self._num_qubits):
            line = f"q[{q}]: |0⟩"
            for op in self._operations:
                if q in op.targets:
                    if len(op.controls) == 0:
                        line += f"──[{op.gate_name}]──"
                    else:
                        line += f"──[●]──"  # Target of controlled gate
                elif q in op.controls:
                    line += f"──[○]──"  # Control
                else:
                    line += "───────"
            lines.append(line)
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Serialize circuit to dictionary."""
        return {
            "name": self._name,
            "num_qubits": self._num_qubits,
            "depth": self.depth,
            "operations": [
                {
                    "gate": op.gate_name,
                    "targets": op.targets,
                    "controls": op.controls,
                    "parameters": op.parameters
                }
                for op in self._operations
            ],
            "circuit_hash": self._compute_circuit_hash(),
            "audit_count": len(self._audit_log)
        }
    
    def clear(self) -> "QuantumCircuit":
        """Clear all operations from the circuit."""
        self._operations = []
        self._log_operation("CLEAR", {})
        return self
    
    def get_audit_log(self) -> List[dict]:
        """Get audit log."""
        return self._audit_log.copy()
    
    def __repr__(self) -> str:
        return (
            f"QuantumCircuit(name={self._name}, "
            f"qubits={self._num_qubits}, depth={self.depth})"
        )
