"""
Qt Command Interface Widget for Conformity.

Provides a natural language command interface with:
- Text input with autocomplete
- Command history browsing
- Saved queries access
- Results display
- Help system

This widget integrates the command parser, executor, and history systems
into a user-friendly GUI component.
"""

from pathlib import Path
from typing import Optional, List
import logging

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QTextEdit, QCompleter, QLabel, QComboBox, QGroupBox,
        QTableWidget, QTableWidgetItem, QSplitter, QTabWidget,
        QMessageBox, QInputDialog
    )
    from PyQt6.QtCore import Qt, QStringListModel, pyqtSignal
    from PyQt6.QtGui import QFont, QTextCursor
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False

from ..commands.command_parser import CommandParser
from ..commands.command_executor import CommandExecutor, ExecutionResult
from ..commands.command_history import CommandHistory, SavedQueryManager

logger = logging.getLogger(__name__)


class CommandInterfaceWidget(QWidget):
    """
    Natural language command interface widget.

    Provides a complete command interface with input, execution, history,
    and results display.

    Signals:
        command_executed: Emitted when command is executed (query, result)
        results_ready: Emitted when results are available (data)

    Example:
        ```python
        from PyQt6.QtWidgets import QApplication
        from conformity.asset_tracker.asset_database import AssetDatabase
        from conformity.ui_components.command_interface import CommandInterfaceWidget

        app = QApplication([])

        # Setup
        db = AssetDatabase(Path("project.db"))
        cmd_widget = CommandInterfaceWidget(asset_database=db)

        # Connect signals
        cmd_widget.command_executed.connect(
            lambda q, r: print(f"Executed: {q}")
        )

        cmd_widget.show()
        app.exec()
        ```
    """

    # Signals
    command_executed = pyqtSignal(str, object)  # query, result
    results_ready = pyqtSignal(list)  # results data

    def __init__(
        self,
        asset_database=None,
        timeline_manager=None,
        color_manager=None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize command interface widget.

        Args:
            asset_database: AssetDatabase instance
            timeline_manager: TimelineManager instance
            color_manager: ColorManager instance
            parent: Parent Qt widget
        """
        if not HAS_PYQT6:
            raise ImportError("PyQt6 is required for CommandInterfaceWidget")

        super().__init__(parent)

        # Initialize components
        self.parser = CommandParser()
        self.executor = CommandExecutor(
            asset_database=asset_database,
            timeline_manager=timeline_manager,
            color_manager=color_manager
        )

        # History and saved queries
        config_dir = Path.home() / ".conformity"
        self.history = CommandHistory(config_dir / "command_history.json")
        self.saved_queries = SavedQueryManager(config_dir / "saved_queries.json")

        # State
        self.current_result: Optional[ExecutionResult] = None
        self.history_index = -1

        # Initialize UI
        self._init_ui()

        logger.info("CommandInterfaceWidget initialized")

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Natural Language Command Interface")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Input section
        input_group = self._create_input_section()
        layout.addWidget(input_group)

        # Splitter for results and sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Results display
        results_widget = self._create_results_section()
        splitter.addWidget(results_widget)

        # Sidebar with history and saved queries
        sidebar = self._create_sidebar()
        splitter.addWidget(sidebar)

        splitter.setStretchFactor(0, 3)  # Results get more space
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        self.setLayout(layout)

    def _create_input_section(self) -> QGroupBox:
        """Create command input section."""
        group = QGroupBox("Command Input")
        layout = QVBoxLayout()

        # Input field with autocomplete
        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter command (e.g., 'find clips with shot_010')")
        self.input_field.returnPressed.connect(self._on_execute)

        # Setup autocomplete
        self._setup_autocomplete()

        input_layout.addWidget(self.input_field)

        # Execute button
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.clicked.connect(self._on_execute)
        input_layout.addWidget(self.execute_btn)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.input_field.clear())
        input_layout.addWidget(clear_btn)

        layout.addLayout(input_layout)

        # Parsed command display
        parsed_layout = QHBoxLayout()
        parsed_layout.addWidget(QLabel("Interpreted as:"))
        self.parsed_label = QLabel("(enter a command)")
        self.parsed_label.setStyleSheet("color: gray; font-style: italic;")
        parsed_layout.addWidget(self.parsed_label)
        parsed_layout.addStretch()
        layout.addLayout(parsed_layout)

        # Connect input changes to parse preview
        self.input_field.textChanged.connect(self._on_input_changed)

        group.setLayout(layout)
        return group

    def _create_results_section(self) -> QWidget:
        """Create results display section."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Results info
        info_layout = QHBoxLayout()
        self.result_count_label = QLabel("No results")
        info_layout.addWidget(self.result_count_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Tabs for different result views
        self.results_tabs = QTabWidget()

        # Table view
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Name", "Type", "Status", "Color Space", "Path"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_tabs.addTab(self.results_table, "Table View")

        # Text view
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier", 10))
        self.results_tabs.addTab(self.results_text, "Text View")

        layout.addWidget(self.results_tabs)

        widget.setLayout(layout)
        return widget

    def _create_sidebar(self) -> QTabWidget:
        """Create sidebar with history and saved queries."""
        tabs = QTabWidget()

        # History tab
        history_widget = self._create_history_widget()
        tabs.addTab(history_widget, "History")

        # Saved queries tab
        saved_widget = self._create_saved_queries_widget()
        tabs.addTab(saved_widget, "Saved")

        # Help tab
        help_widget = self._create_help_widget()
        tabs.addTab(help_widget, "Help")

        return tabs

    def _create_history_widget(self) -> QWidget:
        """Create history browsing widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Recent commands list
        layout.addWidget(QLabel("Recent Commands:"))

        self.history_list = QTextEdit()
        self.history_list.setReadOnly(True)
        self.history_list.setMaximumHeight(200)
        layout.addWidget(self.history_list)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._update_history_display)
        layout.addWidget(refresh_btn)

        # Clear history button
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._on_clear_history)
        layout.addWidget(clear_btn)

        layout.addStretch()

        widget.setLayout(layout)
        self._update_history_display()
        return widget

    def _create_saved_queries_widget(self) -> QWidget:
        """Create saved queries widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Category selector
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All")
        for category in self.saved_queries.get_categories():
            self.category_combo.addItem(category)
        self.category_combo.currentTextChanged.connect(self._update_saved_display)
        cat_layout.addWidget(self.category_combo)
        layout.addLayout(cat_layout)

        # Saved queries list
        self.saved_text = QTextEdit()
        self.saved_text.setReadOnly(True)
        self.saved_text.setMaximumHeight(200)
        self.saved_text.anchorClicked.connect(self._on_saved_query_clicked)
        layout.addWidget(self.saved_text)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save Current")
        save_btn.clicked.connect(self._on_save_current_query)
        btn_layout.addWidget(save_btn)

        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self._on_import_queries)
        btn_layout.addWidget(import_btn)

        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self._on_export_queries)
        btn_layout.addWidget(export_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        widget.setLayout(layout)
        self._update_saved_display()
        return widget

    def _create_help_widget(self) -> QWidget:
        """Create help and examples widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Help text
        help_text = QTextEdit()
        help_text.setReadOnly(True)

        help_content = """
<h3>Command Interface Help</h3>

<p>Enter natural language queries to search and filter your project assets.</p>

<h4>Basic Commands:</h4>
<ul>
<li><b>find</b> - Find entities matching criteria</li>
<li><b>show</b> - Display entities</li>
<li><b>list</b> - List all entities of a type</li>
<li><b>count</b> - Count matching entities</li>
<li><b>filter</b> - Filter by criteria</li>
</ul>

<h4>Example Queries:</h4>
<ul>
"""
        for query, description in self.parser.get_help_examples():
            help_content += f'<li><code>{query}</code> - {description}</li>\n'

        help_content += """
</ul>

<h4>Filters:</h4>
<ul>
<li><b>keyword</b> - "with [keyword]" or "containing [text]"</li>
<li><b>color space</b> - "in rec709" or "in aces color space"</li>
<li><b>status</b> - "with approved status" or "that are pending"</li>
<li><b>type</b> - "video assets" or "image files"</li>
<li><b>tags</b> - "tagged dailies" or "tagged with vfx"</li>
<li><b>missing</b> - "missing media" or "offline files"</li>
</ul>

<h4>Tips:</h4>
<ul>
<li>Use Tab for autocomplete suggestions</li>
<li>Browse command history in the History tab</li>
<li>Save frequently used queries in the Saved tab</li>
<li>Use Up/Down arrows to navigate history</li>
</ul>
"""
        help_text.setHtml(help_content)
        layout.addWidget(help_text)

        widget.setLayout(layout)
        return widget

    def _setup_autocomplete(self):
        """Setup autocomplete for input field."""
        # Get initial suggestions
        suggestions = self.parser.suggest_completions("")

        # Add saved query names
        for query in self.saved_queries.get_all():
            suggestions.append(query.query)

        # Create completer
        self.completer = QCompleter(suggestions)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.input_field.setCompleter(self.completer)

    def _on_input_changed(self, text: str):
        """Handle input text changes for live parsing."""
        if not text:
            self.parsed_label.setText("(enter a command)")
            self.parsed_label.setStyleSheet("color: gray; font-style: italic;")
            return

        # Parse and show interpretation
        try:
            cmd = self.parser.parse(text)
            self.parsed_label.setText(str(cmd))

            # Color based on confidence
            if cmd.confidence > 0.7:
                color = "green"
            elif cmd.confidence > 0.4:
                color = "orange"
            else:
                color = "red"

            self.parsed_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        except Exception as e:
            self.parsed_label.setText(f"Parse error: {e}")
            self.parsed_label.setStyleSheet("color: red;")

        # Update autocomplete suggestions
        suggestions = self.parser.suggest_completions(text)
        model = QStringListModel(suggestions)
        self.completer.setModel(model)

    def _on_execute(self):
        """Execute the command."""
        query = self.input_field.text().strip()
        if not query:
            return

        try:
            # Parse command
            cmd = self.parser.parse(query)

            # Execute command
            result = self.executor.execute(cmd)

            # Store result
            self.current_result = result

            # Add to history
            self.history.add(
                query,
                success=result.success,
                result_count=result.count
            )

            # Display results
            self._display_results(result)

            # Emit signals
            self.command_executed.emit(query, result)
            if result.success and isinstance(result.data, list):
                self.results_ready.emit(result.data)

            # Update history display
            self._update_history_display()

            logger.info(f"Executed: {query} -> {result.count} results")

        except Exception as e:
            logger.error(f"Execution error: {e}")
            QMessageBox.critical(
                self,
                "Execution Error",
                f"Failed to execute command:\n{e}"
            )

    def _display_results(self, result: ExecutionResult):
        """Display execution results."""
        # Update count label
        if result.success:
            self.result_count_label.setText(result.message)
            self.result_count_label.setStyleSheet("color: green;")
        else:
            self.result_count_label.setText(f"Error: {result.error}")
            self.result_count_label.setStyleSheet("color: red;")
            return

        # Clear previous results
        self.results_table.setRowCount(0)
        self.results_text.clear()

        # Display in table
        if isinstance(result.data, list) and result.data:
            self.results_table.setRowCount(len(result.data))

            for row, item in enumerate(result.data):
                # Handle different data structures
                if isinstance(item, dict):
                    self.results_table.setItem(row, 0, QTableWidgetItem(str(item.get('name', ''))))
                    self.results_table.setItem(row, 1, QTableWidgetItem(str(item.get('type', ''))))
                    self.results_table.setItem(row, 2, QTableWidgetItem(str(item.get('status', ''))))
                    self.results_table.setItem(row, 3, QTableWidgetItem(str(item.get('color_space', ''))))
                    self.results_table.setItem(row, 4, QTableWidgetItem(str(item.get('path', ''))))

        # Display in text view
        text_output = f"{result.message}\n\n"

        if isinstance(result.data, list):
            for item in result.data:
                if isinstance(item, dict):
                    text_output += f"• {item.get('name', 'Unknown')}\n"
                    text_output += f"  Type: {item.get('type', 'N/A')}\n"
                    text_output += f"  Status: {item.get('status', 'N/A')}\n"
                    text_output += f"  Path: {item.get('path', 'N/A')}\n\n"
                else:
                    text_output += f"• {item}\n"

        self.results_text.setPlainText(text_output)

    def _update_history_display(self):
        """Update history display."""
        recent = self.history.get_recent(20)

        history_html = "<table width='100%'>"
        for entry in recent:
            status_icon = "✓" if entry.success else "✗"
            color = "green" if entry.success else "red"

            history_html += f"""
            <tr>
                <td width='20'><span style='color: {color}'>{status_icon}</span></td>
                <td><a href='#' onclick='return false;'>{entry.query}</a></td>
                <td width='40' align='right'>{entry.result_count}</td>
            </tr>
            """

        history_html += "</table>"

        self.history_list.setHtml(history_html)

    def _update_saved_display(self):
        """Update saved queries display."""
        category = self.category_combo.currentText()

        if category == "All":
            queries = self.saved_queries.get_all()
        else:
            queries = self.saved_queries.get_by_category(category)

        saved_html = "<table width='100%'>"
        for query in queries:
            saved_html += f"""
            <tr>
                <td><b><a href='{query.query}'>{query.name}</a></b></td>
            </tr>
            <tr>
                <td><small>{query.description}</small></td>
            </tr>
            <tr><td>&nbsp;</td></tr>
            """

        saved_html += "</table>"

        self.saved_text.setHtml(saved_html)

    def _on_saved_query_clicked(self, url):
        """Handle saved query click."""
        query = url.toString()
        self.input_field.setText(query)
        self._on_execute()

    def _on_save_current_query(self):
        """Save current query."""
        query = self.input_field.text().strip()
        if not query:
            QMessageBox.warning(self, "No Query", "Enter a query first")
            return

        # Get name
        name, ok = QInputDialog.getText(
            self,
            "Save Query",
            "Enter a name for this query:"
        )

        if not ok or not name:
            return

        # Get description
        description, ok = QInputDialog.getText(
            self,
            "Query Description",
            "Enter a description (optional):"
        )

        if not ok:
            description = ""

        # Save
        self.saved_queries.save_query(
            name=name,
            query=query,
            description=description
        )

        self._update_saved_display()

        QMessageBox.information(
            self,
            "Query Saved",
            f"Query saved as '{name}'"
        )

    def _on_clear_history(self):
        """Clear command history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all command history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._update_history_display()

    def _on_import_queries(self):
        """Import saved queries from file."""
        # In full implementation, would use QFileDialog
        QMessageBox.information(
            self,
            "Import",
            "Import functionality would open file dialog"
        )

    def _on_export_queries(self):
        """Export saved queries to file."""
        # In full implementation, would use QFileDialog
        QMessageBox.information(
            self,
            "Export",
            "Export functionality would open file dialog"
        )

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Up/Down arrows for history navigation
        if event.key() == Qt.Key.Key_Up and self.input_field.hasFocus():
            self._navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down and self.input_field.hasFocus():
            self._navigate_history(1)
        else:
            super().keyPressEvent(event)

    def _navigate_history(self, direction: int):
        """Navigate command history with arrow keys."""
        recent = self.history.get_recent(100)
        if not recent:
            return

        self.history_index += direction
        self.history_index = max(-1, min(self.history_index, len(recent) - 1))

        if self.history_index >= 0:
            self.input_field.setText(recent[self.history_index].query)
        else:
            self.input_field.clear()


if not HAS_PYQT6:
    class CommandInterfaceWidget:
        """Stub when PyQt6 not available."""
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is required for CommandInterfaceWidget")
