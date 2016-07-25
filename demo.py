# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 10:55:30 2016

@author: brendanabraham
"""

import namedict
import babyname_scraper
import webscraper
import ps_clean
import namedistance_clean
import ngram_analysis
import heapq
import sys
import time

firstnames = namedict.namedict({}, "first name")
surnames = namedict.namedict({}, "last name")
thresh = .9
stepFile = open('stepFile.txt', 'w') #file which classification steps are written to
model_typ = 'rf' #Defines model to use for ngram analysis. Can also choose logistic reg. (lr), dec. tree (dt), or ada boost (adb)

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
    print "1. creating name dicts"
    createDicts()
    print "2. creating pattern dbs"
    ps_clean.main()
    print "3. creating distance db"
    namedistance_clean.main()
    print "4. creating ngram db"
    ngram_analysis.main(model_typ)
    print "-----------------------"
    print "Model ready to use! call classify(foo) to get foo's ethnicity."
    print "The model writes the results of each step to stepFile.txt."
    print "For more detailed results, check this file."
    print "-----------------------"

def buildModel(typ):
    ngram_analysis.main(model_typ)

def classify(name):
    global stepFile
    retVal = ""
    stepFile = open('stepFile.txt', 'w')
    split = name.split(" ")
    typList = ['1lname', '2fname', '3bayes', '4patsearch', '5dist']
    resDict = dict([(k,(0, ('none', 0))) for k in typList])
    h = []
    if len(split) == 1:
        resDict['1lname'] = classifyPartialName(name, 'l')
        heapq.heappush(h,(-1*resDict['1lname'][1][1],'1lname'))
        if resDict['1lname'][0] == -1:
            resDict['2fname'] = classifyPartialName(name, 'f')
            heapq.heappush(h,(-1*resDict['1lname'][1][1],'1lname'))
    else:
        fname = split[0]
        dashSplit = split[1].split("-")
        lname = dashSplit[0]
        print "doing last name"
        resDict['1lname'] = classifyPartialName(lname, 'l')
        heapq.heappush(h,(-1*resDict['1lname'][1][1],'1lname'))
        if h[0][0] > thresh:
            return resDict[h[0][1]]
        else:     
            if len(dashSplit) > 1:
                lname = dashSplit[1]
                print "doing last name dash"
                resDict['1lname'] = classifyPartialName(lname, 'l')
                heapq.heappush(h,(-1*resDict['1lname'][1][1],'1lname'))
            print "doing first name"
            resDict['2fname'] = classifyPartialName(fname, 'f')
            heapq.heappush(h,(-1*resDict['2fname'][1][1],'2fname'))
            searchName = fname + " " + lname
            print "doing bayes"
            resDict['3bayes'] = naiveBayes(searchName)
            heapq.heappush(h,(-1*resDict['3bayes'][1][1],'3bayes'))
            if -1 * h[0][0] > thresh: #bayes
                retVal = resDict[h[0][1]]
            else:
                print "doing n-gram analysis"
                resDict["4ngram"] = ngram_analysis.predict(lname, prin=False)
                heapq.heappush(h,(-1*resDict['4ngram'][1][1],'4ngram'))
                if -1 * h[0][0] > thresh: #ngram analysis
                    retVal = resDict[h[0][1]]
                else:
                    print "doing pattern search"
                    resDict['5patsearch'] = ps_clean.classifyByPat(lname, prin=False)
                    heapq.heappush(h,(-1*resDict['5patsearch'][1][1],'5patsearch'))                
                    if -1 * h[0][0] > thresh: #pref-suff lookup
                        retVal =  resDict[h[0][1]]
                    else:
                        print "doing distance search" #distance search
                        lnameFound = (resDict['1lname'] != -1)
                        resDict['6dist'] = namedistance_clean.classify(lname, inDict = lnameFound)
                        heapq.heappush(h,(-1*resDict['6dist'][1][1],'6dist'))
    if retVal == "":
        retVal = resDict[h[0][1]]
    stepInd=1
    stepFile.write("-----------Classification steps for " + name + "---------------\n")
    for k,v  in sorted(resDict.items()):
        if v != "(0, ('none', 0))":
            stepString =  str(stepInd) + ". " + k[1:] + ": " + str(v)
            stepFile.write(stepString + '\n')
            stepInd+=1
    stepFile.write("FINAL RESULT: " + str(retVal) + "\n")
    stepFile.close()
    if retVal[0] == -1:
        print "could not classify"
        return (-1, ('none',0), 'none')
    else:
        print "classification: " + str(retVal)
        return retVal
    #return (h, resDict)
        
def resSort(tup):
    return tup[1][1]

def dicSort(tup):
    return tup[0]

def pattern_search(name):
    res = ps_clean.classifyByPat(name)
    print "result: " + str(res)
    return res

def gram_search(name):
    res = ngram_analysis.predict(name)
    print "result: " + str(res)
    return res
    
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
        try:
            lname = split[0].strip()
            fname = split[1].strip()
        except:
            print "line: " + str(line)
            print "split: " + split[0]
        
        lsplit = lname.split(" ")
        if len(lsplit) > 1:
            lname = lsplit[1].strip()
        else:
            lname = lsplit[0].strip()
        if len(fname) <= 2:
            fname = ""
        cleanName = fname + " " + lname
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
        return (aboveThresh, name.getMax(), typ)      
    else:
        return (-1, ('none', 0), 'none')

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
        stepFile.write("couldn't find firstname or last name.\n")
        return (-1, ('none', 0), typ)
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
        #print str(ethList)
        if ethList[0][1] >= thresh:
            aboveThresh = 1
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
        if res[0] == -1 or res == None:
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



