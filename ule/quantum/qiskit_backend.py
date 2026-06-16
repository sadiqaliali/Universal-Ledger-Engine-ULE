"""
IBM Qiskit Backend Integration
==============================
Integration with IBM Qiskit for running quantum circuits on real hardware.

Features:
- Qiskit circuit conversion
- IBM Quantum Computer access
- Qiskit Aer simulator
- Result processing
- Secure API key management
"""

import numpy as np
import os
import hashlib
import json
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from .qubit import QuantumValidationError, QuantumSecurityError
from .circuit import QuantumCircuit, CircuitResult

logger = logging.getLogger(__name__)


class QiskitSecurityError(Exception):
    """Exception raised for Qiskit security violations."""
    pass


class QiskitBackendError(Exception):
    """Exception raised for Qiskit backend errors."""
    pass


@dataclass
class QiskitJobResult:
    """Result from Qiskit job execution."""
    job_id: str
    backend_name: str
    measurements: Dict[str, int]
    state_vector: Optional[np.ndarray] = None
    success: bool = True
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class QiskitBackend:
    """
    IBM Qiskit backend integration with security features.
    
    Supports:
    - Qiskit Aer simulator (local)
    - IBM Quantum computers (remote)
    - Circuit conversion
    - Result processing
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize Qiskit backend.
        
        Args:
            api_token: IBM Quantum API token (optional for simulator)
            user_id: User ID for audit logging
        """
        self._user_id = user_id
        self._api_token = api_token or os.environ.get("IBM_QUANTUM_TOKEN")
        self._qiskit_available = False
        self._provider = None
        self._audit_log: List[dict] = []
        
        # Try to import qiskit
        self._import_qiskit()
        
        self._log_operation("INIT", {
            "api_token_set": self._api_token is not None,
            "qiskit_available": self._qiskit_available
        })
    
    def _log_operation(self, operation: str, details: dict) -> None:
        """Log backend operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "user_id": self._user_id
        })
    
    def _import_qiskit(self) -> None:
        """Import Qiskit with error handling."""
        try:
            import qiskit
            from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
            from qiskit import transpile, assemble
            from qiskit_aer import AerSimulator
            from qiskit.visualization import plot_histogram
            
            self._qiskit = qiskit
            self._QuantumCircuit = QuantumCircuit
            self._QuantumRegister = QuantumRegister
            self._ClassicalRegister = ClassicalRegister
            self._transpile = transpile
            self._assemble = assemble
            self._AerSimulator = AerSimulator
            self._plot_histogram = plot_histogram
            self._qiskit_available = True
            
            logger.info("Qiskit imported successfully")
        except ImportError as e:
            logger.warning(f"Qiskit not available: {e}")
            self._qiskit_available = False
    
    def _validate_api_token(self, token: str) -> bool:
        """Security: Validate API token format."""
        if not token or not isinstance(token, str):
            return False
        if len(token) < 10:
            return False
        # Basic format check (IBM tokens are alphanumeric)
        if not token.replace("_", "").replace("-", "").isalnum():
            return False
        return True
    
    def _secure_token_hash(self, token: str) -> str:
        """Create secure hash of token for logging (without exposing token)."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def connect_to_ibm(self, api_token: Optional[str] = None) -> bool:
        """
        Connect to IBM Quantum service.
        
        Args:
            api_token: IBM Quantum API token
            
        Returns:
            True if connection successful
        """
        if not self._qiskit_available:
            logger.error("Qiskit not available")
            return False
        
        token = api_token or self._api_token
        if not token:
            logger.error("No API token provided")
            return False
        
        # Security: Validate token
        if not self._validate_api_token(token):
            raise QiskitSecurityError("Invalid API token format")
        
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            
            # Save account if not already saved
            from qiskit_ibm_runtime import QiskitRuntimeService
            
            self._provider = QiskitRuntimeService(channel="ibm_quantum", token=token)
            
            self._log_operation("CONNECT_IBM", {
                "token_hash": self._secure_token_hash(token),
                "success": True
            })
            
            logger.info("Connected to IBM Quantum service")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IBM Quantum: {e}")
            self._log_operation("CONNECT_IBM", {
                "error": str(e)
            })
            return False
    
    def convert_to_qiskit(
        self,
        circuit: QuantumCircuit
    ) -> 'qiskit.QuantumCircuit':
        """
        Convert ULE QuantumCircuit to Qiskit QuantumCircuit.
        
        Args:
            circuit: ULE QuantumCircuit
            
        Returns:
            Qiskit QuantumCircuit
        """
        if not self._qiskit_available:
            raise QiskitBackendError("Qiskit not available")
        
        # Security: Validate circuit
        if not isinstance(circuit, QuantumCircuit):
            raise QuantumValidationError(
                f"Expected QuantumCircuit, got {type(circuit)}"
            )
        
        # Create Qiskit circuit
        qreg = self._QuantumRegister(circuit.num_qubits, 'q')
        creg = self._ClassicalRegister(circuit.num_qubits, 'c')
        qiskit_circuit = self._QuantumCircuit(qreg, creg)
        
        # Convert operations
        for op in circuit.operations:
            targets = op.targets
            controls = op.controls
            
            if op.gate_name == "H":
                qiskit_circuit.h(qreg[targets[0]])
            elif op.gate_name == "X":
                qiskit_circuit.x(qreg[targets[0]])
            elif op.gate_name == "Y":
                qiskit_circuit.y(qreg[targets[0]])
            elif op.gate_name == "Z":
                qiskit_circuit.z(qreg[targets[0]])
            elif op.gate_name == "S":
                qiskit_circuit.s(qreg[targets[0]])
            elif op.gate_name == "T":
                qiskit_circuit.t(qreg[targets[0]])
            elif op.gate_name == "CNOT":
                qiskit_circuit.cx(qreg[controls[0]], qreg[targets[0]])
            elif op.gate_name == "CZ":
                qiskit_circuit.cz(qreg[controls[0]], qreg[targets[0]])
            elif op.gate_name == "SWAP":
                qiskit_circuit.swap(qreg[targets[0]], qreg[targets[1]])
            elif op.gate_name == "TOFFOLI":
                qiskit_circuit.ccx(
                    qreg[controls[0]],
                    qreg[controls[1]],
                    qreg[targets[0]]
                )
            elif op.gate_name.startswith("RX"):
                param = op.parameters.get("param", 0) if op.parameters else 0
                qiskit_circuit.rx(param, qreg[targets[0]])
            elif op.gate_name.startswith("RY"):
                param = op.parameters.get("param", 0) if op.parameters else 0
                qiskit_circuit.ry(param, qreg[targets[0]])
            elif op.gate_name.startswith("RZ"):
                param = op.parameters.get("param", 0) if op.parameters else 0
                qiskit_circuit.rz(param, qreg[targets[0]])
            else:
                logger.warning(f"Unknown gate: {op.gate_name}")
        
        self._log_operation("CONVERT_TO_QISKIT", {
            "circuit_name": circuit.name,
            "num_qubits": circuit.num_qubits,
            "num_operations": circuit.depth
        })
        
        return qiskit_circuit
    
    def run_simulator(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
        seed: Optional[int] = None
    ) -> QiskitJobResult:
        """
        Run circuit on Qiskit Aer simulator.
        
        Args:
            circuit: ULE QuantumCircuit
            shots: Number of shots
            seed: Random seed
            
        Returns:
            QiskitJobResult
        """
        import time
        start_time = time.time()
        
        if not self._qiskit_available:
            raise QiskitBackendError("Qiskit not available")
        
        # Security: Validate shots
        if shots < 1 or shots > 100000:
            raise QuantumValidationError(
                f"Shots must be 1-100000, got {shots}"
            )
        
        try:
            # Convert to Qiskit circuit
            qiskit_circuit = self.convert_to_qiskit(circuit)
            
            # Create simulator
            simulator = self._AerSimulator()
            
            # Add measurement
            qiskit_circuit.measure_all()
            
            # Transpile and run
            transpiled = self._transpile(qiskit_circuit, simulator)
            job = simulator.run(transpiled, shots=shots, seed_simulator=seed)
            result = job.result()
            
            # Get counts
            counts = result.get_counts()
            
            execution_time = (time.time() - start_time) * 1000
            
            job_result = QiskitJobResult(
                job_id="simulator",
                backend_name="AerSimulator",
                measurements=counts,
                success=True,
                execution_time_ms=execution_time
            )
            
            self._log_operation("RUN_SIMULATOR", {
                "circuit": circuit.name,
                "shots": shots,
                "outcomes": len(counts)
            })
            
            return job_result
            
        except Exception as e:
            logger.error(f"Simulator error: {e}")
            return QiskitJobResult(
                job_id="error",
                backend_name="AerSimulator",
                measurements={},
                success=False,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def run_on_hardware(
        self,
        circuit: QuantumCircuit,
        backend_name: str = "ibmq_qasm_simulator",
        shots: int = 1024
    ) -> QiskitJobResult:
        """
        Run circuit on IBM quantum hardware.
        
        Args:
            circuit: ULE QuantumCircuit
            backend_name: IBM backend name
            shots: Number of shots
            
        Returns:
            QiskitJobResult
        """
        import time
        start_time = time.time()
        
        if not self._qiskit_available:
            raise QiskitBackendError("Qiskit not available")
        
        if self._provider is None:
            raise QiskitBackendError("Not connected to IBM Quantum")
        
        try:
            # Convert to Qiskit circuit
            qiskit_circuit = self.convert_to_qiskit(circuit)
            
            # Get backend
            backend = self._provider.backend(backend_name)
            
            # Transpile for backend
            transpiled = self._transpile(qiskit_circuit, backend)
            
            # Submit job
            job = backend.run(transpiled, shots=shots)
            
            self._log_operation("SUBMIT_HARDWARE_JOB", {
                "backend": backend_name,
                "job_id": job.job_id()
            })
            
            logger.info(f"Job submitted: {job.job_id()}")
            
            # Return job info (user can poll for results)
            return QiskitJobResult(
                job_id=job.job_id(),
                backend_name=backend_name,
                measurements={},
                success=True,
                execution_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            logger.error(f"Hardware error: {e}")
            return QiskitJobResult(
                job_id="error",
                backend_name=backend_name,
                measurements={},
                success=False,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def get_job_result(self, job_id: str) -> QiskitJobResult:
        """
        Get results from a submitted job.
        
        Args:
            job_id: Job ID
            
        Returns:
            QiskitJobResult with measurements
        """
        if self._provider is None:
            raise QiskitBackendError("Not connected to IBM Quantum")
        
        try:
            from qiskit_ibm_runtime import RuntimeJob
            
            # Get job
            job = self._provider.job(job_id)
            
            # Wait for completion
            result = job.result()
            
            return QiskitJobResult(
                job_id=job_id,
                backend_name=job.backend_name,
                measurements=result.get_counts(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error getting job result: {e}")
            return QiskitJobResult(
                job_id=job_id,
                backend_name="unknown",
                measurements={},
                success=False,
                error_message=str(e)
            )
    
    def list_backends(self) -> List[str]:
        """
        List available backends.
        
        Returns:
            List of backend names
        """
        if not self._qiskit_available:
            return ["simulator (qiskit not available)"]
        
        try:
            # Always include simulator
            backends = ["aer_simulator"]
            
            if self._provider:
                backends.extend([b.name for b in self._provider.backends()])
            
            return backends
            
        except Exception as e:
            logger.error(f"Error listing backends: {e}")
            return ["error listing backends"]
    
    def get_backend_info(self, backend_name: str) -> Dict[str, Any]:
        """
        Get information about a backend.
        
        Args:
            backend_name: Backend name
            
        Returns:
            Backend information dictionary
        """
        if not self._qiskit_available:
            return {"error": "Qiskit not available"}
        
        try:
            if backend_name == "aer_simulator":
                return {
                    "name": "Aer Simulator",
                    "type": "simulator",
                    "qubits": "unlimited (simulation)",
                    "status": "available"
                }
            
            if self._provider:
                backend = self._provider.backend(backend_name)
                return {
                    "name": backend.name,
                    "type": "hardware",
                    "qubits": backend.configuration().n_qubits,
                    "status": backend.status().value
                }
            
            return {"error": "Not connected to IBM Quantum"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_audit_log(self) -> List[dict]:
        """Get audit log."""
        return self._audit_log.copy()
    
    def __repr__(self) -> str:
        status = "connected" if self._provider else "disconnected"
        qiskit_status = "available" if self._qiskit_available else "not available"
        return f"QiskitBackend(status={status}, qiskit={qiskit_status})"
