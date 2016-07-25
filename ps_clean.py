# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 17:46:13 2016

@author: brendanabraham
"""
import random
import webscraper
import namedict
import sys

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
ethDict = {'amInd': 0, 'asian': 1, 'black': 2, 'hispanic': 3, 'white': 4}
thresh = .9
            

def main():
    global preflist
    global sufflist
    getSurnames()
    preflist = sorted(prefprobs.keys())
    sufflist = sorted(suffprobs.keys())
    print "generating all prefixes and suffixes..."
    getTables(True)

def getSurnames():
    global nameDict
    global nameList
    nameDict = webscraper.createDB(True)
    nameList = nameDict.keys()
    
def classifyByPat(name, prin=True):
    typ = 'none'
    prefres = findpref(name)
    sufres = findsuf(name)
    suffix = sufres[1]
    prefix = prefres[1]        
    aboveThresh = 0
    if sufres[0] != -1 and sufres is not None: 
        if prefres != -1 and prefres is not None:      
            pat = prefix + "/" + suffix
            probs = getProbs(pat, 'b')
            if probs != -1 and probs is not None:
                ret = sorted(probs[1], reverse = True, key = ethsort)[0]
                if prin:
                    print name + " - " + str(ret)
            else:
                typ = ('bayes', pat)
                ret = bayesprefsuf(pat)
        else:
            typ = ('suff', '-'+suffix)
            ret = (sufres[0])            
    elif prefres[0] != -1 and prefres is not None:
        typ = ('pref', prefix+'-')
        ret = (prefres[0])
    else:
        ret = ('none', 0)
    if ret != -1:
        if prin:
            print "retval: " + str(ret)
        if ret[1] >= thresh:
            aboveThresh = 1
    else:
        aboveThresh = -1
    return (aboveThresh, ret, typ)
    
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


def writeProbstoFile(typ):
    if typ == 's':
        ftype = 'suffix'
    else:
        ftype = 'prefix'
    out = open(ftype+'probs_new.csv', 'w')
    #header
    out.write(ftype + ',occurences,amInd,asian,black,hispanic,white\n')
    for k, v in suffprobs.items():
        out.write(v.name)
        out.write(", " + str(v.occurences))
        for a in v.ethList:
            out.write(',' + str(a[1]))
        out.write('\n')
    out.close()
       
def findsuf(name):
    suflen = 5
    retList = []
    name = name.lower()
    if len(name) <= 2:
        suffix = name
    else:
        while suflen > 1:
            suffix = name[-1*suflen:]
            if suffix in suffprobs:
                ret = suffprobs[suffix]
                retList.append((ret.getMax(), suffix))
            suflen = suflen - 1
        if len(retList) == 0:
            return (-1, "None")
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
            if prefix in prefprobs:
                ret = prefprobs[prefix]
                retList.append((ret.getMax(), prefix))
            preflen = preflen - 1
        if len(retList) == 0:
            return (-1, "None")
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
    
#----------------------MINE PREFS./SUFFS FROM DATA---------------#
def getTables(fromFile):
    global prefprobs
    global suffprobs
    if fromFile:
        prefprobs = readingrams('p')
        suffprobs = readingrams('s')
    else:
        genAllGrams()
    
def genAllGrams():
    global prefprobs
    global suffprobs
    prefprobs = {}
    suffprobs = {}
    prefprobs = genGrams('p')
    suffprobs = genGrams('s')

def readingrams(typ):
    global prefprobs
    global suffprobs   
    if typ == 'p':
        f = open('prefgramprobs.csv', 'r')
        table = prefprobs
        prefprobs = {}
    elif typ == 's':
        f = open('suffgramprobs.csv', 'r')
        table = suffprobs
        suffprobs = {}
    else:
        print "please enter valid type (p = pref, s = suf)"
        sys.exit(0)
    f.readline()
    lines = f.readlines()
    for l in lines:
        split = l.split(",")
        pat = split[0].strip()
        ethList = []
        for e in split[1:6]:
            e = e.strip().replace("'","")
            ethList.append(float(e))
        occurences = int(split[6])
        statList = [-1, occurences]
        patObj = webscraper.surname(pat, statList, ethList)
        table[pat] = patObj
    f.close()
    return table     

def genGrams(typ):
    tgFinal = {}
    global surnames
    global prefprobs
    global suffprobs
    ethProbs = {}
    
    d = nameDict
    if typ == 's':
        ethProbs = suffprobs
        ftype = 'suff'
    elif typ == 'p':
        ethProbs = prefprobs
        ftype = 'pref'
    else:
        print 'please enter valid type (p = prefix, s = suffix)'
        sys.exit(0)
    out = open(ftype+'gramprobs.csv', 'w')
    for i in xrange(2,4):
        print "finding " + str(i) + "-grams"
        for s in d.keys():
            if d.keys().index(s) % 10000 == 0:
                print str(d.keys().index(s)) + " / " + str(len(d.keys()))
            threeG = getprefsufs(s, typ, i)
            if threeG is not None:
                for g in threeG:
                    if g in ethProbs:
                        ethProbs[g].occurences += d[s].occurences
                        eLen = len(d[s].ethList)
                        tempList = [(ethProbs[g].ethList[j][0], ethProbs[g].ethList[j][1] + d[s].ethList[j][1]*d[s].occurences) for j in range(eLen)]
                        ethProbs[g].ethList = tempList
                    else:
                        statList = [-1, d[s].occurences]
                        ethList = [(a[0], a[1]*d[s].occurences) for a in d[s].ethList]
                        gramObj = webscraper.surname(g, statList, ethList)
                        ethProbs[g] = gramObj
    out.write(ftype+',amInd,asian,black,hispanic,white,occurences\n')
    for g in ethProbs.keys():
        ethProbs[g].ethList = [(a[0], a[1]/ethProbs[g].occurences) for a in ethProbs[g].ethList]
        if ethProbs[g].getMax()[1] >= .8:
            #print str(ethProbs[g].getMax()[1])
            out.write(g)
            for e in ethProbs[g].ethList:
                out.write(','+ str(e[1]))
            out.write(','+ str(ethProbs[g].occurences) + '\n')
            tgFinal[g] = ethProbs[g]
    ethProbs = tgFinal
    print "total grams found: " + str(len(ethProbs))
    out.close()
    return tgFinal
    
def getprefsufs(string, typ, n):
    retList = []
    string = string.lower()
    if typ != 'p' and typ != 's':
        print "invalid pattern type (p = prefix, s = suffix)"
        sys.exit(0)
    if n < len(string):
        if typ == 'p':
            retList.append(string[0:n])
        else:
            retList.append(string[-n:])
    return retList

#--------------------SUPPLEMENTARY METHODS-----------------#
def getMaxArr(arr):
    maxi = 0
    l = len(arr)
    maxInd = 0
    for i in range(l):
        print str(arr[i])
        if arr[i] > maxi:
            maxi = arr[i]
            maxInd = i
    return maxInd    


def namesort(tup):
    return tup[0]
    
def ethsort(tup):
    return tup[0]
    
def setThresh(t):
    global thresh
    thresh = t
    
def sufsort(tup):
    return tup[-1]
    
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

def testModel():
    out = open('new_ps_results.csv', 'w')
    for k in surnames.dic.keys():
        res = classifyByPat(k)
        out.write(k + "," + str(res) + "\n")
    out.close()
        

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
    
