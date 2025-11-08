"""
Shot Tracking Manager for Production Tracker.

High-level interface for managing shots, sequences, and department workflows.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from .production_database import (
    ProductionDatabase, Department, ShotStatus,
    TaskPriority, TaskStatus, VFXComplexity
)


class ShotTracker:
    """
    High-level shot tracking manager.

    Provides workflow management for shots through department pipelines.

    Example:
        ```python
        tracker = ShotTracker(Path("project.db"))

        # Create project structure
        project_id = tracker.create_project("My Film")
        seq_id = tracker.add_sequence(project_id, "SEQ_010", "Opening")

        # Add shot with details
        shot_id = tracker.add_shot(
            sequence_id=seq_id,
            shot_name="010_010",
            description="Wide establishing",
            vfx_complexity=VFXComplexity.MEDIUM
        )

        # Progress shot through VFX pipeline
        tracker.start_vfx(shot_id, vendor="VFX Studio Inc")
        tracker.submit_for_review(shot_id, Department.VFX)
        tracker.approve_shot(shot_id, Department.VFX, "john@studio.com")

        # Get progress summary
        stats = tracker.get_shot_progress(project_id)
        print(f"VFX Progress: {stats['vfx_complete']}/{stats['total_shots']}")
        ```
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize shot tracker."""
        self.db = ProductionDatabase(db_path)

    def create_project(self, name: str, **kwargs) -> int:
        """Create project."""
        return self.db.create_project(name, **kwargs)

    def add_sequence(
        self,
        project_id: int,
        sequence_name: str,
        description: str = ""
    ) -> int:
        """Add sequence to project."""
        return self.db.create_sequence(project_id, sequence_name, description)

    def add_shot(
        self,
        sequence_id: int,
        shot_name: str,
        description: str = "",
        vfx_complexity: Optional[VFXComplexity] = None,
        **kwargs
    ) -> int:
        """
        Add shot to sequence.

        Args:
            sequence_id: Parent sequence ID
            shot_name: Shot identifier (e.g., "010_010")
            description: Shot description
            vfx_complexity: VFX complexity level
            **kwargs: Additional shot properties

        Returns:
            Shot ID
        """
        shot_kwargs = kwargs.copy()
        if vfx_complexity:
            shot_kwargs['vfx_complexity'] = vfx_complexity.value

        return self.db.create_shot(
            sequence_id=sequence_id,
            shot_name=shot_name,
            description=description,
            **shot_kwargs
        )

    def start_vfx(self, shot_id: int, vendor: str = "") -> bool:
        """Start VFX work on shot."""
        shot = self.db.get_shot(shot_id)
        if not shot:
            return False

        # Update shot
        if vendor:
            self.db.cursor.execute(
                "UPDATE shots SET vfx_vendor = ? WHERE id = ?",
                (vendor, shot_id)
            )
            self.db.conn.commit()

        return self.db.update_shot_status(shot_id, Department.VFX, ShotStatus.IN_PROGRESS)

    def submit_for_review(
        self,
        shot_id: int,
        department: Department,
        notes: str = ""
    ) -> bool:
        """Submit shot for review."""
        return self.db.update_shot_status(shot_id, department, ShotStatus.REVIEW)

    def approve_shot(
        self,
        shot_id: int,
        department: Department,
        reviewer: str,
        comments: str = ""
    ) -> int:
        """Approve shot for department."""
        # Create review
        review_id = self.db.create_review(
            department=department,
            reviewer=reviewer,
            shot_id=shot_id,
            comments=comments
        )

        # Update to approved
        self.db.update_review_status(review_id, "approved")
        self.db.update_shot_status(shot_id, department, ShotStatus.APPROVED)

        return review_id

    def request_revision(
        self,
        shot_id: int,
        department: Department,
        reviewer: str,
        feedback: str
    ) -> int:
        """Request revision on shot."""
        # Create review
        review_id = self.db.create_review(
            department=department,
            reviewer=reviewer,
            shot_id=shot_id,
            comments=feedback
        )

        # Update status
        self.db.update_review_status(review_id, "revision_requested", feedback)
        self.db.update_shot_status(shot_id, department, ShotStatus.REVISION)

        return review_id

    def get_shot_progress(self, project_id: int) -> Dict[str, Any]:
        """Get shot progress statistics for project."""
        stats = self.db.get_project_stats(project_id)

        # Calculate totals
        sequences = self.db.list_sequences(project_id)
        total_shots = 0
        for seq in sequences:
            shots = self.db.list_shots(sequence_id=seq['id'])
            total_shots += len(shots)

        # Count by department
        for dept in Department:
            dept_stats = stats.get(f"{dept.value}_status", {})
            stats[f"{dept.value}_complete"] = dept_stats.get('approved', 0) + dept_stats.get('final', 0)

        stats['total_shots'] = total_shots

        return stats

    def get_shots_needing_attention(self, project_id: int) -> Dict[str, List[Dict]]:
        """Get shots requiring attention (in review, revision, blocked)."""
        sequences = self.db.list_sequences(project_id)
        needing_attention = {
            'review': [],
            'revision': [],
            'blocked': []
        }

        for seq in sequences:
            shots = self.db.list_shots(sequence_id=seq['id'])

            for shot in shots:
                # Check each department
                for dept in Department:
                    status_col = f"{dept.value}_status"
                    status = shot.get(status_col, 'not_started')

                    if status == 'review':
                        needing_attention['review'].append({
                            'shot_id': shot['id'],
                            'shot_name': shot['shot_name'],
                            'department': dept.value,
                            'sequence': seq['sequence_name']
                        })
                    elif status == 'revision':
                        needing_attention['revision'].append({
                            'shot_id': shot['id'],
                            'shot_name': shot['shot_name'],
                            'department': dept.value,
                            'sequence': seq['sequence_name']
                        })

        return needing_attention

    def close(self):
        """Close database connection."""
        self.db.close()
