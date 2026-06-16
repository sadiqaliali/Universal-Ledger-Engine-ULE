"""
ULE Tutorial System

Interactive tutorials for learning ULE features.
Provides step-by-step guides with validation and progress tracking.
"""

import json
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class TutorialStatus(Enum):
    """Tutorial completion status."""
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'


@dataclass
class TutorialStep:
    """A single step in a tutorial."""
    id: int
    title: str
    description: str
    code: str
    expected_output: Optional[str] = None
    validation_fn: Optional[Callable] = None
    hint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'code': self.code,
            'expected_output': self.expected_output,
            'hint': self.hint
        }


@dataclass
class Tutorial:
    """A complete tutorial."""
    id: str
    title: str
    description: str
    category: str
    difficulty: str  # 'beginner', 'intermediate', 'advanced'
    estimated_time: int  # minutes
    steps: List[TutorialStep] = field(default_factory=list)
    status: TutorialStatus = TutorialStatus.NOT_STARTED
    current_step: int = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def progress(self) -> float:
        """Calculate completion progress (0.0 to 1.0)."""
        if not self.steps:
            return 0.0
        return self.current_step / len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'estimated_time': self.estimated_time,
            'steps': [s.to_dict() for s in self.steps],
            'status': self.status.value,
            'current_step': self.current_step,
            'progress': self.progress
        }


class TutorialManager:
    """
    Tutorial System Manager.
    
    Provides interactive tutorials for learning ULE features.
    
    Usage:
        tutorials = TutorialManager(db)
        
        # List available tutorials
        available = tutorials.list_tutorials()
        
        # Start a tutorial
        tutorial = tutorials.start_tutorial('basic_sql')
        
        # Get current step
        step = tutorials.get_current_step()
        
        # Execute step
        result = tutorials.execute_step()
        
        # Move to next step
        tutorials.next_step()
    """
    
    def __init__(self, db_connection=None, tutorials_dir: Optional[str] = None):
        self.db = db_connection
        self.tutorials_dir = tutorials_dir
        self._tutorials: Dict[str, Tutorial] = {}
        self._active_tutorial: Optional[Tutorial] = None
        self._progress: Dict[str, Dict[str, Any]] = {}
        
        # Load built-in tutorials
        self._load_builtin_tutorials()
        
        if self.db:
            self._create_progress_table()
            self._load_progress()
    
    def _create_progress_table(self):
        """Create tutorial progress tracking table."""
        conn = self.db.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tutorial_progress (
                tutorial_id TEXT NOT NULL,
                user_id TEXT DEFAULT 'default',
                status TEXT NOT NULL DEFAULT 'not_started',
                current_step INTEGER DEFAULT 0,
                started_at REAL,
                completed_at REAL,
                PRIMARY KEY (tutorial_id, user_id)
            )
        """)
        conn.commit()
    
    def _load_progress(self):
        """Load tutorial progress from database."""
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("SELECT tutorial_id, status, current_step, started_at, completed_at FROM tutorial_progress")
            for row in cursor.fetchall():
                tutorial_id, status, current_step, started_at, completed_at = row
                if tutorial_id in self._tutorials:
                    self._tutorials[tutorial_id].status = TutorialStatus(status)
                    self._tutorials[tutorial_id].current_step = current_step
                    self._tutorials[tutorial_id].started_at = started_at
                    self._tutorials[tutorial_id].completed_at = completed_at
        except Exception:
            pass
    
    def _load_builtin_tutorials(self):
        """Load built-in tutorials."""
        tutorials = [
            self._tutorial_basic_sql(),
            self._tutorial_nosql(),
            self._tutorial_nlq(),
            self._tutorial_security(),
            self._tutorial_graph(),
            self._tutorial_vector(),
            self._tutorial_timeseries(),
            self._tutorial_geospatial(),
            self._tutorial_migrations(),
            self._tutorial_offline_mode(),
        ]
        
        for tutorial in tutorials:
            self._tutorials[tutorial.id] = tutorial
    
    def _tutorial_basic_sql(self) -> Tutorial:
        """Basic SQL tutorial."""
        return Tutorial(
            id='basic_sql',
            title='Basic SQL Operations',
            description='Learn how to perform basic SQL operations with ULE',
            category='SQL',
            difficulty='beginner',
            estimated_time=10,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create a Database',
                    description='Initialize a new ULE database',
                    code='from ule.core import Database\ndb = Database("mydb.sqlite")\ndb.init()',
                    hint='Database initialization creates the necessary tables'
                ),
                TutorialStep(
                    id=2,
                    title='Create a Table',
                    description='Create your first table with columns',
                    code='db.execute("""\n    CREATE TABLE users (\n        id INTEGER PRIMARY KEY,\n        name TEXT NOT NULL,\n        email TEXT UNIQUE,\n        age INTEGER\n    )\n""")',
                    hint='Use standard SQL CREATE TABLE syntax'
                ),
                TutorialStep(
                    id=3,
                    title='Insert Data',
                    description='Insert rows into your table',
                    code='db.execute("INSERT INTO users (name, email, age) VALUES (?, ?, ?)",\n         ("Alice", "alice@example.com", 30))\ndb.commit()',
                    hint='Use parameterized queries to prevent SQL injection'
                ),
                TutorialStep(
                    id=4,
                    title='Query Data',
                    description='Retrieve data with SELECT',
                    code='results = db.execute("SELECT * FROM users WHERE age > ?", (25,))\nfor row in results:\n    print(row)',
                    hint='Results are returned as tuples'
                ),
                TutorialStep(
                    id=5,
                    title='Update Data',
                    description='Modify existing records',
                    code='db.execute("UPDATE users SET age = ? WHERE name = ?", (31, "Alice"))\ndb.commit()',
                    hint='Always commit after UPDATE operations'
                ),
                TutorialStep(
                    id=6,
                    title='Delete Data',
                    description='Remove records from table',
                    code='db.execute("DELETE FROM users WHERE name = ?", ("Alice",))\ndb.commit()',
                    hint='Use WHERE clause to avoid deleting all rows'
                ),
            ]
        )
    
    def _tutorial_nosql(self) -> Tutorial:
        """NoSQL tutorial."""
        return Tutorial(
            id='nosql_basics',
            title='NoSQL Document Operations',
            description='Learn document-based operations with ULE',
            category='NoSQL',
            difficulty='beginner',
            estimated_time=10,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create a Collection',
                    description='Create a document collection',
                    code='from ule.engines import NoSQLEngine\nnosql = NoSQLEngine(db)\nnosql.create_collection("products")',
                    hint='Collections are like tables but for JSON documents'
                ),
                TutorialStep(
                    id=2,
                    title='Insert a Document',
                    description='Insert a JSON document',
                    code='doc = {\n    "name": "Laptop",\n    "price": 999.99,\n    "specs": {"ram": "16GB", "storage": "512GB"}\n}\nnosql.insert("products", doc)',
                    hint='Documents can have nested structures'
                ),
                TutorialStep(
                    id=3,
                    title='Query Documents',
                    description='Find documents matching criteria',
                    code='results = nosql.find("products", {"price": {"$lt": 1000}})\nfor doc in results:\n    print(doc)',
                    hint='Use MongoDB-like query syntax'
                ),
                TutorialStep(
                    id=4,
                    title='Update Documents',
                    description='Modify existing documents',
                    code='nosql.update("products",\n         {"name": "Laptop"},\n         {"$set": {"price": 899.99}})',
                    hint='Use update operators like $set, $inc, etc.'
                ),
            ]
        )
    
    def _tutorial_nlq(self) -> Tutorial:
        """NLQ tutorial."""
        return Tutorial(
            id='nlq_basics',
            title='Natural Language Queries',
            description='Query your database using plain English',
            category='AI',
            difficulty='beginner',
            estimated_time=8,
            steps=[
                TutorialStep(
                    id=1,
                    title='Initialize NLQ Engine',
                    description='Set up the natural language query engine',
                    code='from ule.ai import NLQEngine\nnlq = NLQEngine(db, language="en")',
                    hint='NLQ supports 20+ languages'
                ),
                TutorialStep(
                    id=2,
                    title='Simple Query',
                    description='Ask a simple question',
                    code='result = nlq.query("show me all users")\nprint(result["sql"])\n# SELECT * FROM users',
                    hint='Start with simple SELECT queries'
                ),
                TutorialStep(
                    id=3,
                    title='Query with Conditions',
                    description='Add filtering conditions',
                    code='result = nlq.query("find users older than 25")\nprint(result["sql"])\n# SELECT * FROM users WHERE age > 25',
                    hint='Use words like "older than", "under", "equal to"'
                ),
                TutorialStep(
                    id=4,
                    title='Aggregate Queries',
                    description='Use COUNT, SUM, AVG',
                    code='result = nlq.query("how many users are there")\nprint(result["sql"])\n# SELECT COUNT(*) FROM users',
                    hint='Try "how many", "total", "average"'
                ),
            ]
        )
    
    def _tutorial_security(self) -> Tutorial:
        """Security tutorial."""
        return Tutorial(
            id='security_basics',
            title='Database Security',
            description='Learn to secure your database with encryption and access control',
            category='Security',
            difficulty='intermediate',
            estimated_time=12,
            steps=[
                TutorialStep(
                    id=1,
                    title='Enable Column Encryption',
                    description='Encrypt sensitive columns',
                    code='from ule.security import ColumnEncryption\nenc = ColumnEncryption(db)\nenc.enable_encryption("users", "ssn")',
                    hint='Encrypted columns are automatically encrypted/decrypted'
                ),
                TutorialStep(
                    id=2,
                    title='Set Up Row-Level Security',
                    description='Restrict access to rows',
                    code='from ule.security import AccessControl\nacl = AccessControl(db)\nacl.create_policy("users", "department = ?", ("sales",))',
                    hint='Users only see rows matching their policy'
                ),
                TutorialStep(
                    id=3,
                    title='Apply Data Masking',
                    description='Mask sensitive data',
                    code='from ule.security import DataMasking\nmask = DataMasking()\nmasked = mask.apply("email", "user@example.com")\n# u***@example.com',
                    hint='Masking hides sensitive data in query results'
                ),
            ]
        )
    
    def _tutorial_graph(self) -> Tutorial:
        """Graph database tutorial."""
        return Tutorial(
            id='graph_basics',
            title='Graph Database Operations',
            description='Learn to work with graph data and relationships',
            category='Graph',
            difficulty='intermediate',
            estimated_time=15,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create Graph Engine',
                    description='Initialize the graph engine',
                    code='from ule.engines import GraphEngine\ngraph = GraphEngine(db)',
                    hint='Graph engine manages nodes and relationships'
                ),
                TutorialStep(
                    id=2,
                    title='Add Nodes',
                    description='Create graph nodes',
                    code='graph.add_node("person", {"name": "Alice", "age": 30})\ngraph.add_node("person", {"name": "Bob", "age": 25})',
                    hint='Nodes have labels and properties'
                ),
                TutorialStep(
                    id=3,
                    title='Create Relationships',
                    description='Connect nodes with relationships',
                    code='graph.create_relationship(0, 1, "FRIENDS", {"since": 2020})',
                    hint='Relationships can also have properties'
                ),
                TutorialStep(
                    id=4,
                    title='Query Graph',
                    description='Find paths and patterns',
                    code='friends = graph.find_friends("Alice")\nfor friend in friends:\n    print(friend)',
                    hint='Graph queries traverse relationships'
                ),
            ]
        )
    
    def _tutorial_vector(self) -> Tutorial:
        """Vector database tutorial."""
        return Tutorial(
            id='vector_basics',
            title='Vector Similarity Search',
            description='Learn vector embeddings and similarity search',
            category='Vector',
            difficulty='intermediate',
            estimated_time=12,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create Vector Engine',
                    description='Initialize vector search',
                    code='from ule.engines import VectorEngine\nvector = VectorEngine(db, dimensions=128)',
                    hint='Specify vector dimensions based on your embeddings'
                ),
                TutorialStep(
                    id=2,
                    title='Add Vectors',
                    description='Insert vector embeddings',
                    code='embedding = [0.1, 0.2, ...]  # 128 dimensions\nvector.add_item("doc1", embedding, metadata={"text": "Hello"})',
                    hint='Store metadata with vectors for context'
                ),
                TutorialStep(
                    id=3,
                    title='Similarity Search',
                    description='Find similar vectors',
                    code='query_embedding = [0.15, 0.18, ...]\nresults = vector.search(query_embedding, k=5)\nfor item in results:\n    print(item.metadata)',
                    hint='Results are ordered by similarity'
                ),
            ]
        )
    
    def _tutorial_timeseries(self) -> Tutorial:
        """Time-series tutorial."""
        return Tutorial(
            id='timeseries_basics',
            title='Time-Series Data',
            description='Work with time-series data and analytics',
            category='Time-Series',
            difficulty='intermediate',
            estimated_time=10,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create Time-Series Engine',
                    description='Initialize time-series engine',
                    code='from ule.engines import TimeSeriesEngine\nts = TimeSeriesEngine(db)',
                    hint='Time-series engine optimizes time-based queries'
                ),
                TutorialStep(
                    id=2,
                    title='Insert Time-Series Data',
                    description='Add time-stamped data points',
                    code='import time\nts.insert("temperature", time.time(), 25.5, {"sensor": "room1"})',
                    hint='Include metadata with your data points'
                ),
                TutorialStep(
                    id=3,
                    title='Query Time Range',
                    description='Query data in a time range',
                    code='start = time.time() - 3600  # 1 hour ago\nend = time.time()\ndata = ts.query_range("temperature", start, end)',
                    hint='Use Unix timestamps for time ranges'
                ),
            ]
        )
    
    def _tutorial_geospatial(self) -> Tutorial:
        """Geospatial tutorial."""
        return Tutorial(
            id='geospatial_basics',
            title='Geospatial Queries',
            description='Work with location and geographic data',
            category='Geospatial',
            difficulty='intermediate',
            estimated_time=10,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create Geospatial Engine',
                    description='Initialize geospatial engine',
                    code='from ule.engines import GeospatialEngine\ngeo = GeospatialEngine(db)',
                    hint='Geospatial engine uses R-tree indexing'
                ),
                TutorialStep(
                    id=2,
                    title='Add Location Points',
                    description='Insert geographic points',
                    code='geo.add_point("store1", lat=40.7128, lon=-74.0060, metadata={"name": "NYC Store"})',
                    hint='Points have latitude, longitude, and metadata'
                ),
                TutorialStep(
                    id=3,
                    title='Find Nearby Points',
                    description='Search for nearby locations',
                    code='nearby = geo.find_nearby(lat=40.7128, lon=-74.0060, radius_km=10)\nfor point in nearby:\n    print(point.metadata)',
                    hint='Radius is in kilometers'
                ),
            ]
        )
    
    def _tutorial_migrations(self) -> Tutorial:
        """Migrations tutorial."""
        return Tutorial(
            id='migrations_basics',
            title='Database Migrations',
            description='Learn to manage schema changes with migrations',
            category='DevTools',
            difficulty='beginner',
            estimated_time=8,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create Migration Manager',
                    description='Initialize migration system',
                    code='from ule.migrations import MigrationManager\nmigrations = MigrationManager(db)',
                    hint='Migration manager tracks schema versions'
                ),
                TutorialStep(
                    id=2,
                    title='Create a Migration',
                    description='Define a schema change',
                    code='migrations.create_migration(\n    version="001",\n    description="Create users table",\n    up_sql="CREATE TABLE users (...)",\n    down_sql="DROP TABLE users"\n)',
                    hint='Always provide both up and down SQL'
                ),
                TutorialStep(
                    id=3,
                    title='Apply Migrations',
                    description='Run pending migrations',
                    code='result = migrations.migrate()\nprint(f"Applied {result[\'applied\']} migrations")',
                    hint='Migrations are applied in version order'
                ),
                TutorialStep(
                    id=4,
                    title='Rollback Migration',
                    description='Undo the last migration',
                    code='result = migrations.rollback(steps=1)\nprint(f"Rolled back {result[\'rolled_back\']} migrations")',
                    hint='Rollback uses the down SQL'
                ),
            ]
        )
    
    def _tutorial_offline_mode(self) -> Tutorial:
        """Offline mode tutorial."""
        return Tutorial(
            id='offline_basics',
            title='Offline Mode',
            description='Learn to work offline and sync changes',
            category='Replication',
            difficulty='advanced',
            estimated_time=10,
            steps=[
                TutorialStep(
                    id=1,
                    title='Create Offline Manager',
                    description='Initialize offline mode',
                    code='from ule.replication import OfflineManager\noffline = OfflineManager(db)',
                    hint='Offline manager queues operations'
                ),
                TutorialStep(
                    id=2,
                    title='Go Offline',
                    description='Switch to offline mode',
                    code='offline.go_offline()\nprint(f"Online: {offline.is_online}")',
                    hint='Operations are queued while offline'
                ),
                TutorialStep(
                    id=3,
                    title='Queue Operations',
                    description='Execute operations while offline',
                    code='offline.execute(\n    "INSERT INTO users (name) VALUES (?)",\n    ("Alice",),\n    table="users"\n)',
                    hint='Operations are queued for later sync'
                ),
                TutorialStep(
                    id=4,
                    title='Sync Changes',
                    description='Go online and sync',
                    code='offline.go_online()\nstats = offline.sync()\nprint(f"Synced: {stats[\'synced\']}")',
                    hint='Sync applies all queued operations'
                ),
            ]
        )
    
    def list_tutorials(self, category: Optional[str] = None,
                      difficulty: Optional[str] = None) -> List[Tutorial]:
        """
        List available tutorials.
        
        Args:
            category: Filter by category
            difficulty: Filter by difficulty
            
        Returns:
            List of tutorials
        """
        tutorials = list(self._tutorials.values())
        
        if category:
            tutorials = [t for t in tutorials if t.category.lower() == category.lower()]
        if difficulty:
            tutorials = [t for t in tutorials if t.difficulty.lower() == difficulty.lower()]
        
        return tutorials
    
    def start_tutorial(self, tutorial_id: str) -> Optional[Tutorial]:
        """
        Start a tutorial.
        
        Args:
            tutorial_id: Tutorial ID
            
        Returns:
            The tutorial, or None if not found
        """
        if tutorial_id not in self._tutorials:
            return None
        
        tutorial = self._tutorials[tutorial_id]
        tutorial.status = TutorialStatus.IN_PROGRESS
        tutorial.current_step = 0
        tutorial.started_at = time.time()
        
        self._active_tutorial = tutorial
        
        # Save progress
        if self.db:
            conn = self.db.get_connection()
            conn.execute(
                "INSERT OR REPLACE INTO tutorial_progress (tutorial_id, status, current_step, started_at) VALUES (?, ?, ?, ?)",
                (tutorial_id, tutorial.status.value, tutorial.current_step, tutorial.started_at)
            )
            conn.commit()
        
        return tutorial
    
    def get_current_step(self) -> Optional[TutorialStep]:
        """Get the current step in the active tutorial."""
        if not self._active_tutorial:
            return None
        
        if self._active_tutorial.current_step >= len(self._active_tutorial.steps):
            return None
        
        return self._active_tutorial.steps[self._active_tutorial.current_step]
    
    def execute_step(self) -> Dict[str, Any]:
        """
        Execute the current step.
        
        Returns:
            Execution result
        """
        step = self.get_current_step()
        if not step:
            return {'error': 'No current step'}
        
        result = {
            'step_id': step.id,
            'title': step.title,
            'code': step.code,
            'description': step.description,
            'hint': step.hint
        }
        
        # Validate if validation function exists
        if step.validation_fn:
            try:
                valid = step.validation_fn(self.db)
                result['valid'] = valid
            except Exception as e:
                result['valid'] = False
                result['error'] = str(e)
        
        return result
    
    def next_step(self) -> Optional[TutorialStep]:
        """Move to the next step."""
        if not self._active_tutorial:
            return None
        
        self._active_tutorial.current_step += 1
        
        # Check if tutorial is complete
        if self._active_tutorial.current_step >= len(self._active_tutorial.steps):
            self._active_tutorial.status = TutorialStatus.COMPLETED
            self._active_tutorial.completed_at = time.time()
            
            # Save completion
            if self.db:
                conn = self.db.get_connection()
                conn.execute(
                    "UPDATE tutorial_progress SET status = ?, current_step = ?, completed_at = ? WHERE tutorial_id = ?",
                    (self._active_tutorial.status.value, 
                     self._active_tutorial.current_step,
                     self._active_tutorial.completed_at,
                     self._active_tutorial.id)
                )
                conn.commit()
            
            return None
        
        # Save progress
        if self.db:
            conn = self.db.get_connection()
            conn.execute(
                "UPDATE tutorial_progress SET current_step = ? WHERE tutorial_id = ?",
                (self._active_tutorial.current_step, self._active_tutorial.id)
            )
            conn.commit()
        
        return self.get_current_step()
    
    def previous_step(self) -> Optional[TutorialStep]:
        """Move to the previous step."""
        if not self._active_tutorial:
            return None
        
        if self._active_tutorial.current_step > 0:
            self._active_tutorial.current_step -= 1
        
        return self.get_current_step()
    
    def get_progress(self, tutorial_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get tutorial progress.
        
        Args:
            tutorial_id: Specific tutorial (None for all)
            
        Returns:
            Progress information
        """
        if tutorial_id:
            if tutorial_id in self._tutorials:
                tutorial = self._tutorials[tutorial_id]
                return tutorial.to_dict()
            return {}
        
        # Return all progress
        return {
            tid: t.to_dict() 
            for tid, t in self._tutorials.items()
        }
    
    def reset_tutorial(self, tutorial_id: str):
        """Reset a tutorial to start over."""
        if tutorial_id in self._tutorials:
            tutorial = self._tutorials[tutorial_id]
            tutorial.status = TutorialStatus.NOT_STARTED
            tutorial.current_step = 0
            tutorial.started_at = None
            tutorial.completed_at = None
            
            if self.db:
                conn = self.db.get_connection()
                conn.execute(
                    "DELETE FROM tutorial_progress WHERE tutorial_id = ?",
                    (tutorial_id,)
                )
                conn.commit()
