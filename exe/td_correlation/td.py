# File: main.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow,QVBoxLayout,QHBoxLayout,QTabWidget,QApplication,QPushButton,QMessageBox,QLayout,QCheckBox,QComboBox,QLabel, QTableWidget,QWidget,QSpinBox,QDockWidget,QTableWidgetItem,QDateEdit,QLineEdit
from PySide2.QtCore import QFile,Signal,QDateTime,QDate,QTimer
from PySide2 import QtCore, QtGui

import logging,math
from lib.widgets.qtLogger import qtLoggingHandler, logWidget
import lib.card.card_io as card_io
import lib.card.qt_card as QCard
from lib.widgets.seqPlotWidget import seqPlotWidget
import lib.widgets.td1_options.td1Options as td1OptionsWidget
import lib.sigpro.kalman as kalman
import numpy as np
 
class mainWindow(QMainWindow):
    def __init__(self):
        # QMainWindow.__init__(self)
        super(mainWindow, self).__init__()

        mainWidget=QWidget(self)
        self.setCentralWidget(mainWidget)

        vbox = QVBoxLayout()
        mainWidget.setLayout(vbox)  

        #####################
        # card interface
        # configure card & setup callback
        #####################

        self.card = QCard.qtCard()
        port = self.card.findSerialPort()

        # acquisition parameters
        self.currentFrame = 0
        self.Te = 1.0/10000

        if ((port[0]==None)|(port[1]==None)):
            msgBox = QMessageBox()
            msgBox.setText("Carte non detectée. Est ce qu'elle est branchée?\r\nLe logiciel va se fermer.")
            msgBox.exec()
            QTimer.singleShot(0, self.close)
            return

        self.card.connectToPort(port,card_io.FREQUENCY_10KHZ,card_io.NO_FILTER )  # 10kHz, no anti-aliasing filter
        self.card.dataReceived.connect(self.seqReceived)    # when a sequence is received, call function seqReceived
        self.card.startAcqui()

        #####
        # Setup control widget (left of GUI)
        #####
        self.options = td1OptionsWidget.td1OptionsWidget()
        dockLeft = QDockWidget("Options", self)
        dockLeft.setWidget(self.options)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,dockLeft)

        # set up control variables
        self.pauseStatus = self.options.pauseStatus
        self.currentMode = self.options.currentMode
        self.filter_coeff = self.options.coeffFilter

        # configure callback to manage change of values
        self.options.currentModeChanged.connect(self.changeCorrelationFunction)
        self.options.pauseChanged.connect(self.setPause)
        self.options.coeffChanged.connect(self.changeCoeff)

        # correlation options:
        # for accumulation & Kalman filters
        self.previousCorrIndex = 0
        self.previousCorr = None


        #####
        # Setup curves
        #####

        self.ch0PlotWidget = seqPlotWidget(['b'],['channel 1'])
        mainWidget.layout().addWidget(self.ch0PlotWidget)

        self.ch1PlotWidget = seqPlotWidget(['g'],['channel 2'])
        mainWidget.layout().addWidget(self.ch1PlotWidget)

        self.correlationWidget = seqPlotWidget(['r'],['correlation'])
        mainWidget.layout().addWidget(self.correlationWidget)

    # stop card when close button is pressed
    def closeEvent(self,event):
        self.card.stopAcqui()
        event.accept()

    ##################
    # Data received callback
    ##################

    # this function is called when two sequences are received on both inputs
    def seqReceived(self,ch0,ch1):
        self.currentFrame = self.currentFrame + 1
        self.currentTimeIndex = self.currentFrame * len(ch0) * self.Te
        if not self.pauseStatus:    # if not on pause
            tps = [self.currentTimeIndex + self.Te * k for k in range(len(ch0))]
            self.ch0PlotWidget.setData(tps,[ch0])
            self.ch1PlotWidget.setData(tps,[ch1])

            ####################
            # compute correlation:
            ####################
            # Ex = np.sum(np.array(ch0)**2)
            # Ey = np.sum(np.array(ch1)**2)

            corr = np.correlate(ch0, ch1, mode='full')
            # corr = corr / (math.sqrt(Ex*Ey))
            NbDrop = 1
            corr = corr[NbDrop:-NbDrop]
            N = len(ch0)
            corr = np.array([corr[k]*1/(N-math.fabs(k+NbDrop-N)) for k in range(len(corr))])
            tps = [(k-int(len(corr)*0.5))*self.Te for k in range(len(corr))]

            if self.currentMode==1:
                if (self.previousCorr is None):
                    self.previousCorr = corr
                    self.previousCorrIndex = 1
                else:
                    corr =  corr + self.previousCorr * self.previousCorrIndex 
                    self.previousCorrIndex = self.previousCorrIndex + 1
                    corr = corr / self.previousCorrIndex
                    self.previousCorr = corr

            if self.currentMode==2:
                if (self.previousCorr is None):
                    self.previousCorr = corr
                else:
                    corr = (1-self.filter_coeff) * corr + self.previousCorr * self.filter_coeff 
                    self.previousCorrIndex = corr

            # plot correlation
            self.correlationWidget.setData(tps,[corr])
            # self.correlationWidget.setUnitYRange()

            return 
    
    ##################
    # Parameters changed callback
    ##################
    def changeCorrelationFunction(self,value):
        self.currentMode = value 
        if (self.currentMode==1):
            self.previousCorr = None
            self.previousCorrIndex = 0
        if (self.currentMode==2):
            self.previousCorr = None

    def setPause(self,pause):
        self.pauseStatus = pause

    def changeCoeff(self,coeff):
        self.filter_coeff = coeff


    
if __name__ == "__main__":

    os.environ['KMP_DUPLICATE_LIB_OK']='True'
    app = QApplication(sys.argv)

    # on crée et on lance l'application
    mW = mainWindow()
    mW.show()
    sys.exit(app.exec_())

