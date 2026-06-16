"""Tests for Qubit and QubitRegister classes."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ule.quantum.qubit import (
    Qubit, QubitRegister,
    QuantumSecurityError, QuantumValidationError
)
from ule.quantum.gates import QuantumGates


class TestQubit:
    """Test Qubit class."""
    
    def test_init_default(self):
        """Test qubit initialization with default values."""
        q = Qubit()
        assert q.alpha == 1.0
        assert q.beta == 0.0
        assert q.qubit_id.startswith("qubit_")
    
    def test_init_custom(self):
        """Test qubit initialization with custom values."""
        q = Qubit(alpha=0.6, beta=0.8j)
        assert np.isclose(abs(q.alpha) ** 2 + abs(q.beta) ** 2, 1.0)
    
    def test_init_not_normalized(self):
        """Test that non-normalized states raise error."""
        with pytest.raises(QuantumValidationError):
            Qubit(alpha=2.0, beta=0.0)
    
    def test_init_nan(self):
        """Test that NaN values raise error."""
        with pytest.raises(QuantumValidationError):
            Qubit(alpha=float('nan'), beta=0.0)
    
    def test_state_vector(self):
        """Test state vector property."""
        q = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
        state = q.state_vector
        assert len(state) == 2
        assert np.isclose(abs(state[0]), 1/np.sqrt(2))
        assert np.isclose(abs(state[1]), 1/np.sqrt(2))
    
    def test_probabilities(self):
        """Test probability calculation."""
        q = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
        prob_0, prob_1 = q.get_probabilities()
        assert np.isclose(prob_0, 0.5)
        assert np.isclose(prob_1, 0.5)
    
    def test_measure_zero_state(self):
        """Test measurement of |0⟩ state."""
        q = Qubit(alpha=1.0, beta=0.0)
        result = q.measure(seed=42)
        assert result == 0
        assert q.alpha == 1.0
        assert q.beta == 0.0
    
    def test_measure_one_state(self):
        """Test measurement of |1⟩ state."""
        q = Qubit(alpha=0.0, beta=1.0)
        result = q.measure(seed=42)
        assert result == 1
        assert q.alpha == 0.0
        assert q.beta == 1.0
    
    def test_apply_gate_x(self):
        """Test applying Pauli-X gate."""
        q = Qubit()  # |0⟩
        gates = QuantumGates()
        q.apply_gate(gates.pauli_x(), "X")
        assert np.isclose(abs(q.beta), 1.0)  # Should be |1⟩
    
    def test_apply_gate_h(self):
        """Test applying Hadamard gate."""
        q = Qubit()  # |0⟩
        gates = QuantumGates()
        q.apply_gate(gates.hadamard(), "H")
        prob_0, prob_1 = q.get_probabilities()
        assert np.isclose(prob_0, 0.5)
        assert np.isclose(prob_1, 0.5)
    
    def test_apply_non_unitary_gate(self):
        """Test that non-unitary gate raises error."""
        q = Qubit()
        non_unitary = np.array([[1, 1], [0, 1]], dtype=complex)
        with pytest.raises(QuantumSecurityError):
            q.apply_gate(non_unitary, "NonUnitary")
    
    def test_reset(self):
        """Test reset operation."""
        q = Qubit(alpha=0.0, beta=1.0)  # |1⟩
        q.reset()
        assert q.alpha == 1.0
        assert q.beta == 0.0
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        q = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
        d = q.to_dict()
        assert "qubit_id" in d
        assert "alpha" in d
        assert "beta" in d
        assert "probabilities" in d
    
    def test_audit_log(self):
        """Test audit logging."""
        q = Qubit()
        q.reset()
        log = q.audit_log
        assert len(log) >= 2  # INIT and RESET


class TestQubitRegister:
    """Test QubitRegister class."""
    
    def test_init_default(self):
        """Test register initialization."""
        reg = QubitRegister(num_qubits=2, initial_state="00")
        assert reg.num_qubits == 2
        assert len(reg.qubits) == 2
    
    def test_init_invalid_state(self):
        """Test initialization with invalid state."""
        with pytest.raises(QuantumValidationError):
            QubitRegister(num_qubits=2, initial_state="02")
    
    def test_init_state_length_mismatch(self):
        """Test initialization with state length mismatch."""
        with pytest.raises(QuantumValidationError):
            QubitRegister(num_qubits=3, initial_state="00")
    
    def test_get_qubit(self):
        """Test getting qubit by index."""
        reg = QubitRegister(num_qubits=3, initial_state="000")
        q = reg.get_qubit(1)
        assert isinstance(q, Qubit)
    
    def test_get_qubit_invalid_index(self):
        """Test getting qubit with invalid index."""
        reg = QubitRegister(num_qubits=2, initial_state="00")
        with pytest.raises(QuantumValidationError):
            reg.get_qubit(5)
    
    def test_state_vector(self):
        """Test multi-qubit state vector."""
        reg = QubitRegister(num_qubits=2, initial_state="00")
        state = reg.state_vector
        assert len(state) == 4  # 2^2 = 4
    
    def test_apply_gate(self):
        """Test applying gate to register."""
        reg = QubitRegister(num_qubits=2, initial_state="00")
        gates = QuantumGates()
        reg.apply_gate(gates.pauli_x(), 0)
        # First qubit should now be |1⟩
        q0 = reg.get_qubit(0)
        assert np.isclose(abs(q0.beta), 1.0)
    
    def test_measure_all(self):
        """Test measuring all qubits."""
        reg = QubitRegister(num_qubits=3, initial_state="000")
        result = reg.measure_all(seed=42)
        assert len(result) == 3
        assert all(c in "01" for c in result)
    
    def test_reset_all(self):
        """Test resetting all qubits."""
        reg = QubitRegister(num_qubits=2, initial_state="11")
        reg.reset_all()
        for q in reg.qubits:
            assert q.alpha == 1.0
            assert q.beta == 0.0
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        reg = QubitRegister(num_qubits=2, initial_state="00")
        d = reg.to_dict()
        assert d["num_qubits"] == 2
        assert "qubits" in d
        assert "state_vector_shape" in d


class TestQubitSecurity:
    """Test security features."""
    
    def test_input_validation(self):
        """Test input validation."""
        with pytest.raises(QuantumValidationError):
            Qubit(alpha="invalid", beta=0.0)
    
    def test_state_integrity(self):
        """Test state integrity verification."""
        q = Qubit()
        state_hash = q._compute_state_hash()
        assert len(state_hash) == 32
    
    def test_audit_trail(self):
        """Test audit trail completeness."""
        q = Qubit(user_id="test_user")
        gates = QuantumGates()
        q.apply_gate(gates.pauli_x(), "X")
        q.measure()
        
        log = q.audit_log
        assert len(log) >= 3
        
        # Check user_id is recorded
        for entry in log:
            assert entry.user_id == "test_user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
