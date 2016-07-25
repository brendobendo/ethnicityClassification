# -*- coding: utf-8 -*-

import requests
from lxml import html

class surname:
    name = ""
    rank = 0
    occurences = 0
    ethList = []
    def __init__(self, name, stats, ethnicities):
        self.name = name
        self.rank = int(stats[0])
        self.raw = list(ethnicities)
        self.occurences = int(stats[1])
        if type(ethnicities[0]) == tuple:
            self.setEthsFromTups(ethnicities)
        else:
            self.amInd = ('amInd', ethnicities[0])
            self.asian = ('asian', ethnicities[1])
            self.black = ('black', ethnicities[2])
            self.hisp = ('hispanic', ethnicities[3])
            self.white = ('white', ethnicities[4])
        self.ethList = [self.amInd, self.asian, self.black, self.hisp, self.white]
    def setEthsFromTups (self, ethTups):
        ethTups = sorted(ethTups, key=ethNameSort)
        self.amInd = ethTups[0]
        self.asian = ethTups[1]
        self.black = ethTups[2]
        self.hisp = ethTups[3]
        self.white = ethTups[4]
    def getEth(self, eth):
        for n in self.ethList:
            if n[0] == eth:
                return n
    def setEth(self, eth):
        for n in self.ethList:
            if n[0] == eth:
                return n
    def getEthNames(self):
        edict = dict([(e[0], e[1]) for e in self.ethList])
        return edict.keys()
        
    def getMax(self):
        s = sorted(self.ethList, key = ethSort, reverse = True)
        return s[0]
    def toString(self):
        s = self.name + "\trank: " + str(self.rank) + "\toccure: " + str(self.occurences) + "\nwhite: " + str(self.getEth('white')) + "\nblack: " + str(self.getEth('black')) + "\nasian: " + str(self.getEth('asian'))+ "\namInd: " + str(self.getEth('amInd')) + "\nHisp.: " + str(self.getEth('hispanic')) + "\n"
        return s
    def getList(self):
        return self.ethList

def ethSort(tup):
    return tup[-1]

def ethNameSort(tup):
    return tup[0]
    
def getData(link):
    page = requests.get(link)
    tree = html.fromstring(page.content)
    names = tree.xpath('//tr/td[1]/text()')
    stats = tree.xpath('//tr/td[@class="c1"]/text()')
    eths = tree.xpath('//tr/td[@class="c4"]/text()') 
   
    for i in xrange(0,2):
        if len(stats) > 0:
            stats.pop(0)
    for i in xrange(0,11):
        if len(eths) > 0:        
            eths.pop(0)
    names.pop(0)
    
    out = open("namedata.txt", "a")
    out.write("name\trank\toccurences\twhite\tblack\tasian\tam. ind.\thispanic\n")
    
    ethList = []
    statList = []
    nameDict = {}
    
    for i in xrange(0,len(names)):
        if len(stats) > 0:        
            for j in xrange(0,6):
                if len(eths) > 0:
                    if j == 4:
                        eths.pop(0)
                    else:
                        ethList.append(eths.pop(0))
            for k in xrange(0,3):
                statList.append(stats.pop(0))
            nameRecord = surname(names[i], statList, ethList)
            nameDict[nameRecord.name] = nameRecord
            out.write(nameRecord.toString())
            #print nameRecord.toString()
        ethList = []
        statList = []
    out.close()
    #page.close()
    return nameDict
    
def getInfo(name, dic):
    s = name.upper()
    res = dic[s]
    print res.toString()
    return res

def readFromFile(fileName):
    f = open(fileName, "r")
    f.readline() #burn header
    lines = f.readlines()
    ethList = []
    statList = []
    nameDict = {}
    for l in lines:
        split = l.split(",")
        name = split[0].strip().lower()
        if split[1] != 'rank':
            for k in xrange(1,3):
                statList.append(split[k])
            for j in xrange(3,8):
                if split[j].find('(S)') != -1:
                    split[j] = '0.00'
                ethList.append(float(split[j].strip())/100)
            #ethList.insert(4, 0.00)
            nameRecord = surname(name, statList, ethList)
            nameDict[nameRecord.name] = nameRecord
            ethList = []
            statList = []
            #print nameRecord.toString()
    f.close()
    return nameDict

        
#if fromfile = true, read dict from csv file. otherwise, make dict from 
def createDB(fromfile):
    nameDictRaw = {}    
    if fromfile:
        nameDictRaw = readFromFile("surname_ethnicity_data.csv")
    else:
        baseurl = "http://names.mongabay.com/data/"
        for i in xrange(1,51):
            link = baseurl + str(1000*i)+".html"
            print "looking in " + link
            nameDictRaw.update(getData(link))
    #nameDict = namedict.namedict(nameDictRaw)
    return nameDictRaw
    
def main():   
    return createDB(True)

    #nameDict = createDB()
#if __name__ == '__main__':
#    main()
    
    #class record:
    #gender = ""
    #asian = 0.00
    #black = 0.00
    #hispanic = 0.00
    #white = 0.00
    #def __init__(self, gen, ethTup):
     #   self.gender = gen
    

        
        
        
        
        