from fastapi import FastAPI, HTTPException, Depends, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ule.core.database import ULEDatabase
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ULE Studio API", version="1.0.0")

# Enable CORS for the dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Simple session store (For demo: use JWT in production)
active_dbs: Dict[str, ULEDatabase] = {}

class LoginRequest(BaseModel):
    db_path: str
    password: str

class DataRequest(BaseModel):
    collection: str
    data: Dict[str, Any]

@app.post("/auth/login")
async def login(req: LoginRequest):
    if not os.path.exists(req.db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    db = ULEDatabase(req.db_path, password=req.password)
    try:
        db.open(password=req.password)
        # Unique session token (path as key for now)
        active_dbs[req.db_path] = db
        return {"message": "Vault Unlocked", "token": req.db_path}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/data/{db_path}/{collection}")
async def get_data(db_path: str, collection: str):
    if db_path not in active_dbs:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db = active_dbs[db_path]
    return db.find(collection)

@app.post("/data/{db_path}/{collection}")
async def push_data(db_path: str, collection: str, req: DataRequest):
    if db_path not in active_dbs:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db = active_dbs[db_path]
    doc_id = db.push(collection, req.data)
    return {"doc_id": doc_id}

@app.post("/db/create")
async def create_db(req: LoginRequest):
    if os.path.exists(req.db_path):
        raise HTTPException(status_code=400, detail="Database already exists")
    db = ULEDatabase(req.db_path, password=req.password)
    db.init(password=req.password)
    db.close()
    return {"message": "Database created successfully"}

@app.get("/tutorials")
async def get_tutorials():
    from ule.tutorials.tutorial_system import TutorialManager
    manager = TutorialManager()
    return manager.list_tutorials()

@app.get("/schema/{db_path}")
async def get_schema(db_path: str):
    if db_path not in active_dbs:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db = active_dbs[db_path]
    
    # Discover all models/tables
    schema = {
        "sql_tables": [r[0] for r in db._conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()],
        "collections": [r[0] for r in db._conn.execute("SELECT DISTINCT collection FROM _documents").fetchall()],
        "vector_sets": [r[0] for r in db._conn.execute("SELECT DISTINCT collection FROM _vectors").fetchall()],
        "graph_nodes": ["users"] # Simplified graph discovery
    }
    return schema
