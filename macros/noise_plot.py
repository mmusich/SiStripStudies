#! /usr/bin/evn python

import os
import sys
from optparse import OptionParser
from pdb import set_trace
import subprocess
import logging
import copy
import re
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

parser = OptionParser(description='process a CondDBMonitor output root file')
parser.add_option('--plotOnly', action='store_true', default=False, help='runs only the plotting')
parser.add_option('--gsim', action='store_true', default=False, help='plots gsim')
parser.add_option('--g1', action='store_true', default=False, help='')
parser.add_option('--gratio', action='store_true', default=False, help='')
parser.add_option('--yrange', default='', type=str, help='')
#parser.add_argument('pngname', type=str)
opts, args = parser.parse_args()
tfilename  = args[0]
output_dir = args[1]

import ROOT
import math
ROOT.gROOT.SetStyle('Plain')
ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)

if not os.path.isfile(tfilename):
   raise ValueError('%s is not a valid file' % args.tfilename)

if not os.path.isdir(output_dir):
   os.mkdir(output_dir)

output_tfile=os.path.join(output_dir,'analyzed.root')

tfile = ROOT.TFile.Open(tfilename)
tags_str = tfile.Get('DBTags').GetTitle()
tags = eval(tags_str)
tfile.Close()

if not opts.plotOnly:
   ROOT.gROOT.ProcessLine('.L %s/src/SiStripStudies/macros/noise_analysis.C+' % os.environ['CMSSW_BASE'])
   ROOT.analyze_noise(tfilename, output_tfile, opts.gsim, opts.g1, opts.gratio)

logging.info('done')

drawattrs = [
   ('TID' , {
      'MarkerStyle' : 21,
      'MarkerColor' : 2,
      }), 
   ('TEC' , {
      'MarkerStyle' : 23,
      'MarkerColor' : 4,
      }),
   ('TIB' , {
      'MarkerStyle' : 20,
      'MarkerColor' : 1,
      }), 
   ('TOB' , {
      'MarkerStyle' : 22,
      'MarkerColor' : 3,
      }), 
]

def plot_dir(tfile, dirname, pngname, titletxt='', 
             yrange=(2, 8), xtitle='', ytitle='',
             xrange=(7, 21)):
   c = ROOT.TCanvas()
   c.SetGridx()
   c.SetGridy()
   n_min = 1000
   n_max = 0
   keep = []
   i_am_legend = ROOT.TLegend(0.52,0.1,0.9,0.3)
   i_am_legend.SetFillColor(0)
   first = True
   for region, attrs in drawattrs:
      graph = tfile.Get(
         os.path.join(
            dirname,
            region
            )
         )
      for attr, val in attrs.iteritems():
         getattr(graph, 'Set%s' % attr)(val)
      draw_opt = 'AP' if first else 'P same'
      graph.Draw(draw_opt)
      if first:
         graph.GetXaxis().SetLimits(*xrange)
         graph.GetYaxis().SetRangeUser(*yrange)
         graph.GetXaxis().SetTitle(xtitle)
         graph.GetYaxis().SetTitle(ytitle)
         graph.Draw(draw_opt)
      i_am_legend.AddEntry(graph, region, "p")
      keep.append(graph)
      first=False

   c.Update()
   c.cd()
   lines = titletxt.split('\n')
   title = ROOT.TPaveText(.001,1-0.04*len(lines),.8,.999, "brNDC")
   title.SetFillColor(0)
   title.SetBorderSize(1)
   title.SetMargin(0.)
   logging.debug('%s %s', pngname, titletxt)
   for line in lines:
      title.AddText(line)
   title.Draw('same')
   c.Update()

   i_am_legend.Draw()
   c.SaveAs(
      os.path.join(output_dir, pngname)
      )

   tdir = tfile.Get(dirname)
   keys = [i for i in tdir.GetListOfKeys()]
   regex= re.compile('G.+_T[A-Z]+_\d+\.?\d+')
   for key in keys:
      if not regex.match(key.GetName()):
         continue
      hist = key.ReadObj()
      hist.Draw('hist')
      title = ROOT.TPaveText(.2,1-0.04*(len(lines)+1),.999,.999, "brNDC")
      title.SetFillColor(0)
      title.SetBorderSize(1)
      title.SetMargin(0.)
      title.AddText(key.GetName().replace('_',' '))
      for line in lines:
         title.AddText(line)
      title.Draw('same')
      c.Update()
      c.SaveAs(
         os.path.join(output_dir, '%s.png' % key.GetName())
         )


plot_file = ROOT.TFile.Open(output_tfile, "update")
plots = {}
if opts.gsim:
   plots["GSim"] = {
      'titletxt' : 'stip noise from DB: %s \nAPVGain: %s' % (tags['SiStripNoisesRcd'], tags['SiStripApvGainSimRcd']),
      'xtitle' : 'strip length (cm)', 
      'ytitle' :'noise (ADC counts)',
      'yrange' : eval(opts.yrange) if opts.yrange else (2,8)
      }
if opts.g1:
   plots["G1"] = {
      'titletxt' : 'stip noise from DB: %s \nAPVGain: %s' % (tags['SiStripNoisesRcd'], tags['SiStripApvGainRcd']),
      'xtitle' : 'strip length (cm)',
      'ytitle' :'noise (ADC counts)',
      'yrange' : eval(opts.yrange) if opts.yrange else (2,8)
      }
if opts.gratio:
   plots["GRatio"] = {
      'titletxt' : '(G1*G2)/GSim vs. stip length\ngsim: %s\ng1: %s\ng2: %s' % (
         tags['SiStripApvGainSimRcd'],
         tags['SiStripApvGainRcd'],
         tags['SiStripApvGain2Rcd']
         ),
      'xtitle' : 'Layer',
      'ytitle' :'(G1*G2)/GSim',
      'yrange' : (-0.5, 0.5),
      'xrange' : (-10, 10),
      }

for dirname, kwargs in plots.iteritems():
   d = plot_file.Get(dirname)
   d.cd()
   if not d.Get('title'):
      txt = ROOT.TText(0, 0, kwargs['titletxt'])
      txt.SetName('title')
      txt.Write()
   plot_dir(
      plot_file, 
      dirname, 
      '%s.png' % dirname, 
      **kwargs
      )
