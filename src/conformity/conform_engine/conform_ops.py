"""
Conform operations for matching and aligning media.

This module provides operations for conforming timelines, matching clips,
and performing editorial operations.
"""

import opentimelineio as otio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from ..core.logger import get_logger

logger = get_logger(__name__)


class ConformOperations:
    """Provides conform operations for timeline manipulation."""

    @staticmethod
    def match_clips_by_name(
        source_timeline: otio.schema.Timeline,
        media_directory: Path,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, List[Path]]:
        """
        Match timeline clips to media files by name.

        Args:
            source_timeline: Timeline to match
            media_directory: Directory containing media files
            extensions: List of file extensions to consider

        Returns:
            Dictionary mapping clip names to potential media file matches
        """
        if extensions is None:
            extensions = ['.mov', '.mp4', '.mxf', '.r3d', '.ari', '.dpx']

        logger.info(f"Matching clips from timeline to media in: {media_directory}")

        matches = {}

        # Get all clips from timeline
        clips = ConformOperations._get_all_clips(source_timeline)

        # Get all media files
        media_files = []
        for ext in extensions:
            media_files.extend(media_directory.rglob(f"*{ext}"))

        # Match clips to media
        for clip in clips:
            clip_name = clip.name
            potential_matches = []

            for media_file in media_files:
                if clip_name.lower() in media_file.stem.lower():
                    potential_matches.append(media_file)

            matches[clip_name] = potential_matches
            logger.debug(f"Clip '{clip_name}': {len(potential_matches)} matches found")

        logger.info(f"Matched {len(clips)} clips, found media for {sum(1 for m in matches.values() if m)} clips")
        return matches

    @staticmethod
    def _get_all_clips(timeline: otio.schema.Timeline) -> List[otio.schema.Clip]:
        """
        Get all clips from a timeline.

        Args:
            timeline: Timeline to extract clips from

        Returns:
            List of all clips in the timeline
        """
        clips = []
        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    clips.append(item)
        return clips

    @staticmethod
    def relink_clips(
        timeline: otio.schema.Timeline,
        media_map: Dict[str, Path]
    ) -> int:
        """
        Relink clips in a timeline to new media paths.

        Args:
            timeline: Timeline to modify
            media_map: Dictionary mapping clip names to new media paths

        Returns:
            Number of clips successfully relinked
        """
        logger.info(f"Relinking clips with {len(media_map)} mappings")

        relinked_count = 0

        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    if item.name in media_map:
                        new_path = media_map[item.name]
                        item.media_reference = otio.schema.ExternalReference(
                            target_url=str(new_path)
                        )
                        relinked_count += 1
                        logger.debug(f"Relinked '{item.name}' to {new_path}")

        logger.info(f"Successfully relinked {relinked_count} clips")
        return relinked_count

    @staticmethod
    def extract_clip_metadata(
        clip: otio.schema.Clip
    ) -> Dict[str, any]:
        """
        Extract metadata from a clip.

        Args:
            clip: Clip to extract metadata from

        Returns:
            Dictionary of metadata
        """
        metadata = {
            "name": clip.name,
            "source_range": clip.source_range,
            "available_range": clip.available_range(),
            "duration": clip.duration(),
            "metadata": clip.metadata,
        }

        if clip.media_reference:
            if isinstance(clip.media_reference, otio.schema.ExternalReference):
                metadata["media_path"] = clip.media_reference.target_url
            metadata["available_range"] = clip.media_reference.available_range

        return metadata

    @staticmethod
    def create_conform_report(
        timeline: otio.schema.Timeline,
        matched_clips: Dict[str, List[Path]]
    ) -> Dict[str, any]:
        """
        Create a conform report showing match status.

        Args:
            timeline: Timeline being conformed
            matched_clips: Dictionary of matched clips from match_clips_by_name

        Returns:
            Report dictionary with statistics and details
        """
        clips = ConformOperations._get_all_clips(timeline)

        total_clips = len(clips)
        matched = sum(1 for matches in matched_clips.values() if matches)
        unmatched = total_clips - matched
        ambiguous = sum(1 for matches in matched_clips.values() if len(matches) > 1)

        report = {
            "timeline_name": timeline.name,
            "total_clips": total_clips,
            "matched_clips": matched,
            "unmatched_clips": unmatched,
            "ambiguous_matches": ambiguous,
            "match_rate": (matched / total_clips * 100) if total_clips > 0 else 0,
            "details": {}
        }

        # Add details for each clip
        for clip_name, matches in matched_clips.items():
            status = "matched" if len(matches) == 1 else (
                "ambiguous" if len(matches) > 1 else "unmatched"
            )
            report["details"][clip_name] = {
                "status": status,
                "match_count": len(matches),
                "matches": [str(m) for m in matches]
            }

        logger.info(f"Conform report: {matched}/{total_clips} matched ({report['match_rate']:.1f}%)")
        return report
