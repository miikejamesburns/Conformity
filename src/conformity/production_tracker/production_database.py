"""
Production Tracker Database for Conformity.

SQLite database for comprehensive production tracking including:
- Projects and sequences
- Shots with department statuses
- Tasks and assignments
- Reviews and approvals
- Deliverables
- Team and vendor management

Designed for film/TV post-production workflows with multiple departments
(Editorial, VFX, Color, Sound, Finishing).
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Department(Enum):
    """Production departments."""
    EDITORIAL = "editorial"
    VFX = "vfx"
    COLOR = "color"
    SOUND = "sound"
    FINISHING = "finishing"
    DELIVERY = "delivery"


class ShotStatus(Enum):
    """Shot status in department pipeline."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    APPROVED = "approved"
    FINAL = "final"
    ON_HOLD = "on_hold"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    """Task completion status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VFXComplexity(Enum):
    """VFX shot complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class ProductionDatabase:
    """
    SQLite database for production tracking.

    Provides comprehensive project management for post-production with:
    - Project and sequence organization
    - Shot-level tracking across departments
    - Task assignment and progress tracking
    - Review and approval workflows
    - Deliverable checklist management
    - Team and vendor directory

    Example:
        ```python
        db = ProductionDatabase(Path("project.db"))

        # Create project
        project_id = db.create_project(
            name="Short Film Title",
            description="Festival submission",
            target_runtime=600  # 10 minutes
        )

        # Create sequence
        seq_id = db.create_sequence(project_id, "SEQ_010", "Opening Sequence")

        # Add shot
        shot_id = db.create_shot(
            sequence_id=seq_id,
            shot_name="010_010",
            description="Wide establishing shot",
            start_tc="01:00:00:00",
            end_tc="01:00:05:00"
        )

        # Update department status
        db.update_shot_status(shot_id, Department.VFX, ShotStatus.IN_PROGRESS)

        # Create task
        task_id = db.create_task(
            shot_id=shot_id,
            department=Department.VFX,
            title="Cleanup wire removal",
            assignee="john@vfx.com",
            priority=TaskPriority.HIGH,
            due_date="2025-12-01"
        )
        ```
    """

    # Database schema version
    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize production database.

        Args:
            db_path: Path to SQLite database file (None = in-memory)
        """
        if db_path is None:
            self.db_path = ":memory:"
        else:
            self.db_path = str(db_path)

        self._connect()
        self._create_schema()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _create_schema(self):
        """Create database schema."""

        # Projects table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                target_runtime INTEGER,  -- seconds
                actual_runtime INTEGER,
                budget REAL,
                spent REAL DEFAULT 0,
                start_date TEXT,
                target_completion TEXT,
                status TEXT DEFAULT 'active',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Sequences table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                sequence_name TEXT NOT NULL,
                description TEXT,
                scene_number TEXT,
                sort_order INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Shots table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence_id INTEGER NOT NULL,
                shot_name TEXT NOT NULL,
                description TEXT,
                start_timecode TEXT,
                end_timecode TEXT,
                duration_frames INTEGER,
                frame_rate REAL DEFAULT 24.0,

                -- Department statuses
                editorial_status TEXT DEFAULT 'not_started',
                vfx_status TEXT DEFAULT 'not_started',
                color_status TEXT DEFAULT 'not_started',
                sound_status TEXT DEFAULT 'not_started',
                finishing_status TEXT DEFAULT 'not_started',
                delivery_status TEXT DEFAULT 'not_started',

                -- VFX specific
                vfx_complexity TEXT,
                vfx_vendor TEXT,

                -- Color specific
                colorist TEXT,
                color_notes TEXT,

                -- References
                reference_image TEXT,
                director_notes TEXT,

                -- Metadata
                camera_info TEXT,
                lens_info TEXT,
                shot_type TEXT,  -- wide, medium, closeup, etc.
                movement TEXT,   -- static, pan, tilt, dolly, etc.

                is_locked BOOLEAN DEFAULT 0,
                priority INTEGER DEFAULT 0,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE
            )
        """)

        # Tasks table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_id INTEGER,
                project_id INTEGER,
                department TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                assignee TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'todo',
                due_date TEXT,
                completed_at TEXT,
                estimated_hours REAL,
                actual_hours REAL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (shot_id) REFERENCES shots(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Reviews table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_id INTEGER,
                task_id INTEGER,
                department TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending, approved, revision_requested
                comments TEXT,
                version INTEGER DEFAULT 1,
                review_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (shot_id) REFERENCES shots(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)

        # Deliverables table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS deliverables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                category TEXT NOT NULL,  -- master, festival, dcp, marketing
                name TEXT NOT NULL,
                description TEXT,
                format TEXT,
                resolution TEXT,
                codec TEXT,
                status TEXT DEFAULT 'not_started',
                file_path TEXT,
                due_date TEXT,
                completed_date TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Team members table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                is_vendor BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Milestones table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                target_date TEXT NOT NULL,
                completed_date TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Notes/Comments table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_id INTEGER,
                task_id INTEGER,
                author TEXT NOT NULL,
                note_type TEXT,  -- general, technical, creative
                content TEXT NOT NULL,
                timecode TEXT,
                frame_number INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (shot_id) REFERENCES shots(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)

        # Create indices
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_shots_sequence ON shots(sequence_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_shot ON tasks(shot_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_shot ON reviews(shot_id)")

        self.conn.commit()
        logger.info("Production database schema created")

    # Project management
    def create_project(
        self,
        name: str,
        description: str = "",
        target_runtime: Optional[int] = None,
        budget: Optional[float] = None,
        start_date: Optional[str] = None,
        target_completion: Optional[str] = None
    ) -> int:
        """Create a new project."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO projects (
                name, description, target_runtime, budget,
                start_date, target_completion, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, target_runtime, budget, start_date, target_completion, now, now))

        self.conn.commit()
        logger.info(f"Created project: {name}")
        return self.cursor.lastrowid

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        self.cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def list_projects(self, status: str = "active") -> List[Dict[str, Any]]:
        """List all projects."""
        self.cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC", (status,))
        return [dict(row) for row in self.cursor.fetchall()]

    # Sequence management
    def create_sequence(
        self,
        project_id: int,
        sequence_name: str,
        description: str = "",
        scene_number: str = "",
        sort_order: int = 0
    ) -> int:
        """Create a new sequence."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO sequences (
                project_id, sequence_name, description, scene_number,
                sort_order, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id, sequence_name, description, scene_number, sort_order, now, now))

        self.conn.commit()
        logger.info(f"Created sequence: {sequence_name}")
        return self.cursor.lastrowid

    def list_sequences(self, project_id: int) -> List[Dict[str, Any]]:
        """List sequences for a project."""
        self.cursor.execute("""
            SELECT * FROM sequences
            WHERE project_id = ?
            ORDER BY sort_order, sequence_name
        """, (project_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # Shot management
    def create_shot(
        self,
        sequence_id: int,
        shot_name: str,
        description: str = "",
        start_tc: str = "",
        end_tc: str = "",
        duration_frames: Optional[int] = None,
        **kwargs
    ) -> int:
        """Create a new shot."""
        now = datetime.now().isoformat()

        # Build column and value lists dynamically
        columns = [
            'sequence_id', 'shot_name', 'description',
            'start_timecode', 'end_timecode', 'duration_frames',
            'created_at', 'updated_at'
        ]
        values = [sequence_id, shot_name, description, start_tc, end_tc, duration_frames, now, now]

        # Add optional fields
        for key, value in kwargs.items():
            if value is not None:
                columns.append(key)
                values.append(value)

        placeholders = ','.join(['?' for _ in columns])
        query = f"INSERT INTO shots ({','.join(columns)}) VALUES ({placeholders})"

        self.cursor.execute(query, values)
        self.conn.commit()
        logger.info(f"Created shot: {shot_name}")
        return self.cursor.lastrowid

    def get_shot(self, shot_id: int) -> Optional[Dict[str, Any]]:
        """Get shot by ID."""
        self.cursor.execute("SELECT * FROM shots WHERE id = ?", (shot_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def list_shots(
        self,
        sequence_id: Optional[int] = None,
        department: Optional[Department] = None,
        status: Optional[ShotStatus] = None
    ) -> List[Dict[str, Any]]:
        """List shots with optional filters."""
        query = "SELECT * FROM shots WHERE 1=1"
        params = []

        if sequence_id:
            query += " AND sequence_id = ?"
            params.append(sequence_id)

        if department and status:
            status_column = f"{department.value}_status"
            query += f" AND {status_column} = ?"
            params.append(status.value)

        query += " ORDER BY shot_name"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def update_shot_status(
        self,
        shot_id: int,
        department: Department,
        status: ShotStatus
    ) -> bool:
        """Update shot status for a department."""
        status_column = f"{department.value}_status"
        now = datetime.now().isoformat()

        self.cursor.execute(f"""
            UPDATE shots
            SET {status_column} = ?, updated_at = ?
            WHERE id = ?
        """, (status.value, now, shot_id))

        self.conn.commit()
        logger.info(f"Updated shot {shot_id} {department.value} status to {status.value}")
        return self.cursor.rowcount > 0

    def lock_shot(self, shot_id: int, locked: bool = True) -> bool:
        """Lock or unlock a shot."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            UPDATE shots
            SET is_locked = ?, updated_at = ?
            WHERE id = ?
        """, (1 if locked else 0, now, shot_id))

        self.conn.commit()
        return self.cursor.rowcount > 0

    # Task management
    def create_task(
        self,
        department: Department,
        title: str,
        shot_id: Optional[int] = None,
        project_id: Optional[int] = None,
        description: str = "",
        assignee: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[str] = None,
        estimated_hours: Optional[float] = None
    ) -> int:
        """Create a new task."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO tasks (
                shot_id, project_id, department, title, description,
                assignee, priority, due_date, estimated_hours,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            shot_id, project_id, department.value, title, description,
            assignee, priority.value, due_date, estimated_hours, now, now
        ))

        self.conn.commit()
        logger.info(f"Created task: {title}")
        return self.cursor.lastrowid

    def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        actual_hours: Optional[float] = None
    ) -> bool:
        """Update task status."""
        now = datetime.now().isoformat()
        completed_at = now if status == TaskStatus.COMPLETED else None

        self.cursor.execute("""
            UPDATE tasks
            SET status = ?, actual_hours = ?, completed_at = ?, updated_at = ?
            WHERE id = ?
        """, (status.value, actual_hours, completed_at, now, task_id))

        self.conn.commit()
        return self.cursor.rowcount > 0

    def list_tasks(
        self,
        shot_id: Optional[int] = None,
        department: Optional[Department] = None,
        status: Optional[TaskStatus] = None,
        assignee: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if shot_id:
            query += " AND shot_id = ?"
            params.append(shot_id)

        if department:
            query += " AND department = ?"
            params.append(department.value)

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if assignee:
            query += " AND assignee = ?"
            params.append(assignee)

        query += " ORDER BY priority DESC, due_date"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # Review management
    def create_review(
        self,
        department: Department,
        reviewer: str,
        shot_id: Optional[int] = None,
        task_id: Optional[int] = None,
        comments: str = "",
        version: int = 1
    ) -> int:
        """Create a review."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO reviews (
                shot_id, task_id, department, reviewer, comments,
                version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (shot_id, task_id, department.value, reviewer, comments, version, now, now))

        self.conn.commit()
        return self.cursor.lastrowid

    def update_review_status(
        self,
        review_id: int,
        status: str,  # pending, approved, revision_requested
        comments: Optional[str] = None
    ) -> bool:
        """Update review status."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            UPDATE reviews
            SET status = ?, comments = COALESCE(?, comments),
                review_date = ?, updated_at = ?
            WHERE id = ?
        """, (status, comments, now, now, review_id))

        self.conn.commit()
        return self.cursor.rowcount > 0

    def list_reviews(
        self,
        shot_id: Optional[int] = None,
        task_id: Optional[int] = None,
        department: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List reviews with optional filters."""
        query = "SELECT * FROM reviews WHERE 1=1"
        params = []

        if shot_id is not None:
            query += " AND shot_id = ?"
            params.append(shot_id)

        if task_id is not None:
            query += " AND task_id = ?"
            params.append(task_id)

        if department is not None:
            query += " AND department = ?"
            params.append(department)

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        self.cursor.execute(query, params)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    # Deliverables management
    def create_deliverable(
        self,
        project_id: int,
        category: str,
        name: str,
        description: str = "",
        format: str = "",
        resolution: str = "",
        codec: str = "",
        due_date: Optional[str] = None
    ) -> int:
        """Create a deliverable."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO deliverables (
                project_id, category, name, description, format,
                resolution, codec, due_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, category, name, description, format, resolution, codec, due_date, now, now))

        self.conn.commit()
        return self.cursor.lastrowid

    def update_deliverable_status(
        self,
        deliverable_id: int,
        status: str,
        file_path: Optional[str] = None
    ) -> bool:
        """Update deliverable status."""
        now = datetime.now().isoformat()
        completed = now if status == "completed" else None

        self.cursor.execute("""
            UPDATE deliverables
            SET status = ?, file_path = COALESCE(?, file_path),
                completed_date = ?, updated_at = ?
            WHERE id = ?
        """, (status, file_path, completed, now, deliverable_id))

        self.conn.commit()
        return self.cursor.rowcount > 0

    def list_deliverables(
        self,
        project_id: int,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List deliverables."""
        query = "SELECT * FROM deliverables WHERE project_id = ?"
        params = [project_id]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY category, name"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # Team management
    def add_team_member(
        self,
        name: str,
        role: str,
        department: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        is_vendor: bool = False
    ) -> int:
        """Add team member or vendor."""
        now = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO team_members (
                name, role, department, email, phone, company, is_vendor,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, role, department, email, phone, company, 1 if is_vendor else 0, now, now))

        self.conn.commit()
        return self.cursor.lastrowid

    def list_team_members(
        self,
        department: Optional[str] = None,
        is_vendor: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """List team members."""
        query = "SELECT * FROM team_members WHERE 1=1"
        params = []

        if department:
            query += " AND department = ?"
            params.append(department)

        if is_vendor is not None:
            query += " AND is_vendor = ?"
            params.append(1 if is_vendor else 0)

        query += " ORDER BY name"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # Statistics and reporting
    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Get project statistics."""
        stats = {}

        # Shot counts by department status
        for dept in Department:
            status_col = f"{dept.value}_status"
            self.cursor.execute(f"""
                SELECT {status_col}, COUNT(*) as count
                FROM shots s
                JOIN sequences seq ON s.sequence_id = seq.id
                WHERE seq.project_id = ?
                GROUP BY {status_col}
            """, (project_id,))

            stats[f"{dept.value}_status"] = {
                row[status_col]: row['count']
                for row in self.cursor.fetchall()
            }

        # Task statistics
        self.cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM tasks
            WHERE project_id = ?
            GROUP BY status
        """, (project_id,))

        stats['task_status'] = {
            row['status']: row['count']
            for row in self.cursor.fetchall()
        }

        # Deliverable completion
        self.cursor.execute("""
            SELECT
                category,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM deliverables
            WHERE project_id = ?
            GROUP BY category
        """, (project_id,))

        stats['deliverables'] = [dict(row) for row in self.cursor.fetchall()]

        return stats

    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Production database connection closed")
