"""
Asset tracking database using SQLite.

Provides persistent storage for:
- Asset metadata (paths, types, technical specs)
- Timeline associations (clip-to-file relationships)
- Version history and dependencies
- Color space information
- Status tracking and workflow management
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum

from ..core.logger import get_logger

logger = get_logger(__name__)


class AssetType(Enum):
    """Asset type enumeration."""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    SEQUENCE = "sequence"
    OTHER = "other"


class AssetStatus(Enum):
    """Asset workflow status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    ARCHIVED = "archived"


class AssetDatabase:
    """
    SQLite database manager for asset tracking.

    Provides CRUD operations for assets, timeline associations,
    and version tracking.
    """

    # Database schema version
    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (None = in-memory)
        """
        if db_path is None:
            self.db_path = ":memory:"
        else:
            self.db_path = str(db_path)
            # Ensure parent directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_schema()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _create_schema(self):
        """Create database schema if it doesn't exist."""
        try:
            cursor = self.conn.cursor()

            # Assets table - stores media file information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    file_size INTEGER,
                    checksum TEXT,
                    created_date TEXT NOT NULL,
                    modified_date TEXT NOT NULL,
                    last_scanned TEXT,
                    is_online INTEGER DEFAULT 1,
                    notes TEXT
                )
            """)

            # Technical metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    frame_rate REAL,
                    duration REAL,
                    codec TEXT,
                    pixel_format TEXT,
                    bit_depth INTEGER,
                    color_space TEXT,
                    color_primaries TEXT,
                    transfer_function TEXT,
                    audio_channels INTEGER,
                    audio_sample_rate INTEGER,
                    metadata_json TEXT,
                    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
                )
            """)

            # Timeline associations - links clips to assets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS timeline_associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    timeline_path TEXT NOT NULL,
                    clip_name TEXT NOT NULL,
                    track_name TEXT,
                    source_in REAL,
                    source_out REAL,
                    record_in REAL,
                    record_out REAL,
                    created_date TEXT NOT NULL,
                    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
                )
            """)

            # Version history - tracks asset versions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    created_by TEXT,
                    notes TEXT,
                    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
                )
            """)

            # Dependencies - tracks asset relationships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_asset_id INTEGER NOT NULL,
                    dependent_asset_id INTEGER NOT NULL,
                    dependency_type TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    FOREIGN KEY (source_asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                    FOREIGN KEY (dependent_asset_id) REFERENCES assets(id) ON DELETE CASCADE
                )
            """)

            # Tags for organizing assets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
                )
            """)

            # Create indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_path ON assets(file_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_assoc_asset ON timeline_associations(asset_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_assoc_timeline ON timeline_associations(timeline_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_colorspace ON asset_metadata(color_space)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_tag ON asset_tags(tag)")

            # Metadata table for schema version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS database_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Set schema version
            cursor.execute("""
                INSERT OR REPLACE INTO database_metadata (key, value)
                VALUES ('schema_version', ?)
            """, (str(self.SCHEMA_VERSION),))

            self.conn.commit()
            logger.info("Database schema created successfully")

        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise

    def add_asset(
        self,
        file_path: Path,
        asset_type: AssetType,
        status: AssetStatus = AssetStatus.PENDING,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Add a new asset to the database.

        Args:
            file_path: Path to asset file
            asset_type: Type of asset
            status: Workflow status
            file_size: File size in bytes
            checksum: File checksum (MD5/SHA256)
            notes: Optional notes

        Returns:
            Asset ID
        """
        try:
            cursor = self.conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO assets (
                    file_path, file_name, asset_type, status,
                    file_size, checksum, created_date, modified_date,
                    last_scanned, is_online, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(file_path),
                file_path.name,
                asset_type.value,
                status.value,
                file_size,
                checksum,
                now,
                now,
                now,
                1,  # is_online
                notes
            ))

            self.conn.commit()
            asset_id = cursor.lastrowid

            logger.info(f"Added asset: {file_path} (ID: {asset_id})")
            return asset_id

        except sqlite3.IntegrityError:
            logger.warning(f"Asset already exists: {file_path}")
            # Return existing asset ID
            return self.get_asset_by_path(file_path)['id']
        except Exception as e:
            logger.error(f"Failed to add asset: {e}")
            raise

    def add_metadata(
        self,
        asset_id: int,
        metadata: Dict[str, Any]
    ) -> int:
        """
        Add technical metadata for an asset.

        Args:
            asset_id: Asset ID
            metadata: Dictionary of metadata fields

        Returns:
            Metadata ID
        """
        try:
            cursor = self.conn.cursor()

            # Extract common fields
            width = metadata.get('width')
            height = metadata.get('height')
            frame_rate = metadata.get('frame_rate')
            duration = metadata.get('duration')
            codec = metadata.get('codec')
            pixel_format = metadata.get('pixel_format')
            bit_depth = metadata.get('bit_depth')
            color_space = metadata.get('color_space')
            color_primaries = metadata.get('color_primaries')
            transfer_function = metadata.get('transfer_function')
            audio_channels = metadata.get('audio_channels')
            audio_sample_rate = metadata.get('audio_sample_rate')

            # Store full metadata as JSON
            metadata_json = json.dumps(metadata)

            cursor.execute("""
                INSERT INTO asset_metadata (
                    asset_id, width, height, frame_rate, duration,
                    codec, pixel_format, bit_depth, color_space,
                    color_primaries, transfer_function,
                    audio_channels, audio_sample_rate, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id, width, height, frame_rate, duration,
                codec, pixel_format, bit_depth, color_space,
                color_primaries, transfer_function,
                audio_channels, audio_sample_rate, metadata_json
            ))

            self.conn.commit()
            metadata_id = cursor.lastrowid

            logger.debug(f"Added metadata for asset {asset_id}")
            return metadata_id

        except Exception as e:
            logger.error(f"Failed to add metadata: {e}")
            raise

    def add_timeline_association(
        self,
        asset_id: int,
        timeline_path: str,
        clip_name: str,
        track_name: Optional[str] = None,
        source_in: Optional[float] = None,
        source_out: Optional[float] = None,
        record_in: Optional[float] = None,
        record_out: Optional[float] = None
    ) -> int:
        """
        Associate an asset with a timeline clip.

        Args:
            asset_id: Asset ID
            timeline_path: Path to timeline file
            clip_name: Name of clip in timeline
            track_name: Track name
            source_in: Source in point (seconds)
            source_out: Source out point (seconds)
            record_in: Record in point (seconds)
            record_out: Record out point (seconds)

        Returns:
            Association ID
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO timeline_associations (
                    asset_id, timeline_path, clip_name, track_name,
                    source_in, source_out, record_in, record_out,
                    created_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id, timeline_path, clip_name, track_name,
                source_in, source_out, record_in, record_out,
                datetime.now().isoformat()
            ))

            self.conn.commit()
            assoc_id = cursor.lastrowid

            logger.debug(f"Added timeline association for asset {asset_id}")
            return assoc_id

        except Exception as e:
            logger.error(f"Failed to add timeline association: {e}")
            raise

    def get_asset_by_id(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """
        Get asset by ID.

        Args:
            asset_id: Asset ID

        Returns:
            Asset dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get asset: {e}")
            return None

    def get_asset_by_path(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get asset by file path.

        Args:
            file_path: Path to asset file

        Returns:
            Asset dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM assets WHERE file_path = ?", (str(file_path),))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get asset: {e}")
            return None

    def get_asset_metadata(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """
        Get technical metadata for an asset.

        Args:
            asset_id: Asset ID

        Returns:
            Metadata dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM asset_metadata WHERE asset_id = ?
            """, (asset_id,))
            row = cursor.fetchone()

            if row:
                metadata = dict(row)
                # Parse JSON metadata
                if metadata.get('metadata_json'):
                    metadata['full_metadata'] = json.loads(metadata['metadata_json'])
                return metadata
            return None

        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return None

    def search_assets(
        self,
        query: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        status: Optional[AssetStatus] = None,
        color_space: Optional[str] = None,
        tags: Optional[List[str]] = None,
        online_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search assets with filters.

        Args:
            query: Text search in file path and notes
            asset_type: Filter by asset type
            status: Filter by status
            color_space: Filter by color space
            tags: Filter by tags
            online_only: Only return online assets

        Returns:
            List of asset dictionaries
        """
        try:
            cursor = self.conn.cursor()

            sql = "SELECT DISTINCT a.* FROM assets a"

            # Join with metadata if filtering by color space
            if color_space:
                sql += " LEFT JOIN asset_metadata m ON a.id = m.asset_id"

            # Join with tags if filtering by tags
            if tags:
                sql += " LEFT JOIN asset_tags t ON a.id = t.asset_id"

            where_clauses = []
            params = []

            if query:
                where_clauses.append("(a.file_path LIKE ? OR a.notes LIKE ?)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term])

            if asset_type:
                where_clauses.append("a.asset_type = ?")
                params.append(asset_type.value)

            if status:
                where_clauses.append("a.status = ?")
                params.append(status.value)

            if color_space:
                where_clauses.append("m.color_space = ?")
                params.append(color_space)

            if tags:
                placeholders = ','.join('?' * len(tags))
                where_clauses.append(f"t.tag IN ({placeholders})")
                params.extend(tags)

            if online_only:
                where_clauses.append("a.is_online = 1")

            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)

            sql += " ORDER BY a.modified_date DESC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search assets: {e}")
            return []

    def update_asset_status(
        self,
        asset_id: int,
        status: AssetStatus
    ) -> bool:
        """
        Update asset status.

        Args:
            asset_id: Asset ID
            status: New status

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE assets SET status = ?, modified_date = ?
                WHERE id = ?
            """, (status.value, datetime.now().isoformat(), asset_id))

            self.conn.commit()
            logger.info(f"Updated asset {asset_id} status to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False

    def update_asset_online_status(
        self,
        asset_id: int,
        is_online: bool
    ) -> bool:
        """
        Update asset online/offline status.

        Args:
            asset_id: Asset ID
            is_online: Online status

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE assets SET is_online = ?, last_scanned = ?
                WHERE id = ?
            """, (1 if is_online else 0, datetime.now().isoformat(), asset_id))

            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to update online status: {e}")
            return False

    def add_tag(self, asset_id: int, tag: str) -> bool:
        """
        Add a tag to an asset.

        Args:
            asset_id: Asset ID
            tag: Tag name

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO asset_tags (asset_id, tag, created_date)
                VALUES (?, ?, ?)
            """, (asset_id, tag, datetime.now().isoformat()))

            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to add tag: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Statistics dictionary
        """
        try:
            cursor = self.conn.cursor()

            stats = {}

            # Total assets
            cursor.execute("SELECT COUNT(*) FROM assets")
            stats['total_assets'] = cursor.fetchone()[0]

            # Assets by type
            cursor.execute("""
                SELECT asset_type, COUNT(*) FROM assets
                GROUP BY asset_type
            """)
            stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}

            # Assets by status
            cursor.execute("""
                SELECT status, COUNT(*) FROM assets
                GROUP BY status
            """)
            stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}

            # Online/offline
            cursor.execute("""
                SELECT SUM(is_online), SUM(CASE WHEN is_online = 0 THEN 1 ELSE 0 END)
                FROM assets
            """)
            row = cursor.fetchone()
            stats['online'] = row[0] or 0
            stats['offline'] = row[1] or 0

            # Total size
            cursor.execute("SELECT SUM(file_size) FROM assets")
            total_size = cursor.fetchone()[0] or 0
            stats['total_size_bytes'] = total_size
            stats['total_size_gb'] = round(total_size / (1024**3), 2)

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
