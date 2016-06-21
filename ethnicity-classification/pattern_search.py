# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 17:46:13 2016

@author: brendanabraham
"""
import random
import webscraper
import namedict
import sys
import time

pfile = "prefixes.csv"
sfile = "suffixes.csv"
lookupfile = "eth_race_lookup.csv"

ethLookup = {}
prefixes = {}
suffixes = {}
preflist = []
sufflist = []
namelist = []
nameDict = {}
suffprobs = {}
prefprobs = {}

arr = [[]]

thresh = .9

def setThresh(t):
    global thresh
    thresh = t
def sufsort(tup):
    return tup[-1]
    
def makeLookupTable():
    global ethLookup
    f = open(lookupfile, "r")
    f.readline()
    lines = f.readlines()
    for l in lines:
        split = l.split(",")
        eth = split[0].strip().lower()
        race = split[1].strip().lower()
        ethLookup[eth] = race
    f.close()

def findRace(eth):
    if eth in ethLookup.keys():
        return ethLookup[eth].lower()
    else:
        return -1

def getTables():
    print "making race lookup table..."    
    makeLookupTable()
    print "making prefix table..."
    f1 = open(pfile, "r")
    f1.readline() #burn header
    lines = f1.readlines()
    for l in lines: 
        split = l.split(",")
        prefix = split[0].strip().lower()
        eth = split[1].strip().lower()
        race = findRace(eth)
        if race == -1:
            print "couldn't find race for " + eth
        else:
            prefixes[prefix] = (race, eth)
    f1.close()
    
    print "making suffix table..."
    f2 = open(sfile, "r")
    f2.readline()
    lines = f2.readlines()
    for l in lines:
        split = l.split(",")
        suffix = split[0].strip().lower()
        eth = split[1].strip().lower()
        race = findRace(eth)
        if race == -1:
            print "couldn't find race for " + eth
        else:
            suffixes[suffix] = (race, eth)
    f2.close()
    
def getPerf():
    found = 0
    count = 0
    getTables()
    f = open('new_missing_names.csv', 'r')    
    out = open("missing_names_performance.txt", "w")
    lines = f.readlines()
    for l in lines:
        name  = l.strip().replace(",","")
        sufres = findpref(name)
        if sufres == None:
            sufstr = "None"
        elif sufres != -1:
            race = sufres[0]
            eth = sufres[1]
            sufstr = race + "\t" + eth
            found +=1
        else:
            sufstr = -1
        count += 1
        out.write(name + "\t" +  str(sufstr) +  "\n")
    out.close()
    print "coverage: " + str(found) + " / " + str(count) + " - " + str(float(found )/float(count))
    
def findsuf(name):
    suflen = 5
    retList = []
    name = name.lower()
    if len(name) <= 2:
        suffix = name
    else:
        #while suflen > 1 and len(retList) == 0:
        while suflen > 1:
            suffix = name[-1*suflen:]
            if suffix in suffixes:
                if suffix in suffprobs:
                    ret = suffprobs[suffix]
                    retList.append((ret.getMax(), suffix))
                else:              
                   retList.append([suffixes[suffix],suffix])
            suflen = suflen - 1
        if len(retList) == 0:
            return -1
        else:
            retList = sorted(retList, reverse = True, key = sufsort)
            return retList[0]
        
def findpref(name):
    preflen = 5
    retList = []
    if len(name) <= 2:
        prefix = name
    else:
        #while preflen > 1 and len(retList) == 0:
        while preflen > 1:
            prefix = name[:preflen]   
            if prefix in prefixes:
                if prefix in prefprobs:
                    ret = prefprobs[prefix]
                    retList.append((ret.getMax(), prefix))
                else:
                    retList.append((prefixes[prefix], prefix))
            preflen = preflen - 1
        if len(retList) == 0:
            return -1
        else:
            retList = sorted(retList, reverse = True, key = sufsort)
            return retList[0]

def findnames(pattern, typ):
    retDict = {}
    for k, v in nameDict.items():
        if typ == 's':
            check = k.endswith(pattern)
        elif typ == 'p':
            check = k.startswith(pattern)
        else:
            pref = pattern.split("/")[0]
            suf = pattern.split("/")[1]
            check = k.startswith(pref) and k.endswith(suf)
        if check:
            retDict[k] = v
    if len(retDict) == 0:
        return -1
    else:
        dicname = pattern
        retNameDict = namedict.namedict(retDict, dicname)
        return retNameDict
        
def getProbs(pattern, typ):
    res = findnames(pattern.lower(), typ)
    if res == -1:
        return -1
    else:
        eProbs = []
        eNames = res.dic.items()[0][1].getEthNames() #assuming all names have same eth fields
        for ethnicity in eNames:
            pEthTot = 0.00
            for k, v in res.dic.items():
                peth = v.getEth(ethnicity)[1]
                pname = float(v.occurences) / float(res.occurences)
                pEthTot += pname * peth
            eProbs.append((ethnicity, pEthTot))
        return (res.occurences, eProbs)
    
def namesort(tup):
    return tup[0]
    
def ethsort(tup):
    return tup[0]

def getAllProbs(typ):
    if typ == 's':
        typList = suffixes
        fname = "suffixprobs.csv"
        problist = suffprobs
    elif typ == 'p':
        typList = prefixes
        fname = "prefixprobs.csv"
        problist = prefprobs
    else:
        print "please enter a valid type (p = prefixes, s = suffixes)"
        sys.exit(0)
    out = open(fname, 'w')
    out.write("suffix,occurences,amInd,asian,black,hispanic,white\n")
    for s in typList:
        res = getProbs(s, typ)
        if res != -1:
            resSorted = sorted(res[1], key=namesort)
            statList = [-1,res[0]]
            ethName = webscraper.surname(s, statList, resSorted)
            problist[s] = ethName
            out.write(s + "," + str(ethName.occurences))
            for e in ethName.getEthNames():
                out.write(","+str(ethName.getEth(e)[1]))
            out.write("\n")
    out.close()
    
def getProbsFromFile(typ):
    if typ == 's':
        fname = "suffixprobs.csv"
        problist = suffprobs
    elif typ == 'p':
        fname = "prefixprobs.csv"
        problist = prefprobs
    else:
        print "please enter a valid type (p = prefixes, s = suffixes)"
        sys.exit(0)
    f = open(fname, 'r')
    f.readline() #burn header
    lines = f.readlines()
    for l in lines:
        split = l.split(",")
        pat = split[0].strip()
        occure = int(split[1].strip())
        slen = len(split)
        ethList = []
        for i  in xrange(2, slen):
            ethList.append(float(split[i].strip()))
        statList = [-1, occure]
        patObj = webscraper.surname(pat, statList, ethList)
        problist[pat] = patObj
        
        
def getProbsBoth():
    global arr
    ls = len(sufflist)
    lp = len(preflist)
    print "ls: " + str(ls)
    print "lp: " + str(lp)
    arr = [[0 for i in range(lp)] for j in range(ls)]
    combos = ls * lp
    cindex = 0
    out = open('matrix.csv', 'w')
    out2 = open('matrixproblookup.csv', 'w')
    out2.write("pattern,black,white,amInd,asian,hispanic\n")
    for p in preflist:
        for s in sufflist:
            if cindex % 500 == 0:
                print "PROGRESS: " + str(cindex) + " / " + str(combos)
            pat = p + "/" + s
            resprobs = getProbs(pat, 'b')
            pi = preflist.index(p)
            si = sufflist.index(s)
            if resprobs != -1:
                print "match found for " + pat + "!!!!!!!"
                pat = p + "/" + s
                occur = resprobs[0]
                statlist = [-1, occur]
                patObj = webscraper.surname(pat, statlist, resprobs[1])
                arr[si][pi] = patObj
                out.write(","+ str(patObj.occurences))
                out2.write(patObj.name)
                for e in patObj.getEthNames():
                    out2.write(","+str(patObj.getEth(e)[1]))
                out2.write("\n")
            else:
                out.write(",0")
            cindex+=1
        out.write("\n")
    out.close()
    out2.close()
    return arr

def getMatFromFile():
    global arr    
    fname = "matrixproblookup.csv"
    f = open(fname, 'r')
    lp = len(preflist)
    ls = len(sufflist)
    arr = [[0 for i in range(lp)] for j in range(ls)]
    f.readline()
    lines = f.readlines()
    for l in lines:
        split = l.split(",")
        pat = split[0].strip().lower()
        print pat
        pref = pat.split("/")[0]
        suff = pat.split("/")[1]
        black = float(split[1])
        white = float(split[2])
        amInd = float(split[3])
        asian = float(split[4])
        hisp = float(split[5])
        ethProbs = [amInd, asian, black, hisp, white]
        statlist = [-1,-1]
        patObj = webscraper.surname(pat, statlist, ethProbs)
        pi = preflist.index(pref)
        si = sufflist.index(suff)
        arr[si][pi] = patObj
    f.close()
    getMatCounts()
    return arr    

def getMatCounts():
    global arr
    fname = "matrix.csv"
    f = open(fname, 'r')
    lines = f.readlines()
    linelen = len(lines)
    for pi in range(linelen):
        l = lines[pi]
        split = l.split(",")
        for s in split:
            si = split.index(s)
            count = int(s)
            if arr[si][pi] != 0:
                arr[si][pi].occurences = count
    f.close()


def countLines(fname):
    f = open(fname, 'r')
    lines = f.readlines()
    count = 0
    for l in lines:
        count +=1
    return count
    f.close()

def createSample(size):
    fname = "lastnamecount.txt"
    global nameCount
    nameCount = {}
    total = countLines(fname)
    ratio = total / size
    f = open(fname, "r")
    out = open("new_missing_samp.csv", "w")
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

#CLEAN UP RETURN STATEMENTS
def classifyByPat(name):
    prefres = findpref(name)
    sufres = findsuf(name)
    aboveThresh = 0
    if sufres != -1 and sufres is not None:
        suffix = sufres[1]
        if prefres != -1 and prefres is not None:
            prefix = prefres[1]
            pat = prefix + "/" + suffix
            probs = getProbs(pat, 'b')
            if probs != -1 and probs is not None:
                ret = sorted(probs[1], reverse = True, key = ethsort)[0]
                print ret
            else:
                ret = bayesprefsuf(pat)
        else:
            ret = sufres[0]            
    elif prefres != -1 and prefres is not None:
            ret = prefres[0]
    else:
        ret = -1
    if ret != -1:
        if ret[1] >= thresh:
            aboveThresh = 1
    return (aboveThresh, ret)
    
def bayesprefsuf(pattern):
    ethDict = {}
    ethProbs = {}
    prefix = pattern.split("/")[0]
    suffix = pattern.split("/")[1]
    pprobs = getProbs(prefix, 'p')
    sprobs = getProbs(suffix, 's')
    if pprobs != -1:
        for ep in pprobs[1]:
            ethDict[ep[0]] = namedict.ethNameTup(ep[1],0)
    if sprobs != -1:
        for es in sprobs[1]:
            if es[0] in ethDict:
                ethDict[es[0]].problast = es[1]
            else:
                ethDict[es[0]] = namedict.ethNameTup(0,es[1])
    if len(ethDict.items()) > 0:
        for k,v in ethDict.items():
            oddsLast = float(v.problast) / float(1 - v.problast)
            oddsFirst = float(v.probfirst) / float(1 - v.probfirst)
            if oddsLast != 0:
                if oddsFirst != 0:
                    odds = oddsLast * oddsFirst
                else:
                    odds = oddsLast
            else:
                odds = oddsFirst
            prob = float(odds)/float(1 + odds)
            ethProbs[k] = prob
        ethList = sorted(ethProbs.items(), reverse = True, key=ethsort)
        res = ethList[0]
    else:
        res = -1
    print res
    return res
        

def getSurnames():
    global nameDict
    global nameList
    nameDict = webscraper.createDB(True)
    nameList = nameDict.keys()
            
def main():
    global preflist
    global sufflist
    getTables()
    getSurnames()
    print "Getting prefix probabilities..."
    getProbsFromFile('p')
    print "Getting suffix probabilities..."
    getProbsFromFile('s')
    preflist = sorted(prefprobs.keys())
    sufflist = sorted(suffprobs.keys())

if __name__ == '__main__':
    main()

def getPat(pattern):
    pref = pattern.split("/")[0]
    suff = pattern.split("/")[1]
    pi = preflist.index(pref)
    si = sufflist.index(suff)
    return arr[si][pi]
    
def getMax(pattern):
    res = getPat(pattern)
    if res == 0:
        return -1
    else:
        return res.getMax()
        
def test():
    getTables()
    createSample()
    out = open("testresults.csv", "w")
    for n in namelist:
        res = findsuf(n)
        if res == -1:
            res = ('unknown', 'unknown')
        print res
        try:
            out.write(n + "," + str(res[0]) + "," + str(res[1]) + "\n")
        except: 
            pass
            
def testModel():
    f = open("new_missing_samp.csv", "r")
    out = open("new_missing_results.csv", "w")
    ti = time.time()
    lines = f.readlines()
    count = 0
    for l in lines:
        #print l
        if count % 1000 == 0 :
            print str(float(count)/float(1000000))
        name = l.split(",")[0].strip()
        s = name.split(" ")
        if len(s) > 1:
            surname = s[1]
        else:
            surname = name
        res = classifyByPat(surname)
        if res == -1 or res is None:
            subcat = 0
        else:
            #print "-----------classified " + surname + "--------------"
            subcat = res[0]
        out.write(name + "," + str(subcat) + ", " + str(res[1]) + "\n")
        count +=1
    out.close()
    tf = time.time()
    dt = tf - ti
    print "total time: " + str(dt)

def getCoverage():
    f = open("new_missing_results.csv", "r")
    lines = f.readlines()
    aboveThreshCount = 0
    found = 0
    total = 0
    for l in lines:
        if lines.index(l) % 10000 == 0:
            print str(float(lines.index(l))/float(127296))
        l = l.replace(")","")
        split = l.split(",")
        total +=1
        if split[1] == 1:
            aboveThreshCount += 1
            found +=1
        else:
            if split[2].strip() != -1:
                found +=1
                if len(split) == 5:
                    ind = 4
                else:
                    ind = 3
                try:
                    if len(split) > 3 and float(split[ind]) > thresh:
                        aboveThreshCount +=1
                except:
                    pass
    found = float(found) / float(total)
    coverage = float(aboveThreshCount) / float(total)
    print "Prop. of found records: " + str(found)
    print "Total coverage: " + str(coverage)
    f.close()
    
