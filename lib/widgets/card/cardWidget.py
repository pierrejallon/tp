from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal,QTimer
from PySide2 import QtCore, QtGui,QtWidgets
from PySide2.QtWidgets import QMessageBox,QApplication,QWidget,QLayout,QLabel,QVBoxLayout,QComboBox,QPushButton
import logging
from lib.card.card_io import listSerialPort,findSerialPort,cardAcqui
import time 
import gc

class cardWidget(QtWidgets.QWidget):
    
    dataReceivedSig = QtCore.Signal(object,object)
    connectionSet = QtCore.Signal(float)

    def __init__(self):
        super(cardWidget, self).__init__()
        self.initUI()
        
    def initUI(self):   

        ui_file = QFile("lib/widgets/card/cardWidget.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.widget = loader.load(ui_file)
        ui_file.close()

        vbox = QVBoxLayout()
        vbox.addWidget(self.widget)
        vbox.addStretch(1)
        self.setLayout(vbox)

        self.card = None
        self.acqui_start_time = 0
        self.nbSamplesReceived = 0
        self.setupGUI()

    def stopCard(self):
        if (self.card):
            self.card.stopCard()
            self.card = 0

    def setupGUI(self):
        # cannot connect is platform not found automatically 
        self.findChild(QPushButton,"pushButton").setEnabled(False)

        self.findChild(QPushButton,"pushButton_2").clicked.connect(self.refreshCOM)
        self.findChild(QPushButton,"pushButton").clicked.connect(self.connectCard)
        self.refreshCOM()

    def refreshCOM(self):
        COMCB = self.findChild(QComboBox,"comboBox")
        COMCB2 = self.findChild(QComboBox,"comboBox_4")
        
        COMCB.clear()
        COMCB2.clear()
        allPorts = listSerialPort()
        port = findSerialPort()
        if ((port[0]==None)|(port[1]==None)):
            msgBox = QMessageBox()
            msgBox.setText("Carte non detectée. Est ce qu'elle est branchée?")
            msgBox.exec()
    
        for p in allPorts:
            COMCB.addItem(p.name)
            COMCB2.addItem(p.name)
            if (port):
                if (p.device==port[0]) :
                    COMCB.setCurrentIndex(COMCB.count()-1)
                if (p.device==port[1]) :
                    COMCB2.setCurrentIndex(COMCB2.count()-1)

        if (not port):
            self.findChild(QLabel,"label_10").setText("Plateforme non branchée ?")
            self.findChild(QPushButton,"pushButton").setEnabled(False)
        else:
            self.findChild(QPushButton,"pushButton").setEnabled(True)
            self.findChild(QLabel,"label_10").setText("Attente acqui")

    def connectCard(self):
        if (not self.card):
            portCOM = self.findChild(QComboBox,"comboBox").currentText()
            portCOM2 = self.findChild(QComboBox,"comboBox_4").currentText()
            samplingFreq = self.findChild(QComboBox,"comboBox_2").currentIndex()
            antiAliasingFilter = self.findChild(QComboBox,"comboBox_3").currentIndex()+1
            self.card = cardAcqui([portCOM,portCOM2],samplingFreq,antiAliasingFilter)
            self.card.setDataReadyCB( self.dataReceived )
            
            self.card.startAcqui()

            # transmit frequency
            if samplingFreq==0:
                self.connectionSet.emit(100)
            if samplingFreq==1:
                self.connectionSet.emit(500)
            if samplingFreq==2:
                self.connectionSet.emit(1000)
            if samplingFreq==3:
                self.connectionSet.emit(2000)
            if samplingFreq==4:
                self.connectionSet.emit(10000)

            self.findChild(QPushButton,"pushButton").setText("Arreter acquisition")
            self.findChild(QPushButton,"pushButton_2").setEnabled(False)
            self.findChild(QComboBox,"comboBox").setEnabled(False)
            self.findChild(QComboBox,"comboBox_2").setEnabled(False)
            self.findChild(QComboBox,"comboBox_3").setEnabled(False)
            self.findChild(QComboBox,"comboBox_4").setEnabled(False)

            self.acqui_start_time = time.time()
            self.nbSamplesReceived = 0

        else:
            self.findChild(QPushButton,"pushButton").setText("Démarrer acquisition")
            self.findChild(QPushButton,"pushButton_2").setEnabled(True)
            self.findChild(QComboBox,"comboBox").setEnabled(True)
            self.findChild(QComboBox,"comboBox_2").setEnabled(True)
            self.findChild(QComboBox,"comboBox_3").setEnabled(True)
            self.findChild(QComboBox,"comboBox_4").setEnabled(True)
            self.card.stopCard()
            self.card = 0

    def dataReceived(self,ch0,ch1):
        # data rate estimation
        current = time.time()
        # self.nbSamplesReceived = self.nbSamplesReceived + len(ch0)
        self.nbSamplesReceived = self.nbSamplesReceived + 1
        if (current>self.acqui_start_time):
            rate = self.nbSamplesReceived/(current-self.acqui_start_time)
            self.findChild(QLabel,"label_10").setText("rate: {:.2f} Hz".format(rate))

        # emit received data
        self.dataReceivedSig.emit(ch0,ch1)

    def emptyBurst(self,L):
        return [0] * L

    def sendBurst(self,ch0,ch1,ch2,ch3):
        self.card.sendBurst(ch0,ch1,ch2,ch3)
        return 