#!/usr/bin/python
'''
Example to reade the ntuples and produce plots
'''

import sys
import time
import ROOT 
from array import array
import numpy as np
from enum import Enum

################################################
class Layer(Enum):
    TIB1  = 1
    TIB2  = 2
    TIB3  = 3
    TIB4  = 4
    TOB1  = 5
    TOB2  = 6
    TOB3  = 7
    TOB4  = 8
    TOB5  = 9
    TOB6  = 10
    TIDP1 = 11
    TIDP2 = 12
    TIDP3 = 13
    TIDM1 = 14
    TIDM2 = 15
    TIDM3 = 16
    TECP1 = 17
    TECP2 = 18
    TECP3 = 19
    TECP4 = 20
    TECP5 = 21
    TECP6 = 22
    TECP7 = 23
    TECP8 = 24
    TECP9 = 25
    TECM1 = 26
    TECM2 = 27
    TECM3 = 28
    TECM4 = 29
    TECM5 = 30
    TECM6 = 31
    TECM7 = 32
    TECM8 = 33
    TECM9 = 34

###############################################
def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush() 

################################################
def processTree(tree):
    g1=array("f",[0])
    noise=array("f",[0])
    subdetId=array("i",[0])
    layer=array("i",[0])
    side=array("i",[0])
    tree.SetBranchAddress("g1",g1)
    tree.SetBranchAddress("noise",noise)
    tree.SetBranchAddress("subdetId",subdetId)
    tree.SetBranchAddress("layer",layer)
    tree.SetBranchAddress("side",side)
    tree.LoadTree(0)

    idealnoiseratio={}
    stripcount={}
    ratioByLayer={}

    for lay in Layer:
    #print(lay)
        idealnoiseratio[lay]=0.
        stripcount[lay]=0

    i=0
    start=time.time()
    for entry in xrange(tree.GetEntries()):
        tree.GetEntry(entry)
        progress(i,tree.GetEntries(), status='Processing file')
        if(subdetId[0]==3):
            cumulativeLayer=layer[0]
            idealnoiseratio[Layer(cumulativeLayer)]+= (noise[0]/g1[0])
            stripcount[Layer(cumulativeLayer)]+= 1
        if(subdetId[0]==4):
            cumulativeLayer= 10+abs(layer[0]) if (side[0]==1) else 13+abs(layer[0])
            idealnoiseratio[Layer(cumulativeLayer)]+= (noise[0]/g1[0])
            stripcount[Layer(cumulativeLayer)]+= 1
        if(subdetId[0]==5):
            cumulativeLayer=4+layer[0]
            idealnoiseratio[Layer(cumulativeLayer)]+= (noise[0]/g1[0])
            stripcount[Layer(cumulativeLayer)]+= 1
        if(subdetId[0]==6):
            cumulativeLayer= 16+abs(layer[0]) if (side[0]==1) else 25+abs(layer[0])
            idealnoiseratio[Layer(cumulativeLayer)]+= (noise[0]/g1[0])
            stripcount[Layer(cumulativeLayer)]+= 1
        i+=1

    for lay in Layer:
        ratioByLayer[lay]=float(idealnoiseratio[lay]/stripcount[lay])

    print "processTree time:",time.time()-start
    return ratioByLayer
    

print "starting opening first file"
# open the input file and get the tree 
infile1 = ROOT.TFile.Open('db_run309051.root', 'read')
infile1.cd("treeDump")
tree1 = infile1.Get('treeDump/StripDBTree')
tree1.SetBranchStatus("*",0) 
tree1.SetBranchStatus("subdetId",1)
tree1.SetBranchStatus("g1",1)
tree1.SetBranchStatus("noise",1)
tree1.SetBranchStatus("layer",1)
tree1.SetBranchStatus("side",1)

newratio=processTree(tree1)

print "\n starting opening second file"

# open the input file and get the tree 
infile2 = ROOT.TFile.Open('db_run306054.root', 'read')
infile2.cd("treeDump")
tree2 = infile2.Get('treeDump/StripDBTree')
tree2.SetBranchStatus("*",0) 
tree2.SetBranchStatus("subdetId",1)
tree2.SetBranchStatus("g1",1)
tree2.SetBranchStatus("noise",1)
tree2.SetBranchStatus("layer",1)
tree2.SetBranchStatus("side",1)

oldratio=processTree(tree2)

print "\n"

for lay in Layer:
    print "Layer:",lay,"ratio of ratios:",float(newratio[lay]/oldratio[lay])
