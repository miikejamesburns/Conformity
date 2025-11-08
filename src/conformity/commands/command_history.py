"""
Command History and Saved Queries for Conformity.

Provides persistent storage of command history and ability to save
frequently used queries for quick access.

Features:
- Command history with timestamps
- Saved queries with names and descriptions
- Search and filter history
- Export/import saved queries
- Usage statistics
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """
    Single command history entry.

    Attributes:
        query: The query string
        timestamp: When the query was executed
        success: Whether execution succeeded
        result_count: Number of results returned
    """
    query: str
    timestamp: str
    success: bool = True
    result_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'HistoryEntry':
        return HistoryEntry(**data)


@dataclass
class SavedQuery:
    """
    Saved query with metadata.

    Attributes:
        name: User-friendly name for the query
        query: The query string
        description: Optional description
        category: Optional category for organization
        created: When the query was saved
        last_used: Last time the query was executed
        use_count: Number of times used
    """
    name: str
    query: str
    description: str = ""
    category: str = "General"
    created: str = ""
    last_used: str = ""
    use_count: int = 0

    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SavedQuery':
        return SavedQuery(**data)


class CommandHistory:
    """
    Manages command execution history.

    Stores history in JSON format for persistence across sessions.

    Example:
        ```python
        history = CommandHistory(Path("~/.conformity/history.json"))

        # Add entry
        history.add("find clips with shot_010", success=True, result_count=5)

        # Get recent
        recent = history.get_recent(10)
        for entry in recent:
            print(f"{entry.timestamp}: {entry.query}")

        # Search history
        matching = history.search("shot")
        ```
    """

    def __init__(self, history_file: Optional[Path] = None, max_entries: int = 1000):
        """
        Initialize command history.

        Args:
            history_file: Path to history JSON file
            max_entries: Maximum number of entries to keep
        """
        self.history_file = history_file
        self.max_entries = max_entries
        self.entries: List[HistoryEntry] = []

        if history_file:
            self.load()

    def add(self, query: str, success: bool = True, result_count: int = 0) -> None:
        """
        Add entry to history.

        Args:
            query: Query string
            success: Whether execution succeeded
            result_count: Number of results
        """
        entry = HistoryEntry(
            query=query,
            timestamp=datetime.now().isoformat(),
            success=success,
            result_count=result_count
        )

        self.entries.insert(0, entry)  # Most recent first

        # Trim to max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[:self.max_entries]

        # Auto-save if file is set
        if self.history_file:
            self.save()

    def get_recent(self, count: int = 10) -> List[HistoryEntry]:
        """Get most recent entries."""
        return self.entries[:count]

    def get_all(self) -> List[HistoryEntry]:
        """Get all entries."""
        return self.entries.copy()

    def search(self, query: str) -> List[HistoryEntry]:
        """
        Search history for entries matching query.

        Args:
            query: Search string

        Returns:
            Matching history entries
        """
        query_lower = query.lower()
        return [
            entry for entry in self.entries
            if query_lower in entry.query.lower()
        ]

    def get_most_common(self, count: int = 10) -> List[tuple[str, int]]:
        """
        Get most commonly used queries.

        Returns:
            List of (query, count) tuples
        """
        query_counts: Dict[str, int] = {}

        for entry in self.entries:
            query_counts[entry.query] = query_counts.get(entry.query, 0) + 1

        # Sort by count
        sorted_queries = sorted(
            query_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_queries[:count]

    def clear(self) -> None:
        """Clear all history."""
        self.entries = []
        if self.history_file:
            self.save()

    def save(self) -> None:
        """Save history to file."""
        if not self.history_file:
            return

        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'entries': [entry.to_dict() for entry in self.entries]
            }

            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.entries)} history entries")

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def load(self) -> None:
        """Load history from file."""
        if not self.history_file or not self.history_file.exists():
            return

        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)

            self.entries = [
                HistoryEntry.from_dict(entry_data)
                for entry_data in data.get('entries', [])
            ]

            logger.debug(f"Loaded {len(self.entries)} history entries")

        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self.entries = []


class SavedQueryManager:
    """
    Manages saved queries.

    Stores queries in JSON format for reuse across sessions.

    Example:
        ```python
        manager = SavedQueryManager(Path("~/.conformity/saved_queries.json"))

        # Save query
        manager.save(
            name="Missing Media Check",
            query="list missing media",
            description="Find all offline media files",
            category="QC"
        )

        # Get all saved queries
        queries = manager.get_all()

        # Get by category
        qc_queries = manager.get_by_category("QC")

        # Execute saved query
        saved_query = manager.get("Missing Media Check")
        if saved_query:
            # Mark as used
            manager.mark_used(saved_query.name)
        ```
    """

    def __init__(self, queries_file: Optional[Path] = None):
        """
        Initialize saved query manager.

        Args:
            queries_file: Path to saved queries JSON file
        """
        self.queries_file = queries_file
        self.queries: Dict[str, SavedQuery] = {}

        if queries_file:
            self.load()
        else:
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default saved queries."""
        defaults = [
            SavedQuery(
                name="Missing Media",
                query="list missing media",
                description="Find all offline or missing media files",
                category="QC"
            ),
            SavedQuery(
                name="Pending Assets",
                query="show assets with pending status",
                description="Show all assets awaiting review",
                category="Review"
            ),
            SavedQuery(
                name="ACES Assets",
                query="show assets in aces color space",
                description="Find all assets in ACES color space",
                category="Color"
            ),
            SavedQuery(
                name="ProRes Files",
                query="search for ProRes files",
                description="Find all ProRes codec files",
                category="Technical"
            ),
            SavedQuery(
                name="Approved Deliverables",
                query="filter by approved status",
                description="Show approved deliverables ready for output",
                category="Delivery"
            ),
        ]

        for query in defaults:
            self.queries[query.name] = query

    def save_query(
        self,
        name: str,
        query: str,
        description: str = "",
        category: str = "General"
    ) -> SavedQuery:
        """
        Save a new query.

        Args:
            name: Name for the query
            query: Query string
            description: Optional description
            category: Category for organization

        Returns:
            Created SavedQuery
        """
        saved_query = SavedQuery(
            name=name,
            query=query,
            description=description,
            category=category
        )

        self.queries[name] = saved_query

        if self.queries_file:
            self.save()

        logger.info(f"Saved query: {name}")
        return saved_query

    def get(self, name: str) -> Optional[SavedQuery]:
        """Get saved query by name."""
        return self.queries.get(name)

    def get_all(self) -> List[SavedQuery]:
        """Get all saved queries."""
        return list(self.queries.values())

    def get_by_category(self, category: str) -> List[SavedQuery]:
        """Get saved queries in a category."""
        return [
            query for query in self.queries.values()
            if query.category == category
        ]

    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        categories = set(query.category for query in self.queries.values())
        return sorted(categories)

    def mark_used(self, name: str) -> None:
        """Mark a query as used (updates timestamp and count)."""
        if name in self.queries:
            query = self.queries[name]
            query.last_used = datetime.now().isoformat()
            query.use_count += 1

            if self.queries_file:
                self.save()

    def delete(self, name: str) -> bool:
        """
        Delete a saved query.

        Returns:
            True if deleted, False if not found
        """
        if name in self.queries:
            del self.queries[name]

            if self.queries_file:
                self.save()

            logger.info(f"Deleted query: {name}")
            return True

        return False

    def get_most_used(self, count: int = 10) -> List[SavedQuery]:
        """Get most frequently used queries."""
        sorted_queries = sorted(
            self.queries.values(),
            key=lambda q: q.use_count,
            reverse=True
        )
        return sorted_queries[:count]

    def save(self) -> None:
        """Save queries to file."""
        if not self.queries_file:
            return

        try:
            self.queries_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'queries': [query.to_dict() for query in self.queries.values()]
            }

            with open(self.queries_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.queries)} queries")

        except Exception as e:
            logger.error(f"Failed to save queries: {e}")

    def load(self) -> None:
        """Load queries from file."""
        if not self.queries_file or not self.queries_file.exists():
            self._load_defaults()
            return

        try:
            with open(self.queries_file, 'r') as f:
                data = json.load(f)

            self.queries = {
                query_data['name']: SavedQuery.from_dict(query_data)
                for query_data in data.get('queries', [])
            }

            logger.debug(f"Loaded {len(self.queries)} saved queries")

        except Exception as e:
            logger.error(f"Failed to load queries: {e}")
            self._load_defaults()

    def export_json(self, export_path: Path) -> None:
        """Export saved queries to JSON file."""
        data = {
            'queries': [query.to_dict() for query in self.queries.values()],
            'exported': datetime.now().isoformat()
        }

        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self.queries)} queries to {export_path}")

    def import_json(self, import_path: Path, merge: bool = True) -> int:
        """
        Import saved queries from JSON file.

        Args:
            import_path: Path to JSON file
            merge: If True, merge with existing. If False, replace.

        Returns:
            Number of queries imported
        """
        with open(import_path, 'r') as f:
            data = json.load(f)

        if not merge:
            self.queries = {}

        imported_count = 0
        for query_data in data.get('queries', []):
            query = SavedQuery.from_dict(query_data)
            self.queries[query.name] = query
            imported_count += 1

        if self.queries_file:
            self.save()

        logger.info(f"Imported {imported_count} queries from {import_path}")
        return imported_count
