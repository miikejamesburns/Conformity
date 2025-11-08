"""
Asset scanner for recursive directory traversal and media file discovery.

Scans directories for media files, extracts metadata, and populates
the asset database.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import time

from .asset_database import AssetDatabase, AssetType, AssetStatus
from .metadata_extractor import MetadataExtractor
from ..core.logger import get_logger

logger = get_logger(__name__)


class AssetScanner:
    """
    Scan directories for media assets and populate database.

    Provides progress tracking and callback support for UI integration.
    """

    def __init__(self, database: AssetDatabase):
        """
        Initialize asset scanner.

        Args:
            database: Asset database instance
        """
        self.database = database
        self.extractor = MetadataExtractor()

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        update_existing: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Scan directory for media files and add to database.

        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            update_existing: Re-scan existing assets
            progress_callback: Optional callback(current, total, status)

        Returns:
            Scan results dictionary
        """
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return {'error': 'Directory not found'}

        logger.info(f"Scanning directory: {directory}")
        start_time = time.time()

        # Find all media files
        media_files = self._find_media_files(directory, recursive)
        total_files = len(media_files)

        logger.info(f"Found {total_files} media files")

        results = {
            'total_found': total_files,
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_files': []
        }

        # Process each file
        for idx, file_path in enumerate(media_files, 1):
            try:
                if progress_callback:
                    progress_callback(idx, total_files, f"Processing: {file_path.name}")

                # Check if asset already exists
                existing_asset = self.database.get_asset_by_path(file_path)

                if existing_asset and not update_existing:
                    results['skipped'] += 1
                    logger.debug(f"Skipping existing asset: {file_path}")
                    continue

                # Extract metadata
                metadata = self.extractor.extract(file_path)

                if not metadata:
                    logger.warning(f"Failed to extract metadata: {file_path}")
                    results['errors'] += 1
                    results['error_files'].append(str(file_path))
                    continue

                # Determine asset type
                asset_type_str = metadata.get('asset_type') or self.extractor.get_asset_type(file_path)
                asset_type = AssetType(asset_type_str)

                if existing_asset:
                    # Update existing asset
                    asset_id = existing_asset['id']
                    self._update_asset(asset_id, file_path, metadata)
                    results['updated'] += 1
                else:
                    # Add new asset
                    asset_id = self.database.add_asset(
                        file_path=file_path,
                        asset_type=asset_type,
                        status=AssetStatus.PENDING,
                        file_size=metadata.get('file_size'),
                        checksum=metadata.get('checksum')
                    )

                    # Add metadata
                    self.database.add_metadata(asset_id, metadata)
                    results['added'] += 1

                logger.debug(f"Processed: {file_path}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results['errors'] += 1
                results['error_files'].append(str(file_path))

        elapsed_time = time.time() - start_time
        results['scan_time_seconds'] = round(elapsed_time, 2)

        logger.info(
            f"Scan complete: {results['added']} added, "
            f"{results['updated']} updated, {results['skipped']} skipped, "
            f"{results['errors']} errors in {elapsed_time:.1f}s"
        )

        return results

    def verify_assets(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Verify all assets in database are still online.

        Args:
            progress_callback: Optional callback(current, total, status)

        Returns:
            Verification results dictionary
        """
        logger.info("Verifying assets...")

        # Get all assets
        all_assets = self.database.search_assets(online_only=False)
        total = len(all_assets)

        results = {
            'total': total,
            'online': 0,
            'offline': 0,
            'changed': []
        }

        for idx, asset in enumerate(all_assets, 1):
            try:
                if progress_callback:
                    progress_callback(idx, total, f"Verifying: {asset['file_name']}")

                file_path = Path(asset['file_path'])
                is_online = file_path.exists()

                # Update status if changed
                current_status = bool(asset['is_online'])
                if is_online != current_status:
                    self.database.update_asset_online_status(asset['id'], is_online)
                    results['changed'].append({
                        'path': str(file_path),
                        'was_online': current_status,
                        'is_online': is_online
                    })

                if is_online:
                    results['online'] += 1
                else:
                    results['offline'] += 1

            except Exception as e:
                logger.error(f"Error verifying asset {asset['id']}: {e}")

        logger.info(
            f"Verification complete: {results['online']} online, "
            f"{results['offline']} offline, {len(results['changed'])} changed"
        )

        return results

    def find_missing_media(self) -> List[Dict[str, Any]]:
        """
        Find all offline assets.

        Returns:
            List of offline asset dictionaries
        """
        return self.database.search_assets(online_only=False)

    def _find_media_files(
        self,
        directory: Path,
        recursive: bool
    ) -> List[Path]:
        """
        Find all media files in directory.

        Args:
            directory: Directory to search
            recursive: Search subdirectories

        Returns:
            List of file paths
        """
        media_files = []

        try:
            if recursive:
                # Recursively find files
                for file_path in directory.rglob('*'):
                    if file_path.is_file() and self.extractor.is_media_file(file_path):
                        media_files.append(file_path)
            else:
                # Only search immediate directory
                for file_path in directory.glob('*'):
                    if file_path.is_file() and self.extractor.is_media_file(file_path):
                        media_files.append(file_path)

        except Exception as e:
            logger.error(f"Error finding media files: {e}")

        return sorted(media_files)

    def _update_asset(
        self,
        asset_id: int,
        file_path: Path,
        metadata: Dict[str, Any]
    ):
        """
        Update existing asset with new metadata.

        Args:
            asset_id: Asset ID
            file_path: File path
            metadata: New metadata
        """
        # Update file size and checksum
        cursor = self.database.conn.cursor()
        cursor.execute("""
            UPDATE assets
            SET file_size = ?,
                checksum = ?,
                last_scanned = datetime('now'),
                is_online = 1
            WHERE id = ?
        """, (
            metadata.get('file_size'),
            metadata.get('checksum'),
            asset_id
        ))

        # Update metadata (delete old, insert new)
        cursor.execute("DELETE FROM asset_metadata WHERE asset_id = ?", (asset_id,))
        self.database.add_metadata(asset_id, metadata)

        self.database.conn.commit()

    def batch_update_status(
        self,
        asset_ids: List[int],
        status: AssetStatus
    ) -> int:
        """
        Update status for multiple assets.

        Args:
            asset_ids: List of asset IDs
            status: New status

        Returns:
            Number of assets updated
        """
        count = 0
        for asset_id in asset_ids:
            if self.database.update_asset_status(asset_id, status):
                count += 1

        logger.info(f"Updated status for {count} assets to {status.value}")
        return count

    def batch_add_tags(
        self,
        asset_ids: List[int],
        tags: List[str]
    ) -> int:
        """
        Add tags to multiple assets.

        Args:
            asset_ids: List of asset IDs
            tags: Tags to add

        Returns:
            Number of tags added
        """
        count = 0
        for asset_id in asset_ids:
            for tag in tags:
                if self.database.add_tag(asset_id, tag):
                    count += 1

        logger.info(f"Added {count} tags to {len(asset_ids)} assets")
        return count

    def relocate_asset(
        self,
        asset_id: int,
        new_path: Path
    ) -> bool:
        """
        Update asset path (for relocated media).

        Args:
            asset_id: Asset ID
            new_path: New file path

        Returns:
            True if successful
        """
        if not new_path.exists():
            logger.error(f"New path does not exist: {new_path}")
            return False

        try:
            cursor = self.database.conn.cursor()
            cursor.execute("""
                UPDATE assets
                SET file_path = ?,
                    file_name = ?,
                    is_online = 1,
                    last_scanned = datetime('now')
                WHERE id = ?
            """, (str(new_path), new_path.name, asset_id))

            self.database.conn.commit()
            logger.info(f"Relocated asset {asset_id} to {new_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to relocate asset: {e}")
            return False

    def get_scan_statistics(self) -> Dict[str, Any]:
        """
        Get scanning and database statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.database.get_statistics()

        # Add extractor info
        stats['ffprobe_available'] = self.extractor.ffprobe_available

        return stats
