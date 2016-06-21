# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 10:55:30 2016

@author: brendanabraham
"""

import namedict
import babyname_scraper
import webscraper
import sys

firstnames = namedict.namedict({}, "first name")
surnames = namedict.namedict({}, "last name")
thresh = .9

def createDicts():
    surnames.dic = webscraper.createDB(True)
    firstnames.dic = babyname_scraper.createDict()
    
def ethsort(tup):
    return tup[-1]
#assumes fullname format - "firstname lastname"

def setThresh(t):
    global thresh
    thresh = t

def classify(name):
    split = name.split(" " )
    if len(split) == 1:
        res = classifyPartialName(name, 'l')
        if res == -1:
            res = classifyPartialName(name, 'f')
    else:
        lname = split[1]
        res = classifyPartialName(lname, 'l')
        if res != -1:
            if res[0] == 1:
                return res
        else:
            res = naiveBayes(name)
    if res == -1:
        #print "couldn't classify " + name
        return -1
    else:
        #print "classification: " + str(res)
        return res

def naiveBayes(fullname):
    ethDict = {}
    ethProbs = {}
    ethList = []
    aboveThresh = 0
    split = fullname.split(" ")
    #print "------bayes classifier---------"
    f = split[0]
    l = split[1]
    lname = surnames.find(l)
    fname = firstnames.find(f)
    if lname == -1 and fname != -1:
        res = classifyPartialName(f, 'f')
    elif lname != -1 and fname == -1:
        #print 'classifying ' + str(l)
        res = classifyPartialName(l, 'l')
    elif lname == -1 and fname == -1:
        #print "couldn't find firstname or last name."
        return -1
    else:
        for e in fname.ethList:
            ethDict[e[0]] = namedict.ethNameTup(e[1],0)
        for el in lname.ethList:
            if el[0] in ethDict:
                ethDict[el[0]].setlast(el[1])
            else:
                ethDict[el[0]] = namedict.ethNameTup(0,el[1])
        for k, v in ethDict.items():
            oddsFirst = float(v.probfirst / (1 - v.probfirst))
            oddsLast = float(v.problast / (1 - v.problast))
            if oddsFirst == 0 and oddsLast != 0:
                odds = oddsLast
            elif oddsFirst != 0 and oddsLast == 0:
                odds = oddsFirst
            else:
                odds = oddsFirst * oddsLast
            prob = float(odds / (odds + 1))
            ethProbs[k] = prob
        ethList = sorted(ethProbs.items(), reverse = True, key=ethsort)
        if ethList[0][1] >= thresh:
            aboveThresh = 1
            res = (aboveThresh, ethList[0])
    #print str(res)
    return res
        
def getUnclassified():
    f = open("lastnamecount.txt", "r")
    out = open("missingnames.txt", "w")
    lines = f.readlines()
    for l in lines:
        split = l.split("\t")
        lname = split[0].strip().lower()
        res = classifyPartialName(lname, 'l')
        if res == -1 or res == None:
            out.write(lname + "\n")
    out.close()
    f.close()
    
def classifyPartialName(nam, typ):
    aboveThresh = 0
    if typ == 'f':
        name = firstnames.find(nam)
    elif typ == 'l':
        name = surnames.find(nam)
    else:
        print "please enter a valid type (f = first, l = last)"
        sys.exit(0)
        
    if name != -1:
        for e in name.ethList:
            if e[1] >= thresh:
                aboveThresh = 1
        return (aboveThresh, name.getMax())      
    else:
        #print nam + " not found in " + str(dicname)
        return -1

def main():
    createDicts()
    
if __name__ == '__main__':
    main()
    

