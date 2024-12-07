import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal,QThread,QDateTime,QTimer
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QApplication,QMessageBox,QWidget,QLayout,QDateTimeEdit,QButtonGroup,QPushButton,QRadioButton,QTabWidget
import pyqtgraph as pg
import numpy as np
import logging
# import algo.kalman as kalman
# import algo.IMUProcessing as IMU
# import utl.processor as computer
import lib.widgets.plotWidget as ptWidget

class rawDataViewerWidget(QWidget):

    def __init__(self,path,addr):
        super(rawDataViewerWidget, self).__init__()
        self.addr = addr
        # self.IMU = IMU.calibParameters(path)
        # self.IMU.readCalibParameters(addr)
        self.initUI()

    def getAddr(self):
        return self.addr

    def initUI(self):   

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        self.plotAcc = ptWidget.IMURawDataplotWidget(True)
        vbox.addWidget(self.plotAcc)
        self.plotGyro = ptWidget.IMURawDataplotWidget(False)
        vbox.addWidget(self.plotGyro)

    def IMUDataReceived(self,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z):
        [acc_x,acc_y,acc_z] = self.IMU.calibrateAcc(acc_x,acc_y,acc_z)
        self.plotAcc.IMUDataReceived(acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z)
        self.plotGyro.IMUDataReceived(acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z)


class rawDataViewer(QWidget):
    
    path = ''

    def __init__(self,path):
        super(rawDataViewer, self).__init__()
        self.path = path
        self.initUI()

    def initUI(self):   

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        self.tabWidget = QTabWidget()
        vbox.addWidget(self.tabWidget)

    def addDevice(self,addr,name):
        tabWid = rawDataViewerWidget(self.path,addr)
        self.tabWidget.addTab(tabWid,name)

    def removeDevice(self,addr,name):
        for i in range(self.tabWidget.count()):
            if (self.tabWidget.tabText(i)==name):
                self.tabWidget.removeTab(i)

    def dispatchData(self,addr,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z):
        for i in range(self.tabWidget.count()):
            if (self.tabWidget.widget(i).getAddr()==addr):
                self.tabWidget.widget(i).IMUDataReceived(acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z)
    

