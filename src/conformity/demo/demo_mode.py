"""
Demo Mode for Conformity.

Provides pre-populated demonstration environment showcasing all features.
Includes synthetic data for:
- Asset tracking
- Production tracking
- Timelines
- Color management
- All UI components
"""

from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import shutil
from datetime import datetime, timedelta
import random

from ..asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from ..production_tracker.shot_tracker import ShotTracker
from ..production_tracker.production_database import (
    Department, VFXComplexity, TaskPriority, TaskStatus, ShotStatus
)


class DemoProject:
    """
    Complete demo project with all systems initialized and populated.

    Usage:
        demo = DemoProject()
        demo.setup()

        # Access systems
        asset_db = demo.asset_db
        tracker = demo.production_tracker

        # Get demo data
        project_id = demo.project_id
        shots = demo.get_all_shots()

        # Cleanup
        demo.cleanup()
    """

    def __init__(self, persistent: bool = False, data_dir: Optional[Path] = None):
        """
        Initialize demo project.

        Args:
            persistent: If True, uses file-based databases. If False, in-memory.
            data_dir: Directory for demo data. Creates temp dir if None.
        """
        self.persistent = persistent

        if data_dir:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self._owns_data_dir = False
        else:
            self.data_dir = Path(tempfile.mkdtemp(prefix="conformity_demo_"))
            self._owns_data_dir = True

        # System instances
        self.asset_db: Optional[AssetDatabase] = None
        self.production_tracker: Optional[ShotTracker] = None

        # Demo data IDs
        self.project_id: Optional[int] = None
        self.sequence_ids: list[int] = []
        self.shot_ids: list[int] = []
        self.asset_ids: list[int] = []

        # Demo metadata
        self.demo_info: Dict[str, Any] = {}

    def setup(self) -> 'DemoProject':
        """
        Setup complete demo environment.

        Returns:
            Self for chaining
        """
        self._setup_databases()
        self._populate_asset_database()
        self._populate_production_tracker()
        self._link_assets_to_shots()
        self._create_demo_info()

        return self

    def _setup_databases(self):
        """Initialize database systems."""
        if self.persistent:
            asset_db_path = self.data_dir / "demo_assets.db"
            production_db_path = self.data_dir / "demo_production.db"
        else:
            asset_db_path = None
            production_db_path = None

        self.asset_db = AssetDatabase(asset_db_path)
        self.production_tracker = ShotTracker(production_db_path)

    def _populate_asset_database(self):
        """Populate asset database with demo data."""
        # Create demo footage
        footage_data = [
            {
                'name': 'A001_C001.mov',
                'scene': '1A',
                'take': '3',
                'camera': 'A',
                'lens': 'Zeiss Master Prime 50mm',
                'duration': 180,
                'status': AssetStatus.APPROVED
            },
            {
                'name': 'A001_C002.mov',
                'scene': '1A',
                'take': '4',
                'camera': 'B',
                'lens': 'Zeiss Master Prime 35mm',
                'duration': 165,
                'status': AssetStatus.APPROVED
            },
            {
                'name': 'A002_C001.mov',
                'scene': '2A',
                'take': '2',
                'camera': 'A',
                'lens': 'Cooke S4 25mm',
                'duration': 145,
                'status': AssetStatus.APPROVED
            },
            {
                'name': 'A002_C002.mov',
                'scene': '2B',
                'take': '1',
                'camera': 'B',
                'lens': 'Cooke S4 40mm',
                'duration': 120,
                'status': AssetStatus.NEEDS_REVIEW
            },
            {
                'name': 'A003_C001.mov',
                'scene': '3A',
                'take': '5',
                'camera': 'A',
                'lens': 'Zeiss Master Prime 85mm',
                'duration': 200,
                'status': AssetStatus.APPROVED
            }
        ]

        for footage in footage_data:
            footage_file = self.data_dir / "footage" / footage['name']
            footage_file.parent.mkdir(parents=True, exist_ok=True)
            footage_file.touch()

            asset_id = self.asset_db.add_asset(
                file_path=footage_file,
                asset_type=AssetType.VIDEO,
                status=footage['status']
            )

            self.asset_db.add_metadata(asset_id, {
                'scene': footage['scene'],
                'take': footage['take'],
                'camera': footage['camera'],
                'lens': footage['lens'],
                'duration': footage['duration'],
                'frame_rate': 24.0,
                'resolution': '3840x2160',
                'codec': 'ProRes 4444',
                'color_space': 'rec709'
            })

            # Add tags
            for tag in ['footage', f'scene_{footage["scene"]}', f'camera_{footage["camera"]}']:
                self.asset_db.add_tag(asset_id, tag)

            self.asset_ids.append(asset_id)

        # Create demo VFX renders
        render_data = [
            {'shot': '010_010', 'frames': 120, 'complexity': 'simple'},
            {'shot': '010_020', 'frames': 96, 'complexity': 'medium'},
            {'shot': '010_030', 'frames': 144, 'complexity': 'complex'},
            {'shot': '020_010', 'frames': 108, 'complexity': 'medium'},
            {'shot': '020_020', 'frames': 132, 'complexity': 'simple'}
        ]

        for render in render_data:
            render_file = self.data_dir / "renders" / render['shot'] / "frame.%04d.exr"
            render_file.parent.mkdir(parents=True, exist_ok=True)
            (render_file.parent / "frame.1001.exr").touch()

            asset_id = self.asset_db.add_asset(
                file_path=render_file,
                asset_type=AssetType.IMAGE,
                status=AssetStatus.APPROVED if render['complexity'] == 'simple' else AssetStatus.NEEDS_REVIEW
            )

            self.asset_db.add_metadata(asset_id, {
                'shot_name': render['shot'],
                'frame_range': f"1001-{1001 + render['frames']}",
                'resolution': '3840x2160',
                'color_space': 'acescg',
                'channels': 'RGBA',
                'bit_depth': '16',
                'vfx_complexity': render['complexity']
            })

            # Add tags
            for tag in ['vfx', 'render', f'shot_{render["shot"]}', render['complexity']]:
                self.asset_db.add_tag(asset_id, tag)

            self.asset_ids.append(asset_id)

    def _populate_production_tracker(self):
        """Populate production tracker with demo project."""
        # Create project
        self.project_id = self.production_tracker.create_project(
            name="Feature Film Demo Project",
            description="Demonstration project showcasing Conformity features",
            target_runtime=5400,  # 90 minutes
            budget=1500000.0,
            start_date=(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            target_completion=(datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d')
        )

        # Create sequences
        sequences = [
            {'name': 'SEQ_010', 'desc': 'Opening - Beach Scene'},
            {'name': 'SEQ_020', 'desc': 'Interior - Apartment'},
            {'name': 'SEQ_030', 'desc': 'Climax - Rooftop'}
        ]

        for seq_data in sequences:
            seq_id = self.production_tracker.add_sequence(
                self.project_id,
                seq_data['name'],
                seq_data['desc']
            )
            self.sequence_ids.append(seq_id)

        # Create shots for SEQ_010
        seq_010_shots = [
            {
                'name': '010_010',
                'desc': 'Wide establishing beach',
                'complexity': VFXComplexity.SIMPLE,
                'duration': 120,
                'vfx_status': ShotStatus.APPROVED,
                'color_status': ShotStatus.APPROVED
            },
            {
                'name': '010_020',
                'desc': 'Medium actor walking',
                'complexity': VFXComplexity.MEDIUM,
                'duration': 96,
                'vfx_status': ShotStatus.REVIEW,
                'color_status': ShotStatus.IN_PROGRESS
            },
            {
                'name': '010_030',
                'desc': 'Close-up dramatic reveal',
                'complexity': VFXComplexity.COMPLEX,
                'duration': 144,
                'vfx_status': ShotStatus.REVISION,
                'color_status': ShotStatus.NOT_STARTED
            },
            {
                'name': '010_040',
                'desc': 'Insert waves crashing',
                'complexity': VFXComplexity.SIMPLE,
                'duration': 72,
                'vfx_status': ShotStatus.APPROVED,
                'color_status': ShotStatus.APPROVED
            }
        ]

        for shot_data in seq_010_shots:
            shot_id = self.production_tracker.add_shot(
                self.sequence_ids[0],
                shot_data['name'],
                shot_data['desc'],
                vfx_complexity=shot_data['complexity'],
                duration_frames=shot_data['duration'],
                start_timecode=f"01:00:00:00"
            )
            self.shot_ids.append(shot_id)

            # Set department statuses
            self.production_tracker.db.update_shot_status(
                shot_id, Department.VFX, shot_data['vfx_status']
            )
            self.production_tracker.db.update_shot_status(
                shot_id, Department.COLOR, shot_data['color_status']
            )

        # Create shots for SEQ_020
        seq_020_shots = [
            {
                'name': '020_010',
                'desc': 'Wide apartment interior',
                'complexity': VFXComplexity.SIMPLE,
                'duration': 108
            },
            {
                'name': '020_020',
                'desc': 'Medium dialogue',
                'complexity': VFXComplexity.SIMPLE,
                'duration': 132
            }
        ]

        for shot_data in seq_020_shots:
            shot_id = self.production_tracker.add_shot(
                self.sequence_ids[1],
                shot_data['name'],
                shot_data['desc'],
                vfx_complexity=shot_data['complexity'],
                duration_frames=shot_data['duration']
            )
            self.shot_ids.append(shot_id)

        # Add tasks
        self._add_demo_tasks()

        # Add deliverables
        self._add_demo_deliverables()

        # Add team members
        self._add_demo_team()

    def _add_demo_tasks(self):
        """Add demo tasks to project."""
        tasks = [
            {
                'title': 'Wire removal - shot 010_020',
                'department': Department.VFX,
                'shot_name': '010_020',
                'priority': TaskPriority.HIGH,
                'status': TaskStatus.IN_PROGRESS,
                'estimated_hours': 16.0
            },
            {
                'title': 'CG water integration - shot 010_030',
                'department': Department.VFX,
                'shot_name': '010_030',
                'priority': TaskPriority.CRITICAL,
                'status': TaskStatus.TODO,
                'estimated_hours': 40.0
            },
            {
                'title': 'Color grade sequence 010',
                'department': Department.COLOR,
                'priority': TaskPriority.MEDIUM,
                'status': TaskStatus.IN_PROGRESS,
                'estimated_hours': 24.0
            },
            {
                'title': 'ADR session - interior scenes',
                'department': Department.SOUND,
                'priority': TaskPriority.HIGH,
                'status': TaskStatus.TODO,
                'estimated_hours': 8.0
            }
        ]

        for task_data in tasks:
            # Find shot ID if shot_name specified
            shot_id = None
            if 'shot_name' in task_data:
                shots = self.production_tracker.db.list_shots()
                for shot in shots:
                    if shot['shot_name'] == task_data['shot_name']:
                        shot_id = shot['id']
                        break

            task_id = self.production_tracker.db.create_task(
                title=task_data['title'],
                department=task_data['department'],
                shot_id=shot_id,
                project_id=self.project_id if not shot_id else None,
                priority=task_data['priority'],
                estimated_hours=task_data['estimated_hours'],
                due_date=(datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d')
            )

            # Update task status
            if 'status' in task_data:
                self.production_tracker.db.update_task_status(task_id, task_data['status'])

    def _add_demo_deliverables(self):
        """Add demo deliverables."""
        deliverables = [
            {
                'category': 'master',
                'name': 'ProRes Master',
                'format': 'MOV',
                'resolution': '3840x2160',
                'codec': 'ProRes 4444',
                'status': 'in_progress'
            },
            {
                'category': 'festival',
                'name': 'Sundance DCP',
                'format': 'DCP',
                'resolution': '2048x1080',
                'codec': 'JPEG 2000',
                'status': 'not_started'
            },
            {
                'category': 'broadcast',
                'name': 'HD Broadcast Master',
                'format': 'MXF',
                'resolution': '1920x1080',
                'codec': 'DNxHD',
                'status': 'not_started'
            },
            {
                'category': 'marketing',
                'name': 'Trailer Master',
                'format': 'MOV',
                'resolution': '1920x1080',
                'codec': 'H.264',
                'status': 'completed'
            }
        ]

        for deliv_data in deliverables:
            # Extract status separately as it's not part of create_deliverable params
            status = deliv_data.pop('status', 'not_started')

            # Create the deliverable
            deliv_id = self.production_tracker.db.create_deliverable(
                project_id=self.project_id,
                due_date=(datetime.now() + timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d'),
                **deliv_data
            )

            # Update the status if it's not the default
            if status != 'not_started':
                self.production_tracker.db.update_deliverable_status(
                    deliverable_id=deliv_id,
                    status=status
                )

    def _add_demo_team(self):
        """Add demo team members."""
        team = [
            {
                'name': 'Sarah Johnson',
                'role': 'Post Production Supervisor',
                'department': 'finishing',
                'email': 'sarah.j@filmstudio.com',
                'is_vendor': False
            },
            {
                'name': 'John Smith',
                'role': 'VFX Supervisor',
                'department': 'vfx',
                'email': 'john.s@vfxstudio.com',
                'company': 'VFX Studio Inc',
                'is_vendor': True
            },
            {
                'name': 'Emily Chen',
                'role': 'Colorist',
                'department': 'color',
                'email': 'emily@colorhouse.com',
                'company': 'Color House',
                'is_vendor': True
            },
            {
                'name': 'Michael Brown',
                'role': 'Sound Designer',
                'department': 'sound',
                'email': 'michael@soundlab.com',
                'company': 'Sound Lab',
                'is_vendor': True
            }
        ]

        for member_data in team:
            self.production_tracker.db.add_team_member(**member_data)

    def _link_assets_to_shots(self):
        """Link assets to their corresponding shots."""
        # Link VFX renders to shots
        all_assets = self.asset_db.search_assets(asset_type=AssetType.IMAGE)

        for asset in all_assets:
            shot_name = asset.get('metadata', {}).get('shot_name')
            if shot_name:
                # Find corresponding shot
                shots = self.production_tracker.db.list_shots()
                for shot in shots:
                    if shot['shot_name'] == shot_name:
                        # Update asset metadata with shot link
                        self.asset_db.add_metadata(asset['id'], {
                            'shot_id': shot['id'],
                            'project_id': self.project_id
                        })
                        break

    def _create_demo_info(self):
        """Create demo information summary."""
        self.demo_info = {
            'project_name': 'Feature Film Demo Project',
            'created_at': datetime.now().isoformat(),
            'data_directory': str(self.data_dir),
            'persistent': self.persistent,
            'statistics': {
                'total_shots': len(self.shot_ids),
                'total_assets': len(self.asset_ids),
                'sequences': len(self.sequence_ids),
                'video_assets': len(self.asset_db.search_assets(asset_type=AssetType.VIDEO)),
                'image_assets': len(self.asset_db.search_assets(asset_type=AssetType.IMAGE))
            }
        }

    # ============================================================
    # Query Methods
    # ============================================================

    def get_all_shots(self) -> list[Dict[str, Any]]:
        """Get all demo shots."""
        return self.production_tracker.db.list_shots()

    def get_all_assets(self) -> list[Dict[str, Any]]:
        """Get all demo assets."""
        return self.asset_db.search_assets()

    def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics."""
        return self.production_tracker.get_shot_progress(self.project_id)

    def get_shots_needing_attention(self) -> Dict[str, list]:
        """Get shots requiring attention."""
        return self.production_tracker.get_shots_needing_attention(self.project_id)

    def print_summary(self):
        """Print demo project summary."""
        print("=" * 60)
        print("CONFORMITY DEMO PROJECT")
        print("=" * 60)
        print(f"\nProject: {self.demo_info['project_name']}")
        print(f"Created: {self.demo_info['created_at']}")
        print(f"Data Directory: {self.demo_info['data_directory']}")
        print(f"\nStatistics:")
        for key, value in self.demo_info['statistics'].items():
            print(f"  {key}: {value}")

        print(f"\nProduction Progress:")
        stats = self.get_project_stats()
        for dept in Department:
            complete = stats.get(f'{dept.value}_complete', 0)
            total = stats.get('total_shots', 0)
            percent = (complete / total * 100) if total > 0 else 0
            print(f"  {dept.value.upper()}: {complete}/{total} ({percent:.1f}%)")

        print(f"\nAssets:")
        print(f"  Total: {len(self.get_all_assets())}")
        approved = self.asset_db.search_assets(status=AssetStatus.APPROVED)
        print(f"  Approved: {len(approved)}")

        print("\n" + "=" * 60)

    # ============================================================
    # Cleanup
    # ============================================================

    def cleanup(self):
        """Cleanup demo resources."""
        if self.asset_db:
            self.asset_db.close()

        if self.production_tracker:
            self.production_tracker.close()

        if self._owns_data_dir and self.data_dir.exists():
            shutil.rmtree(self.data_dir)


def run_demo():
    """
    Run interactive demo mode.

    Creates demo project and provides interactive exploration.
    """
    print("\n" + "=" * 60)
    print("CONFORMITY DEMO MODE")
    print("=" * 60)
    print("\nInitializing demo project...")

    demo = DemoProject()
    demo.setup()

    demo.print_summary()

    print("\n\nDemo project ready!")
    print("\nAvailable systems:")
    print("  - demo.asset_db: Asset database")
    print("  - demo.production_tracker: Production tracker")
    print("  - demo.project_id: Demo project ID")
    print("\nExample usage:")
    print("  >>> shots = demo.get_all_shots()")
    print("  >>> assets = demo.get_all_assets()")
    print("  >>> stats = demo.get_project_stats()")
    print("\nTo cleanup:")
    print("  >>> demo.cleanup()")

    return demo


if __name__ == '__main__':
    # Run demo when executed directly
    demo = run_demo()
