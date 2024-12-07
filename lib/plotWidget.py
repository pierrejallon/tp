import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal,QThread,QDateTime,QTimer
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QApplication,QMessageBox,QWidget,QLayout,QVBoxLayout,QDateTimeEdit,QButtonGroup,QPushButton,QRadioButton
import pyqtgraph as pg
import numpy as np
import logging

class plotWidget(QWidget):
    
    def __init__(self,memorySize,Te,curves,names):
        super(plotWidget, self).__init__()
        self.initUI()

        self.memorySize = memorySize # in seconds
        self.samplingTime = Te # in seconds
        self.curves = curves
        self.names = names

        self.time = np.linspace(-self.memorySize,0,num=(int)(self.memorySize/self.samplingTime))
        self.rawData = np.zeros((len(curves),(int)(self.memorySize/self.samplingTime)))

    # def __del__(self):
    #     if (self.timer):
    #         self.timer.stop()

    def reset(self):
        self.time = np.linspace(-self.memorySize,0,num=(int)(self.memorySize/self.samplingTime))
        self.rawData = np.zeros((len(self.curves),(int)(self.memorySize/self.samplingTime)))

    def initUI(self):   

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        self.setLayout(vbox)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        plotData = pg.PlotWidget()
        vbox.addWidget(plotData)
        self.plot = plotData.plotItem
        self.plot.addLegend()

        self.timer=QTimer()
        self.timer.timeout.connect(self.replotCurves)
        self.timer.start(300)

    def replotCurves(self):
        self.plot.clear()
        for (ic,c) in enumerate(self.curves):
            self.plotData(self.time,self.rawData[ic,:],c,self.names[ic])
            

    def plotData(self,x,y,color,name):
        curve = self.plot.plot(name=name)
        curve.setData(x,y,pen=pg.mkPen(color, width=2))
        
    def addRawData(self,values):
        # time management
        self.time[:-1] = self.time[1:]   
        self.time[-1] = self.time[-2]+self.samplingTime

        for (ic,c) in enumerate(self.curves):
            self.rawData[ic,:-1] = self.rawData[ic,1:] 
            self.rawData[ic,-1] = values[ic]

class PPGplotWidget(plotWidget):
    
    memorySize = 10.0 # in seconds
    samplingTime = 0.01 # in seconds

    def __init__(self):
        curves = ['b','r']
        names = ['PPG','PPG filt']
        super(PPGplotWidget, self).__init__(self.memorySize,self.samplingTime,curves,names)

    def dataReceived(self,ppg,ppgf):
        self.addRawData( [ppg,ppgf] )   


# class IMURawDataplotWidget(plotWidget):
    
#     memorySize = 10.0 # in seconds
#     samplingTime = 0.05 # in seconds

#     def __init__(self,acc):
#         curves = ['b','r','g']
#         if acc:
#             names = ['a_x','a_y','a_z']
#         else:
#             names = ['g_x','g_y','g_z']
#         super(IMURawDataplotWidget, self).__init__(self.memorySize,self.samplingTime,curves,names)
#         self.acc = acc

#     def IMUDataReceived(self,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z):
#         if self.acc:
#             self.addRawData( [acc_x,acc_y,acc_z] )        
#         else:
#             self.addRawData( [gyro_x,gyro_y,gyro_z] )        

# class IMUplotWidget(plotWidget):
    
#     memorySize = 10.0 # in seconds
#     samplingTime = 0.05 # in seconds

#     def __init__(self):
#         curves = ['b','g','r']
#         names = ['angle acc','angle gyro','angle']
#         super(IMUplotWidget, self).__init__(self.memorySize,self.samplingTime,curves,names)

#         self.calc = computer.processor( self.samplingTime )
#         self.calc.angleDebugComputed.connect(self.dataComputed)

#     def dataComputed(self,angle,angle_acc,angle_gyro,alpha):
#         self.addRawData( [angle_acc,angle_gyro,angle] )        

#     def IMUDataReceived(self,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z):
#         self.calc.IMUDataReceived('dummy',acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z)

# class AlphaplotWidget(plotWidget):
    
#     memorySize = 10.0 # in seconds
#     samplingTime = 0.05 # in seconds

#     def __init__(self):
#         curves = ['b']
#         names = ['alpha']
#         super(AlphaplotWidget, self).__init__(self.memorySize,self.samplingTime,curves,names)

#         self.calc = computer.processor( self.samplingTime )
#         self.calc.angleDebugComputed.connect(self.dataComputed)

#     def dataComputed(self,angle,angle_acc,angle_gyro,alpha):
#         self.addRawData( [alpha] )        

#     def IMUDataReceived(self,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z):
#         self.calc.IMUDataReceived('dummy',acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z)

# class AmortoplotWidget(plotWidget):
    
#     memorySize = 20.0 # in seconds

#     def __init__(self,samplingTime):
#         self.samplingTime = samplingTime
#         curves = ['b','g']
#         names = ['avant','arr']
#         super(AmortoplotWidget, self).__init__(self.memorySize,self.samplingTime,curves,names)

#     def dataReceived(self,df,dr):
#         self.addRawData( [df,dr] )   

# class BikeAngleplotWidget(plotWidget):
    
#     memorySize = 20.0 # in seconds

#     def __init__(self,samplingTime):
#         curves = ['b','g']
#         names = ['front angle','rear angle']
#         super(BikeAngleplotWidget, self).__init__(self.memorySize,samplingTime,curves,names)

#     def angleReceived(self,angle_f,angle_r,theta):
#         self.addRawData( [angle_f,angle_r] )        

# class distGenouxPiedplotWidget(plotWidget):
    
#     memorySize = 20.0 # in seconds

#     def __init__(self,samplingTime):
#         curves = ['b']
#         names = ['dist. genoux - pied']
#         super(distGenouxPiedplotWidget, self).__init__(self.memorySize,samplingTime,curves,names)

#     def distReceived(self,x_d):
#         self.addRawData( [x_d] )        

# class elongationplotWidget(plotWidget):
    
#     memorySize = 20.0 # in seconds

#     def __init__(self,samplingTime):
#         curves = ['b','g']
#         names = ['elongation','max']
#         super(elongationplotWidget, self).__init__(self.memorySize,samplingTime,curves,names)

#     def distReceived(self,x_elongation,x_max):
#         self.addRawData( [x_elongation,x_max] )     


# class BodyAngleplotWidget(plotWidget):
    
#     memorySize = 20.0 # in seconds

#     def __init__(self,samplingTime):
#         curves = ['b','g','r']
#         names = ['cuisse','tibia','pied']
#         super(BodyAngleplotWidget, self).__init__(self.memorySize,samplingTime,curves,names)

#     def angleReceived(self,angle_c,angle_t,angle_p):
#         self.addRawData( [angle_c,angle_t,angle_p] )  
