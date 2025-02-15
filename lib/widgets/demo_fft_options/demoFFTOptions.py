from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal
from PySide2 import QtCore, QtGui,QtWidgets
from PySide2.QtWidgets import QApplication,QWidget,QLayout,QDoubleSpinBox,QVBoxLayout,QSpinBox,QCheckBox
import logging


class demoFFTOptionsWidget(QtWidgets.QWidget):
    
    def __init__(self):
        super(demoFFTOptionsWidget, self).__init__()
        self.initUI()
        
    def initUI(self):   

        ui_file = QFile("lib/widgets/demo_fft_options/demoFFTOptions.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.widget = loader.load(ui_file)
        ui_file.close()

        vbox = QVBoxLayout()
        vbox.addWidget(self.widget)
        vbox.addStretch(1)
        self.setLayout(vbox)

        self.tw = self.findChild(QSpinBox,"spinBox")

