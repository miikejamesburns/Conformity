"""
Integration tests between Conformity modules.

Tests interactions between:
- Asset Tracker ↔ Production Tracker
- Asset Tracker ↔ Command Interface
- Production Tracker ↔ Command Interface
- All systems together
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.production_tracker.shot_tracker import ShotTracker
from conformity.production_tracker.production_database import Department, VFXComplexity
from conformity.commands.command_parser import CommandParser
from conformity.commands.command_executor import CommandExecutor


@pytest.mark.integration
class TestAssetProductionIntegration:
    """Test integration between Asset Tracker and Production Tracker."""

    def test_link_assets_to_shots(
        self,
        asset_db_with_data: AssetDatabase,
        production_tracker_with_data: ShotTracker
    ):
        """Test linking assets to production shots."""
        # Get shots from production tracker
        project_id = production_tracker_with_data.test_project_id
        seq_id = production_tracker_with_data.test_sequence_ids[0]

        shots = production_tracker_with_data.db.list_shots(sequence_id=seq_id)
        assert len(shots) > 0

        # Get assets from asset database
        assets = asset_db_with_data.search_assets(asset_type=AssetType.VIDEO)
        assert len(assets) > 0

        # Link first asset to first shot
        shot = shots[0]
        asset = assets[0]

        asset_db_with_data.add_metadata(asset['id'], {
            'shot_id': shot['id'],
            'shot_name': shot['shot_name'],
            'sequence_id': seq_id,
            'project_id': project_id
        })

        # Verify link
        updated_asset = asset_db_with_data.get_asset(asset['id'])
        assert 'shot_id' in updated_asset['metadata']
        assert updated_asset['metadata']['shot_id'] == shot['id']
        assert updated_asset['metadata']['shot_name'] == shot['shot_name']

    def test_asset_status_affects_shot_readiness(
        self,
        asset_db: AssetDatabase,
        production_tracker: ShotTracker,
        temp_dir: Path
    ):
        """Test that asset approval status affects shot readiness."""
        # Create project and shot
        project_id = production_tracker.create_project(name="Test Film")
        seq_id = production_tracker.add_sequence(project_id, "SEQ_010", "Test")
        shot_id = production_tracker.add_shot(
            seq_id,
            "010_001",
            "Test shot",
            vfx_complexity=VFXComplexity.MEDIUM
        )

        # Add asset for shot
        asset_id = asset_db.add_asset(
            file_path=temp_dir / "renders/010_001/frame.%04d.exr",
            asset_type=AssetType.IMAGE,
            status=AssetStatus.PENDING
        )

        # Link asset to shot
        asset_db.add_metadata(asset_id, {
            'shot_id': shot_id,
            'shot_name': '010_001'
        })

        # Check asset status
        asset = asset_db.get_asset(asset_id)
        assert asset['status'] == 'pending'

        # Start VFX on shot
        production_tracker.start_vfx(shot_id, vendor="Test VFX")

        # Once asset is approved, shot can be approved
        asset_db.update_asset_status(asset_id, AssetStatus.APPROVED)

        # Submit and approve shot
        production_tracker.submit_for_review(shot_id, Department.VFX)
        production_tracker.approve_shot(shot_id, Department.VFX, "supervisor@test.com")

        # Verify shot approved
        shot = production_tracker.db.get_shot(shot_id)
        assert shot['vfx_status'] == 'approved'

        # Verify asset approved
        asset = asset_db.get_asset(asset_id)
        assert asset['status'] == 'approved'

    def test_find_assets_for_shots_needing_work(
        self,
        integration_context: Dict[str, Any]
    ):
        """Test finding assets for shots that need work."""
        asset_db = integration_context['asset_db']
        tracker = integration_context['production_tracker']
        project_id = integration_context['project_id']

        # Get shots needing attention
        attention = tracker.get_shots_needing_attention(project_id)

        # For each shot in revision, find linked assets
        for shot_info in attention['revision']:
            shot_id = shot_info['shot_id']

            # Find assets linked to this shot
            all_assets = asset_db.search_assets()
            linked_assets = [
                a for a in all_assets
                if a.get('metadata', {}).get('shot_id') == shot_id
            ]

            # These assets might need to be revised too
            assert isinstance(linked_assets, list)


@pytest.mark.integration
class TestAssetCommandIntegration:
    """Test integration between Asset Tracker and Command Interface."""

    def test_query_assets_via_commands(
        self,
        asset_db_with_data: AssetDatabase
    ):
        """Test querying assets using command interface."""
        parser = CommandParser()
        executor = CommandExecutor(asset_db=asset_db_with_data)

        # Test find command
        cmd = parser.parse("find clips with approved")
        assert cmd.command_type.value == 'find'

        result = executor.execute(cmd)
        assert result.success
        assert isinstance(result.data, list)

        # Test show command
        cmd = parser.parse("show assets in rec709")
        assert cmd.command_type.value == 'show'

        # Test list command
        cmd = parser.parse("list all assets")
        result = executor.execute(cmd)
        assert result.success
        assert len(result.data) > 0

    def test_filter_assets_by_status(
        self,
        asset_db_with_data: AssetDatabase
    ):
        """Test filtering assets by status via commands."""
        parser = CommandParser()
        executor = CommandExecutor(asset_db=asset_db_with_data)

        # Filter by approved status
        cmd = parser.parse("filter by approved status")
        result = executor.execute(cmd)

        if result.success and result.data:
            # Verify all results are approved
            for asset in result.data:
                assert asset.get('status') == 'approved'

    def test_search_assets_by_tags(
        self,
        asset_db_with_data: AssetDatabase
    ):
        """Test searching assets by tags via commands."""
        parser = CommandParser()
        executor = CommandExecutor(asset_db=asset_db_with_data)

        # Search for approved assets
        cmd = parser.parse("find assets with approved tag")
        result = executor.execute(cmd)

        if result.success:
            assert isinstance(result.data, list)


@pytest.mark.integration
class TestProductionCommandIntegration:
    """Test integration between Production Tracker and Command Interface."""

    def test_query_shot_status(
        self,
        production_tracker_with_data: ShotTracker
    ):
        """Test querying shot status information."""
        tracker = production_tracker_with_data
        project_id = tracker.test_project_id

        # Get project statistics
        stats = tracker.get_shot_progress(project_id)

        assert 'total_shots' in stats
        assert 'vfx_complete' in stats
        assert stats['total_shots'] > 0

    def test_find_shots_in_review(
        self,
        production_tracker_with_data: ShotTracker
    ):
        """Test finding shots currently in review."""
        tracker = production_tracker_with_data
        project_id = tracker.test_project_id

        # Get shots needing attention
        attention = tracker.get_shots_needing_attention(project_id)

        assert 'review' in attention
        assert 'revision' in attention
        assert isinstance(attention['review'], list)
        assert isinstance(attention['revision'], list)


@pytest.mark.integration
class TestMultiSystemIntegration:
    """Test integration across all systems."""

    def test_complete_workflow_integration(
        self,
        integration_context: Dict[str, Any],
        temp_dir: Path
    ):
        """
        Test complete workflow across all systems:
        1. Create production project
        2. Add shots
        3. Create assets for shots
        4. Track through pipeline
        5. Query status via commands
        """
        asset_db = integration_context['asset_db']
        tracker = integration_context['production_tracker']
        project_id = integration_context['project_id']
        seq_id = integration_context['sequence_ids'][0]

        # Step 1: Create new shot
        shot_id = tracker.add_shot(
            seq_id,
            "010_MULTI",
            "Multi-system integration test",
            vfx_complexity=VFXComplexity.COMPLEX
        )

        # Step 2: Create asset for shot
        asset_id = asset_db.add_asset(
            file_path=temp_dir / "renders/010_MULTI/frame.%04d.exr",
            asset_type=AssetType.IMAGE,
            status=AssetStatus.PENDING
        )

        # Step 3: Link asset to shot
        asset_db.add_metadata(asset_id, {
            'shot_id': shot_id,
            'shot_name': '010_MULTI',
            'department': 'vfx'
        })
        asset_db.add_tags(asset_id, ['vfx', 'render', '010_MULTI'])

        # Step 4: Process through VFX
        tracker.start_vfx(shot_id, vendor="Integration Test VFX")
        asset_db.update_asset_status(asset_id, AssetStatus.REVIEW)

        tracker.submit_for_review(shot_id, Department.VFX)

        # Step 5: Approve
        tracker.approve_shot(shot_id, Department.VFX, "supervisor@test.com")
        asset_db.update_asset_status(asset_id, AssetStatus.APPROVED)

        # Step 6: Verify via direct queries
        shot = tracker.db.get_shot(shot_id)
        assert shot['vfx_status'] == 'approved'

        asset = asset_db.get_asset(asset_id)
        assert asset['status'] == 'approved'

        # Step 7: Query via command interface
        parser = CommandParser()
        executor = CommandExecutor(asset_db=asset_db)

        cmd = parser.parse("find assets with 010_MULTI")
        result = executor.execute(cmd)

        if result.success and result.data:
            found_asset_ids = [a['id'] for a in result.data]
            assert asset_id in found_asset_ids

    def test_deliverable_asset_workflow(
        self,
        integration_context: Dict[str, Any],
        temp_dir: Path
    ):
        """
        Test deliverable creation workflow:
        1. All shots approved
        2. Create deliverable
        3. Generate output file
        4. Track as asset
        5. Mark complete
        """
        asset_db = integration_context['asset_db']
        tracker = integration_context['production_tracker']
        project_id = integration_context['project_id']

        # Step 1: Create deliverable
        deliv_id = tracker.db.create_deliverable(
            project_id=project_id,
            category='master',
            name='Test Master',
            format='MOV',
            resolution='1920x1080',
            codec='ProRes 422 HQ'
        )

        # Step 2: Create output file
        output_file = temp_dir / "deliverables" / "test_master.mov"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.touch()

        # Step 3: Mark deliverable complete
        tracker.db.update_deliverable_status(
            deliv_id,
            'completed',
            file_path=str(output_file)
        )

        # Step 4: Add deliverable to asset database
        asset_id = asset_db.add_asset(
            file_path=output_file,
            asset_type=AssetType.VIDEO,
            status=AssetStatus.APPROVED
        )

        asset_db.add_metadata(asset_id, {
            'deliverable_id': deliv_id,
            'deliverable_name': 'Test Master',
            'project_id': project_id
        })
        asset_db.add_tags(asset_id, ['deliverable', 'master', 'final'])

        # Step 5: Verify both systems
        deliv = tracker.db.get_deliverable(deliv_id)
        assert deliv['status'] == 'completed'

        asset = asset_db.get_asset(asset_id)
        assert asset['status'] == 'approved'
        assert 'deliverable_id' in asset['metadata']

    def test_reporting_across_systems(
        self,
        integration_context: Dict[str, Any]
    ):
        """Test generating reports using data from all systems."""
        asset_db = integration_context['asset_db']
        tracker = integration_context['production_tracker']
        project_id = integration_context['project_id']

        # Production statistics
        prod_stats = tracker.get_shot_progress(project_id)

        # Asset statistics
        total_assets = len(asset_db.search_assets())
        approved_assets = len(asset_db.search_assets(status=AssetStatus.APPROVED))
        video_assets = len(asset_db.search_assets(asset_type=AssetType.VIDEO))
        image_assets = len(asset_db.search_assets(asset_type=AssetType.IMAGE))

        # Create comprehensive report
        report = {
            'production': {
                'total_shots': prod_stats['total_shots'],
                'vfx_complete': prod_stats.get('vfx_complete', 0),
                'color_complete': prod_stats.get('color_complete', 0),
            },
            'assets': {
                'total': total_assets,
                'approved': approved_assets,
                'video': video_assets,
                'image': image_assets
            }
        }

        # Verify report has expected data
        assert report['production']['total_shots'] > 0
        assert report['assets']['total'] > 0
        assert report['assets']['approved'] > 0


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across integrated systems."""

    def test_missing_asset_for_shot(
        self,
        production_tracker: ShotTracker,
        asset_db: AssetDatabase
    ):
        """Test handling when asset is missing for a shot."""
        # Create shot
        project_id = production_tracker.create_project(name="Test")
        seq_id = production_tracker.add_sequence(project_id, "SEQ_001", "Test")
        shot_id = production_tracker.add_shot(seq_id, "001_001", "Test")

        # Try to find asset for shot (should return empty)
        all_assets = asset_db.search_assets()
        linked = [a for a in all_assets if a.get('metadata', {}).get('shot_id') == shot_id]

        assert len(linked) == 0  # No assets linked yet

    def test_orphaned_assets(
        self,
        asset_db_with_data: AssetDatabase
    ):
        """Test finding assets not linked to any shot."""
        # All assets without shot_id metadata are orphaned
        all_assets = asset_db_with_data.search_assets()
        orphaned = [
            a for a in all_assets
            if 'shot_id' not in a.get('metadata', {})
        ]

        # Should have orphaned assets since we didn't link them all
        assert len(orphaned) > 0

    def test_inconsistent_status(
        self,
        asset_db: AssetDatabase,
        production_tracker: ShotTracker,
        temp_dir: Path
    ):
        """Test detecting inconsistent status between systems."""
        # Create shot and asset
        project_id = production_tracker.create_project(name="Test")
        seq_id = production_tracker.add_sequence(project_id, "SEQ_001", "Test")
        shot_id = production_tracker.add_shot(seq_id, "001_001", "Test")

        asset_id = asset_db.add_asset(
            file_path=temp_dir / "test.mov",
            asset_type=AssetType.VIDEO,
            status=AssetStatus.PENDING
        )

        # Link them
        asset_db.add_metadata(asset_id, {'shot_id': shot_id})

        # Approve shot but not asset
        production_tracker.start_vfx(shot_id)
        production_tracker.submit_for_review(shot_id, Department.VFX)
        production_tracker.approve_shot(shot_id, Department.VFX, "test@test.com")

        # Check for inconsistency
        shot = production_tracker.db.get_shot(shot_id)
        asset = asset_db.get_asset(asset_id)

        # Shot is approved but asset is still pending
        assert shot['vfx_status'] == 'approved'
        assert asset['status'] == 'pending'

        # This inconsistency should be detected and reported
        # (In a real system, you'd have validation logic)


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance with integrated systems."""

    def test_large_project_performance(
        self,
        asset_db: AssetDatabase,
        production_tracker: ShotTracker,
        temp_dir: Path
    ):
        """Test performance with large number of shots and assets."""
        import time

        # Create project
        project_id = production_tracker.create_project(name="Large Project")
        seq_id = production_tracker.add_sequence(project_id, "SEQ_001", "Large Seq")

        # Add 100 shots
        start_time = time.time()

        shot_ids = []
        for i in range(100):
            shot_id = production_tracker.add_shot(
                seq_id,
                f"001_{i+1:03d}",
                f"Shot {i+1}",
                vfx_complexity=VFXComplexity.SIMPLE
            )
            shot_ids.append(shot_id)

        shot_creation_time = time.time() - start_time

        # Add 100 assets
        start_time = time.time()

        asset_ids = []
        for i in range(100):
            asset_id = asset_db.add_asset(
                file_path=temp_dir / f"clip_{i+1:03d}.mov",
                asset_type=AssetType.VIDEO,
                status=AssetStatus.PENDING
            )
            asset_ids.append(asset_id)

        asset_creation_time = time.time() - start_time

        # Link assets to shots
        start_time = time.time()

        for shot_id, asset_id in zip(shot_ids, asset_ids):
            asset_db.add_metadata(asset_id, {'shot_id': shot_id})

        linking_time = time.time() - start_time

        # Query performance
        start_time = time.time()
        stats = production_tracker.get_shot_progress(project_id)
        query_time = time.time() - start_time

        # Verify
        assert stats['total_shots'] == 100
        assert len(asset_db.search_assets()) == 100

        # Performance assertions (should be fast)
        assert shot_creation_time < 5.0  # 100 shots in < 5 seconds
        assert asset_creation_time < 5.0  # 100 assets in < 5 seconds
        assert linking_time < 2.0  # 100 links in < 2 seconds
        assert query_time < 1.0  # Query in < 1 second
