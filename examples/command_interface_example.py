#!/usr/bin/env python3
"""
Example: Natural Language Command Interface

Demonstrates the command interface system for querying and filtering
assets using natural language:
- Pattern-based command parsing
- Command execution
- History and saved queries
- Qt GUI interface (if PyQt6 available)
- LLM-ready architecture
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conformity.commands.command_parser import CommandParser
from conformity.commands.command_executor import CommandExecutor
from conformity.commands.command_history import CommandHistory, SavedQueryManager
from conformity.asset_tracker.asset_database import AssetDatabase, AssetType, AssetStatus

# Check for PyQt6
try:
    from PyQt6.QtWidgets import QApplication
    from conformity.ui_components.command_interface import CommandInterfaceWidget
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False


def example_basic_parsing():
    """Basic command parsing examples."""
    print("=" * 60)
    print("EXAMPLE: Basic Command Parsing")
    print("=" * 60)

    parser = CommandParser()

    # Example queries
    queries = [
        "find clips with shot_010",
        "show assets in rec709",
        "list missing media",
        "filter by approved status",
        "search for ProRes files",
        "count video assets",
    ]

    print("\nParsing natural language queries:")
    for query in queries:
        cmd = parser.parse(query)
        print(f"\nQuery: '{query}'")
        print(f"  Command: {cmd.command_type.value}")
        print(f"  Entity: {cmd.entity_type.value}")
        print(f"  Filters: {', '.join(f'{k.value}={v}' for k, v in cmd.filters.items())}")
        print(f"  Confidence: {cmd.confidence:.2f}")


def example_command_execution():
    """Command execution with asset database."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Command Execution")
    print("=" * 60)

    # Create database and add sample data
    print("\n1. Setting up sample database...")
    db = AssetDatabase()

    # Add sample assets
    assets = [
        ("clip001.mp4", AssetType.VIDEO, AssetStatus.APPROVED, "rec709"),
        ("clip002.mov", AssetType.VIDEO, AssetStatus.PENDING, "aces"),
        ("render001.exr", AssetType.IMAGE, AssetStatus.APPROVED, "aces"),
        ("audio001.wav", AssetType.AUDIO, AssetStatus.APPROVED, "N/A"),
    ]

    for filename, asset_type, status, color_space in assets:
        asset_id = db.add_asset(
            file_path=Path(f"/media/{filename}"),
            asset_type=asset_type,
            status=status
        )
        db.add_metadata(asset_id, {'color_space': color_space})

    print(f"   Added {len(assets)} sample assets")

    # Setup parser and executor
    parser = CommandParser()
    executor = CommandExecutor(asset_database=db)

    # Example queries
    queries = [
        "show all assets",
        "find video assets",
        "show assets in aces",
        "filter by approved status",
        "count video assets",
    ]

    print("\n2. Executing queries:")
    for query in queries:
        print(f"\n   Query: '{query}'")

        # Parse
        cmd = parser.parse(query)

        # Execute
        result = executor.execute(cmd)

        # Display results
        if result.success:
            print(f"   Result: {result.message}")
            if result.data and isinstance(result.data, list):
                for item in result.data[:3]:  # Show first 3
                    if isinstance(item, dict):
                        print(f"     - {item.get('name', 'Unknown')}")
        else:
            print(f"   Error: {result.error}")


def example_autocomplete():
    """Autocomplete suggestions."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Autocomplete Suggestions")
    print("=" * 60)

    parser = CommandParser()

    partial_queries = [
        "",
        "find",
        "show",
        "list",
        "find clips",
    ]

    print("\nAutocomplete suggestions for partial queries:")
    for partial in partial_queries:
        suggestions = parser.suggest_completions(partial)
        print(f"\nPartial: '{partial}'")
        print(f"Suggestions:")
        for suggestion in suggestions[:5]:
            print(f"  - {suggestion}")


def example_command_history():
    """Command history management."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Command History")
    print("=" * 60)

    history = CommandHistory()  # In-memory for example

    # Add some commands
    print("\n1. Adding commands to history...")
    commands = [
        ("find clips with shot_010", True, 5),
        ("show assets in rec709", True, 12),
        ("list missing media", True, 3),
        ("search for ProRes files", True, 8),
    ]

    for query, success, count in commands:
        history.add(query, success=success, result_count=count)
        print(f"   Added: {query}")

    # Get recent
    print("\n2. Recent commands:")
    recent = history.get_recent(10)
    for entry in recent:
        status = "✓" if entry.success else "✗"
        print(f"   {status} {entry.query} ({entry.result_count} results)")

    # Search history
    print("\n3. Searching history for 'shot':")
    matching = history.search("shot")
    for entry in matching:
        print(f"   - {entry.query}")

    # Most common
    print("\n4. Most common queries:")
    common = history.get_most_common(5)
    for query, count in common:
        print(f"   - {query}: {count} times")


def example_saved_queries():
    """Saved queries management."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Saved Queries")
    print("=" * 60)

    manager = SavedQueryManager()  # Will load defaults

    # Show default queries
    print("\n1. Default saved queries:")
    for query in manager.get_all():
        print(f"\n   Name: {query.name}")
        print(f"   Query: {query.query}")
        print(f"   Category: {query.category}")
        print(f"   Description: {query.description}")

    # Save custom query
    print("\n2. Saving custom query...")
    manager.save_query(
        name="My Custom Query",
        query="find video assets with 24 fps",
        description="Find all 24 fps video files",
        category="Technical"
    )
    print("   Saved: My Custom Query")

    # Get by category
    print("\n3. Queries by category:")
    categories = manager.get_categories()
    for category in categories:
        queries = manager.get_by_category(category)
        print(f"\n   {category}: {len(queries)} queries")
        for query in queries:
            print(f"     - {query.name}")


def example_llm_integration():
    """Example of LLM-ready architecture."""
    print("\n" + "=" * 60)
    print("EXAMPLE: LLM Integration Pattern")
    print("=" * 60)

    print("\nThe command interface is LLM-ready:")
    print("""
    Current Architecture:
    ┌──────────────┐
    │ User Input   │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │ Pattern      │  ← Current: Regex-based
    │ Parser       │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │ ParsedCommand│  ← Structured representation
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │ Executor     │  ← Executes against database
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │ Results      │
    └──────────────┘

    Future with LLM:
    ┌──────────────┐
    │ User Input   │
    └──────┬───────┘
           ↓
    ┌──────────────────────┐
    │ LLM Parser      │  ← Future: LLM generates ParsedCommand
    │ (OpenAI/Claude) │
    └──────┬───────────────┘
           ↓
    ┌──────────────┐
    │ ParsedCommand│  ← Same structure!
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │ Executor     │  ← No changes needed
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │ Results      │
    └──────────────┘
    """)

    print("\nTo integrate an LLM:")
    print("""
    from conformity.commands.command_parser import ParsedCommand, CommandType, EntityType, FilterType

    class LLMCommandParser:
        def __init__(self, llm_client):
            self.llm = llm_client

        def parse(self, query: str) -> ParsedCommand:
            # Send query to LLM with schema
            response = self.llm.complete(
                f"Parse this query: {query}",
                schema=ParsedCommand
            )

            # Return ParsedCommand
            return ParsedCommand(**response)

    # Use exactly like pattern parser
    llm_parser = LLMCommandParser(llm_client)
    executor = CommandExecutor(asset_database=db)

    cmd = llm_parser.parse("show me yesterday's approved 4K files")
    result = executor.execute(cmd)
    """)


def example_gui_interface():
    """GUI interface example."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Qt GUI Interface")
    print("=" * 60)

    if not HAS_PYQT6:
        print("\nSkipped: Requires PyQt6")
        print("Install with: pip install PyQt6")
        print("\nWhen available, the GUI provides:")
        print("  - Text input with autocomplete")
        print("  - Command history browsing")
        print("  - Saved queries access")
        print("  - Table and text result views")
        print("  - Help system")
        return

    print("\nLaunching Qt command interface...")
    print("\nFeatures:")
    print("  - Enter natural language queries")
    print("  - Autocomplete suggestions as you type")
    print("  - Browse command history")
    print("  - Access saved queries")
    print("  - View results in table or text format")
    print("  - Built-in help with examples")

    print("\nExample usage code:")
    print("""
    from PyQt6.QtWidgets import QApplication
    from conformity.asset_tracker.asset_database import AssetDatabase
    from conformity.ui_components.command_interface import CommandInterfaceWidget

    app = QApplication([])

    # Create database
    db = AssetDatabase(Path("project.db"))

    # Create interface
    interface = CommandInterfaceWidget(asset_database=db)

    # Connect signals
    interface.command_executed.connect(
        lambda q, r: print(f"Executed: {q} -> {r.count} results")
    )

    interface.show()
    app.exec()
    """)


def example_help_system():
    """Help system examples."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Help System")
    print("=" * 60)

    parser = CommandParser()

    print("\nExample queries with descriptions:")
    for query, description in parser.get_help_examples():
        print(f"\n  Query: {query}")
        print(f"  Description: {description}")

    from conformity.commands.command_executor import CommandRegistry

    print("\n\nCommand schema (for LLM context):")
    schema = CommandRegistry.get_command_schema()

    print("\nAvailable commands:")
    for cmd, info in schema['commands'].items():
        print(f"\n  {cmd}:")
        print(f"    Description: {info['description']}")
        print(f"    Entities: {', '.join(info['entities'])}")
        print(f"    Filters: {', '.join(info['filters'][:3])}...")

    print("\n\nExamples by category:")
    examples = CommandRegistry.get_examples_by_category()
    for category, queries in examples.items():
        print(f"\n  {category}:")
        for query in queries:
            print(f"    - {query}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("NATURAL LANGUAGE COMMAND INTERFACE EXAMPLES")
    print("=" * 60)
    print("\nDemonstrating natural language query system for Conformity")

    try:
        example_basic_parsing()
        example_command_execution()
        example_autocomplete()
        example_command_history()
        example_saved_queries()
        example_llm_integration()
        example_gui_interface()
        example_help_system()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nFor more information, see:")
        print("  - docs/COMMAND_INTERFACE.md")
        print("  - README.md")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
