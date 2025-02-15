from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal
from PySide2 import QtCore, QtGui,QtWidgets
from PySide2.QtWidgets import QApplication,QWidget,QLayout,QDoubleSpinBox,QVBoxLayout,QPushButton,QCheckBox,QRadioButton
import logging


class demoFiltrageOptionsWidget(QtWidgets.QWidget):
    
    def __init__(self):
        super(demoFiltrageOptionsWidget, self).__init__()
        self.initUI()
        
    def initUI(self):   

        ui_file = QFile("lib/widgets/demo_filtrage_options/demoFiltragePBIdealOptions.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.widget = loader.load(ui_file)
        ui_file.close()

        vbox = QVBoxLayout()
        vbox.addWidget(self.widget)
        vbox.addStretch(1)
        self.setLayout(vbox)

        self.LPRB = self.findChild(QRadioButton,"radioButton_4") 
        self.HPRB = self.findChild(QRadioButton,"radioButton_5") 
        self.fc = self.findChild(QDoubleSpinBox,"doubleSpinBox")

