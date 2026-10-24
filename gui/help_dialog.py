from PyQt6.QtWidgets import QDialog

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Help")
        self.setMinimumSize(500, 200)