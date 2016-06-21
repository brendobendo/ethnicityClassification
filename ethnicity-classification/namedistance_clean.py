# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 14:12:31 2016

@author: brendanabraham
"""
import Levenshtein
import webscraper
import namedict
from lshash import LSHash
import time


#NOTES
#Install following libraries using pip install: 
    #1. Levenstein
    #2. lshash
#To run the comparison test between lsh and linear search, make sure you have
#a sample file of names called controller_samp.csv in this directory. Also make 
#sure you have nameDict webscraper in this directory

#How LSH is done: 
    #1. LSHash object created 
    #2. Each name is converted to a 26 digit vector V containing letter counts
    #3. Each name is quantized into a bucket using its vector ID
    #4. A lookup dictionary is created containing key value pairs of <vector ID, name>
    #5. To search a name, it is converted to a vector which is used to query
    #  the lsh database. The query returns all vector ids in the same bucket as the name. 
    #6. Linear search is preformed on the names in the bucket and the closest match
    # is returned. 
datafile = "controller_samp.csv"

surnames = namedict.namedict({}, 'surnames')
nameList = []
nameDict = {}
thresh = .9
missing_file = 'controller_samp.csv'

#lsh params: bWidth = bin width, num_ht = number of hash tables. 
bWidth = 12
num_ht = 4
#each vector has a length of 26 
lsh = LSHash(bWidth,26, num_hashtables = num_ht)

hashResults = []
linearResults = []
testNames = []

#main creates the name dictionary and creates the buckets for LSH search. 
def main():
    global nameDict
    global nameList
    print "getting surnames..."
    surnames.dic = webscraper.createDB(True)
    nameList = sorted(surnames.dic.keys())
    print "gettin bucketz!!"
    getBuckets(False)
    
#classifies name using LSH
def classify(name):
    res = find(name)
    if res[0] == 1:
        print str(res)
        ethRes = surnames.find(res[1][1]).getMax()
        return (res[0], ethRes)
    else:
        return (-1, res[1])


#runs both lsh and linear search on small sample, then exports results as CSV
def doTest():
    testAlgo('lsh')
    testAlgo('linear')
    exportResults()
    
#Tests performance of either LSH or linear search
#typ: (lsh, linear)
def testAlgo(typ):
    global testNames
    global hashResults
    global linearResults
    getVec = 0
    query = 0
    linearSearch = 0
    ti = time.time()
    f = open('controller_samp.csv', 'r')
    lines = f.readlines()
    distances = []
    testNames = []
    if typ == 'lsh':
        hashResults = []
        resList = hashResults
    else:
        linearResults = []
        resList = linearResults
    for l in lines:
        name = l.strip()
        testNames.append(name)
        if typ == 'lsh':
            res = find(name)
            if len(res) == 0:
                resList.append("none")
        else:
            res = getClosest(name)
        getVec += res[2][0]
        query += res[2][1]
        linearSearch += res[2][2]
        distances.append(float(res[1][0]))
        resList.append(res)
    tf = time.time()
    dt = tf - ti
    print "total time: " + str(dt)
    print "time breakdown:"
    print "getVec: " + str(getVec)
    print "query: " + str(query)
    print "linearSearch: " + str(linearSearch)
    print "len results list: " + str(len(resList))
    f.close()
    
#exports test results to CSV file for comparison
def exportResults():
    print "testNames: " + str(len(testNames))
    print "linearLen: " + str(len(linearResults))
    print "hashLen: " + str(len(hashResults))
    print "exporting results"
    out = open('testResults.csv', 'w')
    l = len(testNames)
    print str(len(testNames))
    for i in range(l):
        out.write(testNames[i] + "," + str(hashResults[i]) + "," + str(linearResults[i]) + "\n")
    out.close()
    

#------------------LSH Methods----------------#

#Creates LSHash table and indexes each name from sample
def getBuckets(fromFile):
    global nameDict
    global lsh
    nameDict = {}
    lsh = LSHash(bWidth,26, num_hashtables = num_ht)
    if fromFile:
        f = open(datafile, 'r')   
        nameList = f.readlines()
    else:
        nameList = surnames.dic.keys()
    for l in nameList:
        name = l.split(" ")[0].strip()
        nameArr = getvec(name)
        arrStr = toStr(nameArr)
        if arrStr in nameDict:
            nameDict[arrStr].append(name)
        else:
            nameDict[arrStr] = [name]
    for k in nameDict.keys():
        lsh.index(toArr(k))

#--------Conversion methods between name, vector, and vector strings----------
badList = [' ','-','/','.',"'"]

#Converts a string into vector format with counts of each letter   
def getvec(string):
    v = [0 for i in range(26)]
    slen = len(string)
    for i in range(slen):
        s = string[i].lower()
        if s not in badList:
            si = ord(s) - 97
            v[si] += 1
    return v

#converts 26 digit array to string - string used as hashkey   
def toStr(arr):
    s = ""
    if len(arr) != 26:
        print "array not correct length."
    else:
        for i in arr:
            s += str(i)
    return s 

#Converts array string (hashkey above) to an actual array
def toArr(string):
    if len(string) != 26:
        print "vector not proper length"
        arr = -1
    else:
        arr = [int(string[i]) for i in range(26)]
    return arr
    

#------------------SEARCH METHODS------------------# 
#LSH search - finds closest match to string s in the bucket it hashes to
def find(s):
    getVec = 0
    query = 0
    linearSearch = 0
    t1 = time.time()
    sv = getvec(s)
    t2 = time.time()
    res = lsh.query(sv, num_results = 20)
    t3 = time.time()
    resList = []
    choice = (0, 'none')
    aboveThresh = 0
    for r in res:
        resList.append([nameDict[toStr(r[0])],r[1]])
    t4 = time.time()
    if len(resList) >= 1:
        rlen = len(resList)
        for i in range(rlen):
            candidate = resList[i][0][0]
            resList[i].append(Levenshtein.jaro(candidate,s))
        if len(resList) > 1:
            resList = sorted(resList, reverse = True, key=distSort)
        choice = (resList[0][2], resList[0][0][0]) # coice = (dist, name)
        if choice[0] >= thresh:
            aboveThresh = 1
    t5 = time.time()
    getVec = (t2 - t1)
    query = (t3 - t2)
    linearSearch = (t5 - t4)
    timeList = [getVec, query, linearSearch]
    
    return (aboveThresh, choice, timeList)

#LINEAR SEARCH - computes jaro distance between name and each last name.
#returns closest match. 
def getClosest(name):
    aboveThresh = 0
    choice = (0, 'none')    
    ti = time.time()    
    for n in nameList:
        dist = Levenshtein.jaro(n, name)
        if dist > choice[0]:
            choice = (dist, n)
    tf = time.time()
    dt = tf - ti
    if choice[0] >= thresh:
        aboveThresh = 1
    return (aboveThresh, choice, [0,dt,0])



#--------------EXTRANEOUS METHODS-----------#
#computes distance between two word vectors  
def getDist(v1,v2):
    dist = 0
    if len(v1) == 27 and len(v2) == 27:
        for i in range(26):
            v1norm = float(v1[i])/float(v1[26])
            v2norm = float(v2[i])/float(v2[26])
            dist += abs(v1norm-v2norm)
    return dist

def getvec2(string):
    v = [[0,0] for i in range(26)]
    l = len(string)
    for i in range(l):
        s = string[i].lower()
        if s not in badList:
            v[i][0] += 1
            v[i][1] += i
    return v

def getdistnew(v1,v2):
    diff = 0
    l1 = 0
    l2 = 0
    for i in range(26):
        cdiff = abs(v2[i][0]-v1[i][0])
        distdiff = abs(v2[i][1]-v1[i][1])
        diff += cdiff * distdiff
        l1 += v1[i][0]
        l2 += v2[i][0]
    d1 = (l1-1)*(l1)/2
    d2 = l2*(l2-1)/2
    worst = (l2 + l1)*(d2+d1)  
    best = (l2-l1)*(d2-d1)
    print "diff: " + str(diff)
    print "best: " + str(best)
    print "worst: " + str(worst)
    sprop = float(abs(diff - worst))/float(abs(best - worst))
    return sprop
    
def test():
    main()
    ti = time.time()
    f = open(missing_file, 'r')
    out = open("distance_results.csv", "w")
    f.readline() #burn header
    lines = f.readlines()
    count = 0
    for l in lines:
        l = l.strip()
        if count % 100 == 0:
            print str(float(count)/float(17101))
        res = classify(l)
        if res[0] != -1:
            out.write(l + "," + str(res[0]) + "," +  str(res[1]) + "\n")
        else:
            out.write(l + "," + str(-1) +"," + str(res[1]) +  "\n")
        count+=1
    out.close()
    tf = time.time()
    dt = tf - ti
    print "total time: " + str(dt)                       
    
def getvecnew(string):
    v = [0 for i in range(27)]
    slen = len(string)
    for i in range(slen):
        s = string[i].lower()
        if s not in badList:
            si = ord(s) - 97
            val = i+1
            v[si] += val
    v[26] = slen
    return v
    
def distSort(res):
    return res[2]
    
def setThresh(t):
    global thresh
    thresh = t
    