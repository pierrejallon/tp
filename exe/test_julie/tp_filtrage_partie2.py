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
        self.ch0PlotWidget = plotWidget(duree_affichage,1.0 / self.fe,['b'],['x'])
        self.ch1PlotWidget = plotWidget(duree_affichage,1.0 / self.fe,['b'],['xf'])
        # self.PlotWidget = plotWidget(duree_affichage,1.0 / self.fe,['b','r'],['x','xf'])

        # wid.layout().addWidget(self.PlotWidget)
        wid.layout().addWidget(self.ch0PlotWidget)
        wid.layout().addWidget(self.ch1PlotWidget)
        mainWidget.layout().addWidget(wid)

        ################
        # Signal processing parameters
        ################
        # time window length in seconds (for FFT analysis)
        self.TWLength = 1

        # # time window
        # self.seqCutter = seqAcquisition(self.seqReceived,self.TWLength,1.0,self.fe,3)

        # init filter
        self.filter_b1 = signal.firwin2(201, [0,200,400,600,800,self.fe/2],[0,0,1,1,0,0],fs=self.fe)
        self.filter_a1 = np.array([1])
        self.f1 = LiveLFilter(self.filter_b1,self.filter_a1)

        # init filter
        self.filter_b2 = signal.firwin2(201, [0,600,800,1200,1400,self.fe/2],[0,0,1,1,0,0],fs=self.fe)
        self.filter_a2 = np.array([1])
        self.f2 = LiveLFilter(self.filter_b2,self.filter_a2)

        # init filter
        self.filter_b3 = signal.firwin2(201, [0,200,300,self.fe/2],[1,1,0,0],fs=self.fe)
        self.filter_a3 = np.array([1])
        self.f3 = LiveLFilter(self.filter_b3,self.filter_a3)



    # called when sampling frequence is defined from card interface
    def setFe(self,Fe):
        self.fe = Fe
        self.ch0PlotWidget.setFe(Fe)
        self.ch1PlotWidget.setFe(Fe)
        # self.PlotWidget.setFe(Fe)



    #############
    # data related functions
    #############
    def dataReceived(self,ch0,ch1):
       # filter signals
        fV1 = [0] * len(ch0)
        fV2 = [0] * len(ch0)
        RfV2 = [0] * len(ch0)        
        fRfV2 = [0] * len(ch0)        
        sortie = [0] * len(ch0)        
        for (ic,v) in enumerate(ch0):
            fV1[ic] = self.f1.process(v)
            fV2[ic] = self.f2.process(v)
            RfV2[ic]=np.abs(fV2[ic])
            fRfV2[ic] = self.f3.process(RfV2[ic])
            if fRfV2[ic]>0.02:
                sortie[ic]=-5
            else :
                sortie[ic]=5



        # plot signals
        # self.PlotWidget.addDataArray([ch0,fV1])
        self.ch0PlotWidget.addDataArray([ch0])
        self.ch1PlotWidget.addDataArray([fRfV2])

        # compute time
        tps = [(k+self.nbDataReceived) * 1.0/self.fe for k in range(len(ch0))]
        self.nbDataReceived = self.nbDataReceived + len(ch0)

        # send data : 
        # filtered signal fV is sent to output 1
        # empty signals (0 with correct number of samples) are sent to channels 2,3,4
        empty = self.status.emptyBurst(len(ch0))
        self.status.sendBurst(fV2,RfV2,fRfV2,sortie)


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



