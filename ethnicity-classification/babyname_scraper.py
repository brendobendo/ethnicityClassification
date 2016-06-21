# -*- coding: utf-8 -*-
"""
Created on Tue May 31 16:45:22 2016

@author: brendanabraham
"""
import PyPDF2

class firstname:
    name = ""
    ethList = []
    occurences = 0
    def __init__(self, name, ethnicities, totCount):
        self.name = name
        self.asian = ('asian', ethnicities[0])
        self.black = ('black', ethnicities[1])
        self.hisp = ('hispanic', ethnicities[2])
        self.white = ('white', ethnicities[3])
        self.ethList = [self.asian, self.black, self.hisp, self.white]
        self.occurences = totCount
        for n in self.ethList:
            self.occurences += n[1]
    def ethSort(self, tup):
        return tup[-1]
    def getWhite(self):
        for e in self.ethList:
            if e[0] == 'white':
                return e[1]
    def getBlack(self):
        for e in self.ethList:
            if e[0] == 'black':
                return e[1]
    def getAsian(self):
          for e in self.ethList:
            if e[0] == 'asian':
                return e[1]
    def getHispanic(self):
         for e in self.ethList:
            if e[0] == 'hispanic':
                return e[1]
    def getMax(self):
        s = sorted(self.ethList, key = self.ethSort, reverse = True)
        return s[0]
    def toString(self):
        s = self.name + "\toccurences: " + str(self.occurences) + "\nwhite: " + str(self.getWhite()) + "\nblack: " + str(self.getBlack()) + "\nasian: " + str(self.getAsian())+ "\nHisp.: " + str(self.getHispanic()) + "\n"
        return s
    def getList(self):
        return self.ethList


#ethnicity by page
#ignore 0-30

#31-36: hispanic male
#37-42: hisp female

#43-45: asian male
#46-48: asian female

#49-54: white male
#55-61: white female

#62-66: black male
#67-69: black female 

pageEth = {}
for i in xrange(31,37):
    pageEth[i] = ("hispanic", "male")
for i in xrange(37,43):
    pageEth[i] = ("hispanic", "female")
for i in xrange(43,46):
    pageEth[i] = ("asian", "male")
for i in xrange(46,49):
    pageEth[i] = ("asian", "female")
for i in xrange(49,55):
    pageEth[i] = ("white", "male")
for i in xrange(55,62):
    pageEth[i] = ("white", "female")
for i in xrange(62,67):
    pageEth[i] = ("black", "male")
for i in xrange(67,70):
    pageEth[i] = ("black", "female")
    
def readPDF(filename):
    nameDict = {}
    pdfFileObj = open(filename, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    numPages = pdfReader.numPages
    for i in xrange(31, numPages):
        page = pdfReader.getPage(i)
        text = page.extractText()
        split = text.split("\n")
        eth = pageEth[i][0]
        gender = pageEth[i][1].upper()
        newText = fixSplit(split, gender)
        addNames(newText, eth, gender, nameDict)
    return nameDict

def readCSV(filename):
    nameDict = {}
    f = open(filename, "r")
    f.readline()
    lines = f.readlines()
    for l in lines:
        split = l.split(",")
        gender = split[1].strip().lower()
        eth = split[2].strip().lower()
        name = split[3]
        count = split[4]
        #ethRank = split[5].strip()
        if name in nameDict:
            nameDict[name].append((eth, count, gender))
        else:
            nameDict[name] = [(eth, count, gender)]
    return nameDict
    
def main():
    #fileName = "baby_names_nyc_2008.pdf"
    #return readPDF(fileName)
    fileName = "baby_names_nyc_2011.csv"
    return readCSV(fileName)
    
def findInt(s):
    retVal = -1
    for i in xrange(0, len(s)):
        try:
            x = int(s[i])
            retVal = i
            break
        except:
            pass
    return retVal

def addNames(lista, eth, gender, nameDict):
    for i in xrange(0, len(lista)):
        if len(lista) > 0:
            try:            
                name = lista.pop(0)
                count = lista.pop(0)
                tup = (eth, count, gender)
                if name in nameDict:
                    nameDict[name].append(tup)
                else:
                    nameDict[name] = [tup]
            except:
                pass
    return nameDict

def fixName(myStr):
    ind = findInt(myStr)
    if ind > 0:
        name = myStr[:ind]
        count = myStr[ind:]
        neededFix = 1
    else:
        name = myStr
        count = ""
        neededFix = 0
    return (neededFix, name, count)
    
def fixSplit(lista, gen):
    newText = []    
    for s in lista:
            pattern = "2008" + gen.upper()            
            newText.append(s.replace(pattern,""))
    if newText[0].find("Year of Birth") != -1:
        newText.pop(0)
    for i in xrange(0,len(newText)):
        res = fixName(newText[i])
        #if i < 20:
            #print "res for " + str(newText[i]) + ": " + str(res)
        if res[0] == 1:
            newText.pop(i)
            newText.insert(i, res[2])
            newText.insert(i, res[1])
            print "fixed record for: " + res[1] + " w/ count of : " + res[2]
    return newText
#dict transformation
    
def createDict():
    nameDict = main()
    newDictRaw= {}
    ethProps = [0,0,0,0]
    ethInd = {"asian":0, "black":1, "hispanic":2, "white":3}
    for k, v in nameDict.items():
        totCount = 0
        ethProps = [0,0,0,0]
        for e in v:
            totCount += float(e[1])
        for e in v:
            ethProps[ethInd[e[0]]] = float(e[1]) / float(totCount)
        fname = firstname(k, ethProps, totCount)  
        newDictRaw[k] = fname
    #newDict = namedict.namedict(newDictRaw)
    return newDictRaw
    
