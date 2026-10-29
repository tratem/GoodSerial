from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
                             QComboBox, QVBoxLayout, QPushButton, QHBoxLayout)
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo

BAUD_RATES = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

DATA_BITS = {"5": QSerialPort.DataBits.Data5, "6": QSerialPort.DataBits.Data6,
             "7": QSerialPort.DataBits.Data7, "8": QSerialPort.DataBits.Data8}
PARITY = {"None": QSerialPort.Parity.NoParity, "Even": QSerialPort.Parity.EvenParity,
          "Odd": QSerialPort.Parity.OddParity, "Space": QSerialPort.Parity.SpaceParity,
          "Mark": QSerialPort.Parity.MarkParity}
STOP_BITS = {"1": QSerialPort.StopBits.OneStop, "1.5": QSerialPort.StopBits.OneAndHalfStop,
             "2": QSerialPort.StopBits.TwoStop}
FLOW_CONTROL = {"None": QSerialPort.FlowControl.NoFlowControl,
                "Hardware (RTS/CTS)": QSerialPort.FlowControl.HardwareControl,
                "Software (XON/XOFF)": QSerialPort.FlowControl.SoftwareControl}


def default_serial_config():
    return {"alias": "", "port": None, "baud": 115200, "data_bits": "8",
            "parity": "None", "stop_bits": "1", "flow": "None"}


class SerialPropertiesDialog(QDialog):
    """Serial (UART) port settings for one terminal."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminal Properties")
        self.setMinimumWidth(360)

        self.alias_edit = QLineEdit(config["alias"])
        self.alias_edit.setPlaceholderText("Terminal")

        self.port_combo = QComboBox()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: self._refresh_ports(self.port_combo.currentText()))
        port_row = QHBoxLayout()
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(refresh_button)
        self._refresh_ports(config["port"])

        self.baud_combo = QComboBox()
        self.baud_combo.setEditable(True)
        self.baud_combo.addItems([str(b) for b in BAUD_RATES])
        self.baud_combo.setCurrentText(str(config["baud"]))

        self.data_bits_combo = self._combo(DATA_BITS, config["data_bits"])
        self.parity_combo = self._combo(PARITY, config["parity"])
        self.stop_bits_combo = self._combo(STOP_BITS, config["stop_bits"])
        self.flow_combo = self._combo(FLOW_CONTROL, config["flow"])

        form = QFormLayout()
        form.addRow("Alias:", self.alias_edit)
        form.addRow("Port:", port_row)
        form.addRow("Baud rate:", self.baud_combo)
        form.addRow("Data bits:", self.data_bits_combo)
        form.addRow("Parity:", self.parity_combo)
        form.addRow("Stop bits:", self.stop_bits_combo)
        form.addRow("Flow control (handshake):", self.flow_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @staticmethod
    def _combo(options, current):
        combo = QComboBox()
        combo.addItems(list(options))
        combo.setCurrentText(current)
        return combo

    def _refresh_ports(self, selected):
        self.port_combo.clear()
        self.port_combo.addItems([p.portName() for p in QSerialPortInfo.availablePorts()])
        if selected:
            if self.port_combo.findText(selected) < 0:
                self.port_combo.addItem(selected)
            self.port_combo.setCurrentText(selected)

    def _accept(self):
        if not self.port_combo.currentText() or not self.baud_combo.currentText().strip().isdigit():
            self.port_combo.setFocus()
            return
        self.accept()

    def get_config(self):
        return {"alias": self.alias_edit.text().strip(),
                "port": self.port_combo.currentText(),
                "baud": int(self.baud_combo.currentText()),
                "data_bits": self.data_bits_combo.currentText(),
                "parity": self.parity_combo.currentText(),
                "stop_bits": self.stop_bits_combo.currentText(),
                "flow": self.flow_combo.currentText()}
