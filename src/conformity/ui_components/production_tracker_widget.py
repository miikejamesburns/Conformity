"""
Qt Production Tracker Widget.

Provides comprehensive GUI for production tracking including:
- Project overview dashboard
- Shot tracking table
- Department status visualization
- Task management
- Review workflow
- Progress reporting
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
        QTableWidget, QTableWidgetItem, QPushButton, QLabel,
        QComboBox, QLineEdit, QTextEdit, QGroupBox, QSplitter,
        QHeaderView, QProgressBar, QMessageBox, QDialog,
        QFormLayout, QDateEdit, QDoubleSpinBox, QSpinBox,
        QCheckBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QDate
    from PyQt6.QtGui import QColor, QBrush
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False
    # Stub classes for when PyQt6 is not available
    QWidget = object
    pyqtSignal = lambda *args: None


if HAS_PYQT6:
    from ..production_tracker.shot_tracker import ShotTracker
    from ..production_tracker.production_database import (
        ProductionDatabase, Department, ShotStatus,
        TaskPriority, TaskStatus, VFXComplexity
    )


class ProductionTrackerWidget(QWidget):
    """
    Main production tracker widget.

    Provides tabbed interface for:
    - Dashboard: Project overview and statistics
    - Shots: Shot tracking table with department statuses
    - Tasks: Task management interface
    - Deliverables: Delivery checklist
    - Team: Team and vendor directory

    Signals:
        shot_selected(int): Emitted when shot is selected
        task_updated(int): Emitted when task is updated
        status_changed(int, str, str): Emitted when shot status changes
    """

    shot_selected = pyqtSignal(int)
    task_updated = pyqtSignal(int)
    status_changed = pyqtSignal(int, str, str)

    def __init__(
        self,
        tracker: Optional['ShotTracker'] = None,
        project_id: Optional[int] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize production tracker widget.

        Args:
            tracker: ShotTracker instance (creates in-memory if None)
            project_id: Project ID to display
            parent: Parent widget
        """
        super().__init__(parent)

        self.tracker = tracker or ShotTracker()
        self.project_id = project_id
        self.current_sequence_id = None

        self._setup_ui()

        if project_id:
            self.load_project(project_id)

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()

        # Dashboard tab
        self.dashboard_widget = DashboardWidget(self.tracker)
        self.tabs.addTab(self.dashboard_widget, "Dashboard")

        # Shots tab
        self.shots_widget = ShotsWidget(self.tracker)
        self.shots_widget.shot_selected.connect(self.shot_selected.emit)
        self.shots_widget.status_changed.connect(self.status_changed.emit)
        self.tabs.addTab(self.shots_widget, "Shots")

        # Tasks tab
        self.tasks_widget = TasksWidget(self.tracker)
        self.tasks_widget.task_updated.connect(self.task_updated.emit)
        self.tabs.addTab(self.tasks_widget, "Tasks")

        # Deliverables tab
        self.deliverables_widget = DeliverablesWidget(self.tracker)
        self.tabs.addTab(self.deliverables_widget, "Deliverables")

        # Team tab
        self.team_widget = TeamWidget(self.tracker)
        self.tabs.addTab(self.team_widget, "Team")

        layout.addWidget(self.tabs)

        # Connect tab changes
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _create_header(self) -> QWidget:
        """Create header with project selector and refresh button."""
        header = QWidget()
        layout = QHBoxLayout(header)

        # Project label
        self.project_label = QLabel("No Project Selected")
        self.project_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.project_label)

        layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        return header

    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        if self.project_id:
            self.refresh()

    def load_project(self, project_id: int):
        """Load project data."""
        self.project_id = project_id

        # Update header
        project = self.tracker.db.get_project(project_id)
        if project:
            self.project_label.setText(project['name'])

        # Refresh all tabs
        self.refresh()

    def refresh(self):
        """Refresh all data."""
        if not self.project_id:
            return

        # Refresh current tab
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh(self.project_id)


class DashboardWidget(QWidget):
    """Dashboard with project overview and statistics."""

    def __init__(self, tracker: 'ShotTracker', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tracker = tracker
        self._setup_ui()

    def _setup_ui(self):
        """Setup dashboard UI."""
        layout = QVBoxLayout(self)

        # Statistics group
        stats_group = QGroupBox("Project Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.total_shots_label = QLabel("Total Shots: 0")
        stats_layout.addWidget(self.total_shots_label)

        # Department progress bars
        self.dept_progress_bars = {}
        for dept in Department:
            dept_layout = QHBoxLayout()
            dept_layout.addWidget(QLabel(f"{dept.value.upper()}:"))
            progress = QProgressBar()
            progress.setFormat("%v/%m (%p%)")
            self.dept_progress_bars[dept] = progress
            dept_layout.addWidget(progress)
            stats_layout.addLayout(dept_layout)

        layout.addWidget(stats_group)

        # Attention group
        attention_group = QGroupBox("Shots Needing Attention")
        attention_layout = QVBoxLayout(attention_group)

        self.review_label = QLabel("In Review: 0")
        attention_layout.addWidget(self.review_label)

        self.revision_label = QLabel("Need Revision: 0")
        attention_layout.addWidget(self.revision_label)

        layout.addWidget(attention_group)

        # Task overview group
        task_group = QGroupBox("Task Overview")
        task_layout = QVBoxLayout(task_group)

        self.task_labels = {}
        for status in ['todo', 'in_progress', 'completed', 'blocked']:
            label = QLabel(f"{status.replace('_', ' ').title()}: 0")
            self.task_labels[status] = label
            task_layout.addWidget(label)

        layout.addWidget(task_group)

        layout.addStretch()

    def refresh(self, project_id: int):
        """Refresh dashboard data."""
        # Get statistics
        stats = self.tracker.get_shot_progress(project_id)

        # Update total shots
        total = stats.get('total_shots', 0)
        self.total_shots_label.setText(f"Total Shots: {total}")

        # Update department progress
        for dept in Department:
            complete = stats.get(f"{dept.value}_complete", 0)
            progress_bar = self.dept_progress_bars[dept]
            progress_bar.setMaximum(total if total > 0 else 1)
            progress_bar.setValue(complete)

        # Get attention shots
        attention = self.tracker.get_shots_needing_attention(project_id)
        self.review_label.setText(f"In Review: {len(attention['review'])}")
        self.revision_label.setText(f"Need Revision: {len(attention['revision'])}")

        # Update task counts
        task_stats = stats.get('task_status', {})
        for status, label in self.task_labels.items():
            count = task_stats.get(status, 0)
            label.setText(f"{status.replace('_', ' ').title()}: {count}")


class ShotsWidget(QWidget):
    """Shot tracking table with department statuses."""

    shot_selected = pyqtSignal(int)
    status_changed = pyqtSignal(int, str, str)

    def __init__(self, tracker: 'ShotTracker', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tracker = tracker
        self.current_project_id = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup shots UI."""
        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()

        # Sequence selector
        controls.addWidget(QLabel("Sequence:"))
        self.sequence_combo = QComboBox()
        self.sequence_combo.currentIndexChanged.connect(self._on_sequence_changed)
        controls.addWidget(self.sequence_combo)

        controls.addStretch()

        # Add shot button
        add_btn = QPushButton("Add Shot")
        add_btn.clicked.connect(self._on_add_shot)
        controls.addWidget(add_btn)

        layout.addLayout(controls)

        # Shots table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Shot", "Description", "Editorial", "VFX", "Color",
            "Sound", "Finishing", "Delivery", "Complexity"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self._on_shot_double_clicked)

        layout.addWidget(self.table)

    def _on_sequence_changed(self, index: int):
        """Handle sequence selection change."""
        if index < 0:
            return

        sequence_id = self.sequence_combo.currentData()
        if sequence_id:
            self._load_shots(sequence_id)

    def _load_shots(self, sequence_id: int):
        """Load shots for sequence."""
        shots = self.tracker.db.list_shots(sequence_id=sequence_id)

        self.table.setRowCount(len(shots))

        for row, shot in enumerate(shots):
            # Shot name
            self.table.setItem(row, 0, QTableWidgetItem(shot['shot_name']))

            # Description
            self.table.setItem(row, 1, QTableWidgetItem(shot.get('description', '')))

            # Department statuses
            for col, dept in enumerate([
                'editorial_status', 'vfx_status', 'color_status',
                'sound_status', 'finishing_status', 'delivery_status'
            ], start=2):
                status = shot.get(dept, 'not_started')
                item = QTableWidgetItem(status.replace('_', ' ').title())

                # Color code by status
                if status == 'approved' or status == 'final':
                    item.setBackground(QBrush(QColor(144, 238, 144)))  # Light green
                elif status == 'in_progress':
                    item.setBackground(QBrush(QColor(255, 255, 153)))  # Light yellow
                elif status == 'review':
                    item.setBackground(QBrush(QColor(173, 216, 230)))  # Light blue
                elif status == 'revision':
                    item.setBackground(QBrush(QColor(255, 182, 193)))  # Light red

                self.table.setItem(row, col, item)

            # Complexity
            complexity = shot.get('vfx_complexity', '')
            self.table.setItem(row, 8, QTableWidgetItem(complexity.title()))

            # Store shot ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, shot['id'])

    def _on_shot_double_clicked(self, item: QTableWidgetItem):
        """Handle shot double-click."""
        row = item.row()
        shot_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if shot_id:
            self.shot_selected.emit(shot_id)
            # TODO: Open shot detail dialog

    def _on_add_shot(self):
        """Handle add shot button."""
        if not self.sequence_combo.currentData():
            QMessageBox.warning(self, "No Sequence", "Please select a sequence first.")
            return

        # TODO: Open add shot dialog
        QMessageBox.information(self, "Add Shot", "Shot creation dialog not yet implemented.")

    def refresh(self, project_id: int):
        """Refresh shots data."""
        self.current_project_id = project_id

        # Load sequences
        sequences = self.tracker.db.list_sequences(project_id)

        self.sequence_combo.clear()
        for seq in sequences:
            self.sequence_combo.addItem(seq['sequence_name'], seq['id'])

        # Load shots for first sequence
        if sequences:
            self._load_shots(sequences[0]['id'])


class TasksWidget(QWidget):
    """Task management interface."""

    task_updated = pyqtSignal(int)

    def __init__(self, tracker: 'ShotTracker', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tracker = tracker
        self.current_project_id = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup tasks UI."""
        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()

        # Department filter
        controls.addWidget(QLabel("Department:"))
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("All Departments", None)
        for dept in Department:
            self.dept_combo.addItem(dept.value.upper(), dept)
        self.dept_combo.currentIndexChanged.connect(self._on_filter_changed)
        controls.addWidget(self.dept_combo)

        # Status filter
        controls.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", None)
        for status in TaskStatus:
            self.status_combo.addItem(status.value.replace('_', ' ').title(), status)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        controls.addWidget(self.status_combo)

        controls.addStretch()

        # Add task button
        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self._on_add_task)
        controls.addWidget(add_btn)

        layout.addLayout(controls)

        # Tasks table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Title", "Department", "Priority", "Status",
            "Assignee", "Due Date", "Hours"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self._on_task_double_clicked)

        layout.addWidget(self.table)

    def _on_filter_changed(self):
        """Handle filter change."""
        if self.current_project_id:
            self._load_tasks()

    def _load_tasks(self):
        """Load tasks with current filters."""
        dept = self.dept_combo.currentData()
        status = self.status_combo.currentData()

        # Get tasks
        tasks = self.tracker.db.list_tasks(
            project_id=self.current_project_id,
            department=dept,
            status=status.value if status else None
        )

        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # Title
            self.table.setItem(row, 0, QTableWidgetItem(task['title']))

            # Department
            self.table.setItem(row, 1, QTableWidgetItem(task['department'].upper()))

            # Priority
            priority = task.get('priority', 'medium')
            item = QTableWidgetItem(priority.title())
            if priority == 'critical':
                item.setBackground(QBrush(QColor(255, 182, 193)))  # Light red
            elif priority == 'high':
                item.setBackground(QBrush(QColor(255, 255, 153)))  # Light yellow
            self.table.setItem(row, 2, item)

            # Status
            status_text = task.get('status', 'todo').replace('_', ' ').title()
            self.table.setItem(row, 3, QTableWidgetItem(status_text))

            # Assignee
            self.table.setItem(row, 4, QTableWidgetItem(task.get('assignee', '')))

            # Due date
            self.table.setItem(row, 5, QTableWidgetItem(task.get('due_date', '')))

            # Hours
            est = task.get('estimated_hours', 0)
            actual = task.get('actual_hours', 0)
            hours_text = f"{actual}/{est}" if actual else f"{est}"
            self.table.setItem(row, 6, QTableWidgetItem(hours_text))

            # Store task ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, task['id'])

    def _on_task_double_clicked(self, item: QTableWidgetItem):
        """Handle task double-click."""
        row = item.row()
        task_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if task_id:
            # TODO: Open task detail dialog
            QMessageBox.information(self, "Task Detail", f"Task detail dialog for ID {task_id} not yet implemented.")

    def _on_add_task(self):
        """Handle add task button."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        # TODO: Open add task dialog
        QMessageBox.information(self, "Add Task", "Task creation dialog not yet implemented.")

    def refresh(self, project_id: int):
        """Refresh tasks data."""
        self.current_project_id = project_id
        self._load_tasks()


class DeliverablesWidget(QWidget):
    """Deliverables checklist interface."""

    def __init__(self, tracker: 'ShotTracker', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tracker = tracker
        self.current_project_id = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup deliverables UI."""
        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()

        # Category filter
        controls.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        for category in ['master', 'festival', 'broadcast', 'marketing', 'archive']:
            self.category_combo.addItem(category.title(), category)
        self.category_combo.currentIndexChanged.connect(self._on_filter_changed)
        controls.addWidget(self.category_combo)

        controls.addStretch()

        # Add deliverable button
        add_btn = QPushButton("Add Deliverable")
        add_btn.clicked.connect(self._on_add_deliverable)
        controls.addWidget(add_btn)

        layout.addLayout(controls)

        # Deliverables table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Category", "Format", "Resolution", "Codec", "Status", "Due Date"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)

    def _on_filter_changed(self):
        """Handle filter change."""
        if self.current_project_id:
            self._load_deliverables()

    def _load_deliverables(self):
        """Load deliverables with current filters."""
        category = self.category_combo.currentData()

        deliverables = self.tracker.db.list_deliverables(
            self.current_project_id,
            category=category
        )

        self.table.setRowCount(len(deliverables))

        for row, deliv in enumerate(deliverables):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(deliv['name']))

            # Category
            self.table.setItem(row, 1, QTableWidgetItem(deliv['category'].title()))

            # Format
            self.table.setItem(row, 2, QTableWidgetItem(deliv['format']))

            # Resolution
            self.table.setItem(row, 3, QTableWidgetItem(deliv.get('resolution', '')))

            # Codec
            self.table.setItem(row, 4, QTableWidgetItem(deliv.get('codec', '')))

            # Status
            status = deliv.get('status', 'not_started')
            item = QTableWidgetItem(status.replace('_', ' ').title())

            if status == 'completed' or status == 'delivered':
                item.setBackground(QBrush(QColor(144, 238, 144)))  # Light green
            elif status == 'in_progress':
                item.setBackground(QBrush(QColor(255, 255, 153)))  # Light yellow

            self.table.setItem(row, 5, item)

            # Due date
            self.table.setItem(row, 6, QTableWidgetItem(deliv.get('due_date', '')))

            # Store deliverable ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, deliv['id'])

    def _on_add_deliverable(self):
        """Handle add deliverable button."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        # TODO: Open add deliverable dialog
        QMessageBox.information(self, "Add Deliverable", "Deliverable creation dialog not yet implemented.")

    def refresh(self, project_id: int):
        """Refresh deliverables data."""
        self.current_project_id = project_id
        self._load_deliverables()


class TeamWidget(QWidget):
    """Team and vendor directory interface."""

    def __init__(self, tracker: 'ShotTracker', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tracker = tracker
        self._setup_ui()

    def _setup_ui(self):
        """Setup team UI."""
        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()

        # Department filter
        controls.addWidget(QLabel("Department:"))
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("All Departments", None)
        for dept in Department:
            self.dept_combo.addItem(dept.value.upper(), dept.value)
        self.dept_combo.currentIndexChanged.connect(self._load_team)
        controls.addWidget(self.dept_combo)

        # Vendor filter
        self.vendor_check = QCheckBox("Vendors Only")
        self.vendor_check.stateChanged.connect(self._load_team)
        controls.addWidget(self.vendor_check)

        controls.addStretch()

        # Add member button
        add_btn = QPushButton("Add Team Member")
        add_btn.clicked.connect(self._on_add_member)
        controls.addWidget(add_btn)

        layout.addLayout(controls)

        # Team table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Role", "Department", "Email", "Company", "Vendor"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)

    def _load_team(self):
        """Load team members with current filters."""
        dept = self.dept_combo.currentData()
        is_vendor = self.vendor_check.isChecked() or None

        members = self.tracker.db.list_team_members(
            department=dept,
            is_vendor=is_vendor
        )

        self.table.setRowCount(len(members))

        for row, member in enumerate(members):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(member['name']))

            # Role
            self.table.setItem(row, 1, QTableWidgetItem(member['role']))

            # Department
            dept_text = member.get('department', '').upper()
            self.table.setItem(row, 2, QTableWidgetItem(dept_text))

            # Email
            self.table.setItem(row, 3, QTableWidgetItem(member.get('email', '')))

            # Company
            self.table.setItem(row, 4, QTableWidgetItem(member.get('company', '')))

            # Vendor
            is_vendor = "Yes" if member.get('is_vendor') else "No"
            self.table.setItem(row, 5, QTableWidgetItem(is_vendor))

            # Store member ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, member['id'])

    def _on_add_member(self):
        """Handle add member button."""
        # TODO: Open add member dialog
        QMessageBox.information(self, "Add Member", "Team member creation dialog not yet implemented.")

    def refresh(self, project_id: int):
        """Refresh team data."""
        self._load_team()


if not HAS_PYQT6:
    # Provide helpful error message if PyQt6 not available
    def ProductionTrackerWidget(*args, **kwargs):
        raise ImportError(
            "PyQt6 is required for ProductionTrackerWidget. "
            "Install with: pip install PyQt6"
        )
