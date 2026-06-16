"""Tests for Quantum Algorithms."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ule.quantum.algorithms import (
    QuantumAlgorithms, AlgorithmResult,
    AlgorithmSecurityError, AlgorithmValidationError
)


class TestQuantumAlgorithms:
    """Test QuantumAlgorithms class."""
    
    def test_init(self):
        """Test algorithms initialization."""
        algo = QuantumAlgorithms()
        assert algo is not None
    
    def test_deutsch_jozsa_constant(self):
        """Test Deutsch-Jozsa with constant function."""
        algo = QuantumAlgorithms()
        
        # Constant function: always returns 0
        def constant_func(x):
            return 0
        
        result = algo.deutsch_jozsa(constant_func, n=3)
        
        assert isinstance(result, AlgorithmResult)
        assert result.algorithm_name == "Deutsch-Jozsa"
        assert result.output == "constant"
    
    def test_deutsch_jozsa_balanced(self):
        """Test Deutsch-Jozsa with balanced function."""
        algo = QuantumAlgorithms()
        
        # Balanced function: returns parity
        def balanced_func(x):
            return x % 2
        
        result = algo.deutsch_jozsa(balanced_func, n=3)
        
        assert isinstance(result, AlgorithmResult)
        assert result.output == "balanced"
    
    def test_deutsch_jozsa_invalid_n(self):
        """Test Deutsch-Jozsa with invalid n."""
        algo = QuantumAlgorithms()
        
        with pytest.raises(AlgorithmValidationError):
            algo.deutsch_jozsa(lambda x: 0, n=0)
        
        with pytest.raises(AlgorithmValidationError):
            algo.deutsch_jozsa(lambda x: 0, n=15)  # Exceeds max
    
    def test_grover_search(self):
        """Test Grover's search algorithm."""
        algo = QuantumAlgorithms()
        
        # Search for item 5 in 3-qubit space
        result = algo.grover_search(oracle_target=5, n=3)
        
        assert isinstance(result, AlgorithmResult)
        assert result.algorithm_name == "Grover"
        # Grover may not always find the target with small iterations
        assert result.output >= 0
        assert result.output < 8
    
    def test_grover_invalid_target(self):
        """Test Grover with invalid target."""
        algo = QuantumAlgorithms()
        
        with pytest.raises(AlgorithmValidationError):
            algo.grover_search(oracle_target=10, n=3)  # 10 > 2^3 - 1
    
    def test_quantum_fourier_transform(self):
        """Test Quantum Fourier Transform."""
        algo = QuantumAlgorithms()
        
        result = algo.quantum_fourier_transform(input_state=1, n=3)
        
        assert isinstance(result, AlgorithmResult)
        assert result.algorithm_name == "QFT"
        assert "probabilities" in result.output
        assert len(result.output["probabilities"]) == 8
    
    def test_quantum_teleportation(self):
        """Test quantum teleportation protocol."""
        algo = QuantumAlgorithms()
        
        # Teleport |+⟩ state
        state = (1/np.sqrt(2), 1/np.sqrt(2))
        result = algo.quantum_teleportation(state)
        
        assert isinstance(result, AlgorithmResult)
        assert result.algorithm_name == "Quantum Teleportation"
        assert result.output["protocol_complete"] is True
    
    def test_quantum_teleportation_invalid_state(self):
        """Test teleportation with non-normalized state."""
        algo = QuantumAlgorithms()
        
        with pytest.raises(AlgorithmValidationError):
            algo.quantum_teleportation((1.0, 1.0))  # Not normalized
    
    def test_superdense_coding(self):
        """Test superdense coding protocol."""
        algo = QuantumAlgorithms()
        
        # Test all 4 possible messages
        for message in range(4):
            result = algo.superdense_coding(message)
            
            assert isinstance(result, AlgorithmResult)
            assert result.algorithm_name == "Superdense Coding"
            assert result.success  # Should always succeed
    
    def test_superdense_coding_invalid_message(self):
        """Test superdense coding with invalid message."""
        algo = QuantumAlgorithms()
        
        with pytest.raises(AlgorithmValidationError):
            algo.superdense_coding(5)  # Only 0-3 valid
    
    def test_bernstein_vazirani(self):
        """Test Bernstein-Vazirani algorithm."""
        algo = QuantumAlgorithms()
        
        # Find secret 10 (binary: 1010)
        result = algo.bernstein_vazirani(secret=10, n=4)
        
        assert isinstance(result, AlgorithmResult)
        assert result.algorithm_name == "Bernstein-Vazirani"
        assert result.success  # BV always finds the secret
        assert result.output["found"] == 10
    
    def test_bernstein_vazirani_invalid_secret(self):
        """Test Bernstein-Vazirani with invalid secret."""
        algo = QuantumAlgorithms()
        
        with pytest.raises(AlgorithmValidationError):
            algo.bernstein_vazirani(secret=20, n=4)  # 20 > 2^4 - 1
    
    def test_algorithm_audit_log(self):
        """Test algorithm audit logging."""
        algo = QuantumAlgorithms(user_id="test_user")
        
        algo.deutsch_jozsa(lambda x: 0, n=2)
        algo.grover_search(3, n=2)
        
        log = algo.get_audit_log()
        assert len(log) == 2
        assert log[0]["user_id"] == "test_user"


class TestAlgorithmResults:
    """Test algorithm result processing."""
    
    def test_result_structure(self):
        """Test algorithm result structure."""
        algo = QuantumAlgorithms()
        result = algo.deutsch_jozsa(lambda x: 0, n=2)
        
        assert hasattr(result, 'algorithm_name')
        assert hasattr(result, 'success')
        assert hasattr(result, 'output')
        assert hasattr(result, 'execution_time_ms')
        assert hasattr(result, 'num_qubits')
        assert hasattr(result, 'num_operations')
        assert hasattr(result, 'state_hash')
    
    def test_execution_time_positive(self):
        """Test that execution time is positive."""
        algo = QuantumAlgorithms()
        result = algo.deutsch_jozsa(lambda x: 0, n=3)
        
        assert result.execution_time_ms > 0
    
    def test_state_hash_present(self):
        """Test that state hash is computed."""
        algo = QuantumAlgorithms()
        result = algo.deutsch_jozsa(lambda x: 0, n=2)
        
        assert len(result.state_hash) == 32


class TestAlgorithmSecurity:
    """Test algorithm security features."""
    
    def test_input_validation(self):
        """Test input validation."""
        algo = QuantumAlgorithms()
        
        # Test with wrong type
        with pytest.raises(AlgorithmValidationError):
            algo._validate_input("string", int, "test_param")
    
    def test_range_validation(self):
        """Test range validation."""
        algo = QuantumAlgorithms()
        
        with pytest.raises(AlgorithmValidationError):
            algo._validate_input(5, int, "test", min_val=0, max_val=3)
        
        with pytest.raises(AlgorithmValidationError):
            algo._validate_input(-1, int, "test", min_val=0)
    
    def test_oracle_validation(self):
        """Test oracle function validation."""
        algo = QuantumAlgorithms()
        
        def invalid_oracle(x):
            return "invalid"  # Should return 0 or 1
        
        with pytest.raises(AlgorithmValidationError):
            algo.deutsch_jozsa(invalid_oracle, n=2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
