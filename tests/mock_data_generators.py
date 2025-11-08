"""
Mock data generators for testing.

Provides generators for:
- Sample timelines with various structures
- Asset databases with different scenarios
- OCIO configurations
- Project structures
- Synthetic media metadata
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

try:
    import opentimelineio as otio
    HAS_OTIO = True
except ImportError:
    HAS_OTIO = False


class TimelineGenerator:
    """Generate sample OTIO timelines for testing."""

    @staticmethod
    def generate_simple_timeline(
        num_clips: int = 5,
        frame_rate: float = 24.0,
        clip_duration: int = 120
    ) -> 'otio.schema.Timeline':
        """
        Generate simple timeline with sequential clips.

        Args:
            num_clips: Number of clips to create
            frame_rate: Timeline frame rate
            clip_duration: Duration of each clip in frames

        Returns:
            OTIO Timeline object
        """
        if not HAS_OTIO:
            raise ImportError("opentimelineio required for timeline generation")

        timeline = otio.schema.Timeline(name=f"Test Timeline {num_clips} Clips")
        track = otio.schema.Track(name="Video 1", kind=otio.schema.TrackKind.Video)
        timeline.tracks.append(track)

        for i in range(num_clips):
            clip = otio.schema.Clip(
                name=f"clip_{i+1:03d}",
                source_range=otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(0, frame_rate),
                    duration=otio.opentime.RationalTime(clip_duration, frame_rate)
                ),
                media_reference=otio.schema.ExternalReference(
                    target_url=f"/media/footage/clip_{i+1:03d}.mov"
                )
            )

            # Add metadata
            clip.metadata = {
                'conformity': {
                    'scene': f"{i+1}A",
                    'take': str(random.randint(1, 5)),
                    'camera': random.choice(['A', 'B', 'C']),
                    'color_space': 'rec709',
                    'clip_index': i
                }
            }

            track.append(clip)

        return timeline

    @staticmethod
    def generate_complex_timeline(
        num_tracks: int = 3,
        clips_per_track: int = 10,
        include_transitions: bool = True,
        include_effects: bool = True
    ) -> 'otio.schema.Timeline':
        """
        Generate complex timeline with multiple tracks, transitions, and effects.

        Args:
            num_tracks: Number of video tracks
            clips_per_track: Clips per track
            include_transitions: Add transitions between clips
            include_effects: Add effects to clips

        Returns:
            OTIO Timeline object
        """
        if not HAS_OTIO:
            raise ImportError("opentimelineio required for timeline generation")

        timeline = otio.schema.Timeline(name="Complex Test Timeline")

        for track_num in range(num_tracks):
            track = otio.schema.Track(
                name=f"Video {track_num + 1}",
                kind=otio.schema.TrackKind.Video
            )

            for clip_num in range(clips_per_track):
                # Create clip
                clip = otio.schema.Clip(
                    name=f"V{track_num+1}_clip_{clip_num+1:03d}",
                    source_range=otio.opentime.TimeRange(
                        start_time=otio.opentime.RationalTime(0, 24.0),
                        duration=otio.opentime.RationalTime(
                            random.randint(48, 240), 24.0
                        )
                    ),
                    media_reference=otio.schema.ExternalReference(
                        target_url=f"/media/footage/V{track_num+1}_clip_{clip_num+1:03d}.mov"
                    )
                )

                # Add metadata
                clip.metadata = {
                    'conformity': {
                        'scene': f"{clip_num+1}{chr(65+track_num)}",
                        'take': str(random.randint(1, 8)),
                        'color_space': random.choice(['rec709', 'srgb', 'acescg']),
                        'status': random.choice(['approved', 'pending', 'rejected'])
                    }
                }

                # Add effects if requested
                if include_effects and random.random() > 0.5:
                    clip.effects.append(
                        otio.schema.Effect(
                            effect_name=random.choice(['Color Correction', 'Blur', 'Sharpen']),
                            metadata={'intensity': random.random()}
                        )
                    )

                track.append(clip)

                # Add transition if requested and not last clip
                if include_transitions and clip_num < clips_per_track - 1 and random.random() > 0.6:
                    transition = otio.schema.Transition(
                        transition_type=otio.schema.TransitionTypes.SMPTE_Dissolve,
                        in_offset=otio.opentime.RationalTime(12, 24.0),
                        out_offset=otio.opentime.RationalTime(12, 24.0)
                    )
                    track.append(transition)

            timeline.tracks.append(track)

        return timeline

    @staticmethod
    def generate_vfx_timeline(
        num_shots: int = 20,
        vfx_ratio: float = 0.3
    ) -> 'otio.schema.Timeline':
        """
        Generate timeline representing VFX workflow.

        Args:
            num_shots: Total number of shots
            vfx_ratio: Proportion of shots requiring VFX (0.0-1.0)

        Returns:
            OTIO Timeline object
        """
        if not HAS_OTIO:
            raise ImportError("opentimelineio required for timeline generation")

        timeline = otio.schema.Timeline(name="VFX Pipeline Timeline")
        track = otio.schema.Track(name="Video 1", kind=otio.schema.TrackKind.Video)

        num_vfx_shots = int(num_shots * vfx_ratio)
        vfx_indices = set(random.sample(range(num_shots), num_vfx_shots))

        for i in range(num_shots):
            is_vfx = i in vfx_indices

            if is_vfx:
                # VFX plate - EXR sequence
                clip = otio.schema.Clip(
                    name=f"shot_{i+1:03d}_vfx",
                    source_range=otio.opentime.TimeRange(
                        start_time=otio.opentime.RationalTime(1001, 24.0),
                        duration=otio.opentime.RationalTime(
                            random.randint(72, 240), 24.0
                        )
                    ),
                    media_reference=otio.schema.ExternalReference(
                        target_url=f"/renders/shot_{i+1:03d}/frame.%04d.exr"
                    )
                )

                clip.metadata = {
                    'conformity': {
                        'shot_name': f"010_{i+1:03d}",
                        'vfx': True,
                        'vfx_vendor': random.choice(['VFX Studio A', 'VFX Studio B', 'In-house']),
                        'vfx_complexity': random.choice(['simple', 'medium', 'complex']),
                        'color_space': 'acescg',
                        'status': random.choice(['approved', 'review', 'revision'])
                    }
                }
            else:
                # Regular footage
                clip = otio.schema.Clip(
                    name=f"shot_{i+1:03d}",
                    source_range=otio.opentime.TimeRange(
                        start_time=otio.opentime.RationalTime(0, 24.0),
                        duration=otio.opentime.RationalTime(
                            random.randint(48, 180), 24.0
                        )
                    ),
                    media_reference=otio.schema.ExternalReference(
                        target_url=f"/media/footage/shot_{i+1:03d}.mov"
                    )
                )

                clip.metadata = {
                    'conformity': {
                        'shot_name': f"010_{i+1:03d}",
                        'vfx': False,
                        'color_space': 'rec709',
                        'status': 'approved'
                    }
                }

            track.append(clip)

        timeline.tracks.append(track)
        return timeline


class AssetDataGenerator:
    """Generate sample asset database data."""

    @staticmethod
    def generate_footage_library(
        num_clips: int = 50,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate sample footage library data.

        Args:
            num_clips: Number of clips to generate
            include_metadata: Include technical metadata

        Returns:
            List of asset dictionaries
        """
        assets = []

        for i in range(num_clips):
            asset = {
                'file_path': f"/media/footage/A{(i//10)+1:03d}_C{(i%10)+1:03d}.mov",
                'asset_type': 'video',
                'status': random.choice(['approved', 'approved', 'pending', 'rejected']),
                'tags': [
                    'footage',
                    f'roll_{(i//10)+1}',
                    random.choice(['wide', 'medium', 'closeup'])
                ]
            }

            if include_metadata:
                asset['metadata'] = {
                    'duration': random.randint(100, 500),
                    'frame_rate': 24.0,
                    'resolution': random.choice(['1920x1080', '3840x2160', '4096x2160']),
                    'codec': random.choice(['ProRes 422', 'ProRes 4444', 'DNxHD']),
                    'color_space': random.choice(['rec709', 'srgb']),
                    'camera': random.choice(['ARRI Alexa', 'RED Dragon', 'Sony Venice']),
                    'lens': random.choice(['Zeiss Master Prime', 'Cooke S4', 'Canon K35']),
                    'iso': random.choice([800, 1600, 3200]),
                    'scene': f"{i//5 + 1}{chr(65 + i%5)}",
                    'take': random.randint(1, 8)
                }

            assets.append(asset)

        return assets

    @staticmethod
    def generate_render_library(
        num_sequences: int = 10,
        shots_per_sequence: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate VFX render library data.

        Args:
            num_sequences: Number of sequences
            shots_per_sequence: Shots per sequence

        Returns:
            List of asset dictionaries
        """
        assets = []

        for seq_num in range(num_sequences):
            for shot_num in range(shots_per_sequence):
                asset = {
                    'file_path': f"/renders/SEQ_{(seq_num+1)*10:03d}/{(seq_num+1)*10}_{shot_num+1:03d}/frame.%04d.exr",
                    'asset_type': 'image',
                    'status': random.choice(['approved', 'approved', 'review', 'revision']),
                    'tags': [
                        'vfx',
                        'render',
                        f'seq_{(seq_num+1)*10:03d}',
                        random.choice(['comp', 'cg', 'matte_painting'])
                    ],
                    'metadata': {
                        'frame_range': f"1001-{1001 + random.randint(72, 240)}",
                        'resolution': random.choice(['3840x2160', '4096x2160']),
                        'color_space': 'acescg',
                        'channels': 'RGBA',
                        'bit_depth': '16',
                        'compression': 'zip',
                        'shot_name': f"{(seq_num+1)*10:03d}_{shot_num+1:03d}",
                        'vfx_complexity': random.choice(['simple', 'medium', 'complex']),
                        'vfx_vendor': random.choice(['VFX Studio A', 'VFX Studio B', 'In-house'])
                    }
                }

                assets.append(asset)

        return assets


class ProductionDataGenerator:
    """Generate sample production tracking data."""

    @staticmethod
    def generate_film_project(
        num_sequences: int = 5,
        shots_per_sequence: int = 10
    ) -> Dict[str, Any]:
        """
        Generate complete film production project data.

        Args:
            num_sequences: Number of sequences in film
            shots_per_sequence: Average shots per sequence

        Returns:
            Complete project structure dictionary
        """
        project = {
            'name': 'Test Feature Film',
            'description': 'Generated test project for integration testing',
            'target_runtime': 5400,  # 90 minutes
            'budget': random.uniform(500000, 2000000),
            'target_completion': (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'sequences': []
        }

        for seq_num in range(1, num_sequences + 1):
            sequence = {
                'name': f'SEQ_{seq_num*10:03d}',
                'description': f'Sequence {seq_num} - {random.choice(["Opening", "Action", "Dialogue", "Montage", "Climax"])}',
                'shots': []
            }

            for shot_num in range(1, shots_per_sequence + 1):
                shot = {
                    'name': f'{seq_num*10:03d}_{shot_num:03d}',
                    'description': f'{random.choice(["Wide", "Medium", "Close-up", "Insert", "POV"])} shot',
                    'vfx_complexity': random.choice(['simple', 'simple', 'medium', 'complex']),
                    'duration_frames': random.randint(48, 240),
                    'departments': {
                        'editorial': random.choice(['approved', 'in_progress', 'not_started']),
                        'vfx': random.choice(['approved', 'review', 'in_progress', 'not_started']),
                        'color': random.choice(['approved', 'in_progress', 'not_started']),
                        'sound': random.choice(['approved', 'in_progress', 'not_started'])
                    },
                    'tasks': []
                }

                # Add VFX tasks if VFX required
                if shot['vfx_complexity'] != 'not_started':
                    num_tasks = {'simple': 1, 'medium': 2, 'complex': 4}[shot['vfx_complexity']]

                    for task_num in range(num_tasks):
                        task = {
                            'title': random.choice([
                                'Cleanup and paint',
                                'CG integration',
                                'Matte painting',
                                'Compositing',
                                'Tracking',
                                'Rotoscoping'
                            ]),
                            'department': 'vfx',
                            'priority': random.choice(['medium', 'high', 'critical']),
                            'status': random.choice(['todo', 'in_progress', 'completed']),
                            'estimated_hours': random.uniform(4, 40)
                        }
                        shot['tasks'].append(task)

                sequence['shots'].append(shot)

            project['sequences'].append(sequence)

        return project


class OCIOConfigGenerator:
    """Generate sample OCIO configurations."""

    @staticmethod
    def generate_simple_config() -> str:
        """Generate simple OCIO config with basic color spaces."""
        return """ocio_profile_version: 2

environment:
  {}

search_path: ""
strictparsing: true
luma: [0.2126, 0.7152, 0.0722]

roles:
  default: Linear
  scene_linear: Linear
  color_timing: sRGB

displays:
  sRGB:
    - !<View> {name: Standard, colorspace: sRGB}

active_displays: [sRGB]
active_views: [Standard]

colorspaces:
  - !<ColorSpace>
    name: Linear
    family: ""
    equalitygroup: ""
    bitdepth: 32f
    isdata: false
    allocation: lg2
    allocationvars: [-8, 8, 0.00390625]

  - !<ColorSpace>
    name: sRGB
    family: ""
    equalitygroup: ""
    bitdepth: 32f
    isdata: false
    allocation: uniform
    allocationvars: [0, 1]

  - !<ColorSpace>
    name: rec709
    family: ""
    equalitygroup: ""
    bitdepth: 32f
    isdata: false
    allocation: uniform
    allocationvars: [0, 1]
"""


class EDLGenerator:
    """Generate sample EDL files."""

    @staticmethod
    def generate_simple_edl(num_events: int = 10) -> str:
        """
        Generate simple CMX 3600 EDL.

        Args:
            num_events: Number of edit events

        Returns:
            EDL as string
        """
        edl = "TITLE: Generated Test EDL\n\n"

        record_tc = 0
        for i in range(num_events):
            event_num = i + 1
            duration = random.randint(48, 240)

            # Format timecode
            def frames_to_tc(frames: int) -> str:
                hours = frames // (24 * 3600)
                frames %= (24 * 3600)
                minutes = frames // (24 * 60)
                frames %= (24 * 60)
                seconds = frames // 24
                frames %= 24
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

            source_in = 0
            source_out = duration
            record_in = record_tc
            record_out = record_tc + duration

            edl += f"{event_num:03d}  AX       V     C        "
            edl += f"{frames_to_tc(source_in)} {frames_to_tc(source_out)} "
            edl += f"{frames_to_tc(record_in)} {frames_to_tc(record_out)}\n"
            edl += f"* FROM CLIP NAME: clip_{event_num:03d}.mov\n"
            edl += f"* SCENE: {event_num}A\n"
            edl += f"* TAKE: {random.randint(1, 5)}\n\n"

            record_tc += duration

        return edl


# ============================================================
# Convenience Functions
# ============================================================

def generate_complete_test_project(output_dir: Path) -> Dict[str, Path]:
    """
    Generate complete test project with all data types.

    Args:
        output_dir: Directory to create project in

    Returns:
        Dictionary of created file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {}

    # Generate timeline
    if HAS_OTIO:
        timeline = TimelineGenerator.generate_simple_timeline(num_clips=10)
        timeline_path = output_dir / "test_timeline.otio"
        otio.adapters.write_to_file(timeline, str(timeline_path))
        files['timeline'] = timeline_path

        # Generate VFX timeline
        vfx_timeline = TimelineGenerator.generate_vfx_timeline(num_shots=20)
        vfx_timeline_path = output_dir / "vfx_timeline.otio"
        otio.adapters.write_to_file(vfx_timeline, str(vfx_timeline_path))
        files['vfx_timeline'] = vfx_timeline_path

    # Generate EDL
    edl = EDLGenerator.generate_simple_edl(num_events=15)
    edl_path = output_dir / "test_timeline.edl"
    edl_path.write_text(edl)
    files['edl'] = edl_path

    # Generate OCIO config
    ocio_config = OCIOConfigGenerator.generate_simple_config()
    ocio_path = output_dir / "config.ocio"
    ocio_path.write_text(ocio_config)
    files['ocio_config'] = ocio_path

    return files
