from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal
from PySide2 import QtCore, QtGui,QtWidgets
from PySide2.QtWidgets import QRadioButton,QApplication,QWidget,QLayout,QDoubleSpinBox,QVBoxLayout,QSpinBox,QCheckBox
import logging


class td1OptionsWidget(QtWidgets.QWidget):
    
    currentModeChanged = QtCore.Signal(int)
    pauseChanged = QtCore.Signal(int)
    coeffChanged = QtCore.Signal(float)

    def __init__(self):
        super(td1OptionsWidget, self).__init__()
        self.initUI()
        
    def initUI(self):   

        ui_file = QFile("lib/widgets/td1_options/td1Options.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.widget = loader.load(ui_file)
        ui_file.close()

        vbox = QVBoxLayout()
        vbox.addWidget(self.widget)
        vbox.addStretch(1)
        self.setLayout(vbox)

        self.changePauseStatut() # init pauseStatus value
        self.changeCurrentMode() # init currentMode value
        self.changeFilterIndex() # init coeffFilter value

        self.findChild(QCheckBox,"checkBox").stateChanged.connect(self.changePauseStatut)
        self.findChild(QRadioButton,"radioButton").clicked.connect(self.changeCurrentMode)
        self.findChild(QRadioButton,"radioButton_2").clicked.connect(self.changeCurrentMode)
        self.findChild(QRadioButton,"radioButton_3").clicked.connect(self.changeCurrentMode)
        self.findChild(QDoubleSpinBox,"doubleSpinBox").valueChanged.connect(self.changeFilterIndex)

    def changePauseStatut(self):
        self.pauseStatus = not self.findChild(QCheckBox,"checkBox").isChecked() 
        self.pauseChanged.emit(self.pauseStatus)

    def changeCurrentMode(self):

        self.currentMode = 0
        if (self.findChild(QRadioButton,"radioButton").isChecked()):
            self.currentMode = 0
        if (self.findChild(QRadioButton,"radioButton_2").isChecked()):
            self.currentMode = 1
        if (self.findChild(QRadioButton,"radioButton_3").isChecked()):
            self.currentMode = 2

        self.currentModeChanged.emit(self.currentMode)

    def changeFilterIndex(self):
        self.coeffFilter = self.findChild(QDoubleSpinBox,"doubleSpinBox").value()
        self.coeffChanged.emit(self.coeffFilter)