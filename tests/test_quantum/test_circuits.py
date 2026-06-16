"""Tests for Quantum Circuit."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ule.quantum.circuit import (
    QuantumCircuit, CircuitOperation, CircuitResult,
    CircuitSecurityError, CircuitValidationError
)
from ule.quantum.gates import QuantumGates


class TestQuantumCircuit:
    """Test QuantumCircuit class."""
    
    def test_init(self):
        """Test circuit initialization."""
        circuit = QuantumCircuit(num_qubits=2, name="test")
        assert circuit.num_qubits == 2
        assert circuit.name == "test"
        assert circuit.depth == 0
    
    def test_init_invalid_qubits(self):
        """Test initialization with invalid qubit count."""
        with pytest.raises(CircuitValidationError):
            QuantumCircuit(num_qubits=0)
        
        with pytest.raises(CircuitValidationError):
            QuantumCircuit(num_qubits=25)  # Exceeds MAX_QUBITS
    
    def test_init_invalid_name(self):
        """Test initialization with invalid name."""
        with pytest.raises(CircuitValidationError):
            QuantumCircuit(num_qubits=2, name="")
    
    def test_add_gate_h(self):
        """Test adding Hadamard gate."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.h(0)
        assert circuit.depth == 1
    
    def test_add_gate_x(self):
        """Test adding Pauli-X gate."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.x(1)
        assert circuit.depth == 1
    
    def test_add_cnot(self):
        """Test adding CNOT gate."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.cnot(0, 1)
        assert circuit.depth == 1
    
    def test_add_gate_invalid_target(self):
        """Test adding gate with invalid target."""
        circuit = QuantumCircuit(num_qubits=2)
        with pytest.raises(CircuitValidationError):
            circuit.h(5)
    
    def test_add_gate_exceeds_limit(self):
        """Test adding too many gates."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.MAX_OPERATIONS = 10
        for _ in range(10):
            circuit.h(0)
        with pytest.raises(CircuitSecurityError):
            circuit.h(0)
    
    def test_bell_state_circuit(self):
        """Test Bell state circuit."""
        circuit = QuantumCircuit(num_qubits=2, name="Bell")
        circuit.h(0)
        circuit.cnot(0, 1)
        
        result = circuit.execute()
        
        # Bell state: (|00⟩ + |11⟩)/√2
        state = result.final_state
        assert np.isclose(abs(state[0]), 1/np.sqrt(2))  # |00⟩
        assert np.isclose(abs(state[3]), 1/np.sqrt(2))  # |11⟩
    
    def test_execute(self):
        """Test circuit execution."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.h(0)
        circuit.x(1)
        
        result = circuit.execute()
        assert isinstance(result, CircuitResult)
        assert len(result.final_state) == 4
    
    def test_execute_with_measurement(self):
        """Test circuit execution with measurement."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.h(0)
        circuit.x(1)
        
        result = circuit.execute(measure=True, seed=42)
        assert result.measurements is not None
        assert len(result.measurements) == 2
    
    def test_simulate(self):
        """Test circuit simulation with shots."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.h(0)
        circuit.h(1)
        
        counts = circuit.simulate(shots=100, seed=42)
        assert sum(counts.values()) == 100
    
    def test_simulate_invalid_shots(self):
        """Test simulation with invalid shots."""
        circuit = QuantumCircuit(num_qubits=2)
        with pytest.raises(CircuitValidationError):
            circuit.simulate(shots=0)
        
        with pytest.raises(CircuitValidationError):
            circuit.simulate(shots=200000)
    
    def test_draw(self):
        """Test circuit drawing."""
        circuit = QuantumCircuit(num_qubits=2, name="Test")
        circuit.h(0)
        circuit.cnot(0, 1)
        
        diagram = circuit.draw()
        assert "Test" in diagram
        assert "q[0]" in diagram
        assert "q[1]" in diagram
    
    def test_to_dict(self):
        """Test circuit serialization."""
        circuit = QuantumCircuit(num_qubits=2, name="Test")
        circuit.h(0)
        circuit.cnot(0, 1)
        
        d = circuit.to_dict()
        assert d["name"] == "Test"
        assert d["num_qubits"] == 2
        assert d["depth"] == 2
        assert len(d["operations"]) == 2
    
    def test_clear(self):
        """Test clearing circuit."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.h(0)
        circuit.x(1)
        assert circuit.depth == 2
        
        circuit.clear()
        assert circuit.depth == 0
    
    def test_get_state_vector(self):
        """Test getting state vector."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.h(0)
        
        state = circuit.get_state_vector()
        assert len(state) == 4
    
    def test_parametrized_gate(self):
        """Test adding parametrized gate."""
        circuit = QuantumCircuit(num_qubits=2)
        gates = QuantumGates()
        circuit.add_parametrized_gate(gates.rotation_x, 0, np.pi/4, "RX(π/4)")
        assert circuit.depth == 1
    
    def test_toffoli_gate(self):
        """Test Toffoli gate."""
        circuit = QuantumCircuit(num_qubits=3)
        circuit.toffoli(0, 1, 2)
        assert circuit.depth == 1
    
    def test_swap_gate(self):
        """Test SWAP gate."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.swap(0, 1)
        assert circuit.depth == 1
    
    def test_audit_log(self):
        """Test audit logging."""
        circuit = QuantumCircuit(num_qubits=2, name="Test", user_id="test_user")
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.execute()
        
        log = circuit.get_audit_log()
        assert len(log) > 0
        assert log[0]["user_id"] == "test_user"


class TestCircuitSecurity:
    """Test circuit security features."""
    
    def test_duplicate_target_control(self):
        """Test that qubit can't be both target and control."""
        circuit = QuantumCircuit(num_qubits=2)
        with pytest.raises(CircuitValidationError):
            circuit.add_gate("CNOT", targets=[0], controls=[0])
    
    def test_gate_mismatch(self):
        """Test gate qubit count mismatch."""
        circuit = QuantumCircuit(num_qubits=3)
        # CNOT needs 2 qubits (1 control + 1 target), but only providing 1
        with pytest.raises(CircuitValidationError):
            circuit.add_gate("CNOT", targets=[0], controls=[])
    
    def test_circuit_hash(self):
        """Test circuit hash computation."""
        circuit = QuantumCircuit(num_qubits=2)
        circuit.h(0)
        circuit.cnot(0, 1)
        
        hash1 = circuit._compute_circuit_hash()
        assert len(hash1) == 32
        
        circuit.x(1)
        hash2 = circuit._compute_circuit_hash()
        assert hash1 != hash2
    
    def test_max_qubits_limit(self):
        """Test maximum qubits limit."""
        with pytest.raises(CircuitValidationError):
            QuantumCircuit(num_qubits=25)


class TestCircuitExecution:
    """Test circuit execution scenarios."""
    
    def test_quantum_teleportation_circuit(self):
        """Test quantum teleportation circuit."""
        circuit = QuantumCircuit(num_qubits=3, name="Teleportation")
        
        # Create Bell pair between qubits 1 and 2
        circuit.h(1)
        circuit.cnot(1, 2)
        
        # Alice's Bell measurement
        circuit.cnot(0, 1)
        circuit.h(0)
        
        result = circuit.execute(initial_state="000", measure=True, seed=42)
        assert result.measurements is not None
    
    def test_superdense_coding_circuit(self):
        """Test superdense coding circuit."""
        circuit = QuantumCircuit(num_qubits=2, name="Superdense")
        
        # Create Bell pair
        circuit.h(0)
        circuit.cnot(0, 1)
        
        # Alice encodes message (e.g., 11 -> ZX)
        circuit.z(0)
        circuit.x(0)
        
        # Bob decodes
        circuit.cnot(0, 1)
        circuit.h(0)
        
        result = circuit.execute(measure=True, seed=42)
        assert result.measurements is not None
    
    def test_grover_iteration(self):
        """Test Grover iteration circuit."""
        circuit = QuantumCircuit(num_qubits=3, name="Grover")
        
        # Superposition
        for i in range(3):
            circuit.h(i)
        
        # Oracle (simplified)
        circuit.z(0)
        
        # Diffusion
        for i in range(3):
            circuit.h(i)
            circuit.x(i)
        circuit.cz(0, 1)
        for i in range(3):
            circuit.x(i)
            circuit.h(i)
        
        result = circuit.execute()
        assert len(result.final_state) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
