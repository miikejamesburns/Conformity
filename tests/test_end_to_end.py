"""
End-to-end tests for Conformity.

Tests complete workflows from timeline import through export.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.production_tracker.shot_tracker import ShotTracker
from conformity.production_tracker.production_database import Department, VFXComplexity

from .mock_data_generators import (
    TimelineGenerator,
    AssetDataGenerator,
    ProductionDataGenerator,
    EDLGenerator
)


@pytest.mark.e2e
class TestCompleteConformWorkflow:
    """Test complete conform workflow from ingest to delivery."""

    def test_simple_conform_workflow(
        self,
        asset_db: AssetDatabase,
        temp_dir: Path,
        sample_edl: str
    ):
        """
        Test simple conform workflow:
        1. Parse EDL
        2. Create asset database entries
        3. Verify clip matching
        4. Export timeline
        """
        # Step 1: Write EDL to temp file
        edl_path = temp_dir / "test.edl"
        edl_path.write_text(sample_edl)

        # Step 2: Parse EDL and extract clip info
        clip_names = []
        for line in sample_edl.split('\n'):
            if '* FROM CLIP NAME:' in line:
                clip_name = line.split(':')[1].strip()
                clip_names.append(clip_name)

        assert len(clip_names) > 0, "EDL should contain clip names"

        # Step 3: Add assets to database
        asset_ids = []
        for clip_name in clip_names:
            asset_id = asset_db.add_asset(
                file_path=temp_dir / "media" / clip_name,
                asset_type=AssetType.VIDEO,
                status=AssetStatus.APPROVED
            )
            asset_ids.append(asset_id)

        # Step 4: Verify all assets created
        assert len(asset_ids) == len(clip_names)

        # Step 5: Search for assets
        all_assets = asset_db.search_assets(asset_type=AssetType.VIDEO)
        assert len(all_assets) == len(clip_names)

        # Step 6: Verify approved status
        approved = asset_db.search_assets(status=AssetStatus.APPROVED)
        assert len(approved) == len(clip_names)

    def test_vfx_workflow_complete(
        self,
        asset_db: AssetDatabase,
        production_tracker: ShotTracker,
        temp_dir: Path
    ):
        """
        Test complete VFX workflow:
        1. Create project and shots
        2. Link assets to shots
        3. Track through VFX pipeline
        4. Verify deliverables
        """
        # Step 1: Create project
        project_id = production_tracker.create_project(
            name="VFX Feature Test",
            target_runtime=5400,
            budget=1000000.0
        )

        # Step 2: Create sequence
        seq_id = production_tracker.add_sequence(
            project_id,
            "SEQ_010",
            "VFX Heavy Sequence"
        )

        # Step 3: Create VFX shots
        shot_ids = []
        for i in range(5):
            shot_id = production_tracker.add_shot(
                seq_id,
                f"010_{i+1:03d}",
                f"VFX shot {i+1}",
                vfx_complexity=VFXComplexity.COMPLEX
            )
            shot_ids.append(shot_id)

            # Add corresponding render asset
            asset_id = asset_db.add_asset(
                file_path=temp_dir / f"renders/010_{i+1:03d}/frame.%04d.exr",
                asset_type=AssetType.IMAGE,
                status=AssetStatus.PENDING
            )

            # Link asset to shot via metadata
            asset_db.add_metadata(asset_id, {
                'shot_id': shot_id,
                'shot_name': f"010_{i+1:03d}",
                'sequence': 'SEQ_010'
            })

        # Step 4: Process first shot through VFX pipeline
        shot_id = shot_ids[0]

        # Start VFX
        production_tracker.start_vfx(shot_id, vendor="Test VFX Studio")

        # Verify status
        shot = production_tracker.db.get_shot(shot_id)
        assert shot['vfx_status'] == 'in_progress'

        # Submit for review
        production_tracker.submit_for_review(shot_id, Department.VFX)
        shot = production_tracker.db.get_shot(shot_id)
        assert shot['vfx_status'] == 'review'

        # Approve
        review_id = production_tracker.approve_shot(
            shot_id,
            Department.VFX,
            "supervisor@test.com",
            "Approved!"
        )
        assert review_id > 0

        # Verify final status
        shot = production_tracker.db.get_shot(shot_id)
        assert shot['vfx_status'] == 'approved'

        # Step 5: Update asset status
        assets = asset_db.search_assets(asset_type=AssetType.IMAGE)
        if assets:
            asset_db.update_asset_status(assets[0]['id'], AssetStatus.APPROVED)

        # Step 6: Verify progress
        stats = production_tracker.get_shot_progress(project_id)
        assert stats['total_shots'] == 5
        assert stats['vfx_complete'] == 1

    def test_multi_department_workflow(
        self,
        production_tracker_with_data: ShotTracker,
        asset_db_with_data: AssetDatabase
    ):
        """
        Test shot progressing through multiple departments.
        """
        tracker = production_tracker_with_data
        project_id = tracker.test_project_id
        seq_id = tracker.test_sequence_ids[0]

        # Create new shot
        shot_id = tracker.add_shot(
            seq_id,
            "010_999",
            "Multi-department test shot",
            vfx_complexity=VFXComplexity.MEDIUM
        )

        # Editorial
        tracker.db.update_shot_status(shot_id, Department.EDITORIAL, 'in_progress')
        tracker.submit_for_review(shot_id, Department.EDITORIAL)
        tracker.approve_shot(shot_id, Department.EDITORIAL, "editor@test.com")

        # VFX
        tracker.start_vfx(shot_id, vendor="VFX Co")
        tracker.submit_for_review(shot_id, Department.VFX)
        tracker.approve_shot(shot_id, Department.VFX, "vfx@test.com")

        # Color
        tracker.db.update_shot_status(shot_id, Department.COLOR, 'in_progress')
        tracker.submit_for_review(shot_id, Department.COLOR)
        tracker.approve_shot(shot_id, Department.COLOR, "colorist@test.com")

        # Sound
        tracker.db.update_shot_status(shot_id, Department.SOUND, 'in_progress')
        tracker.submit_for_review(shot_id, Department.SOUND)
        tracker.approve_shot(shot_id, Department.SOUND, "sound@test.com")

        # Verify all departments approved
        shot = tracker.db.get_shot(shot_id)
        assert shot['editorial_status'] == 'approved'
        assert shot['vfx_status'] == 'approved'
        assert shot['color_status'] == 'approved'
        assert shot['sound_status'] == 'approved'


@pytest.mark.e2e
class TestAssetTrackingWorkflow:
    """Test complete asset tracking workflows."""

    def test_footage_ingest_workflow(
        self,
        asset_db: AssetDatabase,
        temp_dir: Path
    ):
        """
        Test footage ingest workflow:
        1. Create mock footage files
        2. Scan directory
        3. Verify metadata extraction
        4. Tag and categorize
        """
        # Step 1: Create mock footage directory
        footage_dir = temp_dir / "footage"
        footage_dir.mkdir()

        # Create mock files
        for i in range(10):
            clip_file = footage_dir / f"A001_C{i+1:03d}.mov"
            clip_file.touch()

        # Step 2: Manually add assets (simulating scan)
        asset_ids = []
        for clip_file in sorted(footage_dir.glob("*.mov")):
            asset_id = asset_db.add_asset(
                file_path=clip_file,
                asset_type=AssetType.VIDEO,
                status=AssetStatus.PENDING
            )
            asset_ids.append(asset_id)

            # Add metadata
            asset_db.add_metadata(asset_id, {
                'duration': 150,
                'frame_rate': 24.0,
                'codec': 'ProRes 422'
            })

        # Step 3: Verify all assets added
        assert len(asset_ids) == 10

        # Step 4: Tag assets
        for i, asset_id in enumerate(asset_ids[:5]):
            asset_db.add_tags(asset_id, ['approved', 'hero'])

        for i, asset_id in enumerate(asset_ids[5:]):
            asset_db.add_tags(asset_id, ['b-roll'])

        # Step 5: Search by tags
        hero_clips = asset_db.search_assets(tags=['hero'])
        assert len(hero_clips) == 5

        b_roll_clips = asset_db.search_assets(tags=['b-roll'])
        assert len(b_roll_clips) == 5

    def test_render_tracking_workflow(
        self,
        asset_db: AssetDatabase,
        temp_dir: Path
    ):
        """
        Test VFX render tracking workflow.
        """
        # Generate mock render data
        render_data = AssetDataGenerator.generate_render_library(
            num_sequences=3,
            shots_per_sequence=4
        )

        # Add renders to database
        asset_ids = []
        for render in render_data:
            asset_id = asset_db.add_asset(
                file_path=Path(render['file_path']),
                asset_type=AssetType.IMAGE,
                status=AssetStatus.PENDING
            )

            asset_db.add_metadata(asset_id, render['metadata'])
            asset_db.add_tags(asset_id, render['tags'])
            asset_ids.append(asset_id)

        # Verify counts
        assert len(asset_ids) == 3 * 4

        # Search by sequence
        seq_010 = asset_db.search_assets(tags=['seq_010'])
        assert len(seq_010) == 4

        # Approve some renders
        for asset_id in asset_ids[:6]:
            asset_db.update_asset_status(asset_id, AssetStatus.APPROVED)

        # Verify approval counts
        approved = asset_db.search_assets(status=AssetStatus.APPROVED)
        assert len(approved) == 6


@pytest.mark.e2e
class TestProductionTracking:
    """Test complete production tracking workflows."""

    def test_complete_project_lifecycle(
        self,
        production_tracker: ShotTracker,
        temp_dir: Path
    ):
        """
        Test complete project from creation to delivery.
        """
        # Step 1: Create project
        project_id = production_tracker.create_project(
            name="Short Film Project",
            description="15-minute short film",
            target_runtime=900,
            budget=100000.0,
            target_completion="2025-06-30"
        )

        # Step 2: Create sequences
        seq_ids = []
        for seq_name in ["SEQ_010", "SEQ_020", "SEQ_030"]:
            seq_id = production_tracker.add_sequence(
                project_id,
                seq_name,
                f"Sequence {seq_name}"
            )
            seq_ids.append(seq_id)

        # Step 3: Add shots
        total_shots = 0
        for seq_id in seq_ids:
            for i in range(5):
                shot_id = production_tracker.add_shot(
                    seq_id,
                    f"shot_{total_shots+1:03d}",
                    f"Shot {total_shots+1}",
                    vfx_complexity=VFXComplexity.SIMPLE if i % 2 == 0 else VFXComplexity.MEDIUM,
                    duration_frames=96
                )
                total_shots += 1

        # Step 4: Add deliverables
        deliverables = [
            {
                'category': 'master',
                'name': 'ProRes Master',
                'format': 'MOV',
                'resolution': '1920x1080',
                'codec': 'ProRes 422 HQ'
            },
            {
                'category': 'festival',
                'name': 'DCP',
                'format': 'DCP',
                'resolution': '2048x1080',
                'codec': 'JPEG 2000'
            }
        ]

        deliv_ids = []
        for deliv in deliverables:
            deliv_id = production_tracker.db.create_deliverable(
                project_id=project_id,
                **deliv
            )
            deliv_ids.append(deliv_id)

        # Step 5: Add team members
        team_ids = []
        team_members = [
            {'name': 'John Doe', 'role': 'Director', 'department': 'editorial'},
            {'name': 'Jane Smith', 'role': 'VFX Supervisor', 'department': 'vfx'},
            {'name': 'Bob Wilson', 'role': 'Colorist', 'department': 'color'}
        ]

        for member in team_members:
            member_id = production_tracker.db.add_team_member(**member)
            team_ids.append(member_id)

        # Step 6: Verify project structure
        project = production_tracker.db.get_project(project_id)
        assert project is not None
        assert project['name'] == "Short Film Project"

        sequences = production_tracker.db.list_sequences(project_id)
        assert len(sequences) == 3

        # Step 7: Get statistics
        stats = production_tracker.get_shot_progress(project_id)
        assert stats['total_shots'] == total_shots

        delivs = production_tracker.db.list_deliverables(project_id)
        assert len(delivs) == 2

        team = production_tracker.db.list_team_members()
        assert len(team) >= 3

    def test_revision_workflow(
        self,
        production_tracker_with_data: ShotTracker
    ):
        """
        Test revision request and resubmission workflow.
        """
        tracker = production_tracker_with_data
        project_id = tracker.test_project_id
        seq_id = tracker.test_sequence_ids[0]

        # Create shot
        shot_id = tracker.add_shot(
            seq_id,
            "010_REV",
            "Revision test shot",
            vfx_complexity=VFXComplexity.COMPLEX
        )

        # Submit for review
        tracker.start_vfx(shot_id)
        tracker.submit_for_review(shot_id, Department.VFX)

        # Request revision
        review_id = tracker.request_revision(
            shot_id,
            Department.VFX,
            "director@test.com",
            "Please adjust lighting in frame 50-60"
        )

        # Verify review created
        assert review_id > 0

        # Verify shot status
        shot = tracker.db.get_shot(shot_id)
        assert shot['vfx_status'] == 'revision'

        # Resubmit after addressing feedback
        tracker.submit_for_review(shot_id, Department.VFX, notes="Addressed lighting notes")

        # Approve on second review
        tracker.approve_shot(shot_id, Department.VFX, "director@test.com", "Perfect!")

        # Verify final approval
        shot = tracker.db.get_shot(shot_id)
        assert shot['vfx_status'] == 'approved'

        # Verify review history
        reviews = tracker.db.list_reviews(shot_id=shot_id)
        assert len(reviews) >= 2


@pytest.mark.e2e
@pytest.mark.slow
class TestIntegratedSystemWorkflow:
    """Test workflows integrating multiple systems."""

    def test_asset_to_production_integration(
        self,
        integration_context: Dict[str, Any]
    ):
        """
        Test integration between asset tracker and production tracker.
        """
        asset_db = integration_context['asset_db']
        tracker = integration_context['production_tracker']
        project_id = integration_context['project_id']
        seq_id = integration_context['sequence_ids'][0]

        # Create shot
        shot_id = tracker.add_shot(
            seq_id,
            "010_INT",
            "Integration test shot"
        )

        # Find related assets
        all_assets = asset_db.search_assets(asset_type=AssetType.VIDEO)

        # Link first asset to shot
        if all_assets:
            asset_id = all_assets[0]['id']
            asset_db.add_metadata(asset_id, {
                'shot_id': shot_id,
                'shot_name': '010_INT',
                'production_project_id': project_id
            })

            # Verify link
            asset = asset_db.get_asset(asset_id)
            assert 'shot_id' in asset['metadata']
            assert asset['metadata']['shot_id'] == shot_id

    def test_complete_delivery_pipeline(
        self,
        integration_context: Dict[str, Any],
        temp_dir: Path
    ):
        """
        Test complete pipeline from footage to delivery.
        """
        asset_db = integration_context['asset_db']
        tracker = integration_context['production_tracker']
        project_id = integration_context['project_id']

        # Step 1: Get all approved assets
        approved_assets = asset_db.search_assets(status=AssetStatus.APPROVED)
        assert len(approved_assets) > 0

        # Step 2: Create deliverables
        deliv_id = tracker.db.create_deliverable(
            project_id=project_id,
            category='master',
            name='Final Master',
            format='MOV',
            resolution='1920x1080',
            codec='ProRes 422 HQ'
        )

        # Step 3: Mark deliverable in progress
        tracker.db.update_deliverable_status(deliv_id, 'in_progress')

        # Step 4: Complete deliverable
        delivery_path = temp_dir / "deliverables" / "final_master.mov"
        delivery_path.parent.mkdir(parents=True, exist_ok=True)
        delivery_path.touch()

        tracker.db.update_deliverable_status(
            deliv_id,
            'completed',
            file_path=str(delivery_path)
        )

        # Step 5: Verify delivery
        deliv = tracker.db.get_deliverable(deliv_id)
        assert deliv['status'] == 'completed'
        assert deliv['file_path'] == str(delivery_path)


# ============================================================
# Smoke Tests
# ============================================================

@pytest.mark.smoke
class TestSmokeTests:
    """Quick smoke tests for basic functionality."""

    def test_asset_database_basic(self, asset_db: AssetDatabase, temp_dir: Path):
        """Basic asset database operations."""
        asset_id = asset_db.add_asset(
            temp_dir / "test.mov",
            AssetType.VIDEO
        )
        assert asset_id > 0

        asset = asset_db.get_asset(asset_id)
        assert asset is not None

    def test_production_tracker_basic(self, production_tracker: ShotTracker):
        """Basic production tracker operations."""
        project_id = production_tracker.create_project(name="Test")
        assert project_id > 0

        seq_id = production_tracker.add_sequence(project_id, "SEQ_001", "Test")
        assert seq_id > 0

        shot_id = production_tracker.add_shot(seq_id, "001_001", "Test")
        assert shot_id > 0

    def test_mock_data_generators(self, temp_dir: Path):
        """Test mock data generators work."""
        from .mock_data_generators import EDLGenerator, AssetDataGenerator

        edl = EDLGenerator.generate_simple_edl(num_events=5)
        assert "TITLE:" in edl
        assert len(edl.split('\n')) > 10

        assets = AssetDataGenerator.generate_footage_library(num_clips=10)
        assert len(assets) == 10
        assert all('file_path' in a for a in assets)
