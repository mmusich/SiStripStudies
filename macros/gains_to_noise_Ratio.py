'''
Example to reade the ntuples and produce plots
'''

import ROOT
import numpy as np
from enum import Enum
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

idealnoiseratio={}
stripcount={}

for lay in Layer:
    print(lay)
    idealnoiseratio[lay]=0.
    stripcount[lay]=0

# open the input file and get the tree 
infile = ROOT.TFile.Open('db_run309051.root', 'read')
infile.cd("treeDump")
tree = infile.Get('treeDump/StripDBTree')
tree.SetBranchStatus("*",0) 
tree.SetBranchStatus("isTIB",1)
tree.SetBranchStatus("isTOB",1)
tree.SetBranchStatus("isTID",1)
tree.SetBranchStatus("isTEC",1)
tree.SetBranchStatus("g1",1)
tree.SetBranchStatus("noise",1)
tree.SetBranchStatus("layer",1)
tree.SetBranchStatus("side",1)

for entry in tree:
    if(entry.isTIB):
        cumulativeLayer=entry.layer
        idealnoiseratio[Layer(cumulativeLayer)]+= (entry.noise/entry.g1)
        stripcount[Layer(cumulativeLayer)]+= 1
    if(entry.isTID):
        cumulativeLayer= 10+abs(entry.layer) if (entry.side==1) else 13+abs(entry.layer)
        idealnoiseratio[Layer(cumulativeLayer)]+= (entry.noise/entry.g1)
        stripcount[Layer(cumulativeLayer)]+= 1
    if(entry.isTOB):
        cumulativeLayer=4+entry.layer
        idealnoiseratio[Layer(cumulativeLayer)]+= (entry.noise/entry.g1)
        stripcount[Layer(cumulativeLayer)]+= 1
    if(entry.isTEC):
        cumulativeLayer= 16+abs(entry.layer) if (entry.side==1) else 25+abs(entry.layer)
        idealnoiseratio[Layer(cumulativeLayer)]+= (entry.noise/entry.g1)
        stripcount[Layer(cumulativeLayer)]+= 1

for lay in Layer:
    print lay,idealnoiseratio[lay],stripcount[lay]
