"""
Timeline analyzer for asset tracking.

Analyzes OTIO timelines to create associations between clips
and physical media assets in the database.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import opentimelineio as otio

from .asset_database import AssetDatabase
from ..core.logger import get_logger

logger = get_logger(__name__)


class TimelineAnalyzer:
    """
    Analyze timelines and track clip-to-asset relationships.

    Creates associations between timeline clips and database assets,
    enabling media management and relinking workflows.
    """

    def __init__(self, database: AssetDatabase):
        """
        Initialize timeline analyzer.

        Args:
            database: Asset database instance
        """
        self.database = database

    def analyze_timeline(
        self,
        timeline: otio.schema.Timeline,
        timeline_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Analyze timeline and create clip-to-asset associations.

        Args:
            timeline: OTIO timeline
            timeline_path: Path to timeline file

        Returns:
            Analysis results dictionary
        """
        if timeline_path is None:
            timeline_path = Path(f"timeline_{timeline.name or 'untitled'}.otio")

        logger.info(f"Analyzing timeline: {timeline.name}")

        results = {
            'timeline_name': timeline.name,
            'timeline_path': str(timeline_path),
            'total_clips': 0,
            'linked_clips': 0,
            'missing_clips': 0,
            'associations_created': 0,
            'missing_media': []
        }

        # Analyze each track
        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    results['total_clips'] += 1

                    # Get clip media reference
                    media_ref = item.media_reference

                    if media_ref and isinstance(media_ref, otio.schema.ExternalReference):
                        # Get target URL (file path)
                        target_url = media_ref.target_url

                        if target_url:
                            # Try to find asset in database
                            asset = self._find_asset(target_url)

                            if asset:
                                # Create association
                                self._create_association(
                                    asset_id=asset['id'],
                                    timeline_path=timeline_path,
                                    clip=item,
                                    track_name=track.name
                                )
                                results['linked_clips'] += 1
                                results['associations_created'] += 1
                            else:
                                # Asset not in database
                                results['missing_clips'] += 1
                                results['missing_media'].append({
                                    'clip_name': item.name,
                                    'media_path': target_url,
                                    'track': track.name
                                })

                                logger.warning(
                                    f"Media not found in database: {target_url} "
                                    f"(clip: {item.name})"
                                )

        logger.info(
            f"Timeline analysis complete: {results['linked_clips']} linked, "
            f"{results['missing_clips']} missing"
        )

        return results

    def get_timeline_assets(
        self,
        timeline_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Get all assets used in a timeline.

        Args:
            timeline_path: Path to timeline file

        Returns:
            List of asset dictionaries with association info
        """
        try:
            cursor = self.database.conn.cursor()

            cursor.execute("""
                SELECT
                    a.*,
                    ta.clip_name,
                    ta.track_name,
                    ta.source_in,
                    ta.source_out,
                    ta.record_in,
                    ta.record_out
                FROM assets a
                JOIN timeline_associations ta ON a.id = ta.asset_id
                WHERE ta.timeline_path = ?
                ORDER BY ta.record_in
            """, (str(timeline_path),))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get timeline assets: {e}")
            return []

    def get_asset_timelines(
        self,
        asset_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all timelines that use a specific asset.

        Args:
            asset_id: Asset ID

        Returns:
            List of timeline association dictionaries
        """
        try:
            cursor = self.database.conn.cursor()

            cursor.execute("""
                SELECT * FROM timeline_associations
                WHERE asset_id = ?
                ORDER BY timeline_path, record_in
            """, (asset_id,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get asset timelines: {e}")
            return []

    def relink_timeline(
        self,
        timeline: otio.schema.Timeline,
        search_paths: Optional[List[Path]] = None
    ) -> Dict[str, Any]:
        """
        Attempt to relink missing media in timeline using database.

        Args:
            timeline: OTIO timeline
            search_paths: Additional paths to search

        Returns:
            Relink results dictionary
        """
        logger.info(f"Relinking timeline: {timeline.name}")

        results = {
            'total_clips': 0,
            'relinked': 0,
            'still_missing': 0,
            'relinked_clips': []
        }

        for track in timeline.tracks:
            for item in track:
                if isinstance(item, otio.schema.Clip):
                    results['total_clips'] += 1

                    media_ref = item.media_reference

                    if media_ref and isinstance(media_ref, otio.schema.ExternalReference):
                        original_path = media_ref.target_url

                        # Check if media exists
                        if original_path and Path(original_path).exists():
                            continue

                        # Try to find replacement
                        new_path = self._find_media_replacement(
                            clip_name=item.name,
                            original_path=original_path,
                            search_paths=search_paths
                        )

                        if new_path:
                            # Update media reference
                            media_ref.target_url = str(new_path)
                            results['relinked'] += 1
                            results['relinked_clips'].append({
                                'clip_name': item.name,
                                'original_path': original_path,
                                'new_path': str(new_path)
                            })
                            logger.info(f"Relinked {item.name}: {new_path}")
                        else:
                            results['still_missing'] += 1

        logger.info(
            f"Relink complete: {results['relinked']} relinked, "
            f"{results['still_missing']} still missing"
        )

        return results

    def generate_usage_report(
        self,
        timeline_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate asset usage report.

        Args:
            timeline_path: Optional timeline to filter by

        Returns:
            Usage report dictionary
        """
        try:
            cursor = self.database.conn.cursor()

            report = {}

            # Total associations
            if timeline_path:
                cursor.execute("""
                    SELECT COUNT(*) FROM timeline_associations
                    WHERE timeline_path = ?
                """, (str(timeline_path),))
            else:
                cursor.execute("SELECT COUNT(*) FROM timeline_associations")

            report['total_associations'] = cursor.fetchone()[0]

            # Most used assets
            if timeline_path:
                cursor.execute("""
                    SELECT a.id, a.file_name, a.file_path, COUNT(*) as usage_count
                    FROM assets a
                    JOIN timeline_associations ta ON a.id = ta.asset_id
                    WHERE ta.timeline_path = ?
                    GROUP BY a.id
                    ORDER BY usage_count DESC
                    LIMIT 10
                """, (str(timeline_path),))
            else:
                cursor.execute("""
                    SELECT a.id, a.file_name, a.file_path, COUNT(*) as usage_count
                    FROM assets a
                    JOIN timeline_associations ta ON a.id = ta.asset_id
                    GROUP BY a.id
                    ORDER BY usage_count DESC
                    LIMIT 10
                """)

            report['most_used'] = [dict(row) for row in cursor.fetchall()]

            # Unused assets
            cursor.execute("""
                SELECT COUNT(*) FROM assets a
                LEFT JOIN timeline_associations ta ON a.id = ta.asset_id
                WHERE ta.id IS NULL
            """)
            report['unused_assets'] = cursor.fetchone()[0]

            return report

        except Exception as e:
            logger.error(f"Failed to generate usage report: {e}")
            return {}

    def _find_asset(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Find asset in database by file path.

        Args:
            file_path: File path or URL

        Returns:
            Asset dictionary or None
        """
        # Try exact match first
        asset = self.database.get_asset_by_path(Path(file_path))
        if asset:
            return asset

        # Try by filename only
        file_name = Path(file_path).name

        try:
            cursor = self.database.conn.cursor()
            cursor.execute("""
                SELECT * FROM assets WHERE file_name = ?
            """, (file_name,))

            row = cursor.fetchone()
            if row:
                return dict(row)

        except Exception as e:
            logger.debug(f"Error finding asset: {e}")

        return None

    def _create_association(
        self,
        asset_id: int,
        timeline_path: Path,
        clip: otio.schema.Clip,
        track_name: Optional[str]
    ):
        """
        Create timeline-to-asset association.

        Args:
            asset_id: Asset ID
            timeline_path: Timeline file path
            clip: OTIO clip
            track_name: Track name
        """
        # Extract timing information
        source_in = None
        source_out = None
        record_in = None
        record_out = None

        if clip.source_range:
            source_in = float(clip.source_range.start_time.value) / clip.source_range.start_time.rate
            source_out = float(clip.source_range.end_time_exclusive().value) / clip.source_range.end_time_exclusive().rate

        if clip.range_in_parent():
            record_in = float(clip.range_in_parent().start_time.value) / clip.range_in_parent().start_time.rate
            record_out = float(clip.range_in_parent().end_time_exclusive().value) / clip.range_in_parent().end_time_exclusive().rate

        self.database.add_timeline_association(
            asset_id=asset_id,
            timeline_path=str(timeline_path),
            clip_name=clip.name,
            track_name=track_name,
            source_in=source_in,
            source_out=source_out,
            record_in=record_in,
            record_out=record_out
        )

    def _find_media_replacement(
        self,
        clip_name: str,
        original_path: Optional[str],
        search_paths: Optional[List[Path]]
    ) -> Optional[Path]:
        """
        Find replacement media for missing clip.

        Args:
            clip_name: Clip name
            original_path: Original file path
            search_paths: Additional search paths

        Returns:
            New file path or None
        """
        # Search by filename in database
        if original_path:
            file_name = Path(original_path).name
            asset = self._find_asset(file_name)

            if asset and Path(asset['file_path']).exists():
                return Path(asset['file_path'])

        # Search in additional paths
        if search_paths and original_path:
            file_name = Path(original_path).name

            for search_path in search_paths:
                for file_path in search_path.rglob(file_name):
                    if file_path.is_file():
                        return file_path

        return None
