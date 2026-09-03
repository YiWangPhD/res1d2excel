"""PySide6 desktop launcher for res1d2excel."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import spec_model
from .spec_editor import SpecificationEditorWindow


MIN_PYTHON = (3, 13)
REQUIRED_IMPORTS = [
    "pandas",
    "numpy",
    "mikeio1d",
    "clr",
    "openpyxl",
    "plotly",
    "res1d2excel",
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("res1d2excel")
        self.resize(900, 620)
        self.process: QProcess | None = None
        self.current_spec: dict | None = None
        self.spec_source_path: str | None = None
        self.spec_editor: SpecificationEditorWindow | None = None

        self.python_edit = QLineEdit(sys.executable)
        self.input_edit = QLineEdit()
        self.status_label = QLabel("Environment not validated")
        self.status_label.setObjectName("statusLabel")

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log.setFont(QFont("Consolas", 10))

        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)

        self._build_layout()
        self._connect_signals()

    def _build_layout(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QGridLayout()
        form.setColumnStretch(1, 1)

        form.addWidget(QLabel("Python environment"), 0, 0)
        form.addWidget(self.python_edit, 0, 1)

        python_buttons = QHBoxLayout()
        browse_python = QPushButton("Browse")
        browse_python.clicked.connect(self.browse_python)
        validate_python = QPushButton("Validate")
        validate_python.clicked.connect(self.validate_environment)
        python_buttons.addWidget(browse_python)
        python_buttons.addWidget(validate_python)
        form.addLayout(python_buttons, 0, 2)

        form.addWidget(QLabel("Input file"), 1, 0)
        form.addWidget(self.input_edit, 1, 1)
        browse_input = QPushButton("Browse")
        browse_input.clicked.connect(self.browse_input)
        form.addWidget(browse_input, 1, 2)

        form.addWidget(QLabel("Status"), 2, 0)
        form.addWidget(self.status_label, 2, 1, 1, 2)
        layout.addLayout(form)

        actions = QHBoxLayout()
        spec_editor_button = QPushButton("Edit Specifications")
        spec_editor_button.clicked.connect(self.open_spec_editor)
        template_button = QPushButton("Create Template")
        template_button.clicked.connect(self.create_template)
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.log.clear)

        self.run_button.clicked.connect(self.run_conversion)
        self.cancel_button.clicked.connect(self.cancel_run)

        actions.addWidget(self.run_button)
        actions.addWidget(self.cancel_button)
        actions.addWidget(spec_editor_button)
        actions.addWidget(template_button)
        actions.addStretch(1)
        actions.addWidget(clear_button)
        layout.addLayout(actions)

        self.log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.log)

        root.setStyleSheet(
            """
            QLabel { font-size: 12px; }
            QLineEdit, QPlainTextEdit {
                border: 1px solid #b8bec8;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton {
                min-width: 96px;
                padding: 7px 12px;
                color: #102418;
                border: 1px solid #6ba875;
                border-radius: 4px;
                background: #bfe8c4;
            }
            QPushButton:hover { background: #a9dcaf; }
            QPushButton:pressed { background: #8fcb98; }
            QPushButton:disabled {
                color: #68746b;
                border-color: #9ba79e;
                background: #d7ded8;
            }
            #statusLabel { color: #344054; }
            """
        )
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self.python_edit.textChanged.connect(self._mark_environment_unvalidated)

    def _mark_environment_unvalidated(self) -> None:
        self.status_label.setText("Environment not validated")

    def browse_python(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python executable",
            str(Path(sys.executable).parent),
            "Python executable (python.exe pythonw.exe);;All files (*.*)",
        )
        if path:
            self.python_edit.setText(path)

    def browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select res1d2excel input file",
            os.getcwd(),
            "Input files (*.xlsx *.json);;Excel files (*.xlsx);;JSON files (*.json)",
        )
        if path:
            self.current_spec = None
            self.spec_source_path = path
            self.input_edit.setText(path)

    def open_spec_editor(self) -> None:
        if self.spec_editor is not None:
            self.spec_editor.raise_()
            self.spec_editor.activateWindow()
            return

        spec = self.current_spec
        source_path = self.spec_source_path
        input_path = self.input_edit.text().strip()
        if spec is None and input_path and Path(input_path).is_file():
            try:
                spec = spec_model.load_spec(input_path)
                source_path = input_path
            except Exception as exc:
                QMessageBox.warning(self, "Load Failed", str(exc))
                spec = None
                source_path = None

        self.spec_editor = SpecificationEditorWindow(spec, source_path)
        self.spec_editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.spec_editor.spec_changed.connect(self.receive_spec_from_editor)
        self.spec_editor.destroyed.connect(lambda _obj=None: self._spec_editor_closed())
        self.spec_editor.show()

    def receive_spec_from_editor(self, spec: dict, source_path: object) -> None:
        self.current_spec = spec_model.normalize_spec(spec)
        self.spec_source_path = str(source_path) if source_path else None
        if self.spec_source_path:
            self.input_edit.setText(f"Using edited specification from {self.spec_source_path}")
        else:
            self.input_edit.setText("Using edited in-memory specification")
        self._set_status("Edited specification ready", ok=True)

    def _spec_editor_closed(self) -> None:
        self.spec_editor = None

    def validate_environment(self) -> None:
        python = self.python_edit.text().strip()
        if not python:
            self._set_status("Select a Python executable first", ok=False)
            return

        code = (
            "import importlib.util, sys; "
            f"min_version={MIN_PYTHON!r}; "
            f"mods={REQUIRED_IMPORTS!r}; "
            "print(sys.version.split()[0]); "
            "missing=[m for m in mods if importlib.util.find_spec(m) is None]; "
            "print('missing=' + ','.join(missing) if missing else 'missing='); "
            "raise SystemExit("
            "2 if sys.version_info[:2] < min_version else "
            "3 if missing else 0"
            ")"
        )
        process = QProcess(self)
        process.start(python, ["-c", code])
        if not process.waitForFinished(15000):
            process.kill()
            self._set_status("Validation timed out", ok=False)
            return

        stdout = bytes(process.readAllStandardOutput()).decode(errors="replace").strip()
        stderr = bytes(process.readAllStandardError()).decode(errors="replace").strip()
        exit_code = process.exitCode()
        stdout_lines = stdout.splitlines()
        version = stdout_lines[0] if stdout_lines else "?"
        missing = ""
        if len(stdout_lines) > 1 and stdout_lines[1].startswith("missing="):
            missing = stdout_lines[1].removeprefix("missing=")

        if exit_code == 0:
            self._set_status(f"Ready: Python {version}", ok=True)
        elif exit_code == 2:
            self._set_status(f"Python {version} is too old; need 3.13+", ok=False)
        elif exit_code == 3:
            self._set_status(
                f"Missing required packages: {missing}" if missing
                else "Missing required packages in selected environment",
                ok=False,
            )
        else:
            self._set_status("Validation failed", ok=False)

        if stderr:
            self.append_log(stderr)

    def run_conversion(self) -> None:
        if self.current_spec is not None:
            errors = spec_model.validate_spec(self.current_spec)
            if errors:
                QMessageBox.warning(
                    self,
                    "Specification Issues",
                    "\n".join(errors[:10]) + ("\n..." if len(errors) > 10 else ""),
                )
                return
            run_path = spec_model.timestamped_json_path(self.spec_source_path)
            try:
                spec_model.save_spec_to_json(self.current_spec, run_path)
            except Exception as exc:
                QMessageBox.critical(self, "Save Failed", str(exc))
                return
            self.append_log(f"Saved edited specification to {run_path}")
            self._start_package_process([str(run_path)])
            return

        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "Input Required", "Select a .xlsx or .json input file first.")
            return
        if not Path(input_path).is_file():
            QMessageBox.warning(self, "Input Not Found", "The selected input file does not exist.")
            return
        self._start_package_process([input_path])

    def create_template(self) -> None:
        self._start_package_process([])

    def _start_package_process(self, package_args: list[str]) -> None:
        if self.process is not None:
            return

        python = self.python_edit.text().strip()
        if not python:
            QMessageBox.warning(self, "Python Required", "Select a Python executable first.")
            return

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_process_output)
        self.process.finished.connect(self._process_finished)

        args = ["-m", "res1d2excel", *package_args]
        self.append_log("")
        self.append_log(f"> {python} {' '.join(args)}")

        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.process.start(python, args)

        if not self.process.waitForStarted(5000):
            self.append_log("Failed to start process.")
            self._reset_process_buttons()
            self.process = None

    def _read_process_output(self) -> None:
        if self.process is None:
            return
        output = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
        if output:
            self.append_log(output.rstrip())

    def _process_finished(self, exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        if self.process is not None:
            self._read_process_output()
        self.append_log(f"Process finished with exit code {exit_code}.")
        self._reset_process_buttons()
        self.process = None

    def cancel_run(self) -> None:
        if self.process is None:
            return
        self.append_log("Cancel requested.")
        self.process.terminate()
        if not self.process.waitForFinished(5000):
            self.process.kill()

    def _reset_process_buttons(self) -> None:
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def _set_status(self, text: str, ok: bool) -> None:
        color = "#087443" if ok else "#b42318"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(text)

    def append_log(self, text: str) -> None:
        self.log.appendPlainText(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.process is not None:
            reply = QMessageBox.question(
                self,
                "Run In Progress",
                "A run is still active. Cancel it and close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.cancel_run()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("res1d2excel")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
