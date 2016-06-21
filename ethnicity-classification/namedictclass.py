# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 10:13:41 2016

@author: brendanabraham
"""

class namedic:
    dic = {}
    def __init__(self, nameDict):
        self.dic = nameDict
    def classify(self, name):
        if name.upper() in self.dic:
            return self.dic[name.upper()].getMax()
        else:
            print name.upper() + " not found."
    def find(self, name):
        if name.upper() in self.dic:
            print self.dic[name.upper()].toString()
            return self.dic[name.upper()]
        else:
            print name.upper() + " not found."