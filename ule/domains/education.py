"""Education Domain Model for ULE.

Education management data model with:
- Students management
- Courses
- Enrollments
- Grades
- Attendance
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Any


class EducationModel:
    """Education domain model."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create education tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                date_of_birth TEXT,
                enrollment_date TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'graduated', 'suspended', 'withdrawn')),
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                department TEXT,
                specialization TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT UNIQUE NOT NULL,
                course_code TEXT NOT NULL,
                course_name TEXT NOT NULL,
                description TEXT,
                credits INTEGER DEFAULT 3,
                department TEXT,
                teacher_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
            )""",

            """CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id TEXT UNIQUE NOT NULL,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                enrollment_date TEXT NOT NULL,
                status TEXT DEFAULT 'enrolled' CHECK(status IN ('enrolled', 'completed', 'dropped', 'failed')),
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )""",

            """CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grade_id TEXT UNIQUE NOT NULL,
                enrollment_id TEXT NOT NULL,
                grade TEXT CHECK(grade IN ('A', 'B', 'C', 'D', 'F', 'I', 'W')),
                grade_points REAL,
                comments TEXT,
                graded_date TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
            )""",

            """CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attendance_id TEXT UNIQUE NOT NULL,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT CHECK(status IN ('present', 'absent', 'late', 'excused')),
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )""",
        ]

        for table_sql in tables:
            self._conn.execute(table_sql)
        self._conn.commit()

    def add_student(self, **kwargs) -> str:
        """Add a new student."""
        import uuid
        student_id = f"STU-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO students (student_id, first_name, last_name, email, phone,
               date_of_birth, enrollment_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (student_id, kwargs.get('first_name'), kwargs.get('last_name'),
             kwargs.get('email'), kwargs.get('phone'), kwargs.get('date_of_birth'),
             kwargs.get('enrollment_date', datetime.now().isoformat()))
        )
        self._conn.commit()
        return student_id

    def add_teacher(self, **kwargs) -> str:
        """Add a new teacher."""
        import uuid
        teacher_id = f"TCH-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO teachers (teacher_id, first_name, last_name, email, phone,
               department, specialization)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (teacher_id, kwargs.get('first_name'), kwargs.get('last_name'),
             kwargs.get('email'), kwargs.get('phone'), kwargs.get('department'),
             kwargs.get('specialization'))
        )
        self._conn.commit()
        return teacher_id

    def add_course(self, **kwargs) -> str:
        """Add a new course."""
        import uuid
        course_id = f"CRS-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO courses (course_id, course_code, course_name, description,
               credits, department, teacher_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (course_id, kwargs.get('course_code'), kwargs.get('course_name'),
             kwargs.get('description'), kwargs.get('credits', 3),
             kwargs.get('department'), kwargs.get('teacher_id'))
        )
        self._conn.commit()
        return course_id

    def enroll_student(self, student_id: str, course_id: str) -> str:
        """Enroll a student in a course."""
        import uuid
        enrollment_id = f"ENR-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO enrollments (enrollment_id, student_id, course_id, enrollment_date)
               VALUES (?, ?, ?, ?)""",
            (enrollment_id, student_id, course_id, datetime.now().isoformat())
        )
        self._conn.commit()
        return enrollment_id

    def record_grade(self, enrollment_id: str, grade: str, **kwargs) -> str:
        """Record a grade for a student."""
        import uuid
        grade_id = f"GRD-{uuid.uuid4().hex[:8].upper()}"
        grade_points = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}.get(grade, 0.0)
        
        self._conn.execute(
            """INSERT INTO grades (grade_id, enrollment_id, grade, grade_points,
               comments, graded_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (grade_id, enrollment_id, grade, grade_points,
             kwargs.get('comments'), kwargs.get('graded_date', datetime.now().isoformat()))
        )
        self._conn.commit()
        return grade_id

    def mark_attendance(self, student_id: str, course_id: str, 
                       status: str, **kwargs) -> str:
        """Mark attendance for a student."""
        import uuid
        attendance_id = f"ATT-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO attendance (attendance_id, student_id, course_id, date, status, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (attendance_id, student_id, course_id, 
             kwargs.get('date', datetime.now().isoformat()), status, kwargs.get('notes'))
        )
        self._conn.commit()
        return attendance_id

    def get_student_grades(self, student_id: str) -> List[Dict]:
        """Get all grades for a student."""
        cursor = self._conn.execute(
            """SELECT g.*, c.course_name, c.course_code
               FROM grades g
               JOIN enrollments e ON g.enrollment_id = e.enrollment_id
               JOIN courses c ON e.course_id = c.course_id
               WHERE e.student_id = ?""",
            (student_id,)
        )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def get_education_summary(self) -> Dict[str, Any]:
        """Get education summary."""
        return {
            'total_students': self._conn.execute("SELECT COUNT(*) FROM students").fetchone()[0],
            'total_teachers': self._conn.execute("SELECT COUNT(*) FROM teachers").fetchone()[0],
            'total_courses': self._conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
            'total_enrollments': self._conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0],
            'generated_at': datetime.now().isoformat()
        }
