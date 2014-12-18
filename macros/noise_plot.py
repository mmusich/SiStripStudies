#! /usr/bin/evn python

import os
import sys
from optparse import OptionParser
from pdb import set_trace
import subprocess
import logging
import copy
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

parser = OptionParser(description='process a CondDBMonitor output root file')
#parser.add_argument('tfilename', type=str)
#parser.add_argument('pngname', type=str)
_, args = parser.parse_args()
tfilename = args[0]
pngname = args[1]

import ROOT
import math
ROOT.gROOT.SetStyle('Plain')
ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)

def getSubDet(row):
   if   row.isTIB: return 'TIB'
   elif row.isTOB: return 'TOB'
   elif row.isTEC: return 'TEC'
   elif row.isTID: return 'TID'
   return ''

class Entry(object):
   def __init__(self, s=0., sq=0., en=0):
      self.sum = s
      self.sq_sum = sq
      self.entries = en

   def add(self, val):
      self.sum += val
      self.sq_sum += val*val
      self.entries += 1

   def mean(self):
      return self.sum / self.entries

   def std_dev(self):
      return math.sqrt(
         (self.sq_sum - self.entries*(self.mean()**2))/(self.entries -1)
         )

   def __add__(self, other):
      return Entry(
         self.sum     + other.sum    ,         
         self.sq_sum  + other.sq_sum ,         
         self.entries + other.entries,         
         )

   def __iadd__(self, other):
      self.sum     += other.sum    
      self.sq_sum  += other.sq_sum 
      self.entries += other.entries
      return self

if not os.path.isfile(tfilename):
   raise ValueError('%s is not a valid file' % args.tfilename)

#get noise record label
logging.info('getting noise tag')
gTag = tfilename.split('.')[0]
p = subprocess.Popen(['listoftags', 'oracle://cms_orcon_adg/CMS_COND_31X_GLOBALTAG', gTag], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = p.communicate()
noisetag = ''
for line in stdout.split('n'):
   if 'sistripnoise' in line.lower():
      noisetag = [i for i in line.split() if i][3]
logging.info( "noise tag: %s" % noisetag)

tfile = ROOT.TFile.Open(tfilename)
tree  = tfile.Get('treeDump/StripDBTree')

scatterplot = ROOT.TH2F('scatterplot', 'stip noise from DB vs stip length;strip length (cm);noise (ADC counts)', 200, 5, 25, 100, 0, 10)
plot1d = ROOT.TH1F('1dplot', 'stip noise from DB: %s;strip length (cm);noise (ADC counts)' % noisetag, 200, 5, 25)
map_1d = {
   'TIB' : plot1d.Clone('TIB'),
   'TID' : plot1d.Clone('TID'),
   'TOB' : plot1d.Clone('TOB'),
   'TEC' : plot1d.Clone('TEC'),
}

map_length = {'TIB' : {}, 'TID' : {}, 'TOB' : {}, 'TEC' : {}}
tot_entries=tree.GetEntries()
cent=int(tot_entries/100)
logging.info('looping on strip tree (%i entries)' % tot_entries)
for i, entry in enumerate(tree):
   if (i % cent) == 0: 
      logging.info('reading entry %i of %i (%.2f%%)' % (i, tot_entries, 100*float(i)/tot_entries))
   region = getSubDet(entry)
   #scatterplot.Fill(entry.length, entry.noise/entry.APVgain)
   #bin = plot1d.GetXaxis().FindFixBin(entry.length) #avoid rounding issues
   bin = entry.length
   if bin in map_length[region]:
      map_length[region][bin].add(entry.noise/entry.APVgain)
   else:
      map_length[region][bin] = Entry()
      map_length[region][bin].add(entry.noise/entry.APVgain)

logging.info('done')
c = ROOT.TCanvas()
c.SetGridx()
c.SetGridy()

scatterplot.Draw()
c.SaveAs(pngname)
logging.info(map_length['TEC'].keys())
lengths = []
for v in map_length.itervalues():
   lengths.extend(v.keys())
lengths = set(lengths)

for length in lengths:
   noises = Entry()
   for vals in map_length.itervalues():
      if length in vals:
         noises += vals[length]
   bin = plot1d.GetXaxis().FindFixBin(length)
   plot1d.SetBinContent(bin, noises.mean())
   plot1d.SetBinError(bin, noises.std_dev())

plot1d.GetXaxis().SetRangeUser(8, 20)
plot1d.GetYaxis().SetRangeUser(3, 7)
plot1d.Draw()
c.SaveAs(pngname.replace('.png', '_1d.png'))

drawattrs = {
   'TIB' : {
      'MarkerStyle' : 20,
      'MarkerColor' : 1,
      }, 
   'TID' : {
      'MarkerStyle' : 21,
      'MarkerColor' : 2,
      }, 
   'TOB' : {
      'MarkerStyle' : 22,
      'MarkerColor' : 3,
      }, 
   'TEC' : {
      'MarkerStyle' : 23,
      'MarkerColor' : 4,
      }
}
first=True
i_am_legend = ROOT.TLegend(0.1,0.7,0.48,0.9)
i_am_legend.SetFillColor(0)
n_min = 1000
n_max = 0

for region, strips in map_length.iteritems():
   for length, noises in strips.iteritems():
      bin = plot1d.GetXaxis().FindFixBin(length)
      mean    = noises.mean()
      std_dev = noises.std_dev()
      #print n_min, n_max, mean
      n_min = min(n_min, mean)
      n_max = max(n_max, mean)
      map_1d[region].SetBinContent(bin, mean)
      map_1d[region].SetBinError(bin, std_dev)

   for attr, val in drawattrs[region].iteritems():
      getattr(map_1d[region], 'Set%s' % attr)(val)
   draw_opt = '' if first else 'same'
   map_1d[region].Draw(draw_opt)
   map_1d[region].GetXaxis().SetRangeUser(5, 22)
   map_1d[region].GetYaxis().SetRangeUser(n_min, n_max)
   i_am_legend.AddEntry(map_1d[region],region,"p")
   first=False

#print n_min, n_max
map_1d[map_length.keys()[0]].GetYaxis().SetRangeUser(int(n_min)-1, int(n_max)+1)
i_am_legend.Draw()
c.SaveAs(pngname.replace('.png', '_separated_1d.png'))
