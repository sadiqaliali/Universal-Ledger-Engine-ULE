"""Tests for Vector engine."""

import pytest
from ule.engines.vector_engine import VectorEngine


class TestVectorEngine:
    """Test Vector engine operations."""
    
    def test_add_and_get(self, temp_db):
        """Test adding and retrieving vectors."""
        engine = VectorEngine(temp_db._conn)
        vector = [0.1, 0.2, 0.3, 0.4]
        
        vec_hash = engine.add("test_coll", "v1", vector, {"label": "test"})
        
        assert vec_hash is not None
        
        vec_data = engine.get("test_coll", "v1")
        assert vec_data["vec_id"] == "v1"
        assert vec_data["embedding"] == pytest.approx(vector)
        assert vec_data["metadata"]["label"] == "test"
    
    def test_search_brute_force(self, temp_db):
        """Test similarity search (brute-force)."""
        engine = VectorEngine(temp_db._conn)
        
        # Add 3 vectors
        engine.add("items", "1", [1.0, 0.0, 0.0]) # Perfect match
        engine.add("items", "2", [0.8, 0.6, 0.0]) # Close
        engine.add("items", "3", [0.0, 1.0, 0.0]) # Orthogonal
        
        query = [1.0, 0.0, 0.0]
        results = engine.search("items", query, limit=2)
        
        assert len(results) == 2
        assert results[0]["vec_id"] == "1"
        assert results[0]["similarity"] == pytest.approx(1.0)
        assert results[1]["vec_id"] == "2"
        assert results[1]["similarity"] == pytest.approx(0.8)
    
    def test_delete(self, temp_db):
        """Test deleting vectors."""
        engine = VectorEngine(temp_db._conn)
        engine.add("coll", "v1", [1.0, 2.0])
        
        count = engine.delete("coll", "v1")
        assert count == 1
        
        assert engine.get("coll", "v1") is None
    
    def test_count_and_list(self, temp_db):
        """Test counting and listing vectors."""
        engine = VectorEngine(temp_db._conn)
        engine.add("coll", "v1", [1.0, 0.0])
        engine.add("coll", "v2", [0.0, 1.0])
        
        assert engine.count("coll") == 2
        
        vectors = engine.list_vectors("coll")
        assert len(vectors) == 2
        ids = [v["vec_id"] for v in vectors]
        assert "v1" in ids
        assert "v2" in ids

    def test_cosine_similarity(self, temp_db):
        """Test internal similarity calculation."""
        engine = VectorEngine(temp_db._conn)
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        v3 = [1.0, 1.0] # 45 degrees
        
        assert engine._cosine_similarity(v1, v1) == pytest.approx(1.0)
        assert engine._cosine_similarity(v1, v2) == pytest.approx(0.0)
        assert engine._cosine_similarity(v1, v3) == pytest.approx(0.7071, abs=1e-4)

    def test_embed_text(self, temp_db):
        """Test simple text embedding placeholder."""
        engine = VectorEngine(temp_db._conn)
        text = "Hello ULE"
        embedding = engine.embed_text(text)
        
        assert len(embedding) == 32
        # Check normalization
        norm = sum(x*x for x in embedding) ** 0.5
        assert norm == pytest.approx(1.0)
