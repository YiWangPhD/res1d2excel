"""Native PySide6 specification editor."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import spec_model


GREEN_BUTTON_STYLE = (
    "QPushButton[softGreen='true'] {"
    "min-width: 92px;"
    "padding: 7px 12px;"
    "color: #102418;"
    "border: 1px solid #6ba875;"
    "border-radius: 4px;"
    "background: #bfe8c4;"
    "}"
    "QPushButton[softGreen='true']:hover { background: #a9dcaf; }"
    "QPushButton[softGreen='true']:pressed { background: #8fcb98; }"
)


def mark_green_button(button: QPushButton) -> QPushButton:
    button.setProperty("softGreen", True)
    button.setStyleSheet(GREEN_BUTTON_STYLE)
    return button


class CollapsibleSection(QWidget):
    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QToolButton()
        self.button.setText(title)
        self.button.setCheckable(True)
        self.button.setChecked(False)
        self.button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.button.setArrowType(Qt.ArrowType.RightArrow)
        self.button.clicked.connect(self._toggle)

        self.content = QLabel(text)
        self.content.setWordWrap(True)
        self.content.setVisible(False)
        self.content.setContentsMargins(18, 6, 6, 12)

        layout.addWidget(self.button)
        layout.addWidget(self.content)

    def _toggle(self) -> None:
        expanded = self.button.isChecked()
        self.button.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.content.setVisible(expanded)


class TableTab(QWidget):
    changed = Signal()

    def __init__(self, name: str, columns: list[str], rows: list[dict[str, Any]]) -> None:
        super().__init__()
        self.name = name
        self.columns = columns
        self.rows = copy.deepcopy(rows)
        self.selected_row = -1
        self.inputs: dict[str, QLineEdit] = {}
        self._updating = False

        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        for column in columns:
            edit = QLineEdit()
            edit.editingFinished.connect(self._form_editing_finished)
            self.inputs[column] = edit
            self.form.addRow(column, edit)
        layout.addLayout(self.form)

        buttons = QHBoxLayout()
        add_button = mark_green_button(QPushButton("Add Row"))
        add_button.clicked.connect(self.add_row)
        copy_button = mark_green_button(QPushButton("Copy Row"))
        copy_button.clicked.connect(self.copy_row)
        delete_button = mark_green_button(QPushButton("Delete Row"))
        delete_button.clicked.connect(self.delete_row)
        pick_button = mark_green_button(QPushButton("Pick File"))
        pick_button.clicked.connect(self.pick_file)
        pick_button.setVisible(name == "res1d_files")

        buttons.addWidget(add_button)
        buttons.addWidget(copy_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(pick_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.cellClicked.connect(self._cell_clicked)
        layout.addWidget(self.table)

        self.refresh_table()

    def data(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self.rows)

    def add_row(self) -> None:
        row = {column: "" for column in self.columns}
        if self.name == "res1d_files":
            row["result_type"] = "network"
        if "chainage" in row:
            row["chainage"] = 0
        self.rows.append(row)
        self.selected_row = len(self.rows) - 1
        self.refresh_table()
        self._fill_form(row)
        self.changed.emit()

    def copy_row(self) -> None:
        if self.selected_row < 0:
            return
        self.rows.insert(self.selected_row + 1, copy.deepcopy(self.rows[self.selected_row]))
        self.selected_row += 1
        self.refresh_table()
        self.changed.emit()

    def delete_row(self) -> None:
        if self.selected_row < 0:
            return
        del self.rows[self.selected_row]
        self.selected_row = -1
        self.refresh_table()
        self._fill_form({})
        self.changed.emit()

    def pick_file(self) -> None:
        if self.name != "res1d_files":
            return
        if self.selected_row < 0:
            self.add_row()
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select result file",
            str(Path.cwd()),
            "Result files (*.res1d *.res *.resx *.whr);;All files (*.*)",
        )
        if path:
            self.rows[self.selected_row]["res1d_file_path"] = path
            if not self.rows[self.selected_row].get("short_name"):
                self.rows[self.selected_row]["short_name"] = Path(path).stem
            self.refresh_table()
            self._fill_form(self.rows[self.selected_row])
            self.changed.emit()

    def refresh_table(self) -> None:
        self._updating = True
        self.table.setRowCount(len(self.rows))
        for row_index, row in enumerate(self.rows):
            for column_index, column in enumerate(self.columns):
                value = row.get(column)
                item = QTableWidgetItem("" if value is None else str(value))
                self.table.setItem(row_index, column_index, item)
        if 0 <= self.selected_row < len(self.rows):
            self.table.selectRow(self.selected_row)
        self._updating = False

    def _cell_clicked(self, row: int, _column: int) -> None:
        if self._updating:
            return
        self.selected_row = row
        self.table.selectRow(row)
        self._fill_form(self.rows[row])

    def _selection_changed(self) -> None:
        if self._updating:
            return
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            self.selected_row = indexes[0].row()
        else:
            self.selected_row = self.table.currentRow()
        self._fill_form(self.rows[self.selected_row] if self.selected_row >= 0 else {})

    def _fill_form(self, row: dict[str, Any]) -> None:
        self._updating = True
        for column, edit in self.inputs.items():
            value = row.get(column, "")
            edit.setText("" if value is None else str(value))
        self._updating = False

    def _form_editing_finished(self) -> None:
        if self._updating or self.selected_row < 0:
            return
        for column, edit in self.inputs.items():
            self.rows[self.selected_row][column] = edit.text()
        self.refresh_table()
        self.changed.emit()


class OutputTab(QWidget):
    changed = Signal()

    def __init__(self, output: dict[str, Any]) -> None:
        super().__init__()
        self._updating = False
        self.output = copy.deepcopy(spec_model.OUTPUT_DEFAULTS)
        self.output.update(output or {})

        layout = QFormLayout(self)
        self.folder_edit = QLineEdit()
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_edit)
        browse = mark_green_button(QPushButton("Browse"))
        browse.clicked.connect(self.pick_folder)
        folder_row.addWidget(browse)
        layout.addRow("output_folder", folder_row)

        self.resample_edit = QLineEdit()
        self.skip_edit = QLineEdit()
        self.trunc_edit = QLineEdit()
        layout.addRow("resample_interval", self.resample_edit)
        layout.addRow("skip_time", self.skip_edit)
        layout.addRow("trunc_time", self.trunc_edit)

        self.html_check = QCheckBox()
        self.by_element_check = QCheckBox()
        self.by_file_check = QCheckBox()
        self.stats_check = QCheckBox()
        layout.addRow("to_html", self.html_check)
        layout.addRow("export_by_element", self.by_element_check)
        layout.addRow("export_by_result_file", self.by_file_check)
        layout.addRow("export_statistics", self.stats_check)

        for widget in [self.folder_edit, self.resample_edit, self.skip_edit, self.trunc_edit]:
            widget.textChanged.connect(self._changed)
        for widget in [self.html_check, self.by_element_check, self.by_file_check, self.stats_check]:
            widget.stateChanged.connect(self._changed)
        self._fill()

    def data(self) -> dict[str, Any]:
        return copy.deepcopy(self.output)

    def pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder", self.folder_edit.text())
        if folder:
            self.folder_edit.setText(folder)

    def _fill(self) -> None:
        self._updating = True
        self.folder_edit.setText(str(self.output.get("output_folder") or ""))
        self.resample_edit.setText(str(self.output.get("resample_interval") or ""))
        self.skip_edit.setText(str(self.output.get("skip_time") or ""))
        self.trunc_edit.setText(str(self.output.get("trunc_time") or ""))
        self.html_check.setChecked(bool(self.output.get("to_html")))
        self.by_element_check.setChecked(bool(self.output.get("export_by_element")))
        self.by_file_check.setChecked(bool(self.output.get("export_by_result_file")))
        self.stats_check.setChecked(bool(self.output.get("export_statistics")))
        self._updating = False

    def _changed(self) -> None:
        if self._updating:
            return
        self.output = {
            "output_folder": self.folder_edit.text(),
            "resample_interval": self.resample_edit.text() or None,
            "skip_time": self.skip_edit.text() or None,
            "trunc_time": self.trunc_edit.text() or None,
            "to_html": self.html_check.isChecked(),
            "export_by_element": self.by_element_check.isChecked(),
            "export_by_result_file": self.by_file_check.isChecked(),
            "export_statistics": self.stats_check.isChecked(),
        }
        self.changed.emit()


class CombinedTab(QWidget):
    changed = Signal()

    def __init__(self, spec: dict[str, Any]) -> None:
        super().__init__()
        self.spec = spec
        self.combined = copy.deepcopy(spec.get("combined", []))
        self.selected_index = -1
        self._updating = False

        layout = QVBoxLayout(self)

        editor_layout = QGridLayout()
        editor_layout.addWidget(QLabel("Alias"), 0, 0)
        self.alias_edit = QLineEdit()
        self.alias_edit.editingFinished.connect(self._alias_editing_finished)
        editor_layout.addWidget(self.alias_edit, 0, 1)
        editor_layout.addWidget(QLabel("Quantity"), 1, 0)
        editor_layout.addWidget(QLabel("CalculatedDischarge"), 1, 1)
        layout.addLayout(editor_layout)

        terms_header = QHBoxLayout()
        terms_header.addWidget(QLabel("Terms"))
        terms_header.addStretch(1)
        self.add_term_button = QPushButton("Add Term")
        self.add_term_button.clicked.connect(self.add_term)
        terms_header.addWidget(self.add_term_button)
        layout.addLayout(terms_header)

        self.terms_table = QTableWidget(0, 4)
        self.terms_table.setHorizontalHeaderLabels(["Operator", "Source", "Alias", "Actions"])
        self.terms_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.terms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.terms_table.setMaximumHeight(180)
        layout.addWidget(self.terms_table)

        add_button = QPushButton("Add Combined Item")
        add_button.clicked.connect(self.add_item)
        layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Alias", "Quantity", "Terms", "Actions"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.table)
        self.refresh_table()
        self.refresh_editor()

    def update_source_spec(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.refresh_editor()

    def data(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self.combined)

    def add_item(self) -> None:
        self.combined.append({
            "alias": self._next_combined_alias(),
            "quantity": "CalculatedDischarge",
            "terms": [{"op": "+", "source": "node", "alias": ""}],
        })
        self.selected_index = len(self.combined) - 1
        self.refresh_table()
        self.refresh_editor()
        self.changed.emit()

    def _next_combined_alias(self) -> str:
        existing = {
            str(item.get("alias") or "").strip()
            for item in self.combined
        }
        index = len(self.combined) + 1
        while f"combined{index}" in existing:
            index += 1
        return f"combined{index}"

    def delete_item(self, index: int) -> None:
        del self.combined[index]
        if self.combined:
            self.selected_index = min(index, len(self.combined) - 1)
        else:
            self.selected_index = -1
        self.refresh_table()
        self.refresh_editor()
        self.changed.emit()

    def refresh_table(self) -> None:
        self._updating = True
        self.table.setRowCount(len(self.combined))
        for index, item in enumerate(self.combined):
            terms = " ".join(
                f"{term.get('op', '+')} {term.get('source', '')}.{term.get('alias', '')}"
                for term in item.get("terms", [])
            )
            for column, value in enumerate([
                item.get("alias", ""),
                "CalculatedDischarge",
                terms,
            ]):
                self.table.setItem(index, column, QTableWidgetItem(value))
            delete = QPushButton("Delete")
            delete.clicked.connect(lambda _checked=False, i=index: self.delete_item(i))
            self.table.setCellWidget(index, 3, delete)
        if 0 <= self.selected_index < len(self.combined):
            self.table.selectRow(self.selected_index)
        self._updating = False

    def refresh_editor(self) -> None:
        self._updating = True
        if self.selected_index < 0 or self.selected_index >= len(self.combined):
            self.alias_edit.clear()
            self.alias_edit.setEnabled(False)
            self.add_term_button.setEnabled(False)
            self.terms_table.setRowCount(0)
            self._updating = False
            return

        item = self.combined[self.selected_index]
        self.alias_edit.setEnabled(True)
        self.add_term_button.setEnabled(True)
        self.alias_edit.setText(str(item.get("alias") or ""))
        self.refresh_terms_table()
        self._updating = False

    def refresh_terms_table(self) -> None:
        self.terms_table.setRowCount(0)
        if self.selected_index < 0 or self.selected_index >= len(self.combined):
            return

        terms = self.combined[self.selected_index].setdefault("terms", [])
        self.terms_table.setRowCount(len(terms))
        for term_index, term in enumerate(terms):
            self.terms_table.setCellWidget(term_index, 0, self._operator_combo(term_index, term))
            self.terms_table.setCellWidget(term_index, 1, self._source_combo(term_index, term))
            self.terms_table.setCellWidget(term_index, 2, self._alias_combo(term_index, term))
            delete = QPushButton("Delete Term")
            delete.clicked.connect(lambda _checked=False, i=term_index: self.delete_term(i))
            self.terms_table.setCellWidget(term_index, 3, delete)

    def _operator_combo(self, term_index: int, term: dict[str, Any]) -> QComboBox:
        op = QComboBox()
        op.addItems(["+", "-"])
        op.setCurrentText(term.get("op", "+"))
        op.currentTextChanged.connect(lambda value, i=term_index: self.update_term(i, "op", value))
        return op

    def _source_combo(self, term_index: int, term: dict[str, Any]) -> QComboBox:
        source = QComboBox()
        source.addItems(spec_model.COMBINED_SOURCES)
        source.setCurrentText(term.get("source", "node"))
        source.currentTextChanged.connect(lambda value, i=term_index: self.change_term_source(i, value))
        return source

    def _alias_combo(self, term_index: int, term: dict[str, Any]) -> QComboBox:
        alias = QComboBox()
        alias.addItem("")
        alias.addItems(self._aliases_for_source(term.get("source", "node")))
        alias.setCurrentText(term.get("alias", ""))
        alias.currentTextChanged.connect(lambda value, i=term_index: self.update_term(i, "alias", value))
        return alias

    def _aliases_for_source(self, source: str) -> list[str]:
        rows = self.spec.get(source, [])
        return sorted(str(row.get("alias")) for row in rows if row.get("alias"))

    def _selection_changed(self) -> None:
        if self._updating:
            return
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            self.selected_index = indexes[0].row()
        else:
            self.selected_index = self.table.currentRow()
        self.refresh_editor()

    def _alias_editing_finished(self) -> None:
        if self._updating or self.selected_index < 0:
            return
        self.combined[self.selected_index]["alias"] = self.alias_edit.text()
        self.combined[self.selected_index]["quantity"] = "CalculatedDischarge"
        self.refresh_table()
        self.changed.emit()

    def add_term(self) -> None:
        if self.selected_index < 0:
            return
        self.combined[self.selected_index].setdefault("terms", []).append({
            "op": "+",
            "source": "node",
            "alias": "",
        })
        self.refresh_editor()
        self.refresh_table()
        self.changed.emit()

    def delete_term(self, index: int) -> None:
        if self.selected_index < 0:
            return
        del self.combined[self.selected_index]["terms"][index]
        self.refresh_editor()
        self.refresh_table()
        self.changed.emit()

    def change_term_source(self, index: int, source: str) -> None:
        if self._updating or self.selected_index < 0:
            return
        self.combined[self.selected_index]["terms"][index]["source"] = source
        self.combined[self.selected_index]["terms"][index]["alias"] = ""
        self.refresh_editor()
        self.refresh_table()
        self.changed.emit()

    def update_term(self, index: int, field: str, value: str) -> None:
        if self._updating or self.selected_index < 0:
            return
        self.combined[self.selected_index]["terms"][index][field] = value
        self.refresh_table()
        self.changed.emit()


class SpecificationEditorWindow(QWidget):
    spec_changed = Signal(dict, object)

    def __init__(self, spec: dict[str, Any] | None = None, source_path: str | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Specification Editor")
        self.resize(1100, 760)
        self.spec = spec_model.normalize_spec(spec)
        self.source_path = source_path
        self.tabs_by_name: dict[str, QWidget] = {}
        self._updating = False

        self._build_layout()
        self._emit_change()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        load_button = mark_green_button(QPushButton("Load JSON/XLSX"))
        load_button.clicked.connect(self.load_file)
        clear_button = mark_green_button(QPushButton("Clear All"))
        clear_button.clicked.connect(self.clear_all)
        save_button = mark_green_button(QPushButton("Save JSON"))
        save_button.clicked.connect(self.save_json)
        close_button = mark_green_button(QPushButton("Close"))
        close_button.clicked.connect(self.close)

        toolbar.addWidget(load_button)
        toolbar.addWidget(clear_button)
        toolbar.addWidget(save_button)
        toolbar.addStretch(1)
        toolbar.addWidget(close_button)
        layout.addLayout(toolbar)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._create_tabs()

    def _create_tabs(self) -> None:
        self.tabs.clear()
        self.tabs_by_name.clear()
        instructions = self._instructions_tab()
        self.tabs.addTab(instructions, "Instructions")

        for name in spec_model.ELEMENT_TYPES:
            tab = TableTab(name, spec_model.ELEMENT_SCHEMAS[name], self.spec[name])
            tab.changed.connect(self._tab_changed)
            self.tabs_by_name[name] = tab
            self.tabs.addTab(tab, name)

        combined = CombinedTab(self.spec)
        combined.changed.connect(self._tab_changed)
        self.tabs_by_name["combined"] = combined
        self.tabs.addTab(combined, "combined")

        output = OutputTab(self.spec["output_files"])
        output.changed.connect(self._tab_changed)
        self.tabs_by_name["output_files"] = output
        self.tabs.addTab(output, "output_files")

        res1d = TableTab("res1d_files", spec_model.ELEMENT_SCHEMAS["res1d_files"], self.spec["res1d_files"])
        res1d.changed.connect(self._tab_changed)
        self.tabs_by_name["res1d_files"] = res1d
        self.tabs.addTab(res1d, "res1d_files")

    def _instructions_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        for title, text in instruction_sections():
            layout.addWidget(CollapsibleSection(title, text))
        layout.addStretch(1)
        scroll.setWidget(content)
        return scroll

    def load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load specification",
            str(Path.cwd()),
            "Specification files (*.json *.xlsx);;JSON files (*.json);;Excel files (*.xlsx)",
        )
        if not path:
            return
        try:
            self.spec = spec_model.load_spec(path)
        except Exception as exc:
            QMessageBox.critical(self, "Load Failed", str(exc))
            return
        self.source_path = path
        self._create_tabs()
        self._emit_change()

    def clear_all(self) -> None:
        self.spec = spec_model.empty_spec()
        self.source_path = None
        self._create_tabs()
        self._emit_change()

    def save_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save specification JSON",
            str(Path.cwd() / "res1d2excel_spec.json"),
            "JSON files (*.json)",
        )
        if not path:
            return
        self._pull_spec_from_tabs()
        try:
            saved = spec_model.save_spec_to_json(self.spec, path)
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))
            return
        self.source_path = str(saved)
        self._emit_change()

    def _tab_changed(self) -> None:
        if self._updating:
            return
        self._pull_spec_from_tabs()
        combined = self.tabs_by_name.get("combined")
        if isinstance(combined, CombinedTab):
            combined.update_source_spec(self.spec)
        self._emit_change()

    def _pull_spec_from_tabs(self) -> None:
        for name in spec_model.ELEMENT_TYPES:
            tab = self.tabs_by_name.get(name)
            if isinstance(tab, TableTab):
                self.spec[name] = tab.data()

        combined = self.tabs_by_name.get("combined")
        if isinstance(combined, CombinedTab):
            self.spec["combined"] = combined.data()

        output = self.tabs_by_name.get("output_files")
        if isinstance(output, OutputTab):
            self.spec["output_files"] = output.data()

        res1d = self.tabs_by_name.get("res1d_files")
        if isinstance(res1d, TableTab):
            self.spec["res1d_files"] = res1d.data()

        self.spec = spec_model.normalize_spec(self.spec)

    def _emit_change(self) -> None:
        self.spec_changed.emit(copy.deepcopy(self.spec), self.source_path)


def instruction_sections() -> list[tuple[str, str]]:
    return [
        ("0. Environment Required", "Python 3.13 or above with pandas, numpy, mikeio1d, pythonnet, openpyxl, plotly, and PySide6."),
        ("1. Generate Templates", "Run res1d2excel without an input file to create res1d2excel_template.xlsx and res1d2excel_template.json."),
        ("2. Run With Input", "Run res1d2excel with one .xlsx or .json specification file, or use the main GUI Run button."),
        ("3. Element Inputs", "Each element row needs quantity and muid. Alias is optional unless the row will be used in a combined item. Link and regulation rows also support chainage."),
        ("4. Result Files", "Use result_type values such as network or runoff. Short names should be unique within a result type."),
        ("5. Output Files", "Choose an output folder and select at least one output: by element, by result file, statistics, or HTML plots."),
        ("6. Combined Items", "Combined items define CalculatedDischarge equations from aliases in other element tabs. Terms use + or - operators."),
        ("7. EPANET", "Use network for EPANET .res, .resx, and .whr files. For .res files, keep the matching .inp beside the result file."),
    ]
