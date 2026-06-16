"""Tests for Quantum Gates."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ule.quantum.gates import (
    QuantumGates, GateDefinition,
    GateSecurityError, GateValidationError
)


class TestQuantumGates:
    """Test QuantumGates class."""
    
    def test_init(self):
        """Test gates library initialization."""
        gates = QuantumGates()
        assert len(gates.list_gates()) > 0
    
    def test_get_gate(self):
        """Test getting a gate by name."""
        gates = QuantumGates()
        gate = gates.get_gate("HADAMARD")
        assert gate.name == "HADAMARD"
        assert gate.num_qubits == 1
    
    def test_get_unknown_gate(self):
        """Test getting unknown gate raises error."""
        gates = QuantumGates()
        with pytest.raises(GateValidationError):
            gates.get_gate("UNKNOWN")
    
    def test_pauli_i(self):
        """Test Identity gate."""
        I = QuantumGates.pauli_i()
        assert I.shape == (2, 2)
        assert np.allclose(I, np.eye(2))
    
    def test_pauli_x(self):
        """Test Pauli-X gate."""
        X = QuantumGates.pauli_x()
        assert X.shape == (2, 2)
        # X|0⟩ = |1⟩
        result = X @ np.array([1, 0], dtype=complex)
        assert np.allclose(result, np.array([0, 1], dtype=complex))
    
    def test_pauli_y(self):
        """Test Pauli-Y gate."""
        Y = QuantumGates.pauli_y()
        assert Y.shape == (2, 2)
        # Verify unitarity
        assert np.allclose(Y.conj().T @ Y, np.eye(2))
    
    def test_pauli_z(self):
        """Test Pauli-Z gate."""
        Z = QuantumGates.pauli_z()
        assert Z.shape == (2, 2)
        # Z|1⟩ = -|1⟩
        result = Z @ np.array([0, 1], dtype=complex)
        assert np.allclose(result, np.array([0, -1], dtype=complex))
    
    def test_hadamard(self):
        """Test Hadamard gate."""
        H = QuantumGates.hadamard()
        assert H.shape == (2, 2)
        # H|0⟩ = (|0⟩ + |1⟩)/√2
        result = H @ np.array([1, 0], dtype=complex)
        expected = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)
        assert np.allclose(result, expected)
    
    def test_phase_s(self):
        """Test S gate."""
        S = QuantumGates.phase_s()
        assert S.shape == (2, 2)
        # S^2 = Z
        assert np.allclose(S @ S, QuantumGates.pauli_z())
    
    def test_phase_t(self):
        """Test T gate."""
        T = QuantumGates.phase_t()
        assert T.shape == (2, 2)
        # T^2 = S
        assert np.allclose(T @ T, QuantumGates.phase_s())
    
    def test_rotation_x(self):
        """Test Rx gate."""
        gates = QuantumGates()
        Rx = gates.rotation_x(np.pi)
        assert Rx.shape == (2, 2)
        assert np.allclose(Rx.conj().T @ Rx, np.eye(2))
    
    def test_rotation_y(self):
        """Test Ry gate."""
        gates = QuantumGates()
        Ry = gates.rotation_y(np.pi / 2)
        assert Ry.shape == (2, 2)
        assert np.allclose(Ry.conj().T @ Ry, np.eye(2))
    
    def test_rotation_z(self):
        """Test Rz gate."""
        gates = QuantumGates()
        Rz = gates.rotation_z(np.pi)
        assert Rz.shape == (2, 2)
        assert np.allclose(Rz.conj().T @ Rz, np.eye(2))
    
    def test_cnot(self):
        """Test CNOT gate."""
        CNOT = QuantumGates.cnot()
        assert CNOT.shape == (4, 4)
        # CNOT|00⟩ = |00⟩
        result = CNOT @ np.array([1, 0, 0, 0], dtype=complex)
        assert np.allclose(result, np.array([1, 0, 0, 0], dtype=complex))
        # CNOT|10⟩ = |11⟩
        result = CNOT @ np.array([0, 0, 1, 0], dtype=complex)
        assert np.allclose(result, np.array([0, 0, 0, 1], dtype=complex))
    
    def test_cz(self):
        """Test CZ gate."""
        CZ = QuantumGates.cz()
        assert CZ.shape == (4, 4)
        assert np.allclose(CZ.conj().T @ CZ, np.eye(4))
    
    def test_swap(self):
        """Test SWAP gate."""
        SWAP = QuantumGates.swap()
        assert SWAP.shape == (4, 4)
        # SWAP|01⟩ = |10⟩
        result = SWAP @ np.array([0, 1, 0, 0], dtype=complex)
        assert np.allclose(result, np.array([0, 0, 1, 0], dtype=complex))
    
    def test_toffoli(self):
        """Test Toffoli gate."""
        Toffoli = QuantumGates.toffoli()
        assert Toffoli.shape == (8, 8)
        # Toffoli|110⟩ = |111⟩
        state = np.zeros(8, dtype=complex)
        state[6] = 1  # |110⟩
        result = Toffoli @ state
        assert np.allclose(result[7], 1)  # |111⟩
    
    def test_fredkin(self):
        """Test Fredkin gate."""
        Fredkin = QuantumGates.fredkin()
        assert Fredkin.shape == (8, 8)
        assert np.allclose(Fredkin.conj().T @ Fredkin, np.eye(8))
    
    def test_phase_p_parametrized(self):
        """Test parametrized phase gate."""
        gates = QuantumGates()
        P = gates.phase_p(np.pi / 4)
        assert P.shape == (2, 2)
        assert np.allclose(P.conj().T @ P, np.eye(2))
    
    def test_phase_p_invalid_param(self):
        """Test parametrized gate with invalid parameter."""
        gates = QuantumGates()
        with pytest.raises(GateValidationError):
            gates.phase_p("invalid")
    
    def test_register_custom_gate(self):
        """Test registering custom gate."""
        gates = QuantumGates()
        custom = np.array([[0, -1j], [1j, 0]], dtype=complex)
        gates.register_custom_gate("CUSTOM", custom, "Custom gate")
        gate = gates.get_gate("CUSTOM")
        assert gate.name == "CUSTOM"
    
    def test_register_invalid_gate(self):
        """Test registering non-unitary gate raises error."""
        gates = QuantumGates()
        non_unitary = np.array([[1, 1], [0, 1]], dtype=complex)
        with pytest.raises(GateSecurityError):
            gates.register_custom_gate("INVALID", non_unitary)
    
    def test_create_controlled_gate(self):
        """Test creating controlled gate."""
        gates = QuantumGates()
        controlled_x = gates.create_controlled_gate(QuantumGates.pauli_x(), 1)
        assert controlled_x.shape == (4, 4)
        assert np.allclose(controlled_x.conj().T @ controlled_x, np.eye(4))
    
    def test_tensor_product(self):
        """Test tensor product of gates."""
        gates = QuantumGates()
        result = gates.tensor_product([QuantumGates.pauli_x(), QuantumGates.pauli_x()])
        assert result.shape == (4, 4)
    
    def test_unitarity_validation(self):
        """Test unitarity validation."""
        with pytest.raises(GateSecurityError):
            QuantumGates._validate_unitarity(np.array([[1, 1], [0, 1]]), "Invalid")
    
    def test_operation_log(self):
        """Test operation logging."""
        gates = QuantumGates(user_id="test_user")
        gates.get_gate("HADAMARD")
        log = gates.get_operation_log()
        assert len(log) > 0
        assert log[0]["user_id"] == "test_user"


class TestGateMatrices:
    """Test gate matrix properties."""

    def test_all_single_qubit_gates_unitary(self):
        """Test all single-qubit gates are unitary."""
        gates = QuantumGates()
        single_qubit_gates = ["I", "X", "Y", "Z", "HADAMARD", "S", "T"]

        for gate_name in single_qubit_gates:
            gate = gates.get_gate(gate_name)
            U = gate.matrix
            assert np.allclose(U.conj().T @ U, np.eye(2)), f"{gate_name} is not unitary"
    
    def test_all_two_qubit_gates_unitary(self):
        """Test all two-qubit gates are unitary."""
        gates = QuantumGates()
        two_qubit_gates = ["CNOT", "CZ", "SWAP"]
        
        for gate_name in two_qubit_gates:
            gate = gates.get_gate(gate_name)
            U = gate.matrix
            assert np.allclose(U.conj().T @ U, np.eye(4)), f"{gate_name} is not unitary"
    
    def test_hadamard_self_inverse(self):
        """Test Hadamard is self-inverse."""
        H = QuantumGates.hadamard()
        assert np.allclose(H @ H, np.eye(2))
    
    def test_pauli_matrices_square_to_identity(self):
        """Test Pauli matrices square to identity."""
        X = QuantumGates.pauli_x()
        Y = QuantumGates.pauli_y()
        Z = QuantumGates.pauli_z()
        
        assert np.allclose(X @ X, np.eye(2))
        assert np.allclose(Y @ Y, np.eye(2))
        assert np.allclose(Z @ Z, np.eye(2))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
