# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 10:55:30 2016

@author: brendanabraham
"""

import namedict
import babyname_scraper
import webscraper
import sys
import time

firstnames = namedict.namedict({}, "first name")
surnames = namedict.namedict({}, "last name")
thresh = .9
stepFile = open('stepFile.txt', 'w') #file which classification steps are written to

def createDicts():
    surnames.dic = webscraper.createDB(True)
    firstnames.dic = babyname_scraper.createDict()
    
def ethsort(tup):
    return tup[-1]
#assumes fullname format - "firstname lastname"

def setThresh(t):
    global thresh
    thresh = t
    
#ec2-52-90-145-241.compute-1.amazonaws.com:/media/ephemeral0/home/brendanabraham/

def main():
    createDicts()

def test():
    ti = time.time()    
    f = open('lastfirstnamecount.txt', 'r')
    out = open('lfresults.csv', 'w')
    lcount = 37018304
    out.write('fname,lname,classification,conf,type\n')
    line = f.readline()
    count = 0
    while line != "":
        if count % 500000 == 0:
            print str(count) + " out of " + str(lcount) + " - " + str(float(count)/float(lcount))
        line = f.readline()
        split = line.split("\t")
        #print "original lname: " + split[0]
        #print split[1] + " " + split[0]
        try:
            lname = split[0].strip()
            fname = split[1].strip()
        except:
            print "line: " + str(line)
            print "split: " + split[0]
        
        #print fname + " " + lname
        lsplit = lname.split(" ")
        if len(lsplit) > 1:
            lname = lsplit[1].strip()
        else:
            lname = lsplit[0].strip()
        #print "final lname: " + split[0]
        #print "fname: " + fname
        if len(fname) <= 2:
            fname = ""
        #print "adding " + fname + " and " + lname
        cleanName = fname + " " + lname
        #print "clean name: " + cleanName
        res = classify(cleanName)
        if res != -1:
            out.write(fname + "," + lname + "," + res[1][0] + "," + str(res[1][1]) + "," + res[2] + "\n")
        else:
            out.write(fname + "," + lname + ",-1,-1,none\n")
        count+=1
    tf = time.time()
    dt = tf - ti
    print "total time: " + str(dt)
    out.close()    

def createSample(size):    
    lcount = 37018304
    print lcount
    ratio = lcount / size
    print ratio    
    f = open('lastfirstnamecount.txt', 'r')
    out = open('lastfirstnamecountsample.txt', 'w')
    for i in range(size):
        l = f.readline()
        out.write(l)

def classify(name):
    split = name.split(" ")
    if len(split) == 1:
        res = classifyPartialName(name, 'l')
        if res == -1:
            res = classifyPartialName(name, 'f')
    else:
        fname = split[0]
        dashSplit = split[1].split("-")
        lname = dashSplit[0]
        res = classifyPartialName(lname, 'l')
        if res == -1 or res[0] == 0:
            if len(dashSplit) > 1:
                lname = dashSplit[1]
                res = classifyPartialName(lname, 'l')
            if res == -1 or res[0] == 0:
                resfirst = classifyPartialName(fname, 'f')
                if resfirst != -1:
                    res = resfirst
        if res != -1:
            if res[0] == 1:
                return res
            else:
                searchName = fname + " " + lname
                res = naiveBayes(searchName)
                if res[0] == [0]:
                    
    stepFile.write("FINAL RESULT: " + str(res) + "\n")
    stepFile.close()
    if res == -1:
        return -1
    else:
        return res

def classifyPartialName(nam, typ):
    global stepFile
    aboveThresh = 0
    nam = nam.lower()
    if typ == 'f':
        name = firstnames.find(nam)
        typ = 'fname_search'
    elif typ == 'l':
        name = surnames.find(nam)
        typ = 'lname_search'
    else:
        print "please enter a valid type (f = first, l = last)"
        sys.exit(0)
        
    if name != -1:
        for e in name.ethList:
            if e[1] >= thresh:
                aboveThresh = 1
        try:
            stepFile.write(typ + " - " + nam + ":\t" + str(name.ethList)+ "\n")
        except: 
            print "issue writing " + typ + " results"
            pass
        return (aboveThresh, name.getMax(), typ)      
    else:
        try:
            stepFile.write(typ + nam + ":\t None Found\n")
        except: 
            print "issue writing " + typ + " results"
            pass
        return -1

def naiveBayes(fullname):
    ethDict = {}
    ethProbs = {}
    ethList = []
    aboveThresh = 0
    typ = "bayes"
    split = fullname.split(" ")
    #print "------bayes classifier---------"
    f = split[0]
    l = split[1]
    lname = surnames.find(l)
    fname = firstnames.find(f)
    if lname == -1 and fname != -1:
        res = classifyPartialName(f, 'f')
    elif lname != -1 and fname == -1:
        res = classifyPartialName(l, 'l')
    elif lname == -1 and fname == -1:
        print "couldn't find firstname or last name."
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
        print str(ethList)
        if ethList[0][1] >= thresh:
            aboveThresh = 1
        try:
            stepFile.write("------bayes classifier---------\n")
            stepFile.write("bayes probs: " + str(ethList) + "\n")
        except:
            pass
        res = (aboveThresh, ethList[0], typ)
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

def countLines(fname):
    f = open(fname, 'r')
    lines = f.readlines()
    count = 0
    for l in lines:
        count +=1
    f.close()
    return count

def main():
    createDicts()
    
if __name__ == '__main__':
    main()
    

