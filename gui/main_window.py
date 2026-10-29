from datetime import datetime

from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy,
                             QMenuBar, QFrame, QLabel, QSplitter, QPlainTextEdit, QMenu,
                             QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtSerialPort import QSerialPort

from CustomWidgets.custom_widgets import *
from gui.help_dialog import HelpDialog
from gui.preferences_dialog import PreferencesDialog
from gui.serial_dialog import (SerialPropertiesDialog, default_serial_config,
                               DATA_BITS, PARITY, STOP_BITS, FLOW_CONTROL)
from gui.logging_dialog import LoggingConfigDialog, default_logging_config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoodSerialTerminal")
        self.setMinimumSize(800, 500)

        self._create_menu_bar()        
        self._setup_ui()

    def _setup_ui(self):
        # 1. QMainWindow needs a central widget container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        self.panels = []
        self._add_panel()

        # --- Add Terminal Button ---
        self.add_window_button = CustomButton("+")
        self.add_window_button.setToolTip("Add Terminal")
        self.add_window_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.add_window_button.clicked.connect(self._add_terminal_window)
        main_layout.addWidget(self.add_window_button)
    
    def _create_menu_bar(self):
        ''' Create menu bar '''
        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #F7F7F7;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 12px;
            }
            QMenuBar::item:selected {
                background: #D0D0D0;  /* light gray hover */
                color: black;
                border-radius: 4px;
                border: 2px solid #D0D0D0;
            }
            QMenu {
                background-color: #F7F7F7;
            }
            QMenu::item {
                background: transparent;
                padding: 4px 24px;
            }
            QMenu::item:selected {
                background: #D6EAF8;  /* light blue hover in dropdown */
                color: black;
            }
        """)

        # Create File menu
        file_menu = menu_bar.addMenu("File")
        
        # Create Setting menu
        settings_menu = menu_bar.addMenu("Settings")

        preferences_action = settings_menu.addAction("Preferences")
        preferences_action.triggered.connect(self._show_preferences)

        # Create Help menu
        help_action = menu_bar.addAction("Help")
        help_action.triggered.connect(self._show_help)

        self.setMenuBar(menu_bar)
        
    MAX_PANELS = 3

    PANEL_COLORS = ["#f5f6fa", "#e8f4fd", "#fdf2e3", "#eaf7ea"]

    def _add_panel(self):
        # Pick the first color not used by an open panel
        used = {p.background_color for p in self.panels}
        color = next((c for c in self.PANEL_COLORS if c not in used), self.PANEL_COLORS[0])
        panel = WindowPanel("Terminal", color)
        panel.delete_requested.connect(self._remove_terminal_window)
        self.panels.append(panel)
        self.splitter.addWidget(panel)

    def _add_terminal_window(self):
        if len(self.panels) < self.MAX_PANELS:
            self._add_panel()
        self.add_window_button.setVisible(len(self.panels) < self.MAX_PANELS)

    def _remove_terminal_window(self, panel):
        if panel in self.panels:
            self.panels.remove(panel)
            panel.shutdown()
            panel.setParent(None)
            panel.deleteLater()
        self.add_window_button.setVisible(len(self.panels) < self.MAX_PANELS)

    def _show_preferences(self):
        '''Show preferences dialog or message box'''
        settings_dialog = PreferencesDialog(self)
        settings_dialog.exec()

    def _show_help(self):
        '''Show help dialog or message box'''
        help_dialog = HelpDialog(self)
        help_dialog.exec()
    
    def closeEvent(self, event):
        '''Handle any cleanup before the window is closed'''
        for panel in self.panels:
            panel.shutdown()
        event.accept()

class WindowPanel(QFrame):
    """A custom widget representing one of the windows/panels."""
    delete_requested = pyqtSignal(object)  # Emitted with this panel when its close button is clicked

    def __init__(self, title, background_color):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            background-color: {background_color}; 
            border: 1px solid #dcdde1; 
            border-radius: 6px;
        """)
        
        self.default_title = title
        self.background_color = background_color
        self.serial_config = default_serial_config()
        self.logging_config = default_logging_config()
        self.serial = QSerialPort(self)
        self.serial.readyRead.connect(self._on_ready_read)
        self.serial.errorOccurred.connect(self._on_serial_error)
        self._log_file = None
        self._log_buffer = ""

        layout = QVBoxLayout(self)

        # Panel title with close button
        header = QHBoxLayout()
        header.addSpacing(24)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #2f3640; border: none;")
        header.addWidget(self.title_label, 1, Qt.AlignmentFlag.AlignCenter)
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setToolTip("Close terminal")
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setStyleSheet("""
            QPushButton { border: none; background: transparent; color: #636e72; font-size: 14px; }
            QPushButton:hover { background: #e84118; color: white; border-radius: 4px; }
        """)
        self.close_button.clicked.connect(lambda: self.delete_requested.emit(self))
        header.addWidget(self.close_button)
        layout.addLayout(header)

        # Connection status (port, baud rate, connected, logging)
        self.port = None
        self.baud_rate = None
        self.connected = False
        self.logging = False
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 12px; color: #636e72; border: none;")
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self._update_status_label()

        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        # Let right clicks reach the panel's own context menu
        self.terminal_output.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        layout.addWidget(self.terminal_output)

    # ---- context menu ----
    def contextMenuEvent(self, event):
        menu = QMenu(self.window())
        menu.setStyleSheet("""
            QMenu { background-color: #F7F7F7; border: 1px solid #b2bec3; }
            QMenu::item { padding: 4px 24px; color: black; }
            QMenu::item:selected { background: #D6EAF8; }
            QMenu::separator { height: 1px; background: #b2bec3; margin: 4px 0; }
        """)
        if self.connected:
            menu.addAction("Disconnect").triggered.connect(self.disconnect_port)
        else:
            menu.addAction("Connect").triggered.connect(self.connect_port)
        menu.addAction("Reconnect").triggered.connect(self.reconnect_port)
        menu.addSeparator()
        menu.addAction("Clear window").triggered.connect(self.clear_window)
        menu.addSeparator()
        menu.addAction("Logging...").triggered.connect(self.show_logging_config)
        menu.addSeparator()
        menu.addAction("Properties...").triggered.connect(self.show_properties)
        menu.exec(event.globalPos())

    # ---- actions ----
    def connect_port(self):
        if self.connected:
            return
        # Not configured yet: ask for the port settings first
        if not self.serial_config["port"] and not self.show_properties(reconnect=False):
            return
        cfg = self.serial_config
        self.serial.setPortName(cfg["port"])
        self.serial.setBaudRate(cfg["baud"])
        self.serial.setDataBits(DATA_BITS[cfg["data_bits"]])
        self.serial.setParity(PARITY[cfg["parity"]])
        self.serial.setStopBits(STOP_BITS[cfg["stop_bits"]])
        self.serial.setFlowControl(FLOW_CONTROL[cfg["flow"]])
        if self.serial.open(QSerialPort.OpenModeFlag.ReadWrite):
            self.connected = True
            self._append_system(f"Connected to {cfg['port']} @ {cfg['baud']} baud")
        else:
            QMessageBox.warning(self.window(), "Connection failed",
                                f"Could not open {cfg['port']}:\n{self.serial.errorString()}")
        self._refresh_status()

    def disconnect_port(self):
        was_connected = self.connected
        if self.serial.isOpen():
            self.serial.close()
        self.connected = False
        if was_connected:
            self._append_system(f"Disconnected from {self.serial_config['port']}")
        self._refresh_status()

    def reconnect_port(self):
        self.disconnect_port()
        self.connect_port()

    def clear_window(self):
        self.terminal_output.clear()

    def show_properties(self, reconnect=True):
        """Open the serial properties dialog. Returns True if accepted."""
        dialog = SerialPropertiesDialog(self.serial_config, self.window())
        if dialog.exec() != dialog.DialogCode.Accepted:
            return False
        self.serial_config = dialog.get_config()
        if reconnect and self.connected:
            self.reconnect_port()
        else:
            self._refresh_status()
        return True

    def show_logging_config(self):
        dialog = LoggingConfigDialog(self.logging_config, self.window())
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self.logging_config = dialog.get_config()
        self._close_log()
        if self.logging_config["enabled"]:
            self._open_log()
        self._refresh_status()

    # ---- serial / logging internals ----
    def _on_ready_read(self):
        text = bytes(self.serial.readAll()).decode("utf-8", errors="replace")
        self.terminal_output.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal_output.insertPlainText(text.replace("\r\n", "\n").replace("\r", "\n"))
        self.terminal_output.ensureCursorVisible()
        if self._log_file:
            self._log_text(text)

    def _on_serial_error(self, error):
        if error == QSerialPort.SerialPortError.ResourceError:  # device unplugged
            self.disconnect_port()
            self._append_system("Connection lost")

    def _append_system(self, message):
        self.terminal_output.appendPlainText(f"[{message}]")

    def _open_log(self):
        try:
            self._log_file = open(self.logging_config["file"],
                                  "a" if self.logging_config["append"] else "w", encoding="utf-8")
        except OSError as e:
            self._log_file = None
            QMessageBox.warning(self.window(), "Logging failed", f"Could not open log file:\n{e}")

    def _close_log(self):
        if self._log_file:
            self._log_file.close()
        self._log_file = None
        self._log_buffer = ""

    def _log_text(self, text):
        if not self.logging_config["timestamp"]:
            self._log_file.write(text)
        else:
            self._log_buffer += text.replace("\r\n", "\n").replace("\r", "\n")
            *lines, self._log_buffer = self._log_buffer.split("\n")
            for line in lines:
                stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                self._log_file.write(f"[{stamp}] {line}\n")
        self._log_file.flush()

    def shutdown(self):
        self.disconnect_port()
        self._close_log()

    def _refresh_status(self):
        cfg = self.serial_config
        self.set_window_title(cfg["alias"] or self.default_title)
        self.set_connection_info(cfg["port"], cfg["baud"] if cfg["port"] else None,
                                 self.connected, self._log_file is not None)

    def set_window_title(self, title):
        self.title_label.setText(title)
        
    def get_window_title(self):
        return self.title_label.text()

    def set_connection_info(self, port=None, baud_rate=None, connected=False, logging=False):
        self.port = port
        self.baud_rate = baud_rate
        self.connected = connected
        self.logging = logging
        self._update_status_label()

    def _update_status_label(self):
        port = self.port or "No port"
        baud = f"{self.baud_rate} baud" if self.baud_rate else "- baud"
        state = "Connected" if self.connected else "Disconnected"
        log = "Logging" if self.logging else "Not logging"
        self.status_label.setText(f"{port}  |  {baud}  |  {state}  |  {log}")
    
    def set_window_background_color(self, background_color):
        self.background_color = background_color
        self.setStyleSheet(f"""
            background-color: {background_color}; 
            border: 1px solid #dcdde1; 
            border-radius: 6px;
        """)