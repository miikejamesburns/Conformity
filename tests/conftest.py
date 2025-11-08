"""
Pytest configuration and shared fixtures.

Provides fixtures for:
- Temporary directories and files
- Mock databases (asset, production)
- Sample timelines and clips
- OCIO configurations
- Mock data generators
"""

import pytest
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
import shutil

# Import Conformity modules
from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus
from conformity.production_tracker.shot_tracker import ShotTracker
from conformity.production_tracker.production_database import Department, VFXComplexity


# ============================================================
# Directory and File Fixtures
# ============================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    tmp = Path(tempfile.mkdtemp(prefix="conformity_test_"))
    yield tmp
    # Cleanup
    if tmp.exists():
        shutil.rmtree(tmp)


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_timeline_path(test_data_dir: Path) -> Path:
    """Path to sample timeline XML."""
    return test_data_dir / "timelines" / "sample_timeline.xml"


@pytest.fixture
def sample_edl_path(test_data_dir: Path) -> Path:
    """Path to sample EDL file."""
    return test_data_dir / "timelines" / "sample_timeline.edl"


# ============================================================
# Database Fixtures
# ============================================================

@pytest.fixture
def asset_db() -> Generator[AssetDatabase, None, None]:
    """Create in-memory asset database."""
    db = AssetDatabase()
    yield db
    db.close()


@pytest.fixture
def asset_db_with_data(asset_db: AssetDatabase, temp_dir: Path) -> AssetDatabase:
    """Asset database populated with sample data."""
    # Add sample video assets
    for i in range(1, 6):
        asset_id = asset_db.add_asset(
            file_path=temp_dir / f"clip_{i:03d}.mov",
            asset_type=AssetType.VIDEO,
            status=AssetStatus.APPROVED if i % 2 == 0 else AssetStatus.PENDING
        )

        # Add metadata
        asset_db.add_metadata(asset_id, {
            'duration': 100 + i * 10,
            'frame_rate': 24.0,
            'resolution': '1920x1080',
            'codec': 'ProRes 422',
            'color_space': 'rec709'
        })

        # Add tags
        tags = ['footage', f'take_{i}']
        if i <= 2:
            tags.append('approved')
        asset_db.add_tags(asset_id, tags)

    # Add sample image sequences
    for i in range(1, 4):
        asset_id = asset_db.add_asset(
            file_path=temp_dir / f"render_{i:03d}" / "frame.%04d.exr",
            asset_type=AssetType.IMAGE,
            status=AssetStatus.APPROVED
        )

        asset_db.add_metadata(asset_id, {
            'frame_range': f'1001-{1001 + 100 + i * 10}',
            'resolution': '3840x2160',
            'color_space': 'acescg'
        })

        asset_db.add_tags(asset_id, ['render', 'vfx', 'approved'])

    return asset_db


@pytest.fixture
def production_tracker() -> Generator[ShotTracker, None, None]:
    """Create in-memory production tracker."""
    tracker = ShotTracker()
    yield tracker
    tracker.close()


@pytest.fixture
def production_tracker_with_data(production_tracker: ShotTracker) -> ShotTracker:
    """Production tracker populated with sample data."""
    # Create project
    project_id = production_tracker.create_project(
        name="Test Film",
        description="Test project for integration tests",
        target_runtime=5400,  # 90 minutes
        budget=500000.0,
        target_completion="2025-12-31"
    )

    # Create sequences
    seq_ids = []
    for seq_num in [10, 20, 30]:
        seq_id = production_tracker.add_sequence(
            project_id,
            f"SEQ_{seq_num:03d}",
            f"Sequence {seq_num}"
        )
        seq_ids.append(seq_id)

    # Add shots to first sequence
    for shot_num in range(1, 6):
        shot_id = production_tracker.add_shot(
            sequence_id=seq_ids[0],
            shot_name=f"010_{shot_num:03d}",
            description=f"Test shot {shot_num}",
            vfx_complexity=VFXComplexity.MEDIUM if shot_num % 2 == 0 else VFXComplexity.SIMPLE,
            start_timecode=f"01:00:{shot_num:02d}:00",
            duration_frames=120
        )

        # Progress some shots through workflow
        if shot_num <= 2:
            production_tracker.start_vfx(shot_id, vendor="Test VFX Studio")
            production_tracker.submit_for_review(shot_id, Department.VFX)
            if shot_num == 1:
                production_tracker.approve_shot(
                    shot_id, Department.VFX,
                    "supervisor@test.com",
                    "Looks good!"
                )

    # Store project_id for easy access
    production_tracker.test_project_id = project_id
    production_tracker.test_sequence_ids = seq_ids

    return production_tracker


# ============================================================
# Mock Data Fixtures
# ============================================================

@pytest.fixture
def sample_clip_data() -> list[Dict[str, Any]]:
    """Sample clip data for timeline creation."""
    return [
        {
            'name': 'clip_001',
            'source_file': '/media/footage/clip_001.mov',
            'start_tc': '01:00:00:00',
            'duration': 120,
            'metadata': {
                'scene': '1A',
                'take': '3',
                'camera': 'A',
                'color_space': 'rec709'
            }
        },
        {
            'name': 'clip_002',
            'source_file': '/media/footage/clip_002.mov',
            'start_tc': '01:00:05:00',
            'duration': 96,
            'metadata': {
                'scene': '1B',
                'take': '1',
                'camera': 'B',
                'color_space': 'rec709'
            }
        },
        {
            'name': 'vfx_plate_001',
            'source_file': '/renders/vfx_001/frame.%04d.exr',
            'start_tc': '01:00:09:00',
            'duration': 144,
            'metadata': {
                'scene': '2A',
                'shot': '010_010',
                'color_space': 'acescg',
                'vfx': True
            }
        }
    ]


@pytest.fixture
def sample_project_structure() -> Dict[str, Any]:
    """Sample project directory structure."""
    return {
        'name': 'Feature Film Project',
        'directories': {
            'footage': ['A001_C001.mov', 'A001_C002.mov', 'A002_C001.mov'],
            'renders': {
                'vfx_001': ['frame.%04d.exr'],
                'vfx_002': ['frame.%04d.exr']
            },
            'timelines': ['edit_v001.xml', 'edit_v002.xml'],
            'exports': [],
            'deliverables': []
        },
        'metadata': {
            'frame_rate': 24.0,
            'resolution': '1920x1080',
            'color_space': 'rec709',
            'project_fps': 24.0
        }
    }


# ============================================================
# OCIO Configuration Fixtures
# ============================================================

@pytest.fixture
def sample_ocio_config() -> str:
    """Sample OCIO configuration YAML."""
    return """ocio_profile_version: 2

environment:
  {}

search_path: luts
strictparsing: true
luma: [0.2126, 0.7152, 0.0722]

roles:
  color_picking: sRGB
  color_timing: ACEScct
  compositing_log: ACEScct
  data: Raw
  default: ACES - ACEScg
  matte_paint: ACEScct
  reference: Raw
  scene_linear: ACEScg
  texture_paint: sRGB

displays:
  sRGB:
    - !<View> {name: ACES, colorspace: ACES2065-1}
    - !<View> {name: sRGB, colorspace: sRGB}
    - !<View> {name: Raw, colorspace: Raw}

active_displays: [sRGB]
active_views: [ACES, sRGB, Raw]

colorspaces:
  - !<ColorSpace>
    name: ACES - ACES2065-1
    family: ACES
    equalitygroup: ""
    bitdepth: 32f
    description: ACES2065-1 AP0 primaries
    isdata: false
    allocation: lg2
    allocationvars: [-8.5, 5, 0.00390625]

  - !<ColorSpace>
    name: ACES - ACEScg
    family: ACES
    equalitygroup: ""
    bitdepth: 32f
    description: ACEScg AP1 primaries (working space)
    isdata: false
    allocation: lg2
    allocationvars: [-8.5, 5, 0.00390625]

  - !<ColorSpace>
    name: sRGB
    family: Display
    equalitygroup: ""
    bitdepth: 32f
    description: Standard sRGB
    isdata: false
    allocation: uniform
    allocationvars: [0, 1]

  - !<ColorSpace>
    name: rec709
    family: Display
    equalitygroup: ""
    bitdepth: 32f
    description: Rec.709
    isdata: false
    allocation: uniform
    allocationvars: [0, 1]

  - !<ColorSpace>
    name: Raw
    family: Raw
    equalitygroup: ""
    bitdepth: 32f
    description: Raw data
    isdata: true
    allocation: uniform
    allocationvars: [0, 1]
"""


# ============================================================
# Timeline Fixtures
# ============================================================

@pytest.fixture
def sample_timeline_xml() -> str:
    """Sample OTIO timeline as XML."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<timeline>
  <name>Sample Edit v001</name>
  <global_start_time>
    <RationalTime>0/24</RationalTime>
  </global_start_time>
  <tracks>
    <track>
      <name>Video 1</name>
      <kind>Video</kind>
      <children>
        <clip>
          <name>clip_001</name>
          <source_range>
            <TimeRange>
              <start_time><RationalTime>86400/24</RationalTime></start_time>
              <duration><RationalTime>120/24</RationalTime></duration>
            </TimeRange>
          </source_range>
          <media_reference>
            <ExternalReference>
              <target_url>/media/footage/clip_001.mov</target_url>
            </ExternalReference>
          </media_reference>
          <metadata>
            <scene>1A</scene>
            <take>3</take>
            <color_space>rec709</color_space>
          </metadata>
        </clip>
        <clip>
          <name>clip_002</name>
          <source_range>
            <TimeRange>
              <start_time><RationalTime>86520/24</RationalTime></start_time>
              <duration><RationalTime>96/24</RationalTime></duration>
            </TimeRange>
          </source_range>
          <media_reference>
            <ExternalReference>
              <target_url>/media/footage/clip_002.mov</target_url>
            </ExternalReference>
          </media_reference>
          <metadata>
            <scene>1B</scene>
            <take>1</take>
            <color_space>rec709</color_space>
          </metadata>
        </clip>
      </children>
    </track>
  </tracks>
</timeline>
"""


@pytest.fixture
def sample_edl() -> str:
    """Sample EDL (CMX 3600 format)."""
    return """TITLE: Sample Edit v001

001  AX       V     C        01:00:00:00 01:00:05:00 00:00:00:00 00:00:05:00
* FROM CLIP NAME: clip_001.mov
* SCENE: 1A
* TAKE: 3

002  AX       V     C        01:00:00:00 01:00:04:00 00:00:05:00 00:00:09:00
* FROM CLIP NAME: clip_002.mov
* SCENE: 1B
* TAKE: 1

003  AX       V     C        01:00:00:00 01:00:06:00 00:00:09:00 00:00:15:00
* FROM CLIP NAME: vfx_plate_001.exr
* SCENE: 2A
* SHOT: 010_010
* VFX: TRUE
"""


# ============================================================
# Utility Fixtures
# ============================================================

@pytest.fixture
def mock_file_creator(temp_dir: Path):
    """Factory fixture for creating mock files."""
    def create_file(relative_path: str, content: str = "") -> Path:
        """Create a file in temp directory with optional content."""
        file_path = temp_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    return create_file


@pytest.fixture
def mock_project_structure(temp_dir: Path, sample_project_structure: Dict[str, Any]) -> Path:
    """Create complete mock project directory structure."""
    project_root = temp_dir / sample_project_structure['name'].replace(' ', '_')

    def create_structure(base_path: Path, structure: Dict):
        """Recursively create directory structure."""
        for name, content in structure.items():
            path = base_path / name

            if isinstance(content, list):
                # Create directory with files
                path.mkdir(parents=True, exist_ok=True)
                for filename in content:
                    (path / filename).touch()

            elif isinstance(content, dict):
                # Nested directory
                path.mkdir(parents=True, exist_ok=True)
                create_structure(path, content)

    create_structure(project_root, sample_project_structure['directories'])

    return project_root


# ============================================================
# Integration Test Helpers
# ============================================================

@pytest.fixture
def integration_context(
    asset_db_with_data: AssetDatabase,
    production_tracker_with_data: ShotTracker,
    temp_dir: Path
) -> Dict[str, Any]:
    """
    Complete integration test context with all systems initialized.

    Returns dict with:
    - asset_db: Populated asset database
    - production_tracker: Populated production tracker
    - project_id: Test project ID
    - temp_dir: Temporary directory for test files
    """
    return {
        'asset_db': asset_db_with_data,
        'production_tracker': production_tracker_with_data,
        'project_id': production_tracker_with_data.test_project_id,
        'sequence_ids': production_tracker_with_data.test_sequence_ids,
        'temp_dir': temp_dir
    }


# ============================================================
# Markers and Hooks
# ============================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "requires_display: mark test as requiring GUI display"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to tests in integration folder
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add e2e marker to end-to-end tests
        if "e2e" in item.name or "end_to_end" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add gui marker to GUI tests
        if "gui" in item.name or "widget" in item.name:
            item.add_marker(pytest.mark.gui)
