import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow,QVBoxLayout,QHBoxLayout,QTabWidget,QApplication,QPushButton,QMessageBox,QLayout,QCheckBox,QComboBox,QLabel, QTableWidget,QWidget,QSpinBox,QDockWidget,QTableWidgetItem,QDateEdit,QLineEdit
from PySide2.QtCore import QFile,Signal,QDateTime,QDate,QTimer
from PySide2 import QtCore, QtGui

import logging
from lib.widgets.qtLogger import qtLoggingHandler, logWidget
from lib.widgets.plotWidget import plotWidget
from lib.widgets.seqPlotWidget import seqPlotWidget
from lib.sigpro.seqAcquisition import seqAcquisition
from lib.sigpro.liveFilter import LiveLFilter
from lib.widgets.card.cardWidget import cardWidget


import math
import numpy as np
from scipy import signal

class mainWindow(QMainWindow):
    def __init__(self,handler):
        # QMainWindow.__init__(self)
        super(mainWindow, self).__init__()  
        
        mainWidget=QWidget(self)
        self.setCentralWidget(mainWidget)
        self.setWindowTitle("FILTRAGE")

        vbox = QVBoxLayout()
        mainWidget.setLayout(vbox)  

        ################
        # Add the card status widget to interface
        ################
        self.status = cardWidget()
        dockLeft = QDockWidget("Card status", self)
        dockLeft.setWidget(self.status)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,dockLeft)

        self.status.connectionSet.connect(self.setFe)
        self.status.dataReceivedSig.connect(self.dataReceived)

        ################
        # init counter for time tracking
        ################
        self.nbDataReceived = 0
        self.fe = 10000

        ################
        # Set up GUI for data display
        ################
        wid = QWidget()
        vbox = QHBoxLayout()
        wid.setLayout(vbox)  

        duree_affichage=1
        # self.ch0PlotWidget = plotWidget(duree_affichage,1.0 / self.fe,['b'],['x'])
        # self.ch1PlotWidget = plotWidget(duree_affichage,1.0 / self.fe,['b'],['xf'])
        self.PlotWidget = plotWidget(duree_affichage,1.0 / self.fe,['b','r'],['x','xf'])

        wid.layout().addWidget(self.PlotWidget)
        # wid.layout().addWidget(self.ch0PlotWidget)
        # wid.layout().addWidget(self.ch1PlotWidget)
        mainWidget.layout().addWidget(wid)

        ################
        # Signal processing parameters
        ################
        # time window length in seconds (for FFT analysis)
        self.TWLength = 1

        # # time window
        # self.seqCutter = seqAcquisition(self.seqReceived,self.TWLength,1.0,self.fe,3)

        # init filter
        self.filter_b = signal.firwin2(201, [0,200,400,600,800,self.fe/2],[0,0,1,1,0,0],fs=self.fe)
        self.filter_a = np.array([1])
        self.f = LiveLFilter(self.filter_b,self.filter_a)

    # called when sampling frequence is defined from card interface
    def setFe(self,Fe):
        self.fe = Fe
        # self.ch0PlotWidget.setFe(Fe)
        # self.ch1PlotWidget.setFe(Fe)
        self.PlotWidget.setFe(Fe)



    #############
    # data related functions
    #############
    def dataReceived(self,ch0,ch1):
       # filter signals
        fV = [0] * len(ch0)
        for (ic,v) in enumerate(ch0):
            fV[ic] = self.f.process(v)
        
       
        # plot signals
        self.PlotWidget.addDataArray([ch0,fV])
        # self.ch0PlotWidget.addDataArray([ch0])
        # self.ch1PlotWidget.addDataArray([fV])

        # compute time
        tps = [(k+self.nbDataReceived) * 1.0/self.fe for k in range(len(ch0))]
        self.nbDataReceived = self.nbDataReceived + len(ch0)



if __name__ == "__main__":

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

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



