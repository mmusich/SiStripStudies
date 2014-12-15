#! /usr/bin/evn python

import os
import sys
from optparse import OptionParser
from pdb import set_trace

parser = OptionParser(description='process a CondDBMonitor output root file')
#parser.add_argument('tfilename', type=str)
#parser.add_argument('pngname', type=str)
_, args = parser.parse_args()
tfilename = args[0]
pngname = args[1]

import ROOT
ROOT.gROOT.SetStyle('Plain')
ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)

def GetContent(dir):
   'does not read key content'
   keys = dir.GetListOfKeys()
   return [(getattr(ROOT, i.GetClassName()), i.GetName(), i.GetTitle() if hasattr(i, 'GetTitle') else '') for i in keys]

def inherits_from(test, target):
    if test == target:
        return True
    return any( inherits_from(test, sub) 
                for sub in target.__subclasses__())

def mapdir(directory, dirName=''):
   dirContent = GetContent(directory)
   for obj_type, obj_name, _ in dirContent:
      path = os.path.join(dirName,obj_name)
      if inherits_from(obj_type, ROOT.TDirectory):
         entry= directory.Get(obj_name)
         for i in mapdir(entry, path):
            yield i #relay returned objects
      else:
         yield path

if not os.path.isfile(tfilename):
   raise ValueError('%s is not a valid file' % args.tfilename)

tfile = ROOT.TFile.Open(tfilename)

scatterplot = ROOT.TH2F('scatterplot', 'stip noise from DB vs stip length;strip length (cm);noise (ADC counts)', 200, 5, 25, 100, 0, 10)
plot1d = ROOT.TH1F('1dplot', 'stip noise from DB;strip length (cm);noise (ADC counts)', 200, 5, 25)
map_1d = {
   'TIB' : plot1d.Clone('TIB'),
   'TID' : plot1d.Clone('TID'),
   'TOB' : plot1d.Clone('TOB'),
   'TEC' : plot1d.Clone('TEC'),
}
needed_paths = [i for i in mapdir(tfile) if 'ProfileSummary_' in i]
groups = {}
for path in needed_paths:
   dirname = os.path.dirname(path)
   base = os.path.basename(path)
   info = base.split('_')[1]
   if dirname in groups:
      groups[dirname][info] = path
   else:
      groups[dirname] = {info : path}

strip_length = {}
map_length = {'TIB' : {}, 'TID' : {}, 'TOB' : {}, 'TEC' : {}}
for info in groups.itervalues():
   tracker_region = info['NoiseFromCondDB'].split('/')[3]
   h_noise  = tfile.Get(info['NoiseFromCondDB'])
   h_length = tfile.Get(info['LengthFromCondDB'])
   h_gain   = tfile.Get(info['ApvGainFromCondDB'])
   nstrips = h_noise.GetNbinsX()
   for i in xrange(1, nstrips+1):
      noise  = h_noise.GetBinContent(i) 
      length = h_length.GetBinContent(i) 
      apv = (i - 1)/128+1
      gain   = h_gain.GetBinContent(apv) 
      scatterplot.Fill(length, noise/gain)
      bin = plot1d.GetXaxis().FindFixBin(length) #avoid rounding issues
      if bin in strip_length:
         strip_length[bin].append(noise/gain)
      else:
         strip_length[bin] = [noise/gain]
      if bin in map_length[tracker_region]:
         map_length[tracker_region][bin].append(noise/gain)
      else:
         map_length[tracker_region][bin] = [noise/gain]

c = ROOT.TCanvas()
scatterplot.Draw()
c.SaveAs(pngname)

import numpy
for bin, noises in strip_length.iteritems():
   mean = numpy.mean(noises)
   std_dev  = numpy.std(noises)
   plot1d.SetBinContent(bin, mean)
   plot1d.SetBinError(bin, std_dev)

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
for region, strips in map_length.iteritems():
   for bin, noises in strips.iteritems():
      mean = numpy.mean(noises)
      std_dev  = numpy.std(noises)
      map_1d[region].SetBinContent(bin, mean)
      map_1d[region].SetBinError(bin, std_dev)

   for attr, val in drawattrs[region].iteritems():
      getattr(map_1d[region], 'Set%s' % attr)(val)
   draw_opt = '' if first else 'same'
   map_1d[region].Draw(draw_opt)
   map_1d[region].GetYaxis().SetRangeUser(3, 8)
   i_am_legend.AddEntry(map_1d[region],region,"p")
   first=False
i_am_legend.Draw()
c.SaveAs(pngname.replace('.png', '_separated_1d.png'))
