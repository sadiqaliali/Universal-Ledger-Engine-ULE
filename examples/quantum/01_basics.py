#!/usr/bin/env python3
"""
Quantum Basics Examples
=======================
Introduction to qubits, gates, and measurements.
"""

import numpy as np
from ule.quantum import Qubit, QubitRegister, QuantumGates, QuantumVisualizer

print("=" * 60)
print("ULE Quantum Computing - Basics Examples")
print("=" * 60)

# ========== 1. Single Qubit ==========
print("\n1. SINGLE QUBIT")
print("-" * 40)

# Create qubit in |0⟩ state
q0 = Qubit()
print(f"Qubit in |0⟩ state: {q0}")
print(f"  P(|0⟩) = {q0.get_probabilities()[0]:.2f}")
print(f"  P(|1⟩) = {q0.get_probabilities()[1]:.2f}")

# Create qubit in |1⟩ state
q1 = Qubit(alpha=0.0, beta=1.0)
print(f"\nQubit in |1⟩ state: {q1}")

# Create qubit in superposition |+⟩
q_plus = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
print(f"\nQubit in |+⟩ superposition: {q_plus}")
print(f"  P(|0⟩) = {q_plus.get_probabilities()[0]:.2f}")
print(f"  P(|1⟩) = {q_plus.get_probabilities()[1]:.2f}")

# ========== 2. Quantum Gates ==========
print("\n2. QUANTUM GATES")
print("-" * 40)

gates = QuantumGates()

# Start with |0⟩
q = Qubit()
print(f"Initial state: {q}")

# Apply Hadamard gate
q.apply_gate(gates.hadamard(), "H")
print(f"After Hadamard (H): {q}")
print(f"  Now in superposition!")

# Apply Pauli-X gate (NOT)
q.apply_gate(gates.pauli_x(), "X")
print(f"After Pauli-X (NOT): {q}")

# Reset and apply different gates
q.reset()
print(f"\nAfter reset: {q}")

q.apply_gate(gates.pauli_z(), "Z")
print(f"After Pauli-Z: {q}")

# ========== 3. Measurement ==========
print("\n3. MEASUREMENT")
print("-" * 40)

q = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
print(f"Before measurement: {q}")

# Measure the qubit (collapses to |0⟩ or |1⟩)
result = q.measure(seed=42)
print(f"Measurement result: {result}")
print(f"After measurement: {q}")

# ========== 4. Multi-Qubit Register ==========
print("\n4. MULTI-QUBIT REGISTER")
print("-" * 40)

# Create 3-qubit register
reg = QubitRegister(num_qubits=3, initial_state="000")
print(f"3-qubit register: {reg}")
print(f"State vector shape: {reg.state_vector.shape}")

# Apply gate to specific qubit
reg.apply_gate(gates.hadamard(), 0)
q0 = reg.get_qubit(0)
print(f"\nAfter H on qubit 0: {q0}")

# Measure all qubits
reg.reset_all()
reg.apply_gate(gates.hadamard(), 0)
reg.apply_gate(gates.hadamard(), 1)
reg.apply_gate(gates.hadamard(), 2)

measurement = reg.measure_all(seed=42)
print(f"Measurement of 3 qubits: {measurement}")

# ========== 5. Visualization ==========
print("\n5. VISUALIZATION")
print("-" * 40)

visualizer = QuantumVisualizer()

# Bloch sphere (ASCII)
q = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
print(visualizer.bloch_sphere(q, "Qubit |+⟩"))

# State vector
reg = QubitRegister(num_qubits=2, initial_state="00")
print("\n" + visualizer.state_vector(reg, "2-Qubit |00⟩ State"))

# Probability distribution
print("\n" + visualizer.probability_distribution(reg, "Probability Distribution"))

print("\n" + "=" * 60)
print("Examples completed!")
print("=" * 60)
