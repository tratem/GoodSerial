from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QCheckBox,
                             QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog)


def default_logging_config():
    return {"enabled": False, "file": "", "append": True, "timestamp": True}


class LoggingConfigDialog(QDialog):
    """Logging settings for one terminal."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logging Configuration")
        self.setMinimumWidth(420)

        self.enabled_check = QCheckBox("Enable logging")
        self.enabled_check.setChecked(config["enabled"])

        self.file_edit = QLineEdit(config["file"])
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_button)

        self.append_check = QCheckBox("Append to existing file")
        self.append_check.setChecked(config["append"])
        self.timestamp_check = QCheckBox("Prefix each line with a timestamp")
        self.timestamp_check.setChecked(config["timestamp"])

        form = QFormLayout()
        form.addRow(self.enabled_check)
        form.addRow("Log file:", file_row)
        form.addRow(self.append_check)
        form.addRow(self.timestamp_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(self, "Log file", self.file_edit.text(),
                                              "Log files (*.log *.txt);;All files (*)")
        if path:
            self.file_edit.setText(path)

    def _accept(self):
        if self.enabled_check.isChecked() and not self.file_edit.text().strip():
            self._browse()
            if not self.file_edit.text().strip():
                return
        self.accept()

    def get_config(self):
        return {"enabled": self.enabled_check.isChecked(),
                "file": self.file_edit.text().strip(),
                "append": self.append_check.isChecked(),
                "timestamp": self.timestamp_check.isChecked()}
