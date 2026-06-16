"""Healthcare Domain Model for ULE.

HIPAA-compliant healthcare data model with:
- Patient management
- Appointments scheduling
- Medical records
- Prescriptions
- Billing
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


class HealthcareModel:
    """Healthcare domain model."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create healthcare tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT CHECK(gender IN ('M', 'F', 'Other')),
                phone TEXT,
                email TEXT,
                address TEXT,
                emergency_contact TEXT,
                insurance_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                specialty TEXT,
                phone TEXT,
                email TEXT,
                license_number TEXT,
                department TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT UNIQUE NOT NULL,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'completed', 'cancelled', 'no-show')),
                reason TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )""",

            """CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE NOT NULL,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                visit_date TEXT NOT NULL,
                diagnosis TEXT,
                symptoms TEXT,
                treatment TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )""",

            """CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prescription_id TEXT UNIQUE NOT NULL,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                medication TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                duration TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'cancelled')),
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )""",

            """CREATE TABLE IF NOT EXISTS billing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id TEXT UNIQUE NOT NULL,
                patient_id TEXT NOT NULL,
                appointment_id TEXT,
                amount REAL NOT NULL,
                insurance_amount REAL,
                patient_amount REAL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'rejected', 'partial')),
                insurance_claim_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
            )""",
        ]

        for table_sql in tables:
            self._conn.execute(table_sql)
        self._conn.commit()

    def add_patient(self, **kwargs) -> str:
        """Add a new patient."""
        import uuid
        patient_id = f"PAT-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, 
               gender, phone, email, address, emergency_contact, insurance_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (patient_id, kwargs.get('first_name'), kwargs.get('last_name'),
             kwargs.get('date_of_birth'), kwargs.get('gender'),
             kwargs.get('phone'), kwargs.get('email'), kwargs.get('address'),
             kwargs.get('emergency_contact'), kwargs.get('insurance_id'))
        )
        self._conn.commit()
        return patient_id

    def add_doctor(self, **kwargs) -> str:
        """Add a new doctor."""
        import uuid
        doctor_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO doctors (doctor_id, first_name, last_name, specialty,
               phone, email, license_number, department)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (doctor_id, kwargs.get('first_name'), kwargs.get('last_name'),
             kwargs.get('specialty'), kwargs.get('phone'), kwargs.get('email'),
             kwargs.get('license_number'), kwargs.get('department'))
        )
        self._conn.commit()
        return doctor_id

    def schedule_appointment(self, patient_id: str, doctor_id: str, 
                            appointment_date: str, **kwargs) -> str:
        """Schedule a new appointment."""
        import uuid
        appointment_id = f"APT-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO appointments (appointment_id, patient_id, doctor_id,
               appointment_date, start_time, end_time, reason)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (appointment_id, patient_id, doctor_id, appointment_date,
             kwargs.get('start_time'), kwargs.get('end_time'), kwargs.get('reason'))
        )
        self._conn.commit()
        return appointment_id

    def get_patient_records(self, patient_id: str) -> List[Dict]:
        """Get all medical records for a patient."""
        cursor = self._conn.execute(
            "SELECT * FROM medical_records WHERE patient_id = ?",
            (patient_id,)
        )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def add_prescription(self, patient_id: str, doctor_id: str, **kwargs) -> str:
        """Add a new prescription."""
        import uuid
        prescription_id = f"RX-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO prescriptions (prescription_id, patient_id, doctor_id,
               medication, dosage, frequency, duration, start_date, end_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (prescription_id, patient_id, doctor_id, kwargs.get('medication'),
             kwargs.get('dosage'), kwargs.get('frequency'), kwargs.get('duration'),
             kwargs.get('start_date'), kwargs.get('end_date'))
        )
        self._conn.commit()
        return prescription_id

    def get_patient_appointments(self, patient_id: str) -> List[Dict]:
        """Get all appointments for a patient."""
        cursor = self._conn.execute(
            """SELECT a.*, d.first_name as doctor_first_name, d.last_name as doctor_last_name
               FROM appointments a
               JOIN doctors d ON a.doctor_id = d.doctor_id
               WHERE a.patient_id = ?
               ORDER BY a.appointment_date""",
            (patient_id,)
        )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def get_upcoming_appointments(self, days: int = 7) -> List[Dict]:
        """Get upcoming appointments."""
        future_date = (datetime.now() + timedelta(days=days)).isoformat()
        cursor = self._conn.execute(
            """SELECT a.*, p.first_name as patient_first_name, p.last_name as patient_last_name,
                      d.first_name as doctor_first_name, d.last_name as doctor_last_name
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               JOIN doctors d ON a.doctor_id = d.doctor_id
               WHERE a.appointment_date <= ? AND a.status = 'scheduled'
               ORDER BY a.appointment_date""",
            (future_date,)
        )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate HIPAA compliance report."""
        stats = {
            'total_patients': self._conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            'total_doctors': self._conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
            'total_appointments': self._conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
            'total_prescriptions': self._conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0],
            'pending_bills': self._conn.execute("SELECT COUNT(*) FROM billing WHERE status='pending'").fetchone()[0],
            'generated_at': datetime.now().isoformat()
        }
        return stats
