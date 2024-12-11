# File: main.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow,QVBoxLayout,QTabWidget,QApplication,QPushButton,QMessageBox,QLayout,QCheckBox,QComboBox,QLabel, QTableWidget,QWidget,QSpinBox,QDockWidget,QTableWidgetItem,QDateEdit,QLineEdit
from PySide2.QtCore import QFile,Signal,QDateTime,QDate
from PySide2 import QtCore, QtGui

import logging
from lib.widgets.qtLogger import qtLoggingHandler, logWidget
from lib.card.qt_card import qtCard
from lib.widgets.card.cardWidget import cardWidget
# from lib.widgets.cardStatus.cardStatus import cardStatusWidget
# from lib.widgets.hr_options.hrOptions import hrOptionsWidget
from lib.widgets.plotWidget import plotWidget
from lib.widgets.viewerWidget.viewerWidget import viewerWidget
# from lib.widgets.seqPlotWidget import seqPlotWidget
# from lib.sigpro.kalman import kalmanFilter 
# from lib.sigpro.seqAcquisition import seqAcquisition

import numpy as np
from scipy import signal
import gc

class mainWindow(QMainWindow):
    def __init__(self,handler):
        # QMainWindow.__init__(self)
        super(mainWindow, self).__init__()

        mainWidget=QWidget(self)
        self.setCentralWidget(mainWidget)
        self.setWindowTitle("Démo visualisation signaux")

        vbox = QVBoxLayout()
        mainWidget.setLayout(vbox)  

        # card status widget
        self.status = cardWidget()
        dockLeft = QDockWidget("Card status", self)
        dockLeft.setWidget(self.status)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,dockLeft)

        # viewer config widget
        self.param = viewerWidget()
        dockLeft = QDockWidget("Viewer parameters", self)
        dockLeft.setWidget(self.param)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,dockLeft)

        self.status.connectionSet.connect(self.setFe)
        self.status.dataReceivedSig.connect(self.dataReceived)
        self.param.newTWSig.connect(self.updateTW)

        #####
        # Setup GUI
        #####

        self.ch0PlotWidget = plotWidget(1,0.01,['b'],['channel 1'])
        mainWidget.layout().addWidget(self.ch0PlotWidget)

        self.ch1PlotWidget = plotWidget(1,0.01,['b'],['channel 2'])
        mainWidget.layout().addWidget(self.ch1PlotWidget)

    def updateTW(self,TW):
        self.ch0PlotWidget.updateTW(TW/1000)
        self.ch1PlotWidget.updateTW(TW/1000)

    def setFe(self,fe):
        self.ch0PlotWidget.setFe(fe)
        self.ch1PlotWidget.setFe(fe)

    def dataReceived(self,ch0,ch1):
        self.ch0PlotWidget.addDataArray([ch0])
        self.ch1PlotWidget.addDataArray([ch1])

    def closeEvent(self,event):
        self.status.stopCard()
        event.accept()

if __name__ == "__main__":  

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler = qtLoggingHandler()
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] [%(threadName)-30.30s]   %(message)s")
    handler.setFormatter(log_formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    os.environ['KMP_DUPLICATE_LIB_OK']='True'

    app = QApplication(sys.argv)

    """
    # GO GO GO
    """
    mW = mainWindow(handler)
    mW.show()
    sys.exit(app.exec_())

