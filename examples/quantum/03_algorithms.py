#!/usr/bin/env python3
"""
Quantum Algorithms Examples
===========================
Run famous quantum algorithms.
"""

import numpy as np
from ule.quantum import QuantumAlgorithms, QuantumVisualizer

print("=" * 60)
print("ULE Quantum Computing - Algorithm Examples")
print("=" * 60)

algorithms = QuantumAlgorithms()
visualizer = QuantumVisualizer()

# ========== 1. Deutsch-Jozsa Algorithm ==========
print("\n1. DEUTSCH-JOZSA ALGORITHM")
print("-" * 40)
print("Determines if a function is constant or balanced")

# Constant function (always returns 0)
def constant_func(x):
    return 0

result = algorithms.deutsch_jozsa(constant_func, n=3)
print(f"\nConstant function test:")
print(f"  Result: {result.output}")
print(f"  Success: {result.success}")
print(f"  Execution time: {result.execution_time_ms:.4f} ms")

# Balanced function (returns parity)
def balanced_func(x):
    return x % 2

result = algorithms.deutsch_jozsa(balanced_func, n=3)
print(f"\nBalanced function test:")
print(f"  Result: {result.output}")
print(f"  Success: {result.success}")

# ========== 2. Grover's Search Algorithm ==========
print("\n2. GROVER'S SEARCH ALGORITHM")
print("-" * 40)
print("Searches unsorted database in O(√N) time")

# Search for item 5 in 8-item database (3 qubits)
result = algorithms.grover_search(oracle_target=5, n=3)
print(f"\nSearching for item 5 in 8-item database:")
print(f"  Found: {result.output}")
print(f"  Success: {result.success}")
print(f"  Execution time: {result.execution_time_ms:.4f} ms")

# Search for different targets
for target in [0, 3, 7]:
    result = algorithms.grover_search(oracle_target=target, n=3)
    print(f"  Target {target}: Found {result.output}, Success: {result.success}")

# ========== 3. Bernstein-Vazirani Algorithm ==========
print("\n3. BERNSTEIN-VAZIRANI ALGORITHM")
print("-" * 40)
print("Finds hidden bit string with single query")

# Find secret = 10 (binary: 1010)
result = algorithms.bernstein_vazirani(secret=10, n=4)
print(f"\nFinding secret 10 (binary: 1010):")
print(f"  Found: {result.output['found']}")
print(f"  Binary: {result.output['binary']}")
print(f"  Success: {result.success}")

# Test with different secrets
for secret in [0, 5, 15]:
    result = algorithms.bernstein_vazirani(secret=secret, n=4)
    print(f"  Secret {secret}: Found {result.output['found']}, Success: {result.success}")

# ========== 4. Quantum Fourier Transform ==========
print("\n4. QUANTUM FOURIER TRANSFORM")
print("-" * 40)
print("Quantum analogue of discrete Fourier transform")

result = algorithms.quantum_fourier_transform(input_state=1, n=3)
print(f"\nQFT on state |001⟩:")
print(f"  Peak index: {result.output['peak_index']}")
print(f"  Probabilities: {result.output['probabilities'][:4]}...")  # Show first 4

# ========== 5. Quantum Teleportation ==========
print("\n5. QUANTUM TELEPORTATION")
print("-" * 40)
print("Teleports quantum state using entanglement")

# Teleport |+⟩ state
state = (1/np.sqrt(2), 1/np.sqrt(2))
result = algorithms.quantum_teleportation(state, seed=42)
print(f"\nTeleporting |+⟩ state:")
print(f"  Protocol complete: {result.output['protocol_complete']}")
print(f"  Alice's measurement: {result.output.get('alice_measurement', 'N/A')}")
print(f"  Success: {result.success}")

# Teleport |0⟩ state
result = algorithms.quantum_teleportation((1.0, 0.0), seed=42)
print(f"\nTeleporting |0⟩ state:")
print(f"  Protocol complete: {result.output['protocol_complete']}")

# ========== 6. Superdense Coding ==========
print("\n6. SUPERDENSE CODING")
print("-" * 40)
print("Send 2 classical bits using 1 qubit")

# Test all 4 possible messages
for message in range(4):
    result = algorithms.superdense_coding(message, seed=42)
    print(f"  Message {message} ({result.output['bits_sent']}): "
          f"Received {result.output['received']} ({result.output['bits_received']}), "
          f"Success: {result.success}")

# ========== 7. Algorithm Comparison ==========
print("\n7. ALGORITHM COMPARISON")
print("-" * 40)

print("\nPerformance comparison (execution time in ms):")

results = []

# Deutsch-Jozsa
result = algorithms.deutsch_jozsa(lambda x: 0, n=3)
results.append(("Deutsch-Jozsa (n=3)", result.execution_time_ms))

# Grover
result = algorithms.grover_search(5, n=3)
results.append(("Grover (n=3)", result.execution_time_ms))

# Bernstein-Vazirani
result = algorithms.bernstein_vazirani(10, n=4)
results.append(("Bernstein-Vazirani (n=4)", result.execution_time_ms))

# QFT
result = algorithms.quantum_fourier_transform(1, n=3)
results.append(("QFT (n=3)", result.execution_time_ms))

for name, time_ms in results:
    print(f"  {name}: {time_ms:.4f} ms")

print("\n" + "=" * 60)
print("Algorithm examples completed!")
print("=" * 60)
