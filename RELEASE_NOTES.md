# ULE 0.1.0 - Initial Release with Quantum Computing

**Release Date:** March 14, 2026

## 🎉 The First Release of ULE!

ULE (Universal Ledger Engine) is a unified database that combines **SQL + NoSQL + Graph + Vector + Quantum** in a single `.udb` file with blockchain audit trail, natural language queries in 9 languages, and quantum computing capabilities!

## ✨ Features in 0.1.0

### Quantum Computing Module
- **Qubit Simulation** - Up to 20 qubits with NumPy backend
- **Quantum Gates** - X, Y, Z, H, S, T, CNOT, CZ, SWAP, Toffoli, Fredkin
- **Circuit Builder** - Build and execute quantum circuits
- **Visualization** - Bloch sphere, circuit diagrams, probability distributions

### Quantum Algorithms
- **Grover's Search** - O(√N) unsorted database search
- **Deutsch-Jozsa** - Constant vs balanced function determination
- **Quantum Fourier Transform** - Quantum analogue of DFT
- **Bernstein-Vazirani** - Hidden string finding
- **Quantum Teleportation** - State transfer via entanglement
- **Superdense Coding** - Send 2 bits with 1 qubit

### IBM Qiskit Integration
- Run circuits on real IBM quantum computers
- Qiskit Aer simulator support
- Job management and result retrieval

### Security Features
- Input validation for all quantum operations
- Unitarity verification for gates
- State normalization checks
- Complete audit logging
- State integrity hashes

## 🚀 Quick Start - Quantum

### Installation
```bash
# Install with quantum support
pip install ule-db[quantum]

# Or install dependencies manually
pip install numpy qiskit qiskit-aer scipy matplotlib
```

### CLI Commands
```bash
# Initialize quantum register
ule quantum init --qubits 2 --state 00

# Apply gates
ule quantum gate --gate H --target 0
ule quantum gate --gate CNOT --target 1 --control 0

# Run circuits
ule quantum circuit --name bell --qubits 2

# Run algorithms
ule quantum algorithm --algorithm grover --params '{"n":3,"target":5}'
ule quantum algorithm --algorithm bernstein-vazirani --params '{"n":4,"secret":10}'

# Show info
ule quantum info
```

### Python API
```python
from ule.quantum import Qubit, QuantumCircuit, QuantumAlgorithms
import numpy as np

# Create qubit in superposition
qubit = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
print(f"P(|0⟩) = {qubit.get_probabilities()[0]:.2f}")

# Build Bell state circuit
circuit = QuantumCircuit(num_qubits=2)
circuit.h(0)
circuit.cnot(0, 1)
result = circuit.execute()

# Run Grover's algorithm
algo = QuantumAlgorithms()
result = algo.grover_search(oracle_target=5, n=3)
print(f"Found: {result.output}")
```

## 📚 New Documentation

- [Quantum Computing Guide](docs/QUANTUM.md) - Complete quantum reference
- [Examples](examples/quantum/) - Working quantum scripts

## 📦 New Example Scripts

```bash
# Quantum basics
python examples/quantum/01_basics.py

# Quantum circuits
python examples/quantum/02_circuits.py

# Quantum algorithms
python examples/quantum/03_algorithms.py
```

## 🔄 This is the First Release

This is the **initial release (v0.1.0)** with:
- SQL + NoSQL + Graph + Vector + Quantum support
- Natural language queries in 9 languages
- Blockchain audit trail
- Web UI and Terminal UI with quantum features
- Full security features
- 6 quantum algorithms
- IBM Qiskit integration

### File Structure
```
ule/
├── quantum/              # NEW - Quantum Module
│   ├── __init__.py
│   ├── qubit.py          # Qubit representation
│   ├── gates.py          # Quantum gates
│   ├── circuit.py        # Circuit builder
│   ├── algorithms.py     # Quantum algorithms
│   ├── qiskit_backend.py # IBM integration
│   └── visualization.py  # Visualizations
├── engines/
│   └── quantum_engine.py # NEW - Quantum storage
```

## 📊 Project Stats (v0.1.0)

- **58 Python files**
- **~6,000 lines of code**
- **10 languages supported**
- **5 database engines** (SQL, NoSQL, Graph, Vector, Quantum)
- **22+ CLI commands**
- **6 quantum algorithms**
- **15+ quantum gates**

## 🔧 Technical Details

### Dependencies
- **Core:** numpy>=1.24.0 (new)
- **Quantum (optional):** qiskit>=0.44.0, qiskit-aer>=0.12.0, scipy>=1.10.0, matplotlib>=3.7.0

### System Requirements
- Python 3.10+
- For quantum: NumPy required
- For IBM hardware: Qiskit and API token

## 🐛 Known Issues

This is an **alpha release**. Some features may be unstable:
- Quantum simulation limited to ~20 qubits (classical simulation)
- IBM Quantum requires API token and internet connection
- Some algorithms use simplified oracles for demonstration
- Matplotlib visualization optional (falls back to ASCII)

## 📝 Previous Releases

### ULE 0.1.0 - Initial Release
**Release Date:** March 14, 2026

The initial release with:
- SQL + NoSQL + Graph + Vector support
- Natural language queries in 9 languages
- Blockchain audit trail
- Web UI and Terminal UI
- Full security features

See full [0.1.0 notes](#ule-010---initial-release) below.

---

**ULE = One File, Every Model, Absolute Trust, Zero Cost, Quantum Ready**
