"""
Natural Language Command Parser for Conformity.

Provides a simple pattern-matching based command parser for natural language
queries about assets, timelines, and media. Designed to be LLM-ready with
clear separation between parsing and execution.

Features:
- Pattern-based query parsing
- Structured command representation
- Extensible command types
- Hook points for future LLM integration

Example queries:
- "find clips with shot_010"
- "show assets in rec709"
- "list missing media"
- "filter by approved status"
- "search for ProRes files"
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of commands that can be parsed."""
    FIND = "find"
    SHOW = "show"
    LIST = "list"
    FILTER = "filter"
    SEARCH = "search"
    COUNT = "count"
    GET = "get"
    UNKNOWN = "unknown"


class EntityType(Enum):
    """Types of entities commands can operate on."""
    CLIPS = "clips"
    ASSETS = "assets"
    TIMELINES = "timelines"
    MEDIA = "media"
    FILES = "files"
    TRACKS = "tracks"
    MARKERS = "markers"


class FilterType(Enum):
    """Types of filters that can be applied."""
    KEYWORD = "keyword"
    COLOR_SPACE = "color_space"
    STATUS = "status"
    TYPE = "type"
    CODEC = "codec"
    RESOLUTION = "resolution"
    FRAME_RATE = "frame_rate"
    MISSING = "missing"
    OFFLINE = "offline"
    TAG = "tag"


@dataclass
class ParsedCommand:
    """
    Structured representation of a parsed command.

    This structure is designed to be LLM-ready - an LLM could generate
    this structure directly, bypassing pattern matching.

    Attributes:
        command_type: The type of command (find, show, list, etc.)
        entity_type: What to operate on (clips, assets, etc.)
        filters: Dictionary of filters to apply
        parameters: Additional command parameters
        raw_query: Original query string
        confidence: Confidence in the parse (0.0-1.0)
        alternatives: Alternative interpretations
    """
    command_type: CommandType
    entity_type: EntityType
    filters: Dict[FilterType, Any]
    parameters: Dict[str, Any]
    raw_query: str
    confidence: float = 1.0
    alternatives: List['ParsedCommand'] = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'command_type': self.command_type.value,
            'entity_type': self.entity_type.value,
            'filters': {k.value: v for k, v in self.filters.items()},
            'parameters': self.parameters,
            'raw_query': self.raw_query,
            'confidence': self.confidence
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        filter_str = ", ".join(f"{k.value}={v}" for k, v in self.filters.items())
        return f"{self.command_type.value} {self.entity_type.value} [{filter_str}]"


class CommandParser:
    """
    Natural language command parser using pattern matching.

    This parser uses regex patterns to interpret natural language queries.
    It's designed to be replaced or augmented by an LLM in the future.

    The parser follows these principles:
    1. Simple pattern matching for now
    2. Clear structure for commands
    3. Easy to extend with new patterns
    4. LLM can bypass this and generate ParsedCommand directly

    Example:
        ```python
        parser = CommandParser()

        # Parse a query
        cmd = parser.parse("find clips with shot_010")
        print(cmd.command_type)  # CommandType.FIND
        print(cmd.entity_type)   # EntityType.CLIPS
        print(cmd.filters)        # {FilterType.KEYWORD: "shot_010"}

        # Execute (delegated to CommandExecutor)
        executor = CommandExecutor(asset_db, timeline_manager)
        results = executor.execute(cmd)
        ```
    """

    def __init__(self):
        """Initialize command parser with pattern definitions."""
        self._init_patterns()

    def _init_patterns(self):
        """Initialize regex patterns for command matching."""

        # Command verb patterns
        self.command_patterns = [
            (r"^(find|search\s+for|look\s+for)\s+", CommandType.FIND),
            (r"^(show|display|get)\s+", CommandType.SHOW),
            (r"^(list|enumerate)\s+", CommandType.LIST),
            (r"^(filter|select)\s+", CommandType.FILTER),
            (r"^(count|how\s+many)\s+", CommandType.COUNT),
        ]

        # Entity type patterns
        self.entity_patterns = [
            (r"clips?", EntityType.CLIPS),
            (r"assets?", EntityType.ASSETS),
            (r"timelines?", EntityType.TIMELINES),
            (r"media|footage", EntityType.MEDIA),
            (r"files?", EntityType.FILES),
            (r"tracks?", EntityType.TRACKS),
            (r"markers?", EntityType.MARKERS),
        ]

        # Filter patterns
        self.filter_patterns = [
            # Color space
            (r"in\s+(rec709|rec2020|aces|srgb|log|[\w\-]+)\s+color\s*space", FilterType.COLOR_SPACE),
            (r"color\s*space\s*[:=]?\s*(rec709|rec2020|aces|srgb|log|[\w\-]+)", FilterType.COLOR_SPACE),

            # Status
            (r"(with|having|in)\s+(approved|pending|rejected|archived|in_progress)\s+status", FilterType.STATUS),
            (r"status\s*[:=]?\s*(approved|pending|rejected|archived|in_progress)", FilterType.STATUS),
            (r"that\s+are\s+(approved|pending|rejected|archived)", FilterType.STATUS),

            # Type
            (r"(video|image|audio)\s+(files|assets)", FilterType.TYPE),
            (r"type\s*[:=]?\s*(video|image|audio)", FilterType.TYPE),

            # Codec
            (r"(prores|h264|h265|dnxhd|exr|dpx)\s+(files|codec)", FilterType.CODEC),
            (r"codec\s*[:=]?\s*(prores|h264|h265|dnxhd|exr|dpx)", FilterType.CODEC),

            # Resolution
            (r"(\d+x\d+|\d+p|\d+k)\s+resolution", FilterType.RESOLUTION),
            (r"resolution\s*[:=]?\s*(\d+x\d+|\d+p|\d+k)", FilterType.RESOLUTION),

            # Frame rate
            (r"(\d+(?:\.\d+)?)\s*fps", FilterType.FRAME_RATE),
            (r"frame\s*rate\s*[:=]?\s*(\d+(?:\.\d+)?)", FilterType.FRAME_RATE),

            # Missing/offline
            (r"missing|offline|unavailable", FilterType.MISSING),

            # Tags
            (r"tagged?\s+(?:with\s+)?(['\"]?)(\w+)\1", FilterType.TAG),

            # Generic keyword (must be last)
            (r"with\s+(['\"]?)([^'\"]+)\1", FilterType.KEYWORD),
            (r"containing\s+(['\"]?)([^'\"]+)\1", FilterType.KEYWORD),
        ]

    def parse(self, query: str) -> ParsedCommand:
        """
        Parse a natural language query into a structured command.

        Args:
            query: Natural language query string

        Returns:
            ParsedCommand with parsed components

        Example:
            >>> parser = CommandParser()
            >>> cmd = parser.parse("find clips with shot_010")
            >>> print(cmd.command_type)
            CommandType.FIND
        """
        query = query.strip().lower()

        # Parse command type
        command_type = self._extract_command_type(query)

        # Parse entity type
        entity_type = self._extract_entity_type(query)

        # Parse filters
        filters = self._extract_filters(query)

        # Calculate confidence based on parse quality
        confidence = self._calculate_confidence(command_type, entity_type, filters)

        # Create parsed command
        cmd = ParsedCommand(
            command_type=command_type,
            entity_type=entity_type,
            filters=filters,
            parameters={},
            raw_query=query,
            confidence=confidence
        )

        logger.info(f"Parsed: '{query}' -> {cmd}")
        return cmd

    def _extract_command_type(self, query: str) -> CommandType:
        """Extract command type from query."""
        for pattern, cmd_type in self.command_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return cmd_type

        # Default: treat as search/find
        return CommandType.FIND

    def _extract_entity_type(self, query: str) -> EntityType:
        """Extract entity type from query."""
        for pattern, entity_type in self.entity_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return entity_type

        # Default: assume assets
        return EntityType.ASSETS

    def _extract_filters(self, query: str) -> Dict[FilterType, Any]:
        """Extract filters from query."""
        filters = {}

        for pattern, filter_type in self.filter_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if filter_type == FilterType.MISSING:
                    filters[filter_type] = True
                elif filter_type == FilterType.KEYWORD:
                    # Get the captured keyword (last group)
                    filters[filter_type] = match.group(match.lastindex)
                elif filter_type == FilterType.TAG:
                    # Tag is in second group (after optional quote)
                    filters[filter_type] = match.group(2)
                else:
                    # Get the captured value (last group)
                    filters[filter_type] = match.group(match.lastindex)

        return filters

    def _calculate_confidence(
        self,
        command_type: CommandType,
        entity_type: EntityType,
        filters: Dict[FilterType, Any]
    ) -> float:
        """
        Calculate confidence in the parse.

        Returns value between 0.0 and 1.0.
        Future LLM integration can provide more sophisticated confidence scoring.
        """
        confidence = 0.5  # Base confidence

        # Higher confidence if we found a clear command
        if command_type != CommandType.UNKNOWN:
            confidence += 0.2

        # Higher confidence if we found an entity
        if entity_type != EntityType.ASSETS:  # ASSETS is default
            confidence += 0.2

        # Higher confidence with more filters
        confidence += min(0.1 * len(filters), 0.3)

        return min(confidence, 1.0)

    def suggest_completions(self, partial_query: str) -> List[str]:
        """
        Suggest query completions for autocomplete.

        Args:
            partial_query: Partial query to complete

        Returns:
            List of suggested completions
        """
        suggestions = []

        partial = partial_query.lower()

        # Command completions
        if not partial or partial in "find":
            suggestions.append("find clips with ")
        if not partial or partial in "show":
            suggestions.append("show assets in ")
        if not partial or partial in "list":
            suggestions.append("list missing media")
        if not partial or partial in "filter":
            suggestions.append("filter by approved status")
        if not partial or partial in "search":
            suggestions.append("search for ProRes files")

        # Entity completions
        if "find" in partial or "show" in partial:
            if "find" in partial and "clips" not in partial:
                suggestions.append(partial + "clips with ")
            if "show" in partial and "assets" not in partial:
                suggestions.append(partial + "assets in ")

        # Filter completions
        if "with" in partial:
            suggestions.extend([
                "find clips with shot_",
                "find assets with keyword"
            ])

        if "in" in partial and "color" not in partial:
            suggestions.extend([
                "show assets in rec709 color space",
                "show assets in aces color space"
            ])

        return [s for s in suggestions if s.startswith(partial)][:10]

    def get_help_examples(self) -> List[Tuple[str, str]]:
        """
        Get example queries with descriptions.

        Returns:
            List of (query, description) tuples
        """
        return [
            ("find clips with shot_010", "Find clips containing 'shot_010' in name or metadata"),
            ("show assets in rec709", "Show assets in Rec.709 color space"),
            ("list missing media", "List all missing or offline media files"),
            ("filter by approved status", "Filter assets by approval status"),
            ("search for ProRes files", "Search for ProRes codec files"),
            ("show video assets", "Show all video assets"),
            ("find clips with 4k resolution", "Find clips at 4K resolution"),
            ("count approved assets", "Count how many assets are approved"),
            ("show assets tagged dailies", "Show assets with 'dailies' tag"),
            ("list timelines", "List all timelines in project"),
            ("find assets with 24 fps", "Find assets at 24 frames per second"),
            ("show offline media", "Show media that is offline or missing"),
        ]


# Hook for future LLM integration
class LLMCommandParser:
    """
    Placeholder for future LLM-based command parser.

    This would use an LLM to generate ParsedCommand structures directly,
    bypassing regex patterns for more flexible natural language understanding.

    Example future implementation:
        ```python
        class LLMCommandParser:
            def __init__(self, llm_client):
                self.llm = llm_client

            def parse(self, query: str) -> ParsedCommand:
                # Send query to LLM with schema
                response = self.llm.complete(
                    f"Parse this query into a structured command: {query}",
                    schema=ParsedCommand
                )
                return ParsedCommand(**response)
        ```
    """

    def __init__(self):
        raise NotImplementedError(
            "LLM integration not yet implemented. "
            "Use CommandParser for now."
        )
