## Natural Language Command Interface

### Overview

The Conformity Command Interface provides a natural language query system for searching and filtering assets, timelines, and media. It's designed to make project navigation intuitive and fast, with built-in support for future LLM integration.

**Key Features:**
- Natural language query parsing
- Autocomplete and suggestions
- Command history with search
- Saved queries for frequent operations
- LLM-ready architecture
- Qt GUI widget

**Philosophy:**
The command interface follows a clear separation of concerns:
1. **Parsing** - Convert natural language to structured commands
2. **Execution** - Execute commands against Conformity systems
3. **Presentation** - Display results in user-friendly format

This architecture allows the parsing layer to be replaced with an LLM in the future while keeping execution and presentation logic intact.

---

## Quick Start

### Basic Usage

```python
from pathlib import Path
from conformity.asset_tracker.asset_database import AssetDatabase
from conformity.commands.command_parser import CommandParser
from conformity.commands.command_executor import CommandExecutor

# Setup
db = AssetDatabase(Path("project.db"))
parser = CommandParser()
executor = CommandExecutor(asset_database=db)

# Execute query
cmd = parser.parse("find clips with shot_010")
result = executor.execute(cmd)

print(result.message)  # "Found 5 clips"
for clip in result.data:
    print(f"  - {clip['name']}")
```

### GUI Usage

```python
from PyQt6.QtWidgets import QApplication
from conformity.asset_tracker.asset_database import AssetDatabase
from conformity.ui_components.command_interface import CommandInterfaceWidget

app = QApplication([])

# Create interface
db = AssetDatabase(Path("project.db"))
interface = CommandInterfaceWidget(asset_database=db)

# Connect signals
interface.command_executed.connect(
    lambda q, r: print(f"Executed: {q} -> {r.count} results")
)

interface.show()
app.exec()
```

---

## Command Syntax

### Command Structure

Commands follow this general structure:

```
<verb> <entity> [filters...]
```

**Examples:**
- `find clips with shot_010`
- `show assets in rec709 color space`
- `list missing media`
- `count approved assets`

### Supported Verbs

| Verb | Description | Example |
|------|-------------|---------|
| `find` | Find entities matching criteria | `find clips with keyword` |
| `search` | Search for entities (alias for find) | `search for ProRes files` |
| `show` | Display entities | `show assets in aces` |
| `list` | List all entities of a type | `list missing media` |
| `count` | Count matching entities | `count approved assets` |
| `filter` | Filter by criteria | `filter by pending status` |

### Supported Entities

| Entity | Description | Example |
|--------|-------------|---------|
| `clips` | Timeline clips | `find clips with shot_010` |
| `assets` | Media assets | `show assets in rec709` |
| `timelines` | Project timelines | `list timelines` |
| `media` | Media files (alias for assets) | `list missing media` |
| `files` | Files (alias for assets) | `search for ProRes files` |

### Filters

#### Keyword Filter

Search for text in names and metadata:

```
find clips with <keyword>
search for <keyword>
containing <keyword>
```

**Examples:**
- `find clips with shot_010`
- `search for interview`
- `find assets containing master`

#### Color Space Filter

Filter by color space:

```
in <color_space> color space
in <color_space>
color space <color_space>
```

**Examples:**
- `show assets in rec709`
- `find clips in aces color space`
- `list media color space log`

**Common color spaces:**
- `rec709` - Rec.709 (HD/SDR standard)
- `rec2020` - Rec.2020 (UHD/HDR)
- `aces` - ACES color space
- `srgb` - sRGB
- `log` - Log color space

#### Status Filter

Filter by asset status:

```
with <status> status
<status> assets
that are <status>
status <status>
```

**Examples:**
- `filter by approved status`
- `show pending assets`
- `find clips that are rejected`

**Valid statuses:**
- `approved` - Approved for use
- `pending` - Awaiting review
- `rejected` - Not approved
- `archived` - Archived
- `in_progress` - Work in progress
- `needs_review` - Needs QC review

#### Type Filter

Filter by asset type:

```
<type> assets
<type> files
type <type>
```

**Examples:**
- `show video assets`
- `list image files`
- `find audio type`

**Valid types:**
- `video` - Video files
- `image` - Image files
- `audio` - Audio files

#### Codec Filter

Filter by codec:

```
<codec> files
<codec> codec
codec <codec>
```

**Examples:**
- `search for ProRes files`
- `find h264 codec`
- `show dnxhd files`

**Common codecs:**
- `prores` - Apple ProRes
- `h264` - H.264/AVC
- `h265` - H.265/HEVC
- `dnxhd` - Avid DNxHD
- `exr` - OpenEXR
- `dpx` - DPX

#### Resolution Filter

Filter by resolution:

```
<resolution> resolution
resolution <resolution>
```

**Examples:**
- `find 4k resolution`
- `show 1080p assets`
- `list 2k media`

**Common resolutions:**
- `1080p` / `1920x1080`
- `4k` / `3840x2160`
- `2k` / `2048x1080`
- `8k`

#### Frame Rate Filter

Filter by frame rate:

```
<fps> fps
frame rate <fps>
```

**Examples:**
- `find 24 fps`
- `show assets frame rate 30`
- `list 60 fps media`

#### Tag Filter

Filter by tags:

```
tagged <tag>
tagged with <tag>
tag <tag>
```

**Examples:**
- `show assets tagged dailies`
- `find clips tagged vfx`
- `list media tagged with approved`

#### Missing/Offline Filter

Show only missing or offline media:

```
missing media
offline assets
unavailable files
```

**Examples:**
- `list missing media`
- `show offline assets`
- `find unavailable clips`

### Combining Filters

Multiple filters can be combined in natural language:

```
find video assets in rec709 with approved status
show clips tagged dailies with 24 fps
list ProRes files that are offline
```

---

## API Reference

### CommandParser

Pattern-based natural language parser.

#### Methods

**`parse(query: str) -> ParsedCommand`**

Parse a natural language query into a structured command.

```python
parser = CommandParser()
cmd = parser.parse("find clips with shot_010")

print(cmd.command_type)  # CommandType.FIND
print(cmd.entity_type)   # EntityType.CLIPS
print(cmd.filters)        # {FilterType.KEYWORD: "shot_010"}
print(cmd.confidence)     # 0.8
```

**`suggest_completions(partial_query: str) -> List[str]`**

Get autocomplete suggestions for partial query.

```python
suggestions = parser.suggest_completions("find")
# Returns: ["find clips with ", "find assets in ", ...]
```

**`get_help_examples() -> List[Tuple[str, str]]`**

Get example queries with descriptions.

```python
for query, description in parser.get_help_examples():
    print(f"{query} - {description}")
```

### ParsedCommand

Structured representation of a parsed command.

**Attributes:**
- `command_type: CommandType` - Command verb (FIND, SHOW, etc.)
- `entity_type: EntityType` - Target entity (CLIPS, ASSETS, etc.)
- `filters: Dict[FilterType, Any]` - Applied filters
- `parameters: Dict[str, Any]` - Additional parameters
- `raw_query: str` - Original query string
- `confidence: float` - Parse confidence (0.0-1.0)

**Methods:**
- `to_dict() -> Dict` - Convert to dictionary
- `__str__() -> str` - Human-readable representation

### CommandExecutor

Execute parsed commands against Conformity systems.

#### Methods

**`execute(command: ParsedCommand) -> ExecutionResult`**

Execute a parsed command.

```python
executor = CommandExecutor(asset_database=db)
result = executor.execute(cmd)

if result.success:
    print(f"Found {result.count} results")
    for item in result.data:
        print(f"  - {item['name']}")
else:
    print(f"Error: {result.error}")
```

### ExecutionResult

Result of command execution.

**Attributes:**
- `success: bool` - Whether execution succeeded
- `data: Any` - Result data (list of items, counts, etc.)
- `message: str` - Human-readable message
- `error: Optional[str]` - Error message if failed
- `count: int` - Number of results

**Methods:**
- `to_dict() -> Dict` - Convert to dictionary
- `__str__() -> str` - Human-readable representation

### CommandHistory

Manages command execution history.

#### Methods

**`add(query: str, success: bool = True, result_count: int = 0)`**

Add entry to history.

```python
history = CommandHistory(Path("~/.conformity/history.json"))
history.add("find clips with shot_010", success=True, result_count=5)
```

**`get_recent(count: int = 10) -> List[HistoryEntry]`**

Get most recent entries.

```python
recent = history.get_recent(20)
for entry in recent:
    print(f"{entry.timestamp}: {entry.query} ({entry.result_count} results)")
```

**`search(query: str) -> List[HistoryEntry]`**

Search history for matching entries.

```python
matching = history.search("shot")
```

**`get_most_common(count: int = 10) -> List[Tuple[str, int]]`**

Get most commonly used queries.

```python
common = history.get_most_common(10)
for query, count in common:
    print(f"{query}: used {count} times")
```

### SavedQueryManager

Manages saved queries.

#### Methods

**`save_query(name: str, query: str, description: str = "", category: str = "General") -> SavedQuery`**

Save a new query.

```python
manager = SavedQueryManager(Path("~/.conformity/queries.json"))

manager.save_query(
    name="Missing Media Check",
    query="list missing media",
    description="Find all offline media files",
    category="QC"
)
```

**`get(name: str) -> Optional[SavedQuery]`**

Get saved query by name.

```python
query = manager.get("Missing Media Check")
if query:
    print(query.query)
```

**`get_by_category(category: str) -> List[SavedQuery]`**

Get queries in a category.

```python
qc_queries = manager.get_by_category("QC")
```

**`mark_used(name: str)`**

Mark query as used (updates timestamp and count).

**`export_json(export_path: Path)`** / **`import_json(import_path: Path, merge: bool = True)`**

Export/import saved queries.

---

## Extending the Command Interface

### Adding New Command Types

To add a new command type:

1. Add to `CommandType` enum in `command_parser.py`:

```python
class CommandType(Enum):
    # ... existing types
    VERIFY = "verify"  # New type
```

2. Add pattern in `_init_patterns()`:

```python
self.command_patterns = [
    # ... existing patterns
    (r"^(verify|check)\s+", CommandType.VERIFY),
]
```

3. Add execution logic in `CommandExecutor`:

```python
def execute(self, command: ParsedCommand) -> ExecutionResult:
    if command.command_type == CommandType.VERIFY:
        return self._execute_verify_command(command)
    # ... existing logic
```

### Adding New Filters

To add a new filter type:

1. Add to `FilterType` enum:

```python
class FilterType(Enum):
    # ... existing types
    DURATION = "duration"  # New filter
```

2. Add pattern:

```python
self.filter_patterns = [
    # ... existing patterns
    (r"duration\s*[:=]?\s*(\d+)", FilterType.DURATION),
]
```

3. Handle in `_build_asset_query_params()`:

```python
if filter_type == FilterType.DURATION:
    params['min_duration'] = float(value)
```

### Custom Parser

You can create a custom parser that generates `ParsedCommand` directly:

```python
class CustomParser:
    def parse(self, query: str) -> ParsedCommand:
        # Custom parsing logic
        return ParsedCommand(
            command_type=CommandType.FIND,
            entity_type=EntityType.ASSETS,
            filters={},
            parameters={},
            raw_query=query,
            confidence=1.0
        )

# Use with executor
parser = CustomParser()
executor = CommandExecutor(asset_database=db)

cmd = parser.parse("custom query format")
result = executor.execute(cmd)
```

---

## LLM Integration

The command interface is designed for easy LLM integration.

### Architecture for LLM

The system has clear separation:

```
┌──────────────┐
│ User Input   │
└──────┬───────┘
       │
       ↓
┌──────────────────────┐      ┌─────────────┐
│ Pattern Parser   │ OR │  LLM Parser     │
│ (Regex-based)    │      │ (Future)        │
└──────┬───────────────┘      └──────┬──────┘
       │                             │
       └────────────┬────────────────┘
                    ↓
           ┌────────────────┐
           │ ParsedCommand  │
           └────────┬───────┘
                    ↓
           ┌────────────────┐
           │ Executor       │
           └────────┬───────┘
                    ↓
           ┌────────────────┐
           │ Results        │
           └────────────────┘
```

### LLM Parser Implementation

Future LLM parser could look like:

```python
from conformity.commands.command_parser import ParsedCommand, CommandType, EntityType, FilterType

class LLMCommandParser:
    def __init__(self, llm_client):
        self.llm = llm_client

    def parse(self, query: str) -> ParsedCommand:
        # Provide schema to LLM
        schema = {
            "command_type": ["find", "show", "list", "count"],
            "entity_type": ["clips", "assets", "timelines"],
            "filters": {
                "keyword": "string",
                "color_space": "string",
                "status": ["approved", "pending", "rejected"],
                # ... etc
            }
        }

        # Get LLM to generate structured output
        response = self.llm.complete(
            prompt=f"Parse this command into structured format: {query}",
            schema=schema
        )

        # Convert LLM response to ParsedCommand
        return ParsedCommand(
            command_type=CommandType(response['command_type']),
            entity_type=EntityType(response['entity_type']),
            filters={
                FilterType(k): v
                for k, v in response['filters'].items()
            },
            parameters=response.get('parameters', {}),
            raw_query=query,
            confidence=response.get('confidence', 1.0)
        )

# Use exactly like pattern parser
llm_parser = LLMCommandParser(llm_client)
executor = CommandExecutor(asset_database=db)

cmd = llm_parser.parse("show me all the approved 4K ProRes files from yesterday")
result = executor.execute(cmd)
```

### Providing Context to LLM

Use `CommandRegistry` to provide context:

```python
from conformity.commands.command_executor import CommandRegistry

# Get schema for LLM context
schema = CommandRegistry.get_command_schema()
examples = CommandRegistry.get_examples_by_category()

# Include in LLM prompt
context = f"""
Available commands: {schema}
Example queries: {examples}

Parse user query: "{user_query}"
"""
```

---

## Best Practices

### Query Optimization

**Do:**
- Use specific filters to narrow results
- Combine multiple filters when possible
- Use saved queries for frequent operations

**Don't:**
- Query without filters on large databases
- Use overly broad keywords

**Example:**
```
Good: "find video assets in rec709 with approved status"
Bad: "find assets"
```

### Command History

- Review history to find patterns
- Save frequently used queries
- Use history search to find past queries

### Saved Queries

Organize saved queries by category:
- **QC** - Quality control checks
- **Review** - Review workflows
- **Delivery** - Delivery prep
- **Technical** - Technical queries
- **Color** - Color space queries

### Error Handling

Always check execution results:

```python
result = executor.execute(cmd)

if not result.success:
    print(f"Error: {result.error}")
    # Handle error
else:
    # Process results
    for item in result.data:
        # ... process
```

---

## Troubleshooting

### Parse Confidence Low

If parse confidence is low (<0.5):

1. Check query syntax against examples
2. Use autocomplete for suggestions
3. Break complex queries into simpler ones
4. Check for typos in filter keywords

### No Results

If query returns no results:

1. Verify database has data
2. Try broader filters
3. Check filter values are correct
4. Use "list all assets" to verify database

### Autocomplete Not Working

1. Check PyQt6 is installed
2. Verify completer is initialized
3. Try typing at least one character

### History Not Saving

1. Check file permissions on history file
2. Verify directory exists: `~/.conformity/`
3. Check disk space

---

## Examples

### Asset Management

```python
# Find all approved assets
"show assets with approved status"

# Find offline media
"list missing media"

# Find by codec
"search for ProRes files"

# Find by resolution
"find 4k assets"
```

### Color Workflows

```python
# Find assets by color space
"show assets in aces color space"

# Find log footage
"list media in log"

# Count by color space
"count assets in rec709"
```

### QC and Review

```python
# Find pending reviews
"show assets with pending status"

# Find rejected items
"list clips that are rejected"

# Count approvals
"count approved assets"
```

### Timeline Queries

```python
# Find specific clips
"find clips with shot_010"

# Search in clips
"search clips containing interview"
```

### Combined Queries

```python
# Complex filter
"find video assets in rec709 with approved status"

# Multiple criteria
"show ProRes files tagged dailies with 24 fps"

# Technical + status
"list 4k assets that are offline"
```

---

## Future Enhancements

### Planned Features

1. **LLM Integration**
   - Natural language understanding
   - Conversational queries
   - Context awareness

2. **Advanced Filters**
   - Date ranges
   - Custom metadata fields
   - Relationship queries

3. **Command Chaining**
   - Multi-step commands
   - Conditional execution
   - Result transformation

4. **Smart Suggestions**
   - Context-aware autocomplete
   - Query refinement
   - Similar query suggestions

5. **Export/Reporting**
   - CSV export
   - Report generation
   - Visualization

### Contributing

To contribute new commands or filters:

1. Follow existing patterns in `command_parser.py`
2. Add execution logic in `command_executor.py`
3. Add tests for new functionality
4. Update documentation with examples
5. Submit PR with clear description

---

## Additional Resources

- **Examples**: See `examples/command_interface_example.py`
- **API Reference**: See docstrings in source files
- **Pattern Reference**: See `command_parser.py` for regex patterns
- **GUI Integration**: See `command_interface.py` for Qt implementation
