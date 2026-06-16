"""Web UI Routes for ULE."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import numpy as np

from ule import connect
from ule.ai import NaturalLanguageQuery
from ule.security.web_security import require_auth, validate_request_data
from ule.quantum import (
    Qubit, QubitRegister, QuantumGates, QuantumCircuit,
    QuantumAlgorithms, QuantumVisualizer
)
from ule.engines.quantum_engine import QuantumEngine

router = APIRouter()

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Global database connection
_db = None
_db_path = None


def get_db():
    """Get database connection."""
    global _db
    if _db is None:
        raise HTTPException(status_code=400, detail="No database connected")
    return _db


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with login check."""
    is_authenticated = hasattr(request.state, "user") and request.state.user
    return templates.TemplateResponse("index.html", {
        "request": request,
        "db_path": _db_path,
        "connected": _db is not None,
        "authenticated": is_authenticated
    })


@router.post("/connect")
@require_auth
async def connect_db(db_path: str = Form(...)):
    """Connect to database."""
    global _db, _db_path
    try:
        # Sanitize path
        db_path = db_path.strip()
        if not db_path.endswith('.udb'):
            db_path = db_path + '.udb'

        _db = connect(db_path, create_if_missing=True)
        _db_path = db_path
        return {"success": True, "message": f"Connected to {db_path}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disconnect")
@require_auth
async def disconnect_db():
    """Disconnect from database."""
    global _db, _db_path
    if _db:
        _db.close()
        _db = None
        _db_path = None
    return {"success": True, "message": "Disconnected"}


@router.post("/query")
@require_auth
async def run_query(
    sql: str = Form(...),
    query_type: str = Form(default="sql")
):
    """Execute SQL or natural language query."""
    db = get_db()
    try:
        # Sanitize SQL input
        sql = sql.strip()

        if query_type == "nlq":
            nlq = NaturalLanguageQuery(db._conn)
            results = nlq.ask(sql, language="en")
        else:
            results = db.execute(sql)

        # Convert to list of dicts
        if isinstance(results, list):
            rows = [dict(row) for row in results]
        else:
            rows = [{"result": results}]

        return JSONResponse(content={"success": True, "rows": rows, "count": len(rows)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
@require_auth
async def get_stats():
    """Get database statistics."""
    db = get_db()
    try:
        tables = db.execute("SELECT COUNT(*) as count FROM _tables")[0]['count']
        docs = db.execute("SELECT COUNT(*) as count FROM _documents")[0]['count']
        edges = db.execute("SELECT COUNT(*) as count FROM _edges")[0]['count']
        vectors = db.execute("SELECT COUNT(*) as count FROM _vectors")[0]['count']
        audit = db.execute("SELECT COUNT(*) as count FROM _audit")[0]['count']

        return {
            "success": True,
            "stats": {
                "tables": tables,
                "documents": docs,
                "edges": edges,
                "vectors": vectors,
                "audit_blocks": audit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tables")
@require_auth
async def list_tables():
    """List all tables."""
    db = get_db()
    try:
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'")
        return {"success": True, "tables": [t['name'] for t in tables]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/push")
@require_auth
async def push_document(
    collection: str = Form(...),
    data: str = Form(...)
):
    """Push document to collection."""
    db = get_db()
    try:
        # Validate collection name
        collection = collection.strip()
        if not collection.isidentifier():
            raise HTTPException(status_code=400, detail="Invalid collection name")

        # Parse and validate JSON
        doc_data = json.loads(data)
        if not isinstance(doc_data, dict):
            raise HTTPException(status_code=400, detail="Data must be a JSON object")

        doc_id = db.push(collection, doc_data)
        return {"success": True, "doc_id": doc_id}
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/find/{collection}")
@require_auth
async def find_documents(collection: str):
    """Find documents in collection."""
    db = get_db()
    try:
        # Validate collection name
        if not collection.isidentifier():
            raise HTTPException(status_code=400, detail="Invalid collection name")

        docs = db.find(collection)
        return {"success": True, "documents": [dict(d) for d in docs], "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/link")
@require_auth
async def create_link(
    from_table: str = Form(...),
    from_id: str = Form(...),
    to_table: str = Form(...),
    to_id: str = Form(...),
    relation: str = Form(...)
):
    """Create graph relationship."""
    db = get_db()
    try:
        # Validate inputs
        from_table = from_table.strip()
        to_table = to_table.strip()
        from_id = from_id.strip()
        to_id = to_id.strip()
        relation = relation.strip().upper()

        if not from_table.isidentifier() or not to_table.isidentifier():
            raise HTTPException(status_code=400, detail="Invalid table name")

        if not relation.isidentifier():
            raise HTTPException(status_code=400, detail="Invalid relation name")

        db.link(from_table, from_id, to_table, to_id, relation)
        return {"success": True, "message": f"Linked {from_table}:{from_id} → {relation} → {to_table}:{to_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/traverse/{table}/{node_id}")
@require_auth
async def traverse_graph(table: str, node_id: str, depth: int = 2):
    """Traverse graph from node."""
    db = get_db()
    try:
        # Validate inputs
        table = table.strip()
        node_id = node_id.strip()

        if not table.isidentifier():
            raise HTTPException(status_code=400, detail="Invalid table name")

        if depth < 1 or depth > 10:
            depth = 2  # Default to safe value

        edges = db.traverse(table, node_id, depth=depth)
        return {"success": True, "edges": [dict(e) for e in edges], "count": len(edges)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify")
@require_auth
async def verify_db():
    """Verify database integrity."""
    db = get_db()
    try:
        is_valid = db.verify()
        return {"success": True, "valid": is_valid, "message": "Database integrity verified" if is_valid else "Database verification failed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/audit")
@require_auth
async def get_audit(limit: int = 20):
    """Get audit trail."""
    db = get_db()
    try:
        # Limit max results
        limit = min(limit, 100)

        audit = db.audit()
        recent = audit[-limit:] if len(audit) > limit else audit
        return {"success": True, "audit": [dict(a) for a in recent], "total": len(audit)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Quantum Computing Routes ============

@router.get("/quantum")
@require_auth
async def quantum_home():
    """Quantum computing home."""
    return {"success": True, "message": "Quantum Computing API", "endpoints": [
        "/quantum/init", "/quantum/gate", "/quantum/circuit",
        "/quantum/algorithm", "/quantum/visualize", "/quantum/info"
    ]}


@router.post("/quantum/init")
@require_auth
async def quantum_init(
    num_qubits: int = Form(...),
    initial_state: str = Form(default=None)
):
    """Initialize quantum register."""
    try:
        # Security: Validate inputs
        if num_qubits < 1 or num_qubits > 10:
            raise HTTPException(status_code=400, detail="Qubits must be 1-10")
        
        if initial_state is None:
            initial_state = "0" * num_qubits
        
        if len(initial_state) != num_qubits:
            raise HTTPException(status_code=400, detail="State length must match qubit count")
        
        if not all(c in "01" for c in initial_state):
            raise HTTPException(status_code=400, detail="State must contain only 0s and 1s")
        
        register = QubitRegister(num_qubits=num_qubits, initial_state=initial_state)
        
        return {
            "success": True,
            "num_qubits": num_qubits,
            "initial_state": initial_state,
            "state_vector_shape": list(register.state_vector.shape),
            "probabilities": [float(q.get_probabilities()[0]) for q in register.qubits]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quantum/gate")
@require_auth
async def quantum_apply_gate(
    gate_name: str = Form(...),
    target: int = Form(...),
    control: int = Form(default=None),
    num_qubits: int = Form(default=2),
    initial_state: str = Form(default=None)
):
    """Apply quantum gate."""
    try:
        # Security: Validate inputs
        if target < 0 or target >= num_qubits:
            raise HTTPException(status_code=400, detail="Invalid target qubit")
        
        if control is not None and control == target:
            raise HTTPException(status_code=400, detail="Control and target must differ")
        
        if initial_state is None:
            initial_state = "0" * num_qubits
        
        register = QubitRegister(num_qubits=num_qubits, initial_state=initial_state)
        gates = QuantumGates()
        
        gate_map = {
            "H": gates.hadamard, "X": gates.pauli_x, "Y": gates.pauli_y,
            "Z": gates.pauli_z, "S": gates.phase_s, "T": gates.phase_t
        }
        
        if gate_name.upper() in gate_map:
            gate_matrix = gate_map[gate_name.upper()]()
            register.apply_gate(gate_matrix, target, gate_name.upper())
        elif gate_name.upper() == "CNOT" and control is not None:
            register.apply_two_qubit_gate(gates.cnot(), control, target, "CNOT")
        elif gate_name.upper() == "CZ" and control is not None:
            register.apply_two_qubit_gate(gates.cz(), control, target, "CZ")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown gate: {gate_name}")
        
        return {
            "success": True,
            "gate": gate_name.upper(),
            "target": target,
            "control": control,
            "probabilities": [float(q.get_probabilities()[0]) for q in register.qubits]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quantum/circuit")
@require_auth
async def quantum_circuit(
    name: str = Form(default="Circuit"),
    num_qubits: int = Form(...),
    operations: str = Form(...)  # JSON string of operations
):
    """Build and run quantum circuit."""
    try:
        import json as json_lib
        ops = json_lib.loads(operations)
        
        # Security: Validate operations
        if not isinstance(ops, list):
            raise HTTPException(status_code=400, detail="Operations must be a list")
        
        if len(ops) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 operations")
        
        circuit = QuantumCircuit(num_qubits=num_qubits, name=name)
        
        for op in ops:
            gate = op.get("gate", "").upper()
            target = op.get("target", 0)
            control = op.get("control")
            
            if gate in ["H", "X", "Y", "Z", "S", "T"]:
                getattr(circuit, gate.lower())(target)
            elif gate == "CNOT" and control is not None:
                circuit.cnot(control, target)
            elif gate == "CZ" and control is not None:
                circuit.cz(control, target)
        
        # Execute circuit
        shots = int(op.get("shots", 100))
        counts = circuit.simulate(shots=shots, seed=42)
        
        return {
            "success": True,
            "name": name,
            "depth": circuit.depth,
            "measurements": counts,
            "total_shots": sum(counts.values())
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quantum/algorithm")
@require_auth
async def quantum_algorithm(
    algorithm: str = Form(...),
    params: str = Form(default="{}")
):
    """Run quantum algorithm."""
    try:
        import json as json_lib
        algo_params = json_lib.loads(params)
        
        algorithms = QuantumAlgorithms()
        
        if algorithm == "deutsch-jozsa":
            n = algo_params.get("n", 3)
            func_type = algo_params.get("type", "constant")
            oracle = lambda x: 0 if func_type == "constant" else lambda x: x % 2
            result = algorithms.deutsch_jozsa(oracle, n)
            
        elif algorithm == "grover":
            n = algo_params.get("n", 3)
            target = algo_params.get("target", 5)
            result = algorithms.grover_search(target, n)
            
        elif algorithm == "bernstein-vazirani":
            n = algo_params.get("n", 4)
            secret = algo_params.get("secret", 10)
            result = algorithms.bernstein_vazirani(secret, n)
            
        elif algorithm == "qft":
            n = algo_params.get("n", 3)
            input_state = algo_params.get("input", 1)
            result = algorithms.quantum_fourier_transform(input_state, n)
            
        elif algorithm == "teleportation":
            state_type = algo_params.get("state", "plus")
            if state_type == "zero":
                state = (1.0, 0.0)
            elif state_type == "one":
                state = (0.0, 1.0)
            else:
                state = (1/np.sqrt(2), 1/np.sqrt(2))
            result = algorithms.quantum_teleportation(state, seed=42)
            
        elif algorithm == "superdense":
            message = algo_params.get("message", 2)
            result = algorithms.superdense_coding(message, seed=42)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown algorithm: {algorithm}")
        
        return {
            "success": True,
            "algorithm": algorithm,
            "result": result.output,
            "success_flag": result.success,
            "execution_time_ms": result.execution_time_ms
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quantum/visualize")
@require_auth
async def quantum_visualize(viz_type: str = "bloch"):
    """Visualize quantum state."""
    try:
        visualizer = QuantumVisualizer()
        qubit = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))
        
        if viz_type == "bloch":
            output = visualizer.bloch_sphere(qubit, "Qubit |+⟩")
        elif viz_type == "state":
            register = QubitRegister(num_qubits=2, initial_state="00")
            output = visualizer.state_vector(register, "2-Qubit Register")
        elif viz_type == "distribution":
            register = QubitRegister(num_qubits=2, initial_state="00")
            output = visualizer.probability_distribution(register, "Probabilities")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown visualization: {viz_type}")
        
        return {"success": True, "visualization": output}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quantum/info")
@require_auth
async def quantum_info():
    """Get quantum engine info."""
    try:
        engine = QuantumEngine()
        stats = engine.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
