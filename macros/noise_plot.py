#! /usr/bin/evn python

import os
import sys
from optparse import OptionParser
from pdb import set_trace
import subprocess
import logging
import copy
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

parser = OptionParser(description='process a CondDBMonitor output root file')
parser.add_option('--limit', type=int, default=-1, help='limits number of strips processed')
#parser.add_argument('pngname', type=str)
opts, args = parser.parse_args()
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
## logging.info('getting noise tag')
## gTag = tfilename.split('.')[0]
## p = subprocess.Popen(['listoftags', 'oracle://cms_orcon_adg/CMS_COND_31X_GLOBALTAG', gTag], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
## stdout, stderr = p.communicate()
## noisetag = ''
## gsim_tag = ''
## g1_tag   = ''
## g2_tag   = ''
## get_tag = lambda line : [i for i in line.split() if i][2]
## for line in stdout.split('\n'):
##    logging.debug(line)
##    if 'sistripnoise' in line.lower():
##       noisetag = get_tag(line)
##    elif 'SiStripApvGainSim' in line:
##       gsim_tag = get_tag(line)
##    elif 'SiStripApvGain2' in line:
##       g2_tag = get_tag(line)
##    elif 'SiStripApvGain' in line:
##       g1_tag = get_tag(line)
## logging.info( "noise tag: %s" % noisetag)
## logging.info( "gsim  tag: %s" % gsim_tag)
## logging.info( "g1    tag: %s" % g1_tag  )
## logging.info( "g2    tag: %s" % g2_tag  )

tfile = ROOT.TFile.Open(tfilename)
tree  = tfile.Get('treeDump/StripDBTree')
tags = eval(tfile.Get('DBTags').GetTitle() )

scatterplot = ROOT.TH2F('scatterplot', 'stip noise from DB vs stip length;strip length (cm);noise (ADC counts)', 200, 5, 25, 100, 0, 10)
plot1d = ROOT.TH1F('1dplot', ' ;strip length (cm);noise (ADC counts)', 200, 5, 25)

title = ' ;strip length (cm);noise (ADC counts)'
## def make_pretty(title):
##    tinfo = title.split(';')
##    lines = tinfo[0].split('\n')
##    while len(lines) > 1:
##       scnd = lines.pop()
##       frst = lines.pop()
##       lines.append(
##          ''.join(   
##             ['#splitline{',frst,'}{',scnd,'}']
##             )
##          )
## 
##    tinfo[0] = lines[0]
##    return ';'.join(tinfo)

set_titles = lambda hmap, title: [i.SetTitle(title) for i in hmap.itervalues()]
map_gsim = {
   'TIB' : plot1d.Clone('TIB'),
   'TID' : plot1d.Clone('TID'),
   'TOB' : plot1d.Clone('TOB'),
   'TEC' : plot1d.Clone('TEC'),
}
set_titles(map_gsim, title)

map_g1 = {
   'TIB' : plot1d.Clone('TIB'),
   'TID' : plot1d.Clone('TID'),
   'TOB' : plot1d.Clone('TOB'),
   'TEC' : plot1d.Clone('TEC'),
}
set_titles(map_g1, title)

map_gratio = {
   'TIB' : plot1d.Clone('TIB'),
   'TID' : plot1d.Clone('TID'),
   'TOB' : plot1d.Clone('TOB'),
   'TEC' : plot1d.Clone('TEC'),
}
set_titles(map_gratio, title)

map_length = {'TIB' : {}, 'TID' : {}, 'TOB' : {}, 'TEC' : {}}
tot_entries=tree.GetEntries()
cent=int(tot_entries/100)
logging.info('looping on strip tree (%i entries)' % tot_entries)
for i, entry in enumerate(tree):
   if (i % cent) == 0 or (opts.limit > 0 and i > opts.limit): 
      logging.info('reading entry %i of %i (%.2f%%)' % (i, tot_entries, 100*float(i)/tot_entries))
      if opts.limit > 0 and i > opts.limit:
         break
   region = getSubDet(entry)
   #scatterplot.Fill(entry.length, entry.noise/entry.APVgain)
   #bin = plot1d.GetXaxis().FindFixBin(entry.length) #avoid rounding issues
   bin = entry.length
   if bin not in map_length[region]:
      map_length[region][bin] = {
         'gsim' : Entry(),
         'g1' :  Entry(),
         'gratio' : Entry(),
         }

   map_length[region][bin]['gsim'].add(entry.noise/entry.gsim)
   map_length[region][bin]['g1'].add(entry.noise/entry.g1)
   map_length[region][bin]['gratio'].add((entry.g1*entry.g2/entry.gsim) -1)

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
         noises += vals[length]['gsim']
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
      },
   'title' : {
      'TextSize' : 0.02,
      'Margin' : 0.0,
      #'BorderSize' : 0,
      }
}
n_min = 1000
n_max = 0
hists = [map_gsim, map_g1, map_gratio]
names = ['gsim', 'g1', 'gratio']

for region, strips in map_length.iteritems():
   for length, info in strips.iteritems():
      gains = ['gsim', 'g1']
      bin = plot1d.GetXaxis().FindFixBin(length)
      for gain, hist in zip(gains, hists):
         noises = info[gain]
         mean    = noises.mean()
         std_dev = noises.std_dev()
         #print n_min, n_max, mean
         n_min = min(n_min, mean)
         n_max = max(n_max, mean)
         hist[region].SetBinContent(bin, mean)
         hist[region].SetBinError(bin, std_dev)

      mean    = info['gratio'].mean()
      std_dev = info['gratio'].std_dev()
      map_gratio[region].SetBinContent(bin, mean)
      map_gratio[region].SetBinError(bin, std_dev)

titles = {
   'gsim'  : 'stip noise from DB: %s \nAPVGain: %s' % (tags['SiStripNoisesRcd'], tags['SiStripApvGainSimRcd']),
   'g1'    : 'stip noise from DB: %s \nAPVGain: %s' % (tags['SiStripNoisesRcd'], tags['SiStripApvGainRcd']),
   'gratio': '(G1*G2)/GSim vs. stip length\ngsim: %s\ng1: %s\ng2: %s' % (
      tags['SiStripApvGainSimRcd'], 
      tags['SiStripApvGainRcd'], 
      tags['SiStripApvGain2Rcd']
      ),
}
for hmap, postfix in zip(hists, names):
   first=True
   ymin, ymax = int(n_min)-1, int(n_max)+1
   if postfix == 'gratio':
      ymin, ymax = -0.2, 0.2
   i_am_legend = ROOT.TLegend(0.52,0.1,0.9,0.4)
   i_am_legend.SetFillColor(0)
   for region in map_length:
      for attr, val in drawattrs[region].iteritems():
         getattr(hmap[region], 'Set%s' % attr)(val)
      draw_opt = '' if first else 'same'
      hmap[region].Draw(draw_opt)
      hmap[region].GetXaxis().SetRangeUser(5, 22)
      hmap[region].GetYaxis().SetRangeUser(ymin, ymax)
      i_am_legend.AddEntry(hmap[region],region,"p")
      first=False

   c.Update()
   c.cd()
   lines = titles[postfix].split('\n')
   title = ROOT.TPaveText(.001,1-0.04*len(lines),.8,.999, "brNDC")
   title.SetFillColor(0)
   title.SetBorderSize(1)
   #title.SetTextSize(12)
   title.SetMargin(0.)
   logging.debug('%s %s', postfix, titles[postfix])
   for line in lines:
      print line.__repr__()
      title.AddText(line)
   #for attr, val in drawattrs['title'].iteritems():
   #   getattr(title, 'Set%s' % attr)(val)      
   title.Draw('same')
   c.Update()
   #set_trace()
   #print n_min, n_max
   #hmap[map_length.keys()[0]].GetYaxis().SetRangeUser(ymin, ymax)
   i_am_legend.Draw()
   c.SaveAs(pngname.replace('.png', '_%s.png' % postfix))
