#! /usr/bin/env python

import os
import sys
from optparse import OptionParser
from pdb import set_trace
import subprocess
import logging
import copy
import uuid
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


parser = OptionParser(description='process a CondDBMonitor output root file')
parser.add_option('--xtitle', default='length (cm)', type=str, help='')
parser.add_option('--ytitle', default='noise (ADC counts)', type=str, help='')
parser.add_option('--yrange', default='(2,8)', type=str, help='')
## #parser.add_argument('pngname', type=str)
## opts, args = parser.parse_args()

opts, args = parser.parse_args()
tfilenames  = args[1:]
output_pic  = args[0]

import ROOT
import math
ROOT.gROOT.SetStyle('Plain')
ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)

c = ROOT.TCanvas()
c.SetGridx()
c.SetGridy()
first = True
first_loop = True
keep = []
i_am_legend = ROOT.TLegend(0.52,0.1,0.9,0.3)
i_am_legend.SetFillColor(0)
offset = 0

def draw(tdir, name, marker, color, first, first_loop):
   g = tdir.Get(name)
   g.SetName(str(uuid.uuid1()))
   g.SetMarkerStyle(marker)
   g.SetMarkerColor(color)
   #g.SetTitleOffset(title_shift, 'Y')
   attr = 'P SAME'
   if first:
      attr = 'AP'
      g.GetXaxis().SetLimits(7, 21)
      g.GetYaxis().SetRangeUser(*eval(opts.yrange))
      first = False
   if first_loop:
      i_am_legend.AddEntry(g, name, "p")
   g.Draw(attr)
   g.GetXaxis().SetTitle(opts.xtitle)
   g.GetYaxis().SetTitle(opts.ytitle)
   keep.append(g)

for info, color, idx in zip(tfilenames, [2,4,1,3], xrange(10000)):
   print info, color, idx
   tfilename, dirname = tuple(info.split(':'))

   if not os.path.isfile(tfilename):
      raise ValueError('%s is not a valid file' % args.tfilename)
   
   tfile = ROOT.TFile.Open(tfilename)
   tdir  = tfile.Get(dirname)
   titletxt = tdir.Get('title').GetTitle()

   draw(tdir, 'TID', 21, color, first, first_loop)
   first = False               
   draw(tdir, 'TEC', 23, color, first, first_loop)
   draw(tdir, 'TIB', 20, color, first, first_loop)
   draw(tdir, 'TOB', 22, color, first, first_loop)
   first_loop = False

   lines = titletxt.split('\n')
   line_offset = 0.04*len(lines)+offset
   title = ROOT.TPaveText(.001,1-line_offset,.8,.999-offset, "brNDC")
   offset = line_offset + 0.005
   title.SetFillColor(0)
   title.SetBorderSize(1)
   title.SetMargin(0.)
   title.SetTextColor(color)
   for line in lines:
      title.AddText(line)
   title.Draw('same')
   keep.append(title)
   
   
i_am_legend.Draw()
c.Update()
c.SaveAs(output_pic)
