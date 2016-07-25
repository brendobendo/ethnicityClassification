# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 14:12:31 2016

@author: brendanabraham
"""
import Levenshtein as lev
import webscraper
import namedict
import lsh
import time
import random

#NOTES
#Install following libraries using pip install: 
    #1. Levenshtein
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
nameDict = {}
thresh = .8
missing_file = 'controller_samp.csv'


#lsh params: bWidth = bin width, num_ht = number of hash tables. 
bWidth = 12
num_shingles = 1
#each vector has a length of 26 
c = lsh.Cluster(12,.8)

hashResults = []
linearResults = []
testNames = []

gramsTable = {}
ethDict = {'amInd': 0, 'asian': 1, 'black': 2, 'hispanic': 3, 'white': 4}

train = {}
test = {}

#main creates the name dictionary and creates the buckets for LSH search. 
def main():
    print "getting surnames..."
    global nameDict
    surnames.dic = webscraper.createDB(True)
    nameDict = dict([(k, 0) for k in surnames.dic.keys()])
    #splitData()
    print "indexing names into cluster..."
    addNames(justTrain=False)

    #res = createSamples()
    #training = res[0]
    #testSet = res[1]

def validateModel():
    total = 0
    errorCt = 0   
    out = open('distance_results.csv', 'w')    
    print "testing test set"
    for k, v in test.items():
        res = classify(k)
        print "res: " + str(res)
        flag = 1
        if res[1][1] != 'none':
            try:
                pred = ethDict[res[1][0]]
                actual = ethDict[v.getMax()[0]]
                if pred != actual:
                    errorCt +=1
                    flag = 0
                total +=1
                out.write(k + "," + str(pred) + "," + str(actual) + "," + res[2] + "," + str(flag) + "\n")
            except:
                pass
        else:
            print "skipping " + str(k)
    out.close()
    print str(errorCt) + " errors out of " + str(total)
            
        

#train_data = [[name] + sub_scores[name] + [len(name), train[name]] for name in train.keys()]
#test_data = [[name] + sub_scores[name] + [len(name), test[name]] for name in test.keys()]

#tr_vector = [t[1:7] for t in train_data]
#tr_tragets = [t[-1] for t in train_data]

#test_vector = [t[1:7] for t in test_data]
#test_tragets = [t[-1] for t in test_data]

#logistic = LogisticRegression()
#logistic.fit(tr_vector, tr_targets)
    
def splitData():     
    global test
    global train
    print "making training set"
    for k, v in surnames.dic.items():
        rand = random.random()
        if rand > .25:
            train[k] = v
        else:
            test[k] = v
#classifies name using LSH
def classify(name, inDict=False):
    res = getMatches(name, inDict)
    if res[0] == 1:
        #print str(res)
        if res[1][1] != 'none':
            ethRes = surnames.dic[res[1][1]].getMax()
            return (res[0], ethRes, res[1][1])
    return (-1, res[1], 'noname')

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
            res = getMatches(name)
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
    print "time breakdown:" + str(dt)
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
    
#------------------SEARCH METHODS------------------# 
#-------------LSH search - finds closest match to string s in the bucket it hashes to
def getMatches(name, inDict = False):
    name = name.lower()
    ti = time.time()
    aboveThresh = 1
    tup = tuple(lsh.hshingle(name, num_shingles))
    sig = c.signer.sign(tup)
    resSet = set()
    choice = (0, "none")
    matchList = []
    for band_inx, hshval in enumerate(c.hasher.hash(sig)):
        for h in c.hashmaps[band_inx][hshval]: 
            resSet.add(h)
    for r in resSet:
        sim = lev.jaro(r, name)
        if sim > .7:
            matchList.append((sim, r))
    dt = time.time() - ti
    if len(matchList) > 0:
        matchList = sorted(matchList, reverse = True, key=simSort)
        choice = tuple(matchList[0])
        if inDict and choice[0] == 1:
            #print "skipping match"
            choice = tuple(matchList[int(inDict)])
        if choice[0] < thresh:
            aboveThresh = 0
    return (aboveThresh, choice, [0,dt,0])
    
def classifyTest():
    f = open('controller_samp.csv', 'r')
    out = open('class_results.csv', 'w')
    line = f.readlines()
    for l in line:
        name = l.strip()
        res = getMatches(name)
        if res[1][1] != 'none':
            if res[0] == 1:
                match = res[1][1]
                classification = surnames.find(match).getMax()
            else:
                classification = ('not high enough', res[1][1], res[1][0])
        else:
            classification = ('none found', 0)
        out.write(name + "," + str(classification) + "\n")
    out.close()

#-----------LINEAR SEARCH - computes jaro distance between and returns closest match. 
def getClosest(name):
    aboveThresh = 0
    choice = (0, 'none')    
    ti = time.time()    
    for n in surnames.dic.keys():
        dist = lev.jaro(n, name)
        if dist > choice[0]:
            choice = (dist, n)
    tf = time.time()
    dt = tf - ti
    if choice[0] >= thresh:
        aboveThresh = 1
    return (aboveThresh, choice, [0,dt,0])
 
def setThresh(t):
    global thresh
    thresh = t
    
def printDict(nameDic):
    for k, v in nameDic.dic.items():
        print k + ": " + str(v.occurences) + "\t" + str(v.ethList)
   
def createSamples():
    training = {}
    test = {}
    for k, v in surnames.dic.items():
        r = random.randrange(0,10)
        if r <= .25:
            test[k] = v
        else:
            training[k] = v
    return (training, test)
#-----------------SORTS-----------------#
def ethSort(tup):
    return tup[-1]

def getMax(ethList):
    s = sorted(ethList, reverse = True, key = ethSort)
    return s[0]
    
def simSort(tup):
    return tup[0]
    
def distSort(res):
    return res[2]

def popSort(tup):
    return tup[1].occurences
#------------------LSH Code----------------------------#
def addName(name):
    global nameDict
    name = name.lower()
    tup = tuple(lsh.hshingle(name, num_shingles))
    try:
        c.add_set(tup, name)
    except:
        print "issue adding record"
    
def addNames(justTrain=False):
    if justTrain:
        keys = train.keys()
    else:
        keys = surnames.dic.keys()
    for k in keys:
        addName(k)
        nameDict[k] +=1

    
                
    