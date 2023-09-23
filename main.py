from PySide6 import QtCore, QtWidgets, QtGui
import sys, time
from pyModbusTCP.client import ModbusClient


# Worker to handle communication with modbus server
class Worker(QtCore.QObject):
    # signals
    modbus_data = QtCore.Signal(list)
    modbus_status = QtCore.Signal(int)

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent=parent)
        self.host = "10.6.129.81"
        self.port = 502
        self.unit_id = 1
        self.auto_open = False
        self.auto_close = False
        self.running = False
        self.response = None
        self.modbus_master = None

    @QtCore.Slot(int, int, str, int)
    def modbus_connect(self, slave_id, slave_scan_rate, host, port):
        self.unit_id = int(slave_id)
        self.host = str(host)
        self.port = int(port)
        if not self.modbus_master:
            print("Connecting to Modbus Server...", self.host, self.port)
            self.modbus_master = ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                                              auto_open=self.auto_open, auto_close=self.auto_close)
            QtCore.QThread.sleep(2)

            if self.modbus_master.open():
                print("Connected to Modbus Server!")
                self.running = True
                self.modbus_status.emit(1)
            else:
                print("Connection to Modbus Server Failed!")
                self.modbus_master = None
                self.modbus_status.emit(0)

    @QtCore.Slot()
    def disconnect(self):
        if self.running:
            print("Closing Modbus Server Connection!")
            self.running = False
            self.modbus_master.close()
            self.modbus_master = None
            self.modbus_status.emit(2)

    @QtCore.Slot(int, int, str)
    def read_registers(self, start_address, no_registers, function_code):
        # while self.running:
        print(start_address)
        print(no_registers)
        print(function_code)
        if self.running:
            # Choose function code
            if function_code == "Read Holding Registers (0x03)":
                self.response = self.modbus_master.read_holding_registers(start_address, no_registers)
            elif function_code == "Read Discrete Inputs (0x02)":
                self.response = self.modbus_master.read_discrete_inputs(start_address, no_registers)
            elif function_code == "Read Input Registers (0x04)":
                self.response = self.modbus_master.read_input_registers(start_address, no_registers)

            if self.response:
                print(self.response)
                self.modbus_data.emit(self.response)
                self.modbus_status.emit(5)
            else:
                print("read error")
                self.modbus_status.emit(4)
            time.sleep(2)


# Main window class
class ModbusMaster(QtWidgets.QMainWindow):
    stop_signal = QtCore.Signal()
    connect_signal = QtCore.Signal(int, int, str, int)
    read_signal = QtCore.Signal(int, int, str)

    def __init__(self):
        super().__init__()

        self.address = "10.6.129.81"
        self.port = 502

        # main window
        self.setWindowTitle("Modbus Master")
        self.setGeometry(100, 100, 500, 200)

        # main widget layout
        self.layout_main = QtWidgets.QFormLayout()

        # Main widget
        self.main_window = QtWidgets.QWidget(self)
        self.main_window.setLayout(self.layout_main)

        # Thread
        self.thread = QtCore.QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        # self.thread.started.connect(self.worker.connect) # when thread starts, start worker
        # self.thread.finished.connect(self.worker.stop) # when thread finishes, stop worker
        # self.stop_signal.connect(self.worker.stop)
        self.connect_signal.connect(self.worker.modbus_connect)
        self.read_signal.connect(self.worker.read_registers)
        self.worker.modbus_data.connect(self.modbus_data_handler)
        self.worker.modbus_status.connect(self.modbus_status_handler)
        self.thread.start()

        # modbus connection and read buttons
        self.button_layout = QtWidgets.QHBoxLayout(self)
        self.button_group = QtWidgets.QGroupBox()
        self.button_group.setLayout(self.button_layout)
        self.btn_start = QtWidgets.QPushButton("Connect")
        self.btn_stop = QtWidgets.QPushButton("Disconnect")
        self.btn_read = QtWidgets.QPushButton("Read")

        # initial button states
        self.btn_read.setDisabled(True)
        self.btn_stop.setDisabled(True)

        self.button_layout.addWidget(self.btn_start)
        self.button_layout.addWidget(self.btn_stop)
        self.button_layout.addWidget(self.btn_read)
        self.button_layout.addStretch()

        # connect slots to buttons
        self.btn_start.clicked.connect(self.connect_modbus)
        self.btn_stop.clicked.connect(self.fill_reg_table)
        self.btn_stop.clicked.connect(self.worker.disconnect)
        self.btn_read.clicked.connect(self.fill_reg_table)
        self.btn_read.clicked.connect(self.read_registers)

        # Main window elements
        self.slave_properties = SlaveProperties()
        self.modbus_request = ModbusRequest()
        self.modbus_request.no_of_registers.valueChanged.connect(self.draw_registers)
        self.modbus_registers = ModbusRegisters()

        # Registers table - Start with one cell
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(1)
        self.table.setRowCount(1)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.setRowHeight(0, 30)
        self.table.setColumnWidth(0, 30)
        self.table.setItem(0, 0, QtWidgets.QTableWidgetItem('-/-'))

        # Modbus status message
        self.modbus_status_message = QtWidgets.QLabel()
        self.modbus_status_message.setHidden(True)

        # add components to main window layout
        self.layout_main.addWidget(self.modbus_status_message)
        self.layout_main.addWidget(self.slave_properties)
        self.layout_main.addWidget(self.modbus_request)
        self.layout_main.addWidget(self.table)

        # add main widget to main window
        self.setCentralWidget(self.main_window)

        # menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        edit_menu = menu_bar.addMenu('&Edit')
        setting_menu = menu_bar.addMenu('&Settings')
        view_menu = menu_bar.addMenu('&View')
        help_menu = menu_bar.addMenu('&Help')

        # exit menu item
        exit_action = QtGui.QAction('&Exit', self)
        exit_action.setStatusTip('Exit')
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.quit)
        file_menu.addAction(exit_action)

        # settings menu item
        settings_action = QtGui.QAction('&Slave Settings', self)
        settings_action.setStatusTip('Set Server')
        settings_action.setShortcut('Alt+F1')
        settings_action.triggered.connect(self.open_dialog)
        setting_menu.addAction(settings_action)

        # toolbar
        toolbar = QtWidgets.QToolBar('Main ToolBar')
        self.addToolBar(toolbar)
        toolbar.setIconSize(QtCore.QSize(16, 16))

        toolbar.addWidget(self.btn_start)
        toolbar.addSeparator()
        toolbar.addWidget(self.btn_stop)
        toolbar.addSeparator()
        toolbar.addWidget(self.btn_read)

        # toolbar.addAction(settings_action)
        # toolbar.addAction(settings_action)
        # toolbar.addAction(settings_action)
        # toolbar.addSeparator()

        # toolbar.addAction(settings_action)
        # toolbar.addAction(settings_action)
        # toolbar.addSeparator()
        # toolbar.addAction(exit_action)

        # status bar
        self.status_bar = self.statusBar()

        # add a permanent widgets to the status bar
        self.data_length = 0
        self.character_count = QtWidgets.QLabel("Length: " + str(self.data_length))
        self.statusbar_address_text = "TCP: " + self.address + ":" + str(self.port)
        self.server_address_port = QtWidgets.QLabel(self.statusbar_address_text)
        self.status_bar.addWidget(self.server_address_port)
        self.status_bar.addPermanentWidget(self.character_count)

        # settings dialog
        self.settings_dialog = SettingsDialog()
        self.settings_dialog.settings_signal.connect(self.save_server_settings)

    # update address and port on ok button in settings dialog
    @QtCore.Slot(str, str)
    def save_server_settings(self, address, port):
        self.address = address
        self.port = int(port)
        self.statusbar_address_text = "TCP: " + self.address + ":" + str(self.port)
        self.server_address_port.setText(self.statusbar_address_text)

    # exit action
    def quit(self):
        self.thread.quit()
        self.worker.deleteLater()
        self.thread.deleteLater()
        self.destroy(sys.exit(1))

    # Open settings dialog
    def open_dialog(self):
        self.settings_dialog.exec()

    @QtCore.Slot()
    def connect_modbus(self):
        slave_id = self.slave_properties.slave_address_selector.value()
        slave_scan_rate = self.slave_properties.slave_scan_rate.value()
        self.connect_signal.emit(slave_id, slave_scan_rate, self.address, self.port)

    @QtCore.Slot()
    def read_registers(self):
        start_address = self.modbus_request.start_adddress.value()
        number_of_registers = self.modbus_request.no_of_registers.value()
        function_code = self.modbus_request.func_code_select.currentText()
        print("Selected Function code ", function_code)
        self.read_signal.emit(start_address, number_of_registers, function_code)

    @QtCore.Slot(list)
    def modbus_data_handler(self, data):
        self.data_length = len(data)
        self.character_count = QtWidgets.QLabel("Length: " + str(self.data_length))
        i = 0
        j = 0
        for reg in data:
            self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(reg)))
            j = j + 1

            if j > 9:
                i = i + 1
                j = 0

    @QtCore.Slot(int)
    def draw_registers(self, registers):
        print(registers)
        if registers % 10 == 0:
            i = registers / 10
        else:
            i = registers / 10 + 1

        self.table.setRowCount(i)
        self.table.setColumnCount(10)
        self.fill_reg_table()

    @QtCore.Slot(int)
    def modbus_status_handler(self, enum):
        if enum == 1:
            self.modbus_status_message.setVisible(False)
            self.btn_start.setDisabled(True)
            self.btn_stop.setDisabled(False)
            self.btn_read.setDisabled(False)
        elif enum == 2:
            self.btn_start.setDisabled(False)
            self.btn_stop.setDisabled(True)
            self.btn_read.setDisabled(True)
        elif enum == 0:
            self.modbus_status_message.setText("Could not connect to Modbus Server")
            self.modbus_status_message.setStyleSheet("QLabel { background-color : red; color : white; }")
            self.modbus_status_message.setVisible(True)
        elif enum == 4:
            self.modbus_status_message.setVisible(True)
            self.modbus_status_message.setText("Error Reading Registers")
        elif enum == 5:
            self.modbus_status_message.setVisible(False)

    def fill_reg_table(self):
        rows = self.table.rowCount()
        columns = self.table.columnCount()
        for i in range(rows):
            for j in range(columns):
                self.table.setRowHeight(i, 30)
                self.table.setColumnWidth(j, 30)
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem('-/-'))


class SlaveProperties(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SlaveProperties, self).__init__(parent)

        # group layout
        self.layout = QtWidgets.QHBoxLayout()

        # add widgets to groupbox 1 layout
        self.slave_address_label = QtWidgets.QLabel("Slave Address", alignment=QtCore.Qt.AlignLeft)
        self.slave_address_selector = QtWidgets.QSpinBox(minimum=1, maximum=100, value=1, alignment=QtCore.Qt.AlignLeft)
        self.slave_scan_rate_label = QtWidgets.QLabel("Scan Rate (ms)")
        self.slave_scan_rate = QtWidgets.QSpinBox(minimum=1000, maximum=10000, value=1000, singleStep=1000)
        self.layout.addWidget(self.slave_address_label)
        self.layout.addWidget(self.slave_address_selector)
        self.layout.addWidget(self.slave_scan_rate_label)
        self.layout.addWidget(self.slave_scan_rate)
        # self.layout.addWidget(self.button)
        self.layout.addStretch()

        # groupbox 1
        self.group = QtWidgets.QGroupBox()
        self.group.setTitle('&Slave Properties')
        self.group.setLayout(self.layout)

        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.addWidget(self.group)


class ModbusRequest(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ModbusRequest, self).__init__(parent)

        # modbus requests layout
        # self.modbus_request = QtWidgets.QGridLayout()
        self.modbus_request = QtWidgets.QHBoxLayout()

        self.func_code_label = QtWidgets.QLabel("Function Code")
        self.func_code_select = QtWidgets.QComboBox()

        self.func_code_select.addItem("Read Holding Registers (0x03)")
        self.func_code_select.addItem("Read Discrete Inputs (0x02)")
        self.func_code_select.addItem("Read Input Registers (0x04)")
        self.func_code_select.addItem("Read Coils (0x01)")

        self.start_address_label = QtWidgets.QLabel("Start Address")
        self.start_adddress = QtWidgets.QSpinBox(minimum=0, maximum=100, value=0, alignment=QtCore.Qt.AlignLeft)

        self.no_of_registers_label = QtWidgets.QLabel("Number of Registers")
        self.no_of_registers = QtWidgets.QSpinBox(minimum=1, maximum=100, value=1, alignment=QtCore.Qt.AlignLeft)

        self.modbus_request.addWidget(self.func_code_label, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.modbus_request.addWidget(self.func_code_select, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.modbus_request.addWidget(self.start_address_label, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.modbus_request.addWidget(self.start_adddress, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.modbus_request.addWidget(self.no_of_registers_label, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.modbus_request.addWidget(self.no_of_registers, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.modbus_request.addStretch()

        # modbus request group box
        self.modbus_request_group = QtWidgets.QGroupBox("Modbus Requests")
        self.modbus_request_group.setLayout(self.modbus_request)

        self.lay = QtWidgets.QHBoxLayout(self)
        self.lay.addWidget(self.modbus_request_group)

# not in use
class ModbusRegisters(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ModbusRegisters, self).__init__(parent)
        # registers layout
        self.register_layout = QtWidgets.QGridLayout()
        # registers group
        self.registers_group = QtWidgets.QGroupBox()
        self.registers_group.setLayout(self.register_layout)
        self.registers_group.resize(200, 50)

        # generate registers
        self.registers = []
        for i in range(1, 100):
            reg = QtWidgets.QLineEdit(placeholderText='-/-', )
            reg.setReadOnly(True)
            reg.setFixedWidth(40)
            reg.setFixedHeight(40)
            self.registers.append(reg)

        self.register_layout.addWidget(self.registers[0], 0, 0)
        self.lay = QtWidgets.QHBoxLayout(self)
        self.lay.addWidget(self.registers_group)


class SettingsDialog(QtWidgets.QDialog):
    settings_signal = QtCore.Signal(str, str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings!")

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.accepted.connect(self.slave_settings)
        # Create widgets
        self.server_label = QtWidgets.QLabel("Server Address")
        self.server = QtWidgets.QLineEdit("10.6.129.81")
        self.server.setInputMask("000.000.000.000")
        self.port_label = QtWidgets.QLabel("Server Port")
        self.port = QtWidgets.QLineEdit("502")

        # Create layout and add widgets
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.server_label, 0, 0)
        layout.addWidget(self.server, 0, 1)
        layout.addWidget(self.port_label, 1, 0)
        layout.addWidget(self.port, 1, 1)

        layout.addWidget(self.buttonBox, 2, 0, 1, 2)
        # Set dialog layout
        self.setLayout(layout)

    def slave_settings(self):
        print(self.server.text())
        print(self.port.text())
        self.settings_signal.emit(self.server.text(), self.port.text())


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    modbusWidget = ModbusMaster()
    modbusWidget.show()
    modbusWidget.resize(800, 300)
    sys.exit(app.exec())