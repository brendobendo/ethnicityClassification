# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 14:37:32 2016

@author: brendanabraham
"""
import statistics
import numpy
import webscraper
import namedict
import random
import sys
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier


datafile = "controller_samp.csv"

surnames = namedict.namedict({}, 'surnames')
nameList = []
nameDict = {}
thresh = .9
missing_file = 'controller_samp.csv'

subset = {}
train = {}
test = {}
tr_vectors = []
tr_targets = []
test_vecotrs = []
test_targets = []

gramsTable = {}
ethDict = {'amInd': 0, 'asian': 1, 'black': 2, 'hispanic': 3, 'white': 4}
revEth = dict([(v, k) for k, v in ethDict.items()])
model = {}

countType = 'gc' #Defines the metric for ethnic counts. Either gc (gram count) or pc (ppl count)

def main(model_typ = 'rf'):
    global nameList
    global surnames
    surnames.dic = webscraper.createDB(True)
    print "sorting names..."
    nameList = sorted(surnames.dic.keys())
    getGramEths(surnames, True)
    print "building model..."
    buildModel(model_typ)

#----------------Build Model (DT/RF/LR?ADA)-----------------#
def buildModel(typ):
    global model
    createDatasets()
    if typ == 'lr':       
        model = LogisticRegression(class_weight = 'balanced')
    elif typ == 'dt':
        model = DecisionTreeClassifier()
    elif typ == 'rf':
        model = RandomForestClassifier(n_estimators=100)
    elif typ == 'adb':
        model = AdaBoostClassifier(n_estimators = 100)
    else:
        print "please enter valid model type (dt = dec. tree, lr = log reg)"
        sys.exit(0)
    model = model.fit(tr_vectors, tr_targets)
    return model
#----------------Get model prediction-----------------------------#
def predict(name, prin=True):
    vec = getScores(name) + [len(name)]
    npvec = numpy.array(vec)
    res = model.predict_proba(npvec.reshape(1, -1))  
    maxres = getMaxArr(res)
    maxeth = revEth[maxres[0]]
    aboveThresh = int((maxres[1] >= thresh))
    if prin:
        print "results for " + name + ": " 
        print str(res)
        print "classification: " + maxeth + ", " + str(maxres[1])
    return (aboveThresh, (maxeth, maxres[1]), 'ml-model')   
#-------------------------Validate Model--------------------------#
def validateModel(testSet):
    total = 0
    errorCt = 0
    out = open('modelresults.csv', 'w')
    out.write('name,pred,actual,correct,probs\n')
    for te in testSet:
        flag = 1
        name = te[0]
        vec = te[1:7]
        res = model.predict_proba(vec)
        maxres = getMaxArr(res[0])[0]
        
        if maxres != subset[te[0]]:
            errorCt +=1
            flag = 0
        out.write(name + "," + str(maxres) + "," + str(subset[te[0]]) + "," + str(flag) + "," + str(res[0]) + "\n")
        total +=1
    errorRate = float(errorCt) / float(total)
    print str(errorCt) + " errors out of " + str(total) + " - " + str(errorRate)
    out.close()
    return errorRate
#---------------------------Create test and training sets----------#
def createDatasets():
    global test
    global train
    global tr_vectors
    global tr_targets
    global test_vectors
    global test_targets
    flushTables()
    for k, v in surnames.dic.items():
        if v.getMax()[1] > .85:
            subset[k] = ethDict[v.getMax()[0]]
    
    for k, v in subset.items():
        rand = random.random()
        if rand > .25:
            train[k] = v
        else:
            test[k] = v
    
    sub_scores = dict([(name, getScores(name, 'gc')) for name in subset.keys()])

    train_data = [[name] + sub_scores[name] + [len(name), train[name]] for name in train.keys()]
    test_data = [[name] + sub_scores[name] + [len(name), test[name]] for name in test.keys()]

    tr_vectors = [t[1:7] for t in train_data]
    tr_targets = [t[-1] for t in train_data]
    test_vectors = [t[1:7] for t in test_data]
    test_targets = [t[-1] for t in test_data]

def flushTables():
    global test
    global train
    global tr_vectors
    global tr_targets
    global test_vectors
    global test_targets
    test = {}
    train = {}
    tr_vectors = []
    tr_targets = []
    test_vectors = []
    test_targets = []

def testModel(testSet):
    total = len(testSet)
    diffList = []
    notFound = 0
    resList = []
    probList = []
    fps = 0
    for k,v in testSet.items():
        res = classifybygram(k)
        if res != -1:
            resMax = getMax(res[1])
            vMax = v.getMax()
            resList.append((k, vMax, resMax))
            probList.append(resMax[1])
            if resMax[0] == vMax[0]: #correct classification
                diff = abs(resMax[1] - vMax[1])
                diffList.append(diff)
            else: 
                fps +=1
        else:
            notFound +=1
    cov = float(total - notFound)/float(total)
    fpr = float(fps) / float(total)
    meanDiff = statistics.mean(diffList)
    meanPred = statistics.mean(probList)
    print "found results for " + str(total - notFound) + " out of " + str(total)
    print "coverage: " + str(cov)
    print "average confidence: " + str(meanPred)
    print "false positive rate: " + str(fpr)
    print "average deviation: " + str(meanDiff)
    
    out = open("gramResults.csv", "w")
    for  r in resList:
        out.write(r[0] + "," + str(r[1]) + "," + str(r[2]) + "\n")
    out.close()

def getGrams(string, n):
    retList = []
    string = string.lower()
    if n <= len(string):
        for i in xrange(0, len(string)-n+1):
            gram  = string[i:i+n]
            retList.append(gram)
    return retList

def getprefsufs(string):
    retList = []
    string = string.lower()
    for n in xrange(2,4):
        if n < len(string):
            retList.append(string[0:n])
            retList.append(string[-n:])
    return retList

def getMaxArr(npArr):
    maxi = 0
    arr = npArr[0]
    l = len(arr)
    maxInd = 0
    for i in range(l):
        #print str(arr[i])
        if arr[i] > maxi:
            maxi = arr[i]
            maxInd = i
    return (maxInd, maxi)

def getGramEths(dic, fromFile):
    global surnames
    global gramsTable
    tgFinal = {}
    gramsTable = {}
    if fromFile:
        readingrams()
    else:
        if type(dic) == dict:
            d = dic
        else:
            d = dic.dic
        for s in d.keys():
            if d.keys().index(s) % 10000 == 0:
                print str(d.keys().index(s)) + " / " + str(len(d.keys()))
            for i in xrange(2,4):
                gList = getGrams(s, i)
                if gList is not None:
                    for g in gList:
                        if g in gramsTable:
                            gramsTable[g].occurences += d[s].occurences
                            eLen = len(d[s].ethList)
                            tempList = [(gramsTable[g].ethList[j][0], gramsTable[g].ethList[j][1] + d[s].ethList[j][1]*d[s].occurences) for j in range(eLen)]
                            gramsTable[g].ethList = tempList
                        else:
                            statList = [-1, d[s].occurences]
                            ethList = [(a[0], a[1]*d[s].occurences) for a in d[s].ethList]
                            gramObj = webscraper.surname(g, statList, ethList)
                            gramsTable[g] = gramObj
        for g in gramsTable.keys():
            gramsTable[g].ethList = [(a[0], a[1]/gramsTable[g].occurences) for a in gramsTable[g].ethList]
            if gramsTable[g].getMax()[1] >= .8:
                tgFinal[g] = (ethDict[gramsTable[g].getMax()[0]], gramsTable[g].occurences)
        gramsTable = tgFinal
    print "total grams found: " + str(len(gramsTable))

def readingrams():
    global gramsTable
    f = open('gramprobsall.csv', 'r')
    f.readline()
    lines = f.readlines()
    for l in lines:
        try:
            split = l.split(",")
            g = split[0].lower().strip()
            typ = int(split[1].strip())
            occure = int(split[2].strip())
            gramsTable[g] = (typ, occure)
        except:
            print str(l)

def getScores(name, typ=countType):   
    grams = getGrams(name, 3)
    grams = grams + getGrams(name, 2)
    scores = [0 for i in range(5)] #[amInd, asian, black, hisp., white] - patCount and occurences
    total = 0
    if typ != 'gc' and typ != 'pc':
        print "please enter a valid metric (gc = gram count, pc = people count)"
    for g in grams:
        if g in gramsTable:
            if typ == 'gc': #gram count
                scores[gramsTable[g][0]] +=1
            elif typ == 'pc':
                scores[gramsTable[g][0]] += gramsTable[g][1] #g[1] = occurences 
            total += gramsTable[g][1]
    return scores
            

def classifybygram(name):
    grams = getGrams(name, 3)
    tempList = [0 for i in range(5)]
    occurences = 0
    gramList = []
    for g in grams:
        if g in gramsTable:
            gramList.append(g)
            for i in range(5):
                tempList[i] += gramsTable[g].ethList[i][1] * gramsTable[g][1]
            occurences += gramsTable[g][1]
    if occurences > 0:
        tempList = [float(a) / float(occurences) for a in tempList]
        statList = [0, occurences]
        nameObj = webscraper.surname(name, statList, tempList)
        return (gramList, nameObj.ethList)
    else:
        #print "No grams found."
        return -1

#---------------SORTS----------------#        
def ethSort(tup):
    return tup[-1]

def getMax(ethList):
    s = sorted(ethList, reverse = True, key = ethSort)
    return s[0]
    
    