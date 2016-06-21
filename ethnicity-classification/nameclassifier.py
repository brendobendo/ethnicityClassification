# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 14:31:56 2016

@author: brendanabraham
"""
import requests
from lxml import html

def getPatterns():
    link = 'https://en.wikipedia.org/wiki/List_of_family_name_affixes'
    