from PyQt6.QtWidgets import QDialog

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Preferences")
        self.setMinimumSize(500, 200)