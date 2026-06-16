"""
Quantum Visualization
=====================
Visualization tools for quantum states and circuits.

Features:
- Bloch sphere visualization
- Circuit diagram (ASCII)
- State vector visualization
- Probability distribution plots
- Security-safe output sanitization
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime
import logging

from .qubit import Qubit, QubitRegister, QuantumValidationError

logger = logging.getLogger(__name__)


class VisualizationError(Exception):
    """Exception raised for visualization errors."""
    pass


class QuantumVisualizer:
    """
    Quantum visualization tools with security features.
    
    Provides:
    - Bloch sphere representation
    - ASCII circuit diagrams
    - State vector visualization
    - Probability distributions
    """
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize quantum visualizer.
        
        Args:
            user_id: User ID for audit logging
        """
        self._user_id = user_id
        self._matplotlib_available = False
        self._plt = None
        self._audit_log: List[dict] = []
        
        # Try to import matplotlib
        self._import_matplotlib()
    
    def _import_matplotlib(self) -> None:
        """Import matplotlib with error handling."""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            self._plt = plt
            self._matplotlib_available = True
            logger.info("Matplotlib imported successfully")
        except ImportError as e:
            logger.warning(f"Matplotlib not available: {e}")
            self._matplotlib_available = False
    
    def _log_operation(self, operation: str, details: dict) -> None:
        """Log visualization operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "user_id": self._user_id
        })
    
    def _sanitize_title(self, title: str, max_length: int = 100) -> str:
        """Security: Sanitize title for display."""
        if not isinstance(title, str):
            title = str(title)
        # Remove potentially dangerous characters
        sanitized = title.replace("<", "&lt;").replace(">", "&gt;")
        sanitized = sanitized.replace("&", "&amp;")
        return sanitized[:max_length]
    
    # ========== Bloch Sphere Visualization ==========
    
    def bloch_sphere(
        self,
        qubit: Qubit,
        title: str = "Bloch Sphere",
        save_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Create Bloch sphere visualization for a qubit.
        
        Args:
            qubit: Qubit to visualize
            title: Plot title
            save_path: Optional path to save image
            
        Returns:
            Image bytes if matplotlib available, None otherwise
        """
        if not self._matplotlib_available:
            return self._bloch_sphere_ascii(qubit, title)
        
        # Security: Validate qubit
        if not isinstance(qubit, Qubit):
            raise QuantumValidationError(f"Expected Qubit, got {type(qubit)}")
        
        try:
            # Calculate Bloch sphere coordinates
            alpha = qubit.alpha
            beta = qubit.beta
            
            # Convert to Bloch sphere coordinates
            # |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩
            theta = 2 * np.arccos(abs(alpha))
            phi = np.angle(beta) - np.angle(alpha)
            
            # Cartesian coordinates
            x = np.sin(theta) * np.cos(phi)
            y = np.sin(theta) * np.sin(phi)
            z = np.cos(theta)
            
            # Create figure
            fig = self._plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # Draw sphere
            u = np.linspace(0, 2 * np.pi, 50)
            v = np.linspace(0, np.pi, 50)
            xs = np.outer(np.cos(u), np.sin(v))
            ys = np.outer(np.sin(u), np.sin(v))
            zs = np.outer(np.ones(np.size(u)), np.cos(v))
            ax.plot_surface(xs, ys, zs, alpha=0.1, color='blue')
            
            # Draw axes
            ax.quiver(0, 0, 0, 1, 0, 0, color='red', arrow_length_ratio=0.1)
            ax.quiver(0, 0, 0, 0, 1, 0, color='green', arrow_length_ratio=0.1)
            ax.quiver(0, 0, 0, 0, 0, 1, color='blue', arrow_length_ratio=0.1)
            ax.text(1.1, 0, 0, '|+⟩', color='red')
            ax.text(0, 1.1, 0, '|i⟩', color='green')
            ax.text(0, 0, 1.1, '|0⟩', color='blue')
            
            # Draw state vector
            ax.quiver(0, 0, 0, x, y, z, color='purple', 
                     arrow_length_ratio=0.1, linewidth=3)
            
            # Draw equator and meridians
            circle_xy = self._plt.Circle((0, 0), 1, color='gray', 
                                          fill=False, linestyle='--', alpha=0.5)
            ax.add_patch(circle_xy)
            
            # Labels
            sanitized_title = self._sanitize_title(title)
            ax.set_title(sanitized_title)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            
            # Set limits
            ax.set_xlim([-1.2, 1.2])
            ax.set_ylim([-1.2, 1.2])
            ax.set_zlim([-1.2, 1.2])
            
            # Save or return image
            if save_path:
                self._plt.savefig(save_path, dpi=100, bbox_inches='tight')
                self._plt.close(fig)
                self._log_operation("BLOCH_SPHERE_SAVE", {
                    "path": save_path,
                    "title": sanitized_title
                })
                return None
            else:
                from io import BytesIO
                buf = BytesIO()
                self._plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                self._plt.close(fig)
                image_bytes = buf.getvalue()
                
                self._log_operation("BLOCH_SPHERE_CREATE", {
                    "title": sanitized_title,
                    "size_bytes": len(image_bytes)
                })
                return image_bytes
                
        except Exception as e:
            logger.error(f"Bloch sphere error: {e}")
            raise VisualizationError(f"Failed to create Bloch sphere: {e}")
    
    def _bloch_sphere_ascii(
        self,
        qubit: Qubit,
        title: str = "Bloch Sphere"
    ) -> str:
        """Create ASCII representation of Bloch sphere."""
        alpha = qubit.alpha
        beta = qubit.beta
        
        # Calculate coordinates
        theta = 2 * np.arccos(abs(alpha))
        phi = np.angle(beta) - np.angle(alpha)
        
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)
        
        # Get probabilities
        prob_0, prob_1 = qubit.get_probabilities()
        
        # Create ASCII representation
        lines = [
            f"  Bloch Sphere: {self._sanitize_title(title)}",
            "  ",
            "         |0⟩ (Z)",
            "          |",
            "          |",
            f"    ------+------  (X) |+⟩",
            "          |",
            "          |",
            "         |1⟩",
            "  ",
            f"  State: |ψ⟩ = {alpha:.3f}|0⟩ + {beta:.3f}|1⟩",
            f"  P(|0⟩) = {prob_0:.3f}, P(|1⟩) = {prob_1:.3f}",
            f"  Coordinates: (x={x:.3f}, y={y:.3f}, z={z:.3f})"
        ]
        
        return "\n".join(lines)
    
    # ========== State Vector Visualization ==========
    
    def state_vector(
        self,
        register: QubitRegister,
        title: str = "State Vector"
    ) -> str:
        """
        Visualize state vector as ASCII art.
        
        Args:
            register: Qubit register
            title: Title for visualization
            
        Returns:
            ASCII representation
        """
        if not isinstance(register, QubitRegister):
            raise QuantumValidationError(f"Expected QubitRegister, got {type(register)}")
        
        state = register.state_vector
        n = register.num_qubits
        dim = len(state)
        
        lines = [
            f"  State Vector: {self._sanitize_title(title)}",
            f"  Qubits: {n}, Dimension: {dim}",
            "  " + "=" * 50
        ]
        
        # Show significant components (amplitude > threshold)
        threshold = 0.01
        shown = 0
        max_show = min(16, dim)  # Limit display
        
        for i in range(min(dim, max_show)):
            amp = state[i]
            prob = abs(amp) ** 2
            
            if prob > threshold or shown < 4:
                binary = format(i, f'0{n}b')
                lines.append(
                    f"  |{binary}⟩: {amp.real:+.4f}{amp.imag:+.4f}i  (P={prob:.4f})"
                )
                shown += 1
        
        if dim > max_show:
            lines.append(f"  ... ({dim - max_show} more states)")
        
        return "\n".join(lines)
    
    # ========== Probability Distribution ==========
    
    def probability_distribution(
        self,
        register: QubitRegister,
        title: str = "Probability Distribution"
    ) -> str:
        """
        Visualize probability distribution as bar chart (ASCII).
        
        Args:
            register: Qubit register
            title: Title
            
        Returns:
            ASCII bar chart
        """
        if not isinstance(register, QubitRegister):
            raise QuantumValidationError(f"Expected QubitRegister, got {type(register)}")
        
        state = register.state_vector
        n = register.num_qubits
        probs = np.abs(state) ** 2
        
        lines = [
            f"  Probability Distribution: {self._sanitize_title(title)}",
            "  " + "=" * 60
        ]
        
        # Create bar chart
        max_bar_width = 40
        
        for i, prob in enumerate(probs):
            if prob < 0.01:
                continue
            
            binary = format(i, f'0{n}b')
            bar_length = int(prob * max_bar_width)
            bar = "█" * bar_length + "░" * (max_bar_width - bar_length)
            lines.append(f"  |{binary}⟩ [{bar}] {prob:.4f}")
        
        return "\n".join(lines)
    
    # ========== Circuit Diagram ==========
    
    def circuit_diagram(
        self,
        circuit: Any,
        title: str = "Quantum Circuit"
    ) -> str:
        """
        Create ASCII circuit diagram.
        
        Args:
            circuit: QuantumCircuit to visualize
            title: Title
            
        Returns:
            ASCII circuit diagram
        """
        # Import here to avoid circular dependency
        from .circuit import QuantumCircuit
        
        if not isinstance(circuit, QuantumCircuit):
            raise QuantumValidationError(f"Expected QuantumCircuit, got {type(circuit)}")
        
        lines = [
            f"  Circuit: {self._sanitize_title(title)}",
            f"  Name: {circuit.name}",
            f"  Qubits: {circuit.num_qubits}, Depth: {circuit.depth}",
            "  " + "=" * 60
        ]
        
        # Draw each qubit line
        for q in range(circuit.num_qubits):
            line = f"  q[{q}]: |0⟩"
            
            for op in circuit.operations:
                if q in op.targets:
                    if len(op.controls) == 0:
                        gate_str = f"──[{op.gate_name}]──"
                    else:
                        gate_str = "──[⊕]──"  # Target of controlled gate
                elif q in op.controls:
                    gate_str = "──[●]──"  # Control
                else:
                    gate_str = "───────"
                
                line += gate_str
            
            lines.append(line)
        
        return "\n".join(lines)
    
    # ========== Measurement Results ==========
    
    def measurement_results(
        self,
        counts: Dict[str, int],
        title: str = "Measurement Results",
        total_shots: Optional[int] = None
    ) -> str:
        """
        Visualize measurement results.
        
        Args:
            counts: Dictionary of outcome counts
            title: Title
            total_shots: Total number of shots
            
        Returns:
            ASCII visualization
        """
        if not isinstance(counts, dict):
            raise QuantumValidationError(f"Expected dict, got {type(counts)}")
        
        if total_shots is None:
            total_shots = sum(counts.values())
        
        lines = [
            f"  Measurement Results: {self._sanitize_title(title)}",
            f"  Total shots: {total_shots}",
            "  " + "=" * 60
        ]
        
        # Sort by count
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        max_bar_width = 40
        
        for outcome, count in sorted_counts:
            prob = count / total_shots if total_shots > 0 else 0
            bar_length = int(prob * max_bar_width)
            bar = "█" * bar_length + "░" * (max_bar_width - bar_length)
            lines.append(f"  |{outcome}⟩ [{bar}] {count} ({prob:.2%})")
        
        return "\n".join(lines)
    
    # ========== Gate Matrix Visualization ==========
    
    def gate_matrix(
        self,
        matrix: np.ndarray,
        gate_name: str = "Gate"
    ) -> str:
        """
        Visualize gate matrix.
        
        Args:
            matrix: Gate matrix
            gate_name: Gate name
            
        Returns:
            ASCII matrix representation
        """
        if not isinstance(matrix, np.ndarray):
            raise QuantumValidationError(f"Expected numpy array, got {type(matrix)}")
        
        lines = [
            f"  {self._sanitize_title(gate_name)} Matrix ({matrix.shape}):",
            "  " + "=" * 50
        ]
        
        for row in matrix:
            row_str = "  | "
            for val in row:
                if isinstance(val, complex) or np.iscomplexobj(val):
                    row_str += f"{val.real:.3f}{val.imag:+.3f}i  "
                else:
                    row_str += f"{val:.3f}     "
            row_str += "|"
            lines.append(row_str)
        
        return "\n".join(lines)
    
    # ========== Algorithm Results ==========
    
    def algorithm_result(
        self,
        result: Any,
        title: str = "Algorithm Result"
    ) -> str:
        """
        Visualize quantum algorithm result.
        
        Args:
            result: AlgorithmResult object
            title: Title
            
        Returns:
            ASCII visualization
        """
        from .algorithms import AlgorithmResult
        
        if not isinstance(result, AlgorithmResult):
            raise QuantumValidationError(f"Expected AlgorithmResult, got {type(result)}")
        
        lines = [
            f"  {self._sanitize_title(title)}",
            f"  Algorithm: {result.algorithm_name}",
            f"  Success: {'✓' if result.success else '✗'}",
            f"  Qubits: {result.num_qubits}, Operations: {result.num_operations}",
            f"  Execution Time: {result.execution_time_ms:.2f} ms",
            "  " + "=" * 50
        ]
        
        # Show output
        if isinstance(result.output, dict):
            for key, value in result.output.items():
                lines.append(f"  {key}: {value}")
        else:
            lines.append(f"  Output: {result.output}")
        
        if result.measurements:
            lines.append(f"  Measurements: {result.measurements}")
        
        return "\n".join(lines)
    
    def get_audit_log(self) -> List[dict]:
        """Get audit log."""
        return self._audit_log.copy()
    
    def __repr__(self) -> str:
        mpl_status = "available" if self._matplotlib_available else "not available"
        return f"QuantumVisualizer(matplotlib={mpl_status})"
