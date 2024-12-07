from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal
from PySide2 import QtCore, QtGui,QtWidgets
from PySide2.QtWidgets import QSpinBox,QApplication,QWidget,QLayout,QLabel,QVBoxLayout,QComboBox,QPushButton
import logging
from lib.card.card_io import listSerialPort,findSerialPort,cardAcqui
import time 

class viewerWidget(QtWidgets.QWidget):
    
    newTWSig = QtCore.Signal(float)

    def __init__(self):
        super(viewerWidget, self).__init__()
        self.initUI()
        
    def initUI(self):   

        ui_file = QFile("lib/widgets/viewerWidget/viewerWidget.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.widget = loader.load(ui_file)
        ui_file.close()

        vbox = QVBoxLayout()
        vbox.addWidget(self.widget)
        vbox.addStretch(1)
        self.setLayout(vbox)

        self.card = None
        self.setupGUI()

    def setupGUI(self):
        self.findChild(QPushButton,"pushButton_2").clicked.connect(self.changeTimeWindow)

    def changeTimeWindow(self):
        self.newTWSig.emit( self.findChild(QSpinBox,"spinBox").value() )
