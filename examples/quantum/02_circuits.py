#!/usr/bin/env python3
"""
Quantum Circuits Examples
=========================
Build and run quantum circuits.
"""

import numpy as np
from ule.quantum import QuantumCircuit, QuantumVisualizer

print("=" * 60)
print("ULE Quantum Computing - Circuit Examples")
print("=" * 60)

# ========== 1. Bell State Circuit ==========
print("\n1. BELL STATE CIRCUIT")
print("-" * 40)

# Create Bell state: (|00⟩ + |11⟩)/√2
circuit = QuantumCircuit(num_qubits=2, name="Bell State")
circuit.h(0)
circuit.cnot(0, 1)

# Visualize
visualizer = QuantumVisualizer()
print(visualizer.circuit_diagram(circuit, "Bell State"))

# Execute
result = circuit.execute()
print(f"\nState vector: {result.final_state}")
print(f"Execution time: {result.execution_time_ms:.4f} ms")

# Simulate with shots
counts = circuit.simulate(shots=100, seed=42)
print("\nMeasurement results (100 shots):")
print(visualizer.measurement_results(counts, "Bell State"))

# ========== 2. GHZ State (3-qubit entanglement) ==========
print("\n2. GHZ STATE (3-QUBIT)")
print("-" * 40)

# Create GHZ state: (|000⟩ + |111⟩)/√2
circuit = QuantumCircuit(num_qubits=3, name="GHZ State")
circuit.h(0)
circuit.cnot(0, 1)
circuit.cnot(1, 2)

print(visualizer.circuit_diagram(circuit, "GHZ State"))

result = circuit.execute()
print(f"\nState vector length: {len(result.final_state)}")

counts = circuit.simulate(shots=100, seed=42)
print("\nMeasurement results (100 shots):")
print(visualizer.measurement_results(counts, "GHZ State"))

# ========== 3. Quantum Random Number Generator ==========
print("\n3. QUANTUM RANDOM NUMBER GENERATOR")
print("-" * 40)

# Use Hadamard gates to generate random bits
circuit = QuantumCircuit(num_qubits=4, name="QRNG")
for i in range(4):
    circuit.h(i)

print(visualizer.circuit_diagram(circuit, "4-qubit QRNG"))

counts = circuit.simulate(shots=50, seed=None)  # No seed for true randomness
print("\nRandom bit generation (50 shots):")
print(visualizer.measurement_results(counts, "QRNG"))

# ========== 4. Swap Test Circuit ==========
print("\n4. SWAP TEST CIRCUIT")
print("-" * 40)

# Simple swap test for comparing states
circuit = QuantumCircuit(num_qubits=3, name="Swap Test")
circuit.h(0)  # Control qubit in superposition
circuit.cnot(1, 2)  # Prepare state to compare
circuit.cswap(0, 1, 2) if hasattr(circuit, 'cswap') else circuit.swap(1, 2)
circuit.h(0)

print(visualizer.circuit_diagram(circuit, "Swap Test"))

# ========== 5. Custom Gate Sequence ==========
print("\n5. CUSTOM GATE SEQUENCE")
print("-" * 40)

circuit = QuantumCircuit(num_qubits=2, name="Custom Sequence")

# Apply sequence of gates
circuit.h(0)
circuit.x(1)
circuit.cnot(0, 1)
circuit.z(0)
circuit.y(1)

print(visualizer.circuit_diagram(circuit, "Custom Sequence"))

result = circuit.execute()
print(f"\nFinal state hash: {result.state_hash}")

counts = circuit.simulate(shots=100, seed=42)
print("\nMeasurement results:")
print(visualizer.measurement_results(counts, "Custom Sequence"))

# ========== 6. Circuit Statistics ==========
print("\n6. CIRCUIT STATISTICS")
print("-" * 40)

circuit = QuantumCircuit(num_qubits=3, name="Stats Demo")
circuit.h(0)
circuit.h(1)
circuit.h(2)
circuit.cnot(0, 1)
circuit.cnot(1, 2)

print(f"Circuit name: {circuit.name}")
print(f"Number of qubits: {circuit.num_qubits}")
print(f"Circuit depth: {circuit.depth}")
print(f"Number of operations: {len(circuit.operations)}")

# Export circuit
circuit_dict = circuit.to_dict()
print(f"\nCircuit as dict: {circuit_dict['name']}")
print(f"Operations: {len(circuit_dict['operations'])}")

print("\n" + "=" * 60)
print("Circuit examples completed!")
print("=" * 60)
