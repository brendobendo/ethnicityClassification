# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 10:13:41 2016

@author: brendanabraham
"""

class namedict:
    dic = {}
    name = ""
    occurences = 0
    def __init__(self, nameDict, name):
        self.dic = nameDict
        self.name = name
        for k, v in self.dic.items():
            self.occurences += v.occurences
    def classify(self, name):
        if name.upper() in self.dic:
            return self.dic[name.upper()].getMax()
    def find(self, n):
        if n.lower() in self.dic:
            return self.dic[n.lower()]
        else:
            return -1
    def first10(self):
        for i in xrange(0, 10):
            print str(i) + ". " + self.dic.items()[i][0] + ": " + str(self.dic.items()[i][1].ethList)
def fix(raw):
        if raw > .999:
            return .999
        else:
            return raw            

class ethNameTup:
    probfirst = 0.00
    problast = 0.00
    pList = []
    def __init__(self,a, b):
        self.setfirst(a)
        self.setlast(b)
    def setfirst(self, a):
        self.probfirst = fix(a)
    def setlast(self, b):
        self.problast = fix(b)
    def toString(self):
        print "(" + str(self.probfirst) + ", " + str(self.problast) + ")"
        
            