# ULE Quantum Computing Guide

## Overview

The ULE Quantum Computing Module provides comprehensive quantum computing capabilities integrated with the Universal Lite Database. This module enables you to:

- Create and manipulate qubits
- Build quantum circuits
- Run quantum algorithms
- Visualize quantum states
- Interface with IBM Quantum computers

## Installation

```bash
pip install ule-db[quantum]
```

Or install dependencies manually:

```bash
pip install qiskit qiskit-aer numpy scipy matplotlib
```

## Quick Start

### 1. Create a Qubit

```python
from ule.quantum import Qubit
import numpy as np

# Create a qubit in superposition
qubit = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))

print(f"State: α={qubit.alpha}, β={qubit.beta}")
print(f"P(|0⟩) = {qubit.get_probabilities()[0]:.2f}")
print(f"P(|1⟩) = {qubit.get_probabilities()[1]:.2f}")

# Measure the qubit
result = qubit.measure()
print(f"Measurement result: {result}")
```

### 2. Apply Quantum Gates

```python
from ule.quantum import Qubit, QuantumGates

# Start with |0⟩
qubit = Qubit()

# Apply Hadamard gate
gates = QuantumGates()
qubit.apply_gate(gates.hadamard(), "H")

print(f"After Hadamard: P(|0⟩) = {qubit.get_probabilities()[0]:.2f}")

# Apply Pauli-X gate
qubit.apply_gate(gates.pauli_x(), "X")

# Measure
result = qubit.measure()
print(f"Measurement: {result}")
```

### 3. Build Quantum Circuits

```python
from ule.quantum import QuantumCircuit, QuantumVisualizer

# Create a 2-qubit circuit
circuit = QuantumCircuit(num_qubits=2, name="Bell State")

# Create Bell state: (|00⟩ + |11⟩)/√2
circuit.h(0)
circuit.cnot(0, 1)

# Visualize
visualizer = QuantumVisualizer()
print(visualizer.circuit_diagram(circuit, "Bell State"))

# Execute
result = circuit.execute()
print(f"State vector: {result.final_state}")

# Simulate with shots
counts = circuit.simulate(shots=100)
print(visualizer.measurement_results(counts, "Bell State Measurements"))
```

### 4. Run Quantum Algorithms

```python
from ule.quantum import QuantumAlgorithms

algorithms = QuantumAlgorithms()

# Grover's Search
result = algorithms.grover_search(oracle_target=5, n=3)
print(f"Grover found: {result.output}, Success: {result.success}")

# Bernstein-Vazirani
result = algorithms.bernstein_vazirani(secret=10, n=4)
print(f"Secret found: {result.output['found']}")

# Superdense Coding
result = algorithms.superdense_coding(message=2)
print(f"Sent: {result.output['bits_sent']}, Received: {result.output['bits_received']}")
```

## CLI Usage

### Initialize Quantum Register

```bash
ule quantum init --qubits 3 --state 000
```

### Apply Gates

```bash
ule quantum gate --gate H --target 0
ule quantum gate --gate CNOT --target 1 --control 0
```

### Run Circuits

```bash
ule quantum circuit --name bell --qubits 2
```

### Run Algorithms

```bash
ule quantum algorithm --algorithm grover --params '{"n": 3, "target": 5}'
ule quantum algorithm --algorithm bernstein-vazirani --params '{"n": 4, "secret": 10}'
```

### Show Info

```bash
ule quantum info
```

## Available Gates

### Single-Qubit Gates

| Gate | Name | Matrix | Description |
|------|------|--------|-------------|
| I | Identity | `[[1,0],[0,1]]` | No operation |
| X | Pauli-X | `[[0,1],[1,0]]` | NOT gate, flips |0⟩ ↔ |1⟩ |
| Y | Pauli-Y | `[[0,-i],[i,0]]` | Rotation around Y-axis |
| Z | Pauli-Z | `[[1,0],[0,-1]]` | Phase flip |
| H | Hadamard | `1/√2[[1,1],[1,-1]]` | Creates superposition |
| S | Phase | `[[1,0],[0,i]]` | √Z gate |
| T | T gate | `[[1,0],[0,e^(iπ/4)]]` | √S gate |

### Two-Qubit Gates

| Gate | Name | Description |
|------|------|-------------|
| CNOT | Controlled-NOT | Flips target if control is |1⟩ |
| CZ | Controlled-Z | Applies Z if control is |1⟩ |
| SWAP | SWAP | Swaps two qubit states |

### Three-Qubit Gates

| Gate | Name | Description |
|------|------|-------------|
| TOFFOLI | CCNOT | Flips target if both controls are |1⟩ |
| FREDKIN | CSWAP | Swaps if control is |1⟩ |

## Quantum Algorithms

### Deutsch-Jozsa Algorithm

Determines if a function is constant or balanced with a single query.

```python
algo = QuantumAlgorithms()

# Constant function
result = algo.deutsch_jozsa(lambda x: 0, n=3)
print(f"Function is: {result.output}")  # "constant"

# Balanced function
result = algo.deutsch_jozsa(lambda x: x % 2, n=3)
print(f"Function is: {result.output}")  # "balanced"
```

### Grover's Search Algorithm

Searches an unsorted database of N items in O(√N) time.

```python
algo = QuantumAlgorithms()

# Find item 5 in 8-item database
result = algo.grover_search(oracle_target=5, n=3)
print(f"Found: {result.output}")
```

### Quantum Fourier Transform

Quantum analogue of the discrete Fourier transform.

```python
algo = QuantumAlgorithms()

result = algo.quantum_fourier_transform(input_state=1, n=3)
print(f"Peak at: {result.output['peak_index']}")
```

### Quantum Teleportation

Teleports a quantum state using entanglement.

```python
algo = QuantumAlgorithms()

# Teleport |+⟩ state
state = (1/np.sqrt(2), 1/np.sqrt(2))
result = algo.quantum_teleportation(state)
print(f"Protocol complete: {result.output['protocol_complete']}")
```

### Superdense Coding

Send 2 classical bits using 1 qubit.

```python
algo = QuantumAlgorithms()

result = algo.superdense_coding(message=3)
print(f"Sent: {result.output['bits_sent']}")
print(f"Received: {result.output['bits_received']}")
```

### Bernstein-Vazirani Algorithm

Finds a hidden bit string with a single query.

```python
algo = QuantumAlgorithms()

result = algo.bernstein_vazirani(secret=10, n=4)
print(f"Secret: {result.output['found']}")
```

## Security Features

### Input Validation

All quantum operations validate inputs:

```python
from ule.quantum import Qubit, QuantumValidationError

try:
    # This will raise an error (not normalized)
    qubit = Qubit(alpha=2.0, beta=0.0)
except QuantumValidationError as e:
    print(f"Validation error: {e}")
```

### Audit Logging

All operations are logged for auditing:

```python
qubit = Qubit(user_id="alice")
qubit.apply_gate(gates.hadamard(), "H")
qubit.measure()

for entry in qubit.audit_log:
    print(f"{entry.operation} at {entry.timestamp}")
```

### State Integrity

State hashes ensure integrity:

```python
circuit = QuantumCircuit(num_qubits=2)
circuit.h(0)
circuit.cnot(0, 1)

result = circuit.execute()
print(f"State hash: {result.state_hash}")
```

## Visualization

### Bloch Sphere

```python
from ule.quantum import Qubit, QuantumVisualizer

qubit = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
visualizer = QuantumVisualizer()

# ASCII representation
print(visualizer.bloch_sphere(qubit, "Qubit |+⟩"))

# Save image (requires matplotlib)
image = visualizer.bloch_sphere(qubit, save_path="bloch.png")
```

### Circuit Diagrams

```python
circuit = QuantumCircuit(num_qubits=2, name="Bell")
circuit.h(0)
circuit.cnot(0, 1)

visualizer = QuantumVisualizer()
print(visualizer.circuit_diagram(circuit, "Bell State Circuit"))
```

### Probability Distributions

```python
from ule.quantum import QubitRegister

register = QubitRegister(num_qubits=3, initial_state="000")
print(visualizer.probability_distribution(register, "Initial State"))
```

## IBM Qiskit Integration

### Setup

```python
from ule.quantum import QiskitBackend

# With API token
qiskit = QiskitBackend(api_token="your_ibm_token")

# Or set environment variable
# export IBM_QUANTUM_TOKEN="your_ibm_token"
qiskit = QiskitBackend()
```

### Run on Simulator

```python
from ule.quantum import QuantumCircuit

circuit = QuantumCircuit(num_qubits=2)
circuit.h(0)
circuit.cnot(0, 1)

result = qiskit.run_simulator(circuit, shots=1024)
print(f"Counts: {result.measurements}")
```

### Run on Real Hardware

```python
# Connect to IBM
qiskit.connect_to_ibm()

# List backends
print(qiskit.list_backends())

# Run on hardware
job = qiskit.run_on_hardware(circuit, backend_name="ibmq_quito")
print(f"Job ID: {job.job_id}")

# Get results later
result = qiskit.get_job_result(job.job_id)
```

## Quantum Engine

The Quantum Engine provides persistent storage for quantum states and circuits.

```python
from ule.engines.quantum_engine import QuantumEngine

engine = QuantumEngine(encryption_key=b"secret_key")

# Create and store state
state = engine.create_state(num_qubits=2, initial_state="00")
print(f"State ID: {state.state_id}")

# Save circuit
circuit = QuantumCircuit(num_qubits=2)
circuit.h(0)
circuit.cnot(0, 1)
record = engine.save_circuit(circuit)
print(f"Circuit ID: {record.circuit_id}")

# List stored items
print(engine.list_states())
print(engine.list_circuits())

# Get stats
print(engine.get_stats())
```

## API Reference

### Qubit

```python
Qubit(alpha=1.0, beta=0.0, qubit_id=None, user_id=None)
```

**Properties:**
- `alpha`: Complex amplitude for |0⟩
- `beta`: Complex amplitude for |1⟩
- `qubit_id`: Unique identifier
- `state_vector`: NumPy array representation
- `audit_log`: List of operations

**Methods:**
- `get_probabilities()`: Returns (P(|0⟩), P(|1⟩))
- `measure(seed=None)`: Measures qubit, returns 0 or 1
- `apply_gate(matrix, gate_name)`: Applies unitary gate
- `reset()`: Resets to |0⟩
- `to_dict()`: Serializes to dictionary

### QubitRegister

```python
QubitRegister(num_qubits, initial_state="0", user_id=None)
```

**Methods:**
- `get_qubit(index)`: Get qubit at index
- `apply_gate(matrix, target, gate_name)`: Apply single-qubit gate
- `apply_two_qubit_gate(matrix, control, target, gate_name)`: Apply two-qubit gate
- `measure_all(seed=None)`: Measure all qubits
- `reset_all()`: Reset all qubits to |0⟩

### QuantumCircuit

```python
QuantumCircuit(num_qubits, name="circuit", user_id=None)
```

**Methods:**
- `h(target)`, `x(target)`, `y(target)`, `z(target)`, `s(target)`, `t(target)`: Single-qubit gates
- `cnot(control, target)`, `cz(control, target)`, `swap(q1, q2)`: Two-qubit gates
- `toffoli(c1, c2, target)`: Three-qubit gate
- `execute(initial_state, measure, seed)`: Execute circuit
- `simulate(initial_state, shots, seed)`: Simulate with multiple shots
- `draw()`: Return ASCII diagram

### QuantumAlgorithms

```python
QuantumAlgorithms(user_id=None)
```

**Methods:**
- `deutsch_jozsa(oracle_func, n)`: Deutsch-Jozsa algorithm
- `grover_search(oracle_target, n, num_iterations)`: Grover's algorithm
- `quantum_fourier_transform(input_state, n)`: QFT
- `quantum_teleportation(state_to_teleport, seed)`: Teleportation
- `superdense_coding(message, seed)`: Superdense coding
- `bernstein_vazirani(secret, n)`: Bernstein-Vazirani

## Troubleshooting

### Qiskit Not Available

If Qiskit is not installed, the module will use the native NumPy simulator:

```bash
pip install qiskit qiskit-aer
```

### Matplotlib Not Available

Visualization will fall back to ASCII art:

```bash
pip install matplotlib
```

### State Not Normalized Error

Ensure |α|² + |β|² = 1:

```python
# Correct
alpha = 1/np.sqrt(2)
beta = 1/np.sqrt(2)
qubit = Qubit(alpha, beta)
```

## Performance Notes

- Maximum 20 qubits supported for simulation
- Maximum 10,000 operations per circuit
- Simulation time grows exponentially with qubit count
- Use IBM Quantum for larger circuits

## License

MIT License - Free and Open Source
