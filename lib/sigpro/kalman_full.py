
import os
import socket
from os.path import exists

from sys import platform
import json
from collections import OrderedDict
import logging
import csv
import numpy as np 
from array import array
import math

###########################
# set of functions to process signals
###########################

class stateMachine:
    def __init__(self):
        self.currentState = 0
        self.nbSamplesSinceInState = 0

    def newValue(self,value):
        if (self.currentState==2):
            if value > 1:
                self.currentState = 0

            return self.currentState

        if (self.currentState==1):
            self.nbSamplesSinceInState = self.nbSamplesSinceInState + 1
            if (self.nbSamplesSinceInState>15):
                self.nbSamplesSinceInState = 0
                self.currentState = 2

            return self.currentState

        if (self.currentState==0):
            self.nbSamplesSinceInState = self.nbSamplesSinceInState + 1
            if (self.nbSamplesSinceInState>5):
                self.nbSamplesSinceInState = 0
                self.currentState = 1
            return self.currentState

class kalmanFilter:
    def __init__(self):
        self._previousValue = 0
        self._init = False

        self._nbPtInMin = 0
        self._meanValue = 0

        self.stateMgr = stateMachine()
        return 

    def reset(self):
        self._nbPtInMin = 0
        self._meanValue = 0
        self._init = False

    def filter(self,value,gain):
        if not self._init:
            self._nbPtInMin = self._nbPtInMin + 1
            self._meanValue = self._meanValue + value
            filteredValue = self._meanValue / self._nbPtInMin
            if (self._nbPtInMin>=50):
                self._init = True
        else:
            filteredValue = self._previousValue + (1-gain) * (value - self._previousValue)

        self._previousValue = filteredValue 
        return filteredValue

    def automaticGain(self,value):
        state = self.stateMgr.newValue( math.fabs(value - self._previousValue) )
        gain = 0.1
        if state==2:
            gain = 0.995
        if state==1:
            gain = 0.9
        # fGain = self.gainFilt.filter(gain,0.5)
        return gain
