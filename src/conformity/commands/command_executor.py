"""
Command Executor for Conformity.

Executes parsed commands against the asset database, timeline manager,
and other Conformity systems. Separated from parsing for clean architecture
and LLM integration.

The executor is stateless and can execute commands from any source:
- Pattern-based parser
- Future LLM parser
- API calls
- Saved queries
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

from .command_parser import (
    ParsedCommand, CommandType, EntityType, FilterType
)

logger = logging.getLogger(__name__)


class ExecutionResult:
    """
    Result of command execution.

    Attributes:
        success: Whether command executed successfully
        data: Result data (list of items, counts, etc.)
        message: Human-readable message
        error: Error message if failed
        count: Number of results
    """

    def __init__(
        self,
        success: bool,
        data: Any = None,
        message: str = "",
        error: Optional[str] = None
    ):
        self.success = success
        self.data = data if data is not None else []
        self.message = message
        self.error = error
        self.count = len(data) if isinstance(data, list) else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'error': self.error,
            'count': self.count
        }

    def __str__(self) -> str:
        if not self.success:
            return f"Error: {self.error}"
        return self.message or f"Found {self.count} results"


class CommandExecutor:
    """
    Execute parsed commands against Conformity systems.

    This executor is designed to be source-agnostic - it doesn't care
    whether commands come from pattern matching, LLMs, or manual creation.

    Example:
        ```python
        from conformity.asset_tracker.asset_database import AssetDatabase
        from conformity.commands.command_parser import CommandParser
        from conformity.commands.command_executor import CommandExecutor

        # Setup
        db = AssetDatabase(Path("project.db"))
        parser = CommandParser()
        executor = CommandExecutor(asset_database=db)

        # Parse and execute
        cmd = parser.parse("find clips with shot_010")
        result = executor.execute(cmd)

        print(result.message)  # "Found 5 clips"
        for clip in result.data:
            print(f"  - {clip['name']}")
        ```
    """

    def __init__(
        self,
        asset_database=None,
        timeline_manager=None,
        color_manager=None
    ):
        """
        Initialize command executor.

        Args:
            asset_database: AssetDatabase instance for asset queries
            timeline_manager: TimelineManager for timeline queries
            color_manager: ColorManager for color space queries
        """
        self.asset_database = asset_database
        self.timeline_manager = timeline_manager
        self.color_manager = color_manager

    def execute(self, command: ParsedCommand) -> ExecutionResult:
        """
        Execute a parsed command.

        Args:
            command: ParsedCommand to execute

        Returns:
            ExecutionResult with data and status
        """
        try:
            logger.info(f"Executing: {command}")

            # Route to appropriate handler
            if command.entity_type == EntityType.ASSETS:
                return self._execute_asset_command(command)
            elif command.entity_type == EntityType.CLIPS:
                return self._execute_clip_command(command)
            elif command.entity_type == EntityType.TIMELINES:
                return self._execute_timeline_command(command)
            elif command.entity_type == EntityType.MEDIA:
                return self._execute_media_command(command)
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unsupported entity type: {command.entity_type.value}"
                )

        except Exception as e:
            logger.error(f"Execution error: {e}")
            return ExecutionResult(
                success=False,
                error=str(e)
            )

    def _execute_asset_command(self, command: ParsedCommand) -> ExecutionResult:
        """Execute commands on assets."""
        if not self.asset_database:
            return ExecutionResult(
                success=False,
                error="Asset database not available"
            )

        # Build query parameters from filters
        query_params = self._build_asset_query_params(command.filters)

        # Execute based on command type
        if command.command_type == CommandType.COUNT:
            # Count assets
            assets = self.asset_database.search_assets(**query_params)
            count = len(assets)
            return ExecutionResult(
                success=True,
                data={'count': count},
                message=f"Found {count} assets"
            )

        else:  # FIND, SHOW, LIST, SEARCH
            # Search assets
            assets = self.asset_database.search_assets(**query_params)

            # Format results
            formatted_assets = [
                {
                    'id': asset['id'],
                    'name': asset['file_name'],
                    'path': asset['file_path'],
                    'type': asset['asset_type'],
                    'status': asset['status'],
                    'color_space': asset.get('color_space', 'unknown')
                }
                for asset in assets
            ]

            message = f"Found {len(formatted_assets)} assets"
            if command.filters:
                filter_desc = self._describe_filters(command.filters)
                message += f" {filter_desc}"

            return ExecutionResult(
                success=True,
                data=formatted_assets,
                message=message
            )

    def _execute_clip_command(self, command: ParsedCommand) -> ExecutionResult:
        """Execute commands on timeline clips."""
        if not self.timeline_manager:
            return ExecutionResult(
                success=False,
                error="Timeline manager not available"
            )

        # For now, treat clips similar to assets
        # In full implementation, would query timeline data
        return ExecutionResult(
            success=True,
            data=[],
            message="Clip search not yet fully implemented"
        )

    def _execute_timeline_command(self, command: ParsedCommand) -> ExecutionResult:
        """Execute commands on timelines."""
        if not self.timeline_manager:
            return ExecutionResult(
                success=False,
                error="Timeline manager not available"
            )

        # Placeholder for timeline queries
        return ExecutionResult(
            success=True,
            data=[],
            message="Timeline search not yet fully implemented"
        )

    def _execute_media_command(self, command: ParsedCommand) -> ExecutionResult:
        """Execute commands on media files."""
        # Media commands delegate to asset commands
        return self._execute_asset_command(command)

    def _build_asset_query_params(self, filters: Dict[FilterType, Any]) -> Dict[str, Any]:
        """
        Build asset database query parameters from filters.

        Maps ParsedCommand filters to AssetDatabase.search_assets() parameters.
        """
        params = {}

        for filter_type, value in filters.items():
            if filter_type == FilterType.KEYWORD:
                params['query'] = value

            elif filter_type == FilterType.COLOR_SPACE:
                params['color_space'] = value

            elif filter_type == FilterType.STATUS:
                # Convert string to AssetStatus enum
                from ..asset_tracker.asset_database import AssetStatus
                status_map = {
                    'approved': AssetStatus.APPROVED,
                    'pending': AssetStatus.PENDING,
                    'archived': AssetStatus.ARCHIVED,
                    'in_progress': AssetStatus.IN_PROGRESS,
                    'needs_review': AssetStatus.NEEDS_REVIEW
                }
                if value in status_map:
                    params['status'] = status_map[value]

            elif filter_type == FilterType.TYPE:
                # Convert string to AssetType enum
                from ..asset_tracker.asset_database import AssetType
                type_map = {
                    'video': AssetType.VIDEO,
                    'image': AssetType.IMAGE,
                    'audio': AssetType.AUDIO
                }
                if value in type_map:
                    params['asset_type'] = type_map[value]

            elif filter_type == FilterType.TAG:
                params['tags'] = [value]

            elif filter_type == FilterType.MISSING:
                params['online_only'] = False  # Include offline media

        return params

    def _describe_filters(self, filters: Dict[FilterType, Any]) -> str:
        """Create human-readable description of filters."""
        descriptions = []

        for filter_type, value in filters.items():
            if filter_type == FilterType.KEYWORD:
                descriptions.append(f"containing '{value}'")
            elif filter_type == FilterType.COLOR_SPACE:
                descriptions.append(f"in {value} color space")
            elif filter_type == FilterType.STATUS:
                descriptions.append(f"with {value} status")
            elif filter_type == FilterType.TYPE:
                descriptions.append(f"of type {value}")
            elif filter_type == FilterType.TAG:
                descriptions.append(f"tagged '{value}'")
            elif filter_type == FilterType.MISSING:
                descriptions.append("that are missing/offline")

        return " and ".join(descriptions) if descriptions else ""


class CommandRegistry:
    """
    Registry of available commands and their capabilities.

    Used for documentation, help text, and future LLM context.
    """

    @staticmethod
    def get_command_schema() -> Dict[str, Any]:
        """
        Get JSON schema describing available commands.

        This can be provided to an LLM as context for command generation.
        """
        return {
            "commands": {
                "find": {
                    "description": "Find entities matching criteria",
                    "entities": ["clips", "assets", "timelines", "media"],
                    "filters": ["keyword", "color_space", "status", "type", "tag", "codec"]
                },
                "show": {
                    "description": "Display entities",
                    "entities": ["clips", "assets", "timelines", "media"],
                    "filters": ["keyword", "color_space", "status", "type", "tag"]
                },
                "list": {
                    "description": "List all entities of a type",
                    "entities": ["clips", "assets", "timelines", "media", "tracks", "markers"],
                    "filters": ["missing", "offline", "status"]
                },
                "count": {
                    "description": "Count entities matching criteria",
                    "entities": ["clips", "assets", "timelines", "media"],
                    "filters": ["status", "type", "color_space"]
                },
                "filter": {
                    "description": "Filter entities by criteria",
                    "entities": ["clips", "assets", "media"],
                    "filters": ["status", "type", "color_space", "tag"]
                }
            },
            "filters": {
                "keyword": "Text search in names and metadata",
                "color_space": "Filter by color space (rec709, aces, etc.)",
                "status": "Filter by status (approved, pending, etc.)",
                "type": "Filter by type (video, image, audio)",
                "tag": "Filter by tag",
                "codec": "Filter by codec (prores, h264, etc.)",
                "resolution": "Filter by resolution (1080p, 4k, etc.)",
                "frame_rate": "Filter by frame rate (24, 30, etc.)",
                "missing": "Show only missing/offline media"
            }
        }

    @staticmethod
    def get_examples_by_category() -> Dict[str, List[str]]:
        """Get example queries organized by category."""
        return {
            "Basic Searches": [
                "find clips with shot_010",
                "search for ProRes files",
                "show video assets"
            ],
            "Color Space": [
                "show assets in rec709",
                "find clips in aces color space",
                "list media in log"
            ],
            "Status and QC": [
                "filter by approved status",
                "show pending assets",
                "count rejected media"
            ],
            "Missing Media": [
                "list missing media",
                "show offline assets",
                "find unavailable clips"
            ],
            "Tags and Organization": [
                "show assets tagged dailies",
                "find clips tagged vfx",
                "list media with tag approved"
            ],
            "Technical Specs": [
                "find 4k assets",
                "show 24 fps media",
                "list ProRes codec files"
            ]
        }
