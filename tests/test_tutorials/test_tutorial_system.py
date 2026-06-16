"""Tests for Tutorial system."""

import pytest
import sqlite3
import tempfile
import os
import time
from ule.core.database import ULEDatabase
from ule.tutorials.tutorial_system import TutorialManager, Tutorial, TutorialStep, TutorialStatus


class TestTutorialManager:
    """Test Tutorial Manager functionality."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.commit()
        
        class SimpleDB:
            def __init__(self, conn):
                self._conn = conn
            def get_connection(self):
                return self._conn
        
        yield SimpleDB(conn)
        
        conn.close()
        os.unlink(db_path)

    @pytest.fixture
    def tutorials(self, db):
        """Create tutorial manager."""
        return TutorialManager(db)

    def test_init(self, tutorials):
        """Test tutorial manager initialization."""
        assert tutorials is not None
        # Should have built-in tutorials
        assert len(tutorials._tutorials) > 0

    def test_list_tutorials(self, tutorials):
        """Test listing tutorials."""
        all_tutorials = tutorials.list_tutorials()
        assert len(all_tutorials) > 0

    def test_list_tutorials_by_category(self, tutorials):
        """Test filtering tutorials by category."""
        sql_tutorials = tutorials.list_tutorials(category='SQL')
        assert len(sql_tutorials) > 0
        assert all(t.category == 'SQL' for t in sql_tutorials)

    def test_list_tutorials_by_difficulty(self, tutorials):
        """Test filtering tutorials by difficulty."""
        beginner_tutorials = tutorials.list_tutorials(difficulty='beginner')
        assert len(beginner_tutorials) > 0
        assert all(t.difficulty == 'beginner' for t in beginner_tutorials)

    def test_start_tutorial(self, tutorials):
        """Test starting a tutorial."""
        tutorial = tutorials.start_tutorial('basic_sql')
        
        assert tutorial is not None
        assert tutorial.status == TutorialStatus.IN_PROGRESS
        assert tutorial.current_step == 0
        assert tutorial.started_at is not None

    def test_start_nonexistent_tutorial(self, tutorials):
        """Test starting a non-existent tutorial."""
        tutorial = tutorials.start_tutorial('nonexistent')
        assert tutorial is None

    def test_get_current_step(self, tutorials):
        """Test getting current step."""
        tutorials.start_tutorial('basic_sql')
        
        step = tutorials.get_current_step()
        assert step is not None
        assert step.id == 1

    def test_execute_step(self, tutorials):
        """Test executing a step."""
        tutorials.start_tutorial('basic_sql')
        
        result = tutorials.execute_step()
        
        assert 'step_id' in result
        assert 'title' in result
        assert 'code' in result
        assert 'description' in result

    def test_next_step(self, tutorials):
        """Test moving to next step."""
        tutorials.start_tutorial('basic_sql')
        
        initial_step = tutorials.get_current_step()
        next_step = tutorials.next_step()
        
        assert next_step.id == initial_step.id + 1

    def test_previous_step(self, tutorials):
        """Test moving to previous step."""
        tutorials.start_tutorial('basic_sql')
        tutorials.next_step()
        
        prev_step = tutorials.previous_step()
        assert prev_step.id == 1

    def test_tutorial_completion(self, tutorials):
        """Test completing a tutorial."""
        tutorial = tutorials.start_tutorial('basic_sql')
        
        # Complete all steps
        while tutorials.get_current_step():
            tutorials.next_step()
        
        assert tutorial.status == TutorialStatus.COMPLETED
        assert tutorial.completed_at is not None

    def test_get_progress(self, tutorials):
        """Test getting tutorial progress."""
        tutorials.start_tutorial('basic_sql')
        
        progress = tutorials.get_progress('basic_sql')
        
        assert progress['status'] == 'in_progress'
        assert progress['current_step'] == 0

    def test_reset_tutorial(self, tutorials):
        """Test resetting a tutorial."""
        tutorials.start_tutorial('basic_sql')
        tutorials.next_step()
        
        tutorials.reset_tutorial('basic_sql')
        
        progress = tutorials.get_progress('basic_sql')
        assert progress['status'] == 'not_started'
        assert progress['current_step'] == 0

    def test_tutorial_progress(self, tutorials):
        """Test tutorial progress calculation."""
        tutorial = tutorials.start_tutorial('basic_sql')
        
        initial_progress = tutorial.progress
        tutorials.next_step()
        updated_progress = tutorial.progress
        
        assert updated_progress > initial_progress


class TestTutorial:
    """Test Tutorial dataclass."""

    def test_tutorial_creation(self):
        """Test creating a tutorial."""
        tutorial = Tutorial(
            id='test',
            title='Test Tutorial',
            description='A test tutorial',
            category='Test',
            difficulty='beginner',
            estimated_time=10
        )
        
        assert tutorial.id == 'test'
        assert tutorial.status == TutorialStatus.NOT_STARTED
        assert len(tutorial.steps) == 0

    def test_tutorial_with_steps(self):
        """Test creating a tutorial with steps."""
        tutorial = Tutorial(
            id='test',
            title='Test Tutorial',
            description='A test tutorial',
            category='Test',
            difficulty='beginner',
            estimated_time=10,
            steps=[
                TutorialStep(id=1, title='Step 1', description='First step', code='print(1)'),
                TutorialStep(id=2, title='Step 2', description='Second step', code='print(2)'),
            ]
        )
        
        assert len(tutorial.steps) == 2
        assert tutorial.progress == 0.0

    def test_tutorial_progress_calculation(self):
        """Test progress calculation."""
        tutorial = Tutorial(
            id='test',
            title='Test',
            description='Test',
            category='Test',
            difficulty='beginner',
            estimated_time=10,
            steps=[
                TutorialStep(id=1, title='Step 1', description='Step 1', code='code1'),
                TutorialStep(id=2, title='Step 2', description='Step 2', code='code2'),
                TutorialStep(id=3, title='Step 3', description='Step 3', code='code3'),
            ]
        )
        
        tutorial.current_step = 1
        assert tutorial.progress == 1/3
        
        tutorial.current_step = 2
        assert tutorial.progress == 2/3
        
        tutorial.current_step = 3
        assert tutorial.progress == 1.0

    def test_tutorial_to_dict(self):
        """Test tutorial serialization."""
        tutorial = Tutorial(
            id='test',
            title='Test Tutorial',
            description='A test',
            category='Test',
            difficulty='beginner',
            estimated_time=10
        )
        
        data = tutorial.to_dict()
        assert data['id'] == 'test'
        assert data['title'] == 'Test Tutorial'
        assert data['progress'] == 0.0


class TestTutorialStep:
    """Test TutorialStep dataclass."""

    def test_step_creation(self):
        """Test creating a tutorial step."""
        step = TutorialStep(
            id=1,
            title='Test Step',
            description='A test step',
            code='print("hello")',
            hint='This is a hint'
        )
        
        assert step.id == 1
        assert step.title == 'Test Step'
        assert step.hint == 'This is a hint'

    def test_step_to_dict(self):
        """Test step serialization."""
        step = TutorialStep(
            id=1,
            title='Test Step',
            description='A test step',
            code='print("hello")'
        )
        
        data = step.to_dict()
        assert data['id'] == 1
        assert data['title'] == 'Test Step'
        assert data['code'] == 'print("hello")'
