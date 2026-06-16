"""Tests for Graph engine."""

import pytest
from ule.engines.graph_engine import GraphEngine


class TestGraphEngine:
    """Test Graph engine operations."""
    
    def test_link(self, temp_db):
        """Test creating relationships."""
        engine = GraphEngine(temp_db._conn)
        
        edge_hash = engine.link("users", "1", "users", "2", "FRIEND", {"since": "2024"})
        
        assert edge_hash is not None
        
        edges = engine.get_edges(from_table="users", from_id="1")
        assert len(edges) == 1
        assert edges[0]["relation"] == "FRIEND"
        assert edges[0]["properties"]["since"] == "2024"
    
    def test_unlink(self, temp_db):
        """Test removing relationships."""
        engine = GraphEngine(temp_db._conn)
        engine.link("users", "1", "users", "2", "FRIEND")
        
        count = engine.unlink("users", "1", "users", "2", "FRIEND")
        assert count == 1
        
        edges = engine.get_edges(from_table="users", from_id="1")
        assert len(edges) == 0
    
    def test_traverse(self, temp_db):
        """Test BFS traversal."""
        engine = GraphEngine(temp_db._conn)
        # 1 -> 2 -> 3
        engine.link("users", "1", "users", "2", "FRIEND")
        engine.link("users", "2", "users", "3", "FRIEND")
        
        results = engine.traverse("users", "1", depth=2)
        
        # Should find 1->2 and 2->3
        assert len(results) == 2
        assert any(e["to"] == "users:2" for e in results)
        assert any(e["to"] == "users:3" for e in results)
    
    def test_find_path(self, temp_db):
        """Test shortest path finding."""
        engine = GraphEngine(temp_db._conn)
        # 1 -> 2 -> 3
        engine.link("users", "1", "users", "2", "FRIEND")
        engine.link("users", "2", "users", "3", "FRIEND")
        # 1 -> 3 (direct)
        engine.link("users", "1", "users", "3", "EMERGENCY_CONTACT")
        
        path = engine.find_path("users", "1", "users", "3")
        
        # BFS should find shortest path (direct link)
        assert len(path) == 1
        assert path[0]["relation"] == "EMERGENCY_CONTACT"
    
    def test_neighbors(self, temp_db):
        """Test neighbor queries."""
        engine = GraphEngine(temp_db._conn)
        engine.link("users", "1", "users", "2", "FOLLOWS")
        engine.link("users", "3", "users", "1", "FOLLOWS")
        
        # Out-neighbors
        out_neighbors = engine.neighbors("users", "1", direction="out")
        assert len(out_neighbors) == 1
        assert out_neighbors[0]["id"] == "2"
        
        # In-neighbors
        in_neighbors = engine.neighbors("users", "1", direction="in")
        assert len(in_neighbors) == 1
        assert in_neighbors[0]["id"] == "3"
        
        # Both
        both = engine.neighbors("users", "1", direction="both")
        assert len(both) == 2
    
    def test_node_degree(self, temp_db):
        """Test degree calculations."""
        engine = GraphEngine(temp_db._conn)
        engine.link("users", "1", "users", "2", "KNOWS")
        engine.link("users", "3", "users", "1", "KNOWS")
        
        degree = engine.get_node_degree("users", "1")
        assert degree["in_degree"] == 1
        assert degree["out_degree"] == 1
        assert degree["total"] == 2
    
    def test_get_relations(self, temp_db):
        """Test listing unique relations."""
        engine = GraphEngine(temp_db._conn)
        engine.link("users", "1", "users", "2", "FRIEND")
        engine.link("users", "1", "users", "3", "COLLEAGUE")
        
        relations = engine.get_relations()
        assert "FRIEND" in relations
        assert "COLLEAGUE" in relations
        assert len(relations) == 2
