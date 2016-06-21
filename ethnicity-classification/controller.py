# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 13:37:53 2016

@author: brendanabraham
"""

import pattern_search
import new_name_classifier
import namedistance
import namedict
import webscraper
import babyname_scraper
import time
import random

sampfile = "controller_samp.csv"
pfile = "prefixes.csv"
sfile = "suffixes.csv"
lookupfile = "eth_race_lookup.csv"

sampsize = 0
pplcount = 0
pplfound = 0
nameCount = {}
missingNames = []
resDict = {} #k,v = name, classification

nameList = []
nameDict = namedict.namedict({},'nameDict')
nameDict.dic = webscraper.createDB(True)
surnames = nameDict
firstnames = namedict.namedict({}, 'firstnames')
firstnames.dic = babyname_scraper.createDict()


ethLookup = {}
prefixes = {}
suffixes = {}
preflist = []
sufflist = []

suffprobs = {}
prefprobs = {}
arr = [[]]

thresh = .9

#  [time, # of names, # of people] 
statDict = {"1nameSearch": [0,0,0], "2patternSearch": [0,0,0], "3distanceSearch": [0,0,0]}

def initialize():
    global sampsize
    global resDict
    global pplcount
    global pplfound
    global missingNames
    pplfound = 0
    pplcount = 0
    if len(nameCount) == 0:
        createSample(10000)
    sampsize = countLines(sampfile)    
    pList = [(k, 0) for k in nameCount.keys()]
    resDict = dict([(l[0],l[1]) for l in pList])
    pplcount = sum(nameCount.values())
    missingNames = []
    
def main():
    initialize()
    print "performing name search"
    nameSearch()
    pattern_search.main()
    print "performing pattern search"
    patternSearch()
    namedistance.main()
    print "performing distance search"
    distanceSearch()
    getStats()


def nameSearch():
    pcount = 0
    ti = time.time()
    size = pattern_search.countLines(sampfile)
    new_name_classifier.createDicts()
    f = open(sampfile, 'r')
    lines = f.readlines()
    for l in lines:
        l = l.strip()
        spacesplit = l.split(" ")
        if len(spacesplit) > 1:
            name = spacesplit[0]
        else:
            name = l
        res = new_name_classifier.classify(name)
        
        if res == -1 and len(spacesplit) > 1:
            secName = spacesplit[1].strip()
            res = new_name_classifier.classify(secName)
            
        if res == -1 or res is None:
            missingNames.append(l)
        else:
            print "match found for " + str(l)
            if res[0] == 1:
                updateStats(l, res, 1)
                pcount += nameCount[l]
            else:
                missingNames.append(l)
    print "# of missing names: " + str(len(missingNames)) + " out of " + str(size)
    print "classified " + str(pcount) + " out of " + str(pplcount)
    tf = time.time()
    dt = tf - ti
    foundNames = size - len(missingNames)
    statDict["1nameSearch"] = [dt, foundNames, pcount]
    print "stats: " + str(statDict["1nameSearch"])
    
def patternSearch():
    ti = time.time()
    size = len(missingNames)
    pcount = 0
    print "starting length: " + str(len(missingNames))
    for n in missingNames:
        res = pattern_search.classifyByPat(n)
        if res != -1 and res is not None:
            if res[0] == 1:
                updateStats(n, res, 2)                
                missingNames.remove(n)
                pcount += nameCount[n]
    tf = time.time()
    dt = tf - ti
    foundNames = size - len(missingNames)
    statDict["2patternSearch"] = [dt, foundNames, pcount]
    print "stats: " + str(statDict["2patternSearch"])
            
def distanceSearch():
    print "starting distance search. # of Missing records: " + str(len(missingNames))
    ti = time.time()
    si = len(missingNames)
    pcount = 0
    for n in missingNames:
        res = namedistance.classify(n)
        print res
        if res != -1 and res is not None:
            if res[0] == 1:
                updateStats(n, res, 3)
                missingNames.remove(n)
                pcount += nameCount[n]
    tf = time.time()
    sf = len(missingNames)
    foundNames = si - sf
    dt = tf - ti
    statDict["3distanceSearch"] = [dt, foundNames, pcount]
    print "stats: " + str(statDict["3distanceSearch"])
    
def getStats():
    print "stats:"
    print str(sorted(statDict.items()))
    classRate = 1 - float(len(missingNames))/float(sampsize)
    print "classification rate: " + str(classRate)
    print "Prop. of people classified: " + str(float(pplfound)/float(pplcount))
    out = open('stats.csv', 'w')
    for k, v in statDict.items():
        out.write("strategy,time,names,people\n")
        out.write(k + "," + str(v) + "\n")
    out.close()

def createSample(size):
    fname = "lastnamecount.txt"
    global nameCount
    nameCount = {}
    total = countLines(fname)
    ratio = total / size
    f = open(fname, "r")
    out = open("controller_samp.csv", "w")
    ncount = 0
    lines = f.readlines()
    for l in lines:
        r = random.randrange(0,ratio)        
        if r == 3:
            split = l.split("\t")
            ncount+=1
            name = split[0].strip().lower()
            count = int(split[1].strip())
            nameCount[name] = count
            out.write(name+"\n")
    out.close()
    print "created sample w/ " + str(ncount) + " records."
    
def countLines(fname):
    f = open(fname, 'r')
    lines = f.readlines()
    count = 0
    for l in lines:
        count +=1
    f.close()
    return count

def updateStats(name, res, type):
    global resDict
    global pplfound
    pplfound += nameCount[name]
    if res[0] != -1 and res is not None:
        resDict[name] = (res[1], type)

def outputResults():
    out = open("resdict.csv", "w")
    for k,v in resDict.items():
        out.write(k + "," + str(v) + "\n")
    out.close()

def setGlobalThresh(t):
    global thresh
    #thresh = t
    new_name_classifier.setThresh(t)
    namedistance.setThresh(t)
    pattern_search.setThresh(t)


def getCoverage():
    found = 0
    total = 0
    f = open('lastnamecount.txt','r')
    lines = f.readlines()
    for l in lines:
        split = l.split("\t")
        if split[0].find(" ") != -1:
            spacesplit = split[0].split(" ")
            name = spacesplit[0]
        else:
            name = split[0].strip()
        res = new_name_classifier.classify(name)
        if res == -1 and len(spacesplit) > 1:
            secName = spacesplit[1].strip()
            res = new_name_classifier.classify(secName)
        if res != -1 and res is not None:
            found+=1
        total+=1
    print "total coverage: " + str(found) + " / " + str(total) + " - " + str(float(found)/float(total))
