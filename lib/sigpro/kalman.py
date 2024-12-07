
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

class kalmanFilter:
    def __init__(self):
        self._previousValue = 0
        self._init = False

        self._nbPtInMin = 0
        self._meanValue = 0

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
            if (self._nbPtInMin>=2):
                self._init = True
        else:
            filteredValue = self._previousValue + (1-gain) * (value - self._previousValue)

        self._previousValue = filteredValue 
        return filteredValue

