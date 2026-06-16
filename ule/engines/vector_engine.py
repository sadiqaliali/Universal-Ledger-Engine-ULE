"""Vector Engine for ULE - Embeddings and similarity search."""

import json
import struct
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

try:
    import hnswlib
    import numpy as np
    HNSW_AVAILABLE = True
except ImportError:
    HNSW_AVAILABLE = False


class VectorEngine:
    """
    Vector search engine for embeddings and similarity.
    
    Supports: add vectors, similarity search, HNSW index
    """
    
    def __init__(self, db_connection, index_dir: str = None, audit_manager: Any = None):
        self._conn = db_connection
        self._index_dir = index_dir
        self._indexes: Dict[str, Any] = {}
        self._audit_manager = audit_manager
    
    def add(self, collection: str, vec_id: str, 
            embedding: List[float], metadata: Dict[str, Any] = None) -> str:
        """
        Add vector embedding to collection.
        
        Args:
            collection: Collection name
            vec_id: Vector identifier
            embedding: Vector values
            metadata: Optional metadata
        
        Returns:
            Vector hash
        """
        # Serialize embedding
        emb_bytes = struct.pack(f'{len(embedding)}f', *embedding)
        
        # Compute hash
        emb_hash = hashlib.sha256(
            f"{collection}{vec_id}{json.dumps(embedding)}".encode()
        ).hexdigest()
        
        # Serialize metadata
        meta_json = json.dumps(metadata) if metadata else None
        
        # Store in database
        self._conn.execute(
            """INSERT OR REPLACE INTO _vectors 
               (collection, vec_id, embedding, metadata, hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (collection, vec_id, emb_bytes, meta_json, emb_hash, 
             datetime.now(timezone.utc).isoformat())
        )
        self._conn.commit()
        
        # Add to HNSW index if available
        if HNSW_AVAILABLE:
            self._add_to_index(collection, vec_id, embedding)
        
        # Audit
        if self._audit_manager:
            self._audit_manager.log(
                operation="VECTOR_ADD",
                table_name="_vectors",
                record_id=f"{collection}:{vec_id}",
                new_value={"collection": collection, "vec_id": vec_id, "hash": emb_hash}
            )
        
        return emb_hash
    
    def search(self, collection: str, query_vector: List[float],
               limit: int = 10, threshold: float = 0.0) -> List[Dict]:
        """
        Find similar vectors.
        
        Args:
            collection: Collection name
            query_vector: Query embedding
            limit: Max results
            threshold: Minimum similarity threshold
        
        Returns:
            List of similar vectors with scores
        """
        # Try HNSW first if available
        if HNSW_AVAILABLE and collection in self._indexes:
            return self._hnsw_search(collection, query_vector, limit, threshold)
        
        # Fallback to brute-force cosine similarity
        return self._brute_force_search(collection, query_vector, limit, threshold)
    
    def _brute_force_search(self, collection: str, 
                            query_vector: List[float],
                            limit: int, threshold: float) -> List[Dict]:
        """Brute-force similarity search."""
        cursor = self._conn.execute(
            "SELECT vec_id, embedding, metadata FROM _vectors WHERE collection = ?",
            (collection,)
        )
        
        results = []
        
        for row in cursor:
            vec_id = row[0]
            emb_bytes = row[1]
            metadata = row[2]
            
            # Deserialize embedding
            dim = len(emb_bytes) // 4
            embedding = list(struct.unpack(f'{dim}f', emb_bytes))
            
            # Compute cosine similarity
            similarity = self._cosine_similarity(query_vector, embedding)
            
            if similarity >= threshold:
                results.append({
                    "vec_id": vec_id,
                    "similarity": similarity,
                    "metadata": json.loads(metadata) if metadata else None
                })
        
        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def _hnsw_search(self, collection: str, query_vector: List[float],
                     limit: int, threshold: float) -> List[Dict]:
        """HNSW index search."""
        index = self._indexes.get(collection)
        if not index:
            return self._brute_force_search(collection, query_vector, limit, threshold)
        
        # Convert to numpy
        query = np.array([query_vector], dtype=np.float32)
        
        # Search
        try:
            labels, distances = index.knn_items(query, k=min(limit, index.element_count))
        except Exception:
            return self._brute_force_search(collection, query_vector, limit, threshold)
        
        results = []
        
        for label, dist in zip(labels[0], distances[0]):
            similarity = 1.0 - dist  # Convert distance to similarity
            
            if similarity >= threshold:
                # Fetch metadata and real ID from DB using hash if needed
                # For now, we assume label matches vec_id if vec_id was int
                cursor = self._conn.execute(
                    "SELECT vec_id, metadata FROM _vectors WHERE collection = ? AND (vec_id = ? OR hash LIKE ?)",
                    (collection, str(label), f"{label}%")
                )
                row = cursor.fetchone()
                
                if row:
                    results.append({
                        "vec_id": row[0],
                        "similarity": similarity,
                        "metadata": json.loads(row[1]) if row[1] else None
                    })
        
        return results
    
    def _add_to_index(self, collection: str, vec_id: str, 
                      embedding: List[float]) -> None:
        """Add vector to HNSW index."""
        dim = len(embedding)
        
        if collection not in self._indexes:
            # Create new index
            index = hnswlib.Index(space="cosine", dim=dim)
            index.init_index(max_elements=10000, ef_construction=200, M=16)
            self._indexes[collection] = index
        else:
            index = self._indexes[collection]
        
        # Add vector
        vector = np.array([embedding], dtype=np.float32)
        # HNSW labels must be integers. Convert vec_id to int if possible, else hash.
        try:
            label = int(vec_id)
        except ValueError:
            label = int(hashlib.md5(vec_id.encode()).hexdigest(), 16) % (2**31 - 1)
            
        index.add_items(vector, [label])
    
    def create_index(self, collection: str, dim: int, 
                     max_elements: int = 10000,
                     ef_construction: int = 200,
                     M: int = 16) -> bool:
        """
        Create HNSW index for collection.
        
        Args:
            collection: Collection name
            dim: Vector dimension
            max_elements: Max elements in index
            ef_construction: Construction parameter
            M: M parameter
        
        Returns:
            True if created, False if HNSW not available
        """
        if not HNSW_AVAILABLE:
            return False
        
        index = hnswlib.Index(space="cosine", dim=dim)
        index.init_index(
            max_elements=max_elements,
            ef_construction=ef_construction,
            M=M
        )
        
        self._indexes[collection] = index
        
        # Load existing vectors
        cursor = self._conn.execute(
            "SELECT vec_id, embedding FROM _vectors WHERE collection = ?",
            (collection,)
        )
        
        for row in cursor:
            vid = row[0]
            emb_bytes = row[1]
            
            d = len(emb_bytes) // 4
            embedding = list(struct.unpack(f'{d}f', emb_bytes))
            
            vector = np.array([embedding], dtype=np.float32)
            try:
                label = int(vid)
            except ValueError:
                label = int(hashlib.md5(vid.encode()).hexdigest(), 16) % (2**31 - 1)
            index.add_items(vector, [label])
        
        return True
    
    def save_index(self, collection: str, path: str) -> bool:
        """Save HNSW index to file."""
        if not HNSW_AVAILABLE or collection not in self._indexes:
            return False
        
        self._indexes[collection].save_index(path)
        return True
    
    def load_index(self, collection: str, path: str, dim: int) -> bool:
        """Load HNSW index from file."""
        if not HNSW_AVAILABLE:
            return False
        
        index = hnswlib.Index(space="cosine", dim=dim)
        index.load_index(path)
        
        self._indexes[collection] = index
        return True
    
    def delete(self, collection: str, vec_id: str) -> int:
        """Delete vector from collection."""
        cursor = self._conn.execute(
            "DELETE FROM _vectors WHERE collection = ? AND vec_id = ?",
            (collection, vec_id)
        )
        self._conn.commit()
        
        # Audit
        if self._audit_manager:
            self._audit_manager.log(
                operation="VECTOR_DELETE",
                table_name="_vectors",
                record_id=f"{collection}:{vec_id}",
                old_value={"collection": collection, "vec_id": vec_id}
            )
            
        return cursor.rowcount
    
    def get(self, collection: str, vec_id: str) -> Optional[Dict]:
        """Get vector by ID."""
        cursor = self._conn.execute(
            "SELECT vec_id, embedding, metadata, hash FROM _vectors WHERE collection = ? AND vec_id = ?",
            (collection, vec_id)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        emb_bytes = row[1]
        dim = len(emb_bytes) // 4
        embedding = list(struct.unpack(f'{dim}f', emb_bytes))
        
        return {
            "vec_id": row[0],
            "embedding": embedding,
            "metadata": json.loads(row[2]) if row[2] else None,
            "hash": row[3]
        }
    
    def list_vectors(self, collection: str, limit: int = 100) -> List[Dict]:
        """List vectors in collection."""
        cursor = self._conn.execute(
            "SELECT vec_id, metadata, hash, created_at FROM _vectors WHERE collection = ? LIMIT ?",
            (collection, limit)
        )
        
        return [
            {
                "vec_id": row[0],
                "metadata": json.loads(row[1]) if row[1] else None,
                "hash": row[2],
                "created_at": row[3]
            }
            for row in cursor
        ]
    
    def count(self, collection: str) -> int:
        """Count vectors in collection."""
        cursor = self._conn.execute(
            "SELECT COUNT(*) FROM _vectors WHERE collection = ?",
            (collection,)
        )
        return cursor.fetchone()[0]
    
    def _cosine_similarity(self, vec1: List[float], 
                           vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text (simple placeholder).

        In production, use sentence-transformers or similar.
        """
        # Simple hash-based embedding (NOT semantic, just for testing)
        hash_val = hashlib.sha256(text.encode()).digest()

        # Convert to 32-dimensional vector
        embedding = []
        for i in range(0, 32):
            byte_val = hash_val[i % 32]
            embedding.append((byte_val - 128) / 128.0)

        # Normalize vector
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding
