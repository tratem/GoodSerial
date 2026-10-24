from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QMenuBar, QFrame, QLabel, QSplitter, QPlainTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal

from CustomWidgets.custom_widgets import *
from gui.help_dialog import HelpDialog
from gui.preferences_dialog import PreferencesDialog

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

        # Window 1 (Always active)
        self.window1 = WindowPanel("Terminal", "#f5f6fa")
        self.splitter.addWidget(self.window1)

        # References for Window 2 and Window 3 (initially None)
        self.window2 = None
        self.window3 = None

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
        
    def _add_terminal_window(self):
        terminal_window = WindowPanel("Terminal", "#f5f6fa")
        terminal_window.delete_requested.connect(lambda title: self._remove_terminal_window(title))
        if self.window2 is None:
            self.window2 = terminal_window
            self.splitter.addWidget(self.window2)
            
        elif self.window3 is None:
            self.window3 = terminal_window
            self.splitter.addWidget(terminal_window)
            
            self.add_window_button.hide()

    def _remove_terminal_window(self, title):
        if self.window2 and self.window2.get_window_title() == title:
            self.splitter.widget(self.splitter.indexOf(self.window2)).setParent(None)
            self.window2 = None
        elif self.window3 and self.window3.get_window_title() == title:
            self.splitter.widget(self.splitter.indexOf(self.window3)).setParent(None)
            self.window3 = None
        self.add_window_button.show()
            
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
        event.accept()
        
class WindowPanel(QFrame):
    """A custom widget representing one of the windows/panels."""
    delete_requested = pyqtSignal(str)  # Signal emitted when the delete button is clicked
    
    def __init__(self, title, background_color):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            background-color: {background_color}; 
            border: 1px solid #dcdde1; 
            border-radius: 6px;
        """)
        
        layout = QVBoxLayout(self)
        
        # Panel Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #2f3640; border: none;")
        layout.addWidget(self.title_label)
        
        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        layout.addWidget(self.terminal_output)
    
    def set_window_title(self, title):
        self.title_label.setText(title)
        
    def get_window_title(self):
        return self.title_label.text()
    
    def set_window_background_color(self, background_color):
        self.setStyleSheet(f"""
            background-color: {background_color}; 
            border: 1px solid #dcdde1; 
            border-radius: 6px;
        """)