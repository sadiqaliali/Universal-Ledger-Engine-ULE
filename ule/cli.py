"""ULE Command Line Interface."""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

from ule.core.database import ULEDatabase
from ule.core.connection import connect
from ule.security.keys import KeyManager
from ule.ai.nlq import NaturalLanguageQuery
from ule.utils.helpers import format_table

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="ule")
def main():
    """
    ULE - Universal Ledger Engine
    
    The People's Database - Free, Open Source, Multi-Model
    """
    pass


# ============ INITIALIZATION ============

@main.command()
@click.argument('dbname')
@click.option('--force', '-f', is_flag=True, help="Overwrite if exists")
def init(dbname: str, force: bool):
    """
    ULE Setup Wizard - Professional Database Initialization.
    """
    db_path = Path(dbname)
    if not dbname.endswith('.udb'):
        db_path = Path(dbname + '.udb')
    
    if db_path.exists() and not force:
        console.print(f"[red]Error:[/red] {db_path} already exists. Use --force to overwrite.")
        return
    
    console.print(Panel.fit(
        "[bold cyan]🌌 Universal Ledger Engine (ULE) Setup Wizard[/bold cyan]",
        subtitle="Professional Database Initialization"
    ))
    
    # 1. Admin Password (MANDATORY)
    while True:
        pwd = Prompt.ask("Set Admin Password", password=True)
        if not pwd or len(pwd) < 8:
            console.print("[red]Error:[/red] Admin password must be at least 8 characters.")
            continue
        pwd_confirm = Prompt.ask("Confirm Admin Password", password=True)
        if pwd == pwd_confirm:
            break
        console.print("[red]Error:[/red] Passwords do not match.")
    
    # 2. Features Configuration
    enable_blockchain = click.confirm("Enable Blockchain Audit Trail?", default=True)
    enable_wal = click.confirm("Enable Write-Ahead Logging (WAL)?", default=True)
    enable_quantum = click.confirm("Enable Quantum Simulation Engine?", default=False)
    
    try:
        from ule.core.config import Config
        config = Config()
        config.set("blockchain_enabled", enable_blockchain)
        config.set("wal_enabled", enable_wal)
        config.set("quantum_enabled", enable_quantum)
        
        db = ULEDatabase(str(db_path), config=config)
        db.init(password=pwd)
        
        # Store admin user in _users table
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        pwd_hash = ph.hash(pwd)
        
        db._conn.execute(
            "INSERT OR REPLACE INTO _users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", pwd_hash, "admin")
        )
        db._conn.commit()
        db.close()
        
        console.print(f"\n[green]✓[/green] Database [bold]{db_path.name}[/bold] initialized successfully.")
        console.print(f"[dim]- Encryption: AES-256-GCM (Master Key/Data Key)[/dim]")
        console.print(f"[dim]- Blockchain: {'Enabled' if enable_blockchain else 'Disabled'}[/dim]")
        console.print(f"[dim]- WAL: {'Enabled' if enable_wal else 'Disabled'}[/dim]")
        console.print(f"[dim]- Quantum: {'Enabled' if enable_quantum else 'Disabled'}[/dim]")
        console.print("\n[bold green]Security:[/bold green] Admin user 'admin' created with your password.")
        console.print("[yellow]Keep your password safe! It is the master key for this .udb file.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error during initialization:[/red] {e}")


# ============ QUERY ============

@main.command()
@click.argument('dbname')
@click.argument('query')
@click.option('--password', '-p', help="Database password")
def query(dbname: str, query: str, password: str):
    """Execute SQL query."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        results = db.execute(query)
        
        if results:
            table = Table(title="Query Results")
            
            # Add columns
            for col in results[0].keys():
                table.add_column(col, style="cyan")
            
            # Add rows
            for row in results:
                table.add_row(*[str(v) for v in row.values()])
            
            console.print(table)
            console.print(f"\n[dim]({len(results)} rows)[/dim]")
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ NATURAL LANGUAGE ============

@main.command()
@click.argument('dbname')
@click.argument('question')
@click.option('--language', '-l', default='en',
              type=click.Choice(['en', 'ur', 'urdu', 'zh', 'zh-cn', 'fr', 'ru', 'ja', 'ko', 'es', 'pt']))
@click.option('--password', '-p', help="Database password")
def ask(dbname: str, question: str, language: str, password: str):
    """Ask a question in natural language."""
    # Normalize language code
    lang_map = {
        'urdu': 'ur',
        'zh-cn': 'zh',
        'hindi': 'hi',
    }
    language = lang_map.get(language.lower(), language)
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        nlq = NaturalLanguageQuery(db._conn)
        
        # Translate and execute
        sql = nlq.translate(question, language)
        
        if sql:
            console.print(f"[dim]SQL: {sql}[/dim]\n")
            results = nlq.ask(question, language)
        else:
            console.print(f"[yellow]Could not understand query. Trying direct execution...[/yellow]")
            results = db.execute(question)
        
        if results:
            console.print(format_table(results))
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ DOCUMENTS ============

@main.command()
@click.argument('dbname')
@click.option('--collection', '-c', required=True, help="Collection name")
@click.option('--data', '-d', required=True, help="JSON data")
@click.option('--password', '-p', help="Database password")
def push(dbname: str, collection: str, data: str, password: str):
    """Push document to collection."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        doc_data = json.loads(data)
        
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        doc_id = db.push(collection, doc_data)
        
        console.print(f"[green]✓[/green] Document pushed to [bold]{collection}[/bold]")
        console.print(f"[dim]ID: {doc_id}[/dim]")
        
        db.close()
        
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.argument('dbname')
@click.option('--collection', '-c', required=True, help="Collection name")
@click.option('--query', '-q', help="Filter query (JSON)")
@click.option('--limit', '-l', default=100, help="Max results")
@click.option('--password', '-p', help="Database password")
def find(dbname: str, collection: str, query: str, limit: int, password: str):
    """Find documents in collection."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        query_dict = json.loads(query) if query else None
        
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        results = db.find(collection, query_dict, limit)
        
        if results:
            console.print(format_table(results))
            console.print(f"\n[dim]({len(results)} documents)[/dim]")
        else:
            console.print("[yellow]No documents found[/yellow]")
        
        db.close()
        
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON query:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ GRAPH ============

@main.command()
@click.argument('dbname')
@click.option('--from', 'from_table', required=True, help="Source table")
@click.option('--from-id', 'from_id', required=True, help="Source ID")
@click.option('--to', 'to_table', required=True, help="Target table")
@click.option('--to-id', 'to_id', required=True, help="Target ID")
@click.option('--relation', '-r', required=True, help="Relation type")
@click.option('--password', '-p', help="Database password")
def link(dbname: str, from_table: str, from_id: str, 
         to_table: str, to_id: str, relation: str, password: str):
    """Create graph relationship."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        db.link(from_table, from_id, to_table, to_id, relation)
        
        console.print(f"[green]✓[/green] Linked [bold]{from_table}:{from_id}[/bold] → [bold]{relation}[/bold] → [bold]{to_table}:{to_id}[/bold]")
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.argument('dbname')
@click.option('--table', '-t', required=True, help="Table name")
@click.option('--id', 'node_id', required=True, help="Node ID")
@click.option('--depth', '-d', default=2, help="Traversal depth")
@click.option('--password', '-p', help="Database password")
def traverse(dbname: str, table: str, node_id: str, depth: int, password: str):
    """Traverse graph from node."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        results = db.traverse(table, node_id, depth)
        
        if results:
            console.print(format_table(results))
        else:
            console.print("[yellow]No connections found[/yellow]")
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ VECTOR ============

@main.command()
@click.argument('dbname')
@click.option('--collection', '-c', required=True, help="Collection name")
@click.option('--id', 'vec_id', required=True, help="Vector ID")
@click.option('--vec', required=True, help="Vector (JSON array)")
@click.option('--metadata', '-m', help="Metadata (JSON)")
@click.option('--password', '-p', help="Database password")
def vector_add(dbname: str, collection: str, vec_id: str,
               vec: str, metadata: str, password: str):
    """Add vector embedding."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        import json
        vector = json.loads(vec)
        meta = json.loads(metadata) if metadata else None

        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.engines.vector_engine import VectorEngine
        engine = VectorEngine(db._conn)
        vec_hash = engine.add(collection, vec_id, vector, meta)

        console.print(f"[green]✓[/green] Vector added to [bold]{collection}[/bold]")
        console.print(f"[dim]ID: {vec_id}, Hash: {vec_hash[:16]}...[/dim]")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.argument('dbname')
@click.option('--collection', '-c', required=True, help="Collection name")
@click.option('--vec', required=True, help="Query vector (JSON array)")
@click.option('--limit', '-l', default=10, help="Max results")
@click.option('--password', '-p', help="Database password")
def vector_search(dbname: str, collection: str, vec: str,
                  limit: int, password: str):
    """Search similar vectors."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        import json
        query_vector = json.loads(vec)

        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.engines.vector_engine import VectorEngine
        engine = VectorEngine(db._conn)
        results = engine.search(collection, query_vector, limit)

        if results:
            table = Table(title=f"Similar Vectors in {collection}")
            table.add_column("ID", style="cyan")
            table.add_column("Similarity", style="green")
            table.add_column("Metadata", style="yellow")

            for result in results:
                meta_str = json.dumps(result.get("metadata", {}))[:50]
                table.add_row(
                    result["vec_id"],
                    f"{result['similarity']:.4f}",
                    meta_str
                )

            console.print(table)
        else:
            console.print("[yellow]No similar vectors found[/yellow]")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.argument('dbname')
@click.option('--collection', '-c', required=True, help="Collection name")
@click.option('--text', '-t', help="Text to embed")
@click.option('--password', '-p', help="Database password")
def vector_embed(dbname: str, collection: str, text: str, password: str):
    """Generate embedding for text."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.engines.vector_engine import VectorEngine
        engine = VectorEngine(db._conn)
        embedding = engine.embed_text(text)

        console.print(f"[green]✓[/green] Embedding generated ({len(embedding)} dimensions)")
        console.print(f"[dim]{embedding[:10]}...[/dim]")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ SECURITY ============

@main.command()
@click.option('--user', '-u', required=True, help="User name")
@click.option('--type', 'key_type', default='ed25519', 
              type=click.Choice(['rsa', 'ed25519']))
def keys_generate(user: str, key_type: str):
    """Generate key pair."""
    try:
        km = KeyManager()
        
        if key_type == 'rsa':
            priv_path, pub_path = km.generate_rsa(user)
        else:
            priv_path, pub_path = km.generate_ed25519(user)
        
        console.print(f"[green]✓[/green] Keys generated for [bold]{user}[/bold]")
        console.print(f"[dim]Private: {priv_path}[/dim]")
        console.print(f"[dim]Public: {pub_path}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ BLOCKCHAIN ============

@main.command()
@click.argument('dbname')
@click.option('--password', '-p', help="Database password")
def verify(dbname: str, password: str):
    """Verify database integrity."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        is_valid = db.verify()
        
        if is_valid:
            console.print("[green]✓[/green] Database integrity verified - chain is intact")
        else:
            console.print("[red]✗[/red] Database integrity check FAILED - possible tampering detected")
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.argument('dbname')
@click.option('--password', '-p', help="Database password")
def repair(dbname: str, password: str):
    """Repair database integrity chain."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    if not click.confirm("This will recompute broken hash links. Proceed?"):
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        result = db.repair()
        
        if result['success']:
            console.print(f"[green]✓[/green] {result['message']}")
        else:
            console.print(f"[red]✗[/red] Repair failed: {result['message']}")
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.argument('dbname')
@click.option('--table', '-t', help="Filter by table")
@click.option('--id', 'record_id', help="Filter by record ID")
@click.option('--password', '-p', help="Database password")
def audit(dbname: str, table: str, record_id: str, password: str):
    """View audit trail."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        results = db.audit(table_name=table or None, record_id=record_id or None)
        
        if results:
            console.print(format_table(results))
        else:
            console.print("[yellow]No audit records found[/yellow]")
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ INFO ============

@main.command()
@click.argument('dbname')
@click.option('--password', '-p', help="Database password")
def stats(dbname: str, password: str):
    """Show database statistics."""
    db_path = Path(dbname)
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return
    
    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)
        
        # Get table count
        tables = db.execute("SELECT COUNT(*) FROM _tables")
        table_count = tables[0]['COUNT(*)'] if tables else 0
        
        # Get document count
        doc_count = db.execute("SELECT COUNT(*) FROM _documents")
        doc_total = doc_count[0]['COUNT(*)'] if doc_count else 0
        
        # Get edge count
        edge_count = db.execute("SELECT COUNT(*) FROM _edges")
        edge_total = edge_count[0]['COUNT(*)'] if edge_count else 0
        
        # Get vector count
        vector_count = db.execute("SELECT COUNT(*) FROM _vectors")
        vector_total = vector_count[0]['COUNT(*)'] if vector_count else 0
        
        # Get audit count
        audit_count = db.execute("SELECT COUNT(*) FROM _audit")
        audit_total = audit_count[0]['COUNT(*)'] if audit_count else 0
        
        # File size
        file_size = db_path.stat().st_size
        
        console.print(Panel.fit(
            f"[bold]{db_path.name}[/bold]\n\n"
            f"Tables:     {table_count}\n"
            f"Documents:  {doc_total}\n"
            f"Edges:      {edge_total}\n"
            f"Vectors:    {vector_total}\n"
            f"Audit:      {audit_total} blocks\n"
            f"Size:       {file_size:,} bytes",
            title="Database Statistics"
        ))
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ TERMINAL UI ============

@main.command()
@click.argument('dbname', required=False)
def ui(dbname: str):
    """Launch interactive terminal UI."""
    try:
        from ule.ui.terminal import ULETerminalUI

        ui = ULETerminalUI(db_path=dbname)
        ui.run()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ QUANTUM COMPUTING ============

@main.group()
def quantum():
    """Quantum computing operations."""
    pass


@quantum.command()
@click.option('--qubits', '-n', default=2, help="Number of qubits")
@click.option('--state', '-s', default="00", help="Initial state (e.g., 00, 01, 11)")
def init(qubits: int, state: str):
    """Initialize quantum register."""
    try:
        from ule.quantum import QubitRegister, QuantumVisualizer
        register = QubitRegister(num_qubits=qubits, initial_state=state)
        
        console.print(f"[green]✓[/green] Quantum register initialized")
        console.print(f"[dim]Qubits: {qubits}, Initial state: {state}[/dim]")
        
        # Show state vector
        visualizer = QuantumVisualizer()
        console.print(visualizer.state_vector(register, "Initial State"))
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@quantum.command()
@click.option('--gate', '-g', required=True, 
              type=click.Choice(['X', 'Y', 'Z', 'H', 'S', 'T', 'CNOT', 'CZ', 'SWAP']))
@click.option('--target', '-t', required=True, type=int, help="Target qubit")
@click.option('--control', '-c', type=int, help="Control qubit (for controlled gates)")
def gate(gate: str, target: int, control: int):
    """Apply quantum gate."""
    try:
        from ule.quantum import QuantumCircuit
        # Create a simple circuit
        num_qubits = max(target + 1, control + 1) if control is not None else target + 1
        circuit = QuantumCircuit(num_qubits, name="Gate Demo")
        
        # Apply gate
        if gate in ['X', 'Y', 'Z', 'H', 'S', 'T']:
            getattr(circuit, gate.lower())(target)
        elif gate == 'CNOT':
            if control is None:
                console.print("[red]Error:[/red] CNOT requires --control")
                return
            circuit.cnot(control, target)
        elif gate == 'CZ':
            if control is None:
                console.print("[red]Error:[/red] CZ requires --control")
                return
            circuit.cz(control, target)
        elif gate == 'SWAP':
            circuit.swap(target, control if control is not None else (target + 1) % circuit.num_qubits)
        
        # Execute and show result
        result = circuit.execute()
        
        console.print(f"[green]✓[/green] Applied {gate} gate")
        console.print(f"[dim]Target: {target}, Control: {control}[/dim]")
        console.print(f"[dim]State hash: {result.state_hash}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@quantum.command()
@click.option('--name', '-n', default="demo", help="Circuit name")
@click.option('--qubits', '-q', default=2, help="Number of qubits")
def circuit(name: str, qubits: int):
    """Create and run quantum circuit."""
    try:
        from ule.quantum import QuantumCircuit, QuantumVisualizer
        circuit = QuantumCircuit(qubits, name=name)
        
        # Demo circuit: Bell state
        if qubits >= 2:
            circuit.h(0)
            circuit.cnot(0, 1)
        
        console.print(f"[green]✓[/green] Created circuit: {name}")
        console.print(QuantumVisualizer().circuit_diagram(circuit, name))
        
        # Execute
        result = circuit.execute()
        console.print(f"\n[dim]Execution time: {result.execution_time_ms:.2f} ms[/dim]")
        
        # Simulate with shots
        counts = circuit.simulate(shots=100)
        console.print("\n" + QuantumVisualizer().measurement_results(counts, "Simulation (100 shots)"))
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@quantum.command()
@click.option('--algorithm', '-a', required=True,
              type=click.Choice(['deutsch-jozsa', 'grover', 'qft', 'teleportation', 'superdense', 'bernstein-vazirani']))
@click.option('--params', '-p', help="Algorithm parameters (JSON)")
def algorithm(algorithm: str, params: str):
    """Run quantum algorithm."""
    try:
        from ule.quantum import QuantumAlgorithms
        import json
        import math
        algo_params = json.loads(params) if params else {}
        
        algorithms = QuantumAlgorithms()
        
        console.print(f"[green]Running:[/green] {algorithm}")
        
        if algorithm == 'deutsch-jozsa':
            # Demo: constant function
            n = algo_params.get('n', 3)
            result = algorithms.deutsch_jozsa(lambda x: 0, n)
            console.print(f"Result: {result.output}")
            
        elif algorithm == 'grover':
            n = algo_params.get('n', 3)
            target = algo_params.get('target', 5)
            result = algorithms.grover_search(target, n)
            console.print(f"Target: {target}, Found: {result.output}, Success: {result.success}")
            
        elif algorithm == 'qft':
            n = algo_params.get('n', 3)
            input_state = algo_params.get('input', 1)
            result = algorithms.quantum_fourier_transform(input_state, n)
            console.print(f"QFT peak index: {result.output['peak_index']}")
            
        elif algorithm == 'teleportation':
            # Use math.sqrt for demo instead of numpy
            state = (1/math.sqrt(2), 1/math.sqrt(2))
            result = algorithms.quantum_teleportation(state)
            console.print(f"Teleportation complete: {result.output['protocol_complete']}")
            
        elif algorithm == 'superdense':
            message = algo_params.get('message', 2)
            result = algorithms.superdense_coding(message)
            console.print(f"Sent: {result.output['bits_sent']}, Received: {result.output['bits_received']}")
            
        elif algorithm == 'bernstein-vazirani':
            n = algo_params.get('n', 4)
            secret = algo_params.get('secret', 10)
            result = algorithms.bernstein_vazirani(secret, n)
            console.print(f"Secret: {secret}, Found: {result.output['found']}, Success: {result.success}")
        
        console.print(f"[dim]Execution time: {result.execution_time_ms:.2f} ms[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@quantum.command()
@click.option('--backend', '-b', default='simulator', help="Backend name")
def backends(backend: str):
    """List available quantum backends."""
    try:
        from ule.quantum import QiskitBackend
        qiskit = QiskitBackend()
        
        if backend == 'simulator':
            console.print("[green]Available backends:[/green]")
            console.print("  - aer_simulator (local)")
        else:
            backends_list = qiskit.list_backends()
            console.print("[green]Available backends:[/green]")
            for b in backends_list[:10]:
                console.print(f"  - {b}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@quantum.command()
@click.option('--state-id', '-s', help="State ID to visualize")
@click.option('--type', '-t', default='bloch', 
              type=click.Choice(['bloch', 'distribution', 'state']))
def visualize(state_id: str, type: str):
    """Visualize quantum state."""
    try:
        from ule.quantum import QuantumVisualizer, Qubit
        import math
        visualizer = QuantumVisualizer()
        
        if state_id:
            # Would need to load from engine
            console.print(f"[yellow]State visualization requires saved state[/yellow]")
        else:
            # Demo visualization using math.sqrt
            qubit = Qubit(alpha=1/math.sqrt(2), beta=1/math.sqrt(2))
            console.print(visualizer.bloch_sphere(qubit, "Demo Qubit |+⟩"))
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@quantum.command()
def info():
    """Show quantum computing info."""
    try:
        from ule.engines.quantum_engine import QuantumEngine
        engine = QuantumEngine()
        stats = engine.get_stats()
        
        console.print(Panel.fit(
            f"[bold]Quantum Computing Module[/bold]\n\n"
            f"Max Qubits:     {stats['max_qubits']}\n"
            f"Max States:     {stats['max_states']}\n"
            f"Stored States:  {stats['states_count']}\n"
            f"Stored Circuits:{stats['circuits_count']}\n"
            f"Encryption:     {'Enabled' if stats['encryption_enabled'] else 'Disabled'}\n"
            f"Qiskit:         {'Available' if stats['qiskit_available'] else 'Not Available'}",
            title="Quantum Engine Status"
        ))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ POST-QUANTUM CRYPTOGRAPHY ============

@main.group()
def pqc():
    """Post-Quantum Cryptography operations."""
    pass


@pqc.command()
@click.option('--level', '-l', default=2, help="Security level (1, 2, or 3)")
def keygen(level: int):
    """Generate ML-KEM and ML-DSA key pairs."""
    try:
        from ule.engines.pqc_engine import PQCEngine
        engine = PQCEngine()
        
        console.print("[bold blue]Generating NIST-Standard PQC Keys...[/bold blue]")
        kem = engine.generate_kem_keys(level)
        dsa = engine.generate_signature_keys(level)
        
        console.print(Panel.fit(
            f"[bold green]ML-KEM (Kyber) Keys Generated[/bold green]\n"
            f"Public Key (Truncated): {kem['public_key'][:60]}...\n"
            f"Secret Key (Truncated): {kem['secret_key'][:60]}...\n\n"
            f"[bold green]ML-DSA (Dilithium) Keys Generated[/bold green]\n"
            f"Verification Key: {dsa['verification_key'][:60]}...\n"
            f"Signing Key:      {dsa['signing_key'][:60]}...",
            title="PQC Key Generation Success"
        ))
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@pqc.command()
@click.argument('message')
@click.option('--key', '-k', required=True, help="Signing key (JSON string)")
def sign(message: str, key: str):
    """Sign a message using ML-DSA."""
    try:
        from ule.engines.pqc_engine import PQCEngine
        engine = PQCEngine()
        
        result = engine.sign(message, key)
        console.print(f"[green]✓[/green] Message signed successfully")
        console.print(f"Signature: [dim]{result['signature'][:100]}...[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@pqc.command()
def stats():
    """Show PQC engine status."""
    try:
        from ule.engines.pqc_engine import PQCEngine
        stats = PQCEngine().get_stats()
        
        console.print(Panel.fit(
            f"Engine:    {stats['engine']}\n"
            f"Standards: {', '.join(stats['pqc_standards'])}\n"
            f"Status:    {stats['status']}\n"
            f"Provider:  {stats['provider']}",
            title="PQC Engine Info"
        ))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ MIGRATIONS ============

@main.group()
def migrate():
    """Database migration operations."""
    pass


@migrate.command()
@click.argument('dbname')
@click.option('--version', '-v', required=True, help="Migration version")
@click.option('--description', '-d', required=True, help="Migration description")
@click.option('--up-sql', help="Up migration SQL")
@click.option('--down-sql', help="Down migration SQL")
@click.option('--password', '-p', help="Database password")
def create(dbname: str, version: str, description: str, up_sql: str, down_sql: str, password: str):
    """Create a new migration."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.migrations import MigrationManager
        mm = MigrationManager(db)
        mm.create_migration(version, description, up_sql=up_sql, down_sql=down_sql)

        console.print(f"[green]✓[/green] Migration created: {version} - {description}")
        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@migrate.command()
@click.argument('dbname')
@click.option('--target', '-t', help="Target version")
@click.option('--dry-run', is_flag=True, help="Show what would be done")
@click.option('--password', '-p', help="Database password")
def up(dbname: str, target: str, dry_run: bool, password: str):
    """Apply pending migrations."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.migrations import MigrationManager
        mm = MigrationManager(db)
        result = mm.migrate(target=target, dry_run=dry_run)

        console.print(f"[green]✓[/green] Migrations applied")
        console.print(f"Applied: {result['applied']}, Failed: {result['failed']}")
        
        for m in result['migrations']:
            status_color = 'green' if m['status'] == 'applied' else 'red'
            console.print(f"  [{status_color}]{m['status']}[/[/status_color]] {m['version']} - {m['description']}")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@migrate.command()
@click.argument('dbname')
@click.option('--steps', '-s', default=1, help="Number of migrations to rollback")
@click.option('--password', '-p', help="Database password")
def rollback(dbname: str, steps: int, password: str):
    """Rollback applied migrations."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.migrations import MigrationManager
        mm = MigrationManager(db)
        result = mm.rollback(steps=steps)

        console.print(f"[green]✓[/green] Rollback complete")
        console.print(f"Rolled back: {result['rolled_back']}, Failed: {result['failed']}")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@migrate.command()
@click.argument('dbname')
@click.option('--password', '-p', help="Database password")
def status(dbname: str, password: str):
    """Show migration status."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.migrations import MigrationManager
        mm = MigrationManager(db)
        status_list = mm.get_status()

        table = Table(title="Migration Status")
        table.add_column("Version", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Status", style="yellow")

        for s in status_list:
            status_color = 'green' if s['status'] == 'applied' else 'yellow'
            table.add_row(s['version'], s['description'], f"[{status_color}]{s['status']}[/{status_color}]")

        console.print(table)
        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ TUTORIALS ============

@main.group()
def tutorial():
    """Interactive tutorial system."""
    pass


@tutorial.command()
@click.option('--category', '-c', help="Filter by category")
@click.option('--difficulty', '-d', help="Filter by difficulty")
def list(category: str, difficulty: str):
    """List available tutorials."""
    try:
        from ule.tutorials import TutorialManager
        tm = TutorialManager()
        tutorials = tm.list_tutorials(category=category, difficulty=difficulty)

        table = Table(title="Available Tutorials")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Category", style="yellow")
        table.add_column("Difficulty", style="magenta")
        table.add_column("Time (min)", style="blue")

        for t in tutorials:
            table.add_row(t.id, t.title, t.category, t.difficulty, str(t.estimated_time))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@tutorial.command()
@click.argument('tutorial_id')
def start(tutorial_id: str):
    """Start a tutorial."""
    try:
        from ule.tutorials import TutorialManager
        tm = TutorialManager()
        tutorial = tm.start_tutorial(tutorial_id)

        if tutorial:
            console.print(Panel.fit(
                f"[bold]{tutorial.title}[/bold]\n\n"
                f"{tutorial.description}\n\n"
                f"Category: {tutorial.category}\n"
                f"Difficulty: {tutorial.difficulty}\n"
                f"Estimated Time: {tutorial.estimated_time} minutes\n"
                f"Steps: {len(tutorial.steps)}",
                title="Tutorial Started"
            ))
            
            # Show first step
            step = tm.get_current_step()
            if step:
                console.print(f"\n[bold]Step {step.id}:[/bold] {step.title}")
                console.print(f"{step.description}")
                console.print(f"\n[dim]Code:[/dim]")
                console.print(f"[green]{step.code}[/green]")
                if step.hint:
                    console.print(f"\n[yellow]Hint:[/yellow] {step.hint}")
        else:
            console.print(f"[red]Error:[/red] Tutorial '{tutorial_id}' not found")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@tutorial.command()
def next():
    """Move to next step in current tutorial."""
    try:
        from ule.tutorials import TutorialManager
        tm = TutorialManager()
        step = tm.next_step()

        if step:
            console.print(f"\n[bold]Step {step.id}:[/bold] {step.title}")
            console.print(f"{step.description}")
            console.print(f"\n[dim]Code:[/dim]")
            console.print(f"[green]{step.code}[/green]")
            if step.hint:
                console.print(f"\n[yellow]Hint:[/yellow] {step.hint}")
        else:
            console.print("[green]✓[/green] Tutorial completed!")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ IoT & MQTT ============

@main.group()
def iot():
    """IoT and MQTT operations."""
    pass


@iot.command()
@click.option('--broker', '-b', default='localhost', help="MQTT broker address")
@click.option('--port', '-p', default=1883, help="MQTT broker port")
@click.option('--topic', '-t', required=True, help="Topic to publish")
@click.option('--message', '-m', required=True, help="Message payload")
def publish(broker: str, port: int, topic: str, message: str):
    """Publish MQTT message."""
    try:
        from ule.iot import MQTTClient
        client = MQTTClient(broker=broker, port=port)
        
        if client.connect():
            client.publish(topic, message)
            console.print(f"[green]✓[/green] Published to {topic}: {message}")
            client.disconnect()
        else:
            console.print("[red]Error:[/red] Could not connect to broker")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@iot.command()
@click.option('--broker', '-b', default='localhost', help="MQTT broker address")
@click.option('--port', '-p', default=1883, help="MQTT broker port")
@click.option('--topic', '-t', required=True, help="Topic to subscribe")
def subscribe(broker: str, port: int, topic: str):
    """Subscribe to MQTT topic."""
    try:
        from ule.iot import MQTTClient
        client = MQTTClient(broker=broker, port=port)
        
        def on_message(client, userdata, msg):
            console.print(f"Received on {msg.topic}: {msg.payload.decode()}")
        
        if client.connect():
            client.subscribe(topic, on_message)
            console.print(f"[green]✓[/green] Subscribed to {topic}")
            console.print("[dim]Press Ctrl+C to exit[/dim]")
            
            import time
            while True:
                time.sleep(1)
        else:
            console.print("[red]Error:[/red] Could not connect to broker")

    except KeyboardInterrupt:
        console.print("\n[yellow]Unsubscribed[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ CDC (Change Data Capture) ============

@main.group()
def cdc():
    """Change Data Capture operations."""
    pass


@cdc.command()
@click.argument('dbname')
@click.option('--table', '-t', required=True, help="Table to track")
@click.option('--password', '-p', help="Database password")
def enable(dbname: str, table: str, password: str):
    """Enable CDC for a table."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.replication import CDCManager
        cdc = CDCManager(db)
        cdc.enable_table(table)

        console.print(f"[green]✓[/green] CDC enabled for {table}")
        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@cdc.command()
@click.argument('dbname')
@click.option('--table', '-t', help="Filter by table")
@click.option('--limit', '-l', default=20, help="Max results")
@click.option('--password', '-p', help="Database password")
def changes(dbname: str, table: str, limit: int, password: str):
    """View recent changes."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.replication import CDCManager
        cdc = CDCManager(db)
        changes = cdc.get_changes(table, limit=limit)

        if changes:
            table = Table(title="Recent Changes")
            table.add_column("Table", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Timestamp", style="yellow")

            for change in changes:
                table.add_row(change.table, change.change_type.value, 
                            f"{change.timestamp:.0f}")

            console.print(table)
        else:
            console.print("[yellow]No changes found[/yellow]")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ OFFLINE MODE ============

@main.group()
def offline():
    """Offline mode operations."""
    pass


@offline.command()
@click.argument('dbname')
@click.option('--password', '-p', help="Database password")
def status(dbname: str, password: str):
    """Show offline queue status."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.replication import OfflineManager
        offline = OfflineManager(db)
        status = offline.get_queue_status()

        console.print(Panel.fit(
            f"Online: {'Yes' if status['is_online'] else 'No'}\n"
            f"Queued: {status['total_queued']}\n"
            f"By Status: {status['by_status']}",
            title="Offline Queue Status"
        ))

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@offline.command()
@click.argument('dbname')
@click.option('--batch-size', '-b', default=100, help="Batch size")
@click.option('--password', '-p', help="Database password")
def sync(dbname: str, batch_size: int, password: str):
    """Sync queued operations."""
    db_path = Path(dbname)

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database {db_path} not found")
        return

    try:
        db = ULEDatabase(str(db_path))
        db.open(password=password)

        from ule.replication import OfflineManager
        offline = OfflineManager(db)
        offline.go_online()
        result = offline.sync(batch_size=batch_size)

        console.print(f"[green]✓[/green] Sync complete")
        console.print(f"Synced: {result['synced']}, Failed: {result['failed']}, Remaining: {result['remaining']}")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


# ============ SERVER ============

@main.command()
@click.option('--host', '-h', default='0.0.0.0', help='Host address')
@click.option('--port', '-p', default=8000, help='Port number')
@click.option('--dbname', '-d', help='Database file to serve')
@click.option('--reload', '-r', is_flag=True, help='Auto-reload on changes')
def serve(host: str, port: int, dbname: str, reload: bool):
    """Start Unified Professional Server (API + Web UI)."""
    import os
    import time
    import threading
    import webbrowser
    from pathlib import Path
    from rich.prompt import Confirm

    # 1. SMART FEATURE: Auto-detect database if none provided
    target_db = dbname
    if not target_db:
        udb_files = list(Path('.').glob("*.udb"))
        if udb_files:
            # Convert WindowsPath to string immediately to avoid Click TypeError
            target_db = str(udb_files[0])
            console.print(f"[dim]ℹ No database specified. Auto-detecting: [bold]{target_db}[/bold][/dim]")

    # 2. Set environment variable so the FastAPI server knows which DB to load
    if target_db:
        os.environ["ULE_DEFAULT_DB"] = target_db

    try:
        import uvicorn
        # Check for FastAPI without importing to avoid crash
        import fastapi
        from ule.server.main import app
        
        console.print(f"[bold green]🚀 ULE Professional Server starting at http://{host}:{port}[/bold green]")
        console.print(f"[dim]Studio UI: http://{host}:{port}/[/dim]")
        if target_db:
            console.print(f"[dim]Active Database: {target_db}[/dim]")

        # 3. SMART FEATURE: Auto-open browser in a separate thread
        def open_browser():
            time.sleep(2) # Wait for server to boot
            url = f"http://127.0.0.1:{port}"
            webbrowser.open(url)
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        uvicorn.run(app, host=host, port=port, reload=reload)

    except (ImportError, ModuleNotFoundError):
        console.print("\n[yellow]⚠️  Required server components (FastAPI/Uvicorn) are missing.[/yellow]")
        if Confirm.ask("Would you like ULE to install these for you automatically?"):
            import subprocess
            import sys
            try:
                with console.status("[bold green]Installing professional server components..."):
                    # Install all web dependencies at once
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "python-multipart", "jinja2"])
                console.print("[green]✓ Components installed! Please run 'ule serve' again.[/green]")
            except Exception as e:
                console.print(f"[red]Error during auto-install: {e}[/red]")
        else:
            console.print("[red]Error:[/red] Server cannot start without dependencies.")
    except Exception as e:
        console.print(f"[red]Critical Server Error:[/red] {e}")


if __name__ == '__main__':
    main()


@main.command()
@click.argument('dbname')
@click.option('--username', '-u', required=True, help="Username")
@click.option('--password', '-p', prompt=True, hide_input=True, required=True, help="Password")
@click.option('--role', '-r', default='user', help="Role (admin/write/user)")
def user_add(dbname: str, username: str, password: str, role: str):
    """Securely add a new user."""
    from argon2 import PasswordHasher
    from ule.core.database import ULEDatabase
    
    db = ULEDatabase(dbname)
    db.open()
    
    ph = PasswordHasher()
    hashed = ph.hash(password)
    
    db._conn.execute(
        "INSERT INTO _users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, hashed, role)
    )
    db._conn.commit()
    db.close()
    
    console.print(f"[green]✓[/green] User [bold]{username}[/bold] added successfully.")
