#! /usr/bin/env python

import os
import sys
from optparse import OptionParser
from pdb import set_trace
import subprocess
import logging
import copy
import re
import shutil
import glob
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

parser = OptionParser(description='process a CondDBMonitor output root file')
parser.add_option('--plotOnly', action='store_true', default=False, help='runs only the plotting')
parser.add_option('--gsim', action='store_true', default=False, help='plots gsim')
parser.add_option('--g1', action='store_true', default=False, help='')
parser.add_option('--gain', action='store_true', default=False, help='')
parser.add_option('--gratio', action='store_true', default=False, help='')
parser.add_option('--maps', action='store_true', default=False, help='')
parser.add_option('--yrange', default='', type=str, help='')
parser.add_option('--mode', default='strip', type=str, help='compute the mean and distribution'
                  ' based on strip, apv, module values')
parser.add_option('--mask', default='', type=str, help='mask bad APVs')

#parser.add_argument('pngname', type=str)
opts, args = parser.parse_args()
tfilename  = args[0]
output_dir = args[1]

import ROOT
import math
ROOT.gROOT.SetStyle('Plain')
ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPalette(53)

if not os.path.isfile(tfilename):
   raise ValueError('%s is not a valid file' % args.tfilename)

if not os.path.isdir(output_dir):
   os.mkdir(output_dir)

output_tfile=os.path.join(output_dir,'analyzed.root')

tfile = ROOT.TFile.Open(tfilename)
tags_str = tfile.Get('DBTags').GetTitle()
with open(os.path.join(output_dir, 'DBTags.json'), 'w') as out:
   out.write(tags_str)
tags = eval(tags_str)
with open(os.path.join(output_dir, 'DBTags.raw_txt'), 'w') as out:
   format = '%30s | %s\n'
   out.write(format % ('record', 'tag'))
   out.write('-'*60+'\n')
   for i in tags.iteritems():
      out.write(format % i)

ropts_str = tfile.Get('Opts').GetTitle()
with open(os.path.join(output_dir, 'Opts.json'), 'w') as out:
   out.write(ropts_str)
ropts = eval(ropts_str)
with open(os.path.join(output_dir, 'Opts.raw_txt'), 'w') as out:
   format = '%30s | %s\n'
   out.write(format % ('option', 'value'))
   out.write('-'*60+'\n')
   for i in ropts.iteritems():
      out.write(format % i)
   out.write(format % ('plot opts', ' '.join(sys.argv[1:])))

tfile.Close()

if not opts.plotOnly:
   ROOT.gROOT.ProcessLine('.L %s/src/SiStripStudies/macros/noise_analysis.C+' % os.environ['CMSSW_BASE'])
   opmode = None
   mask = ROOT.Mask()
   if opts.mask:
      with open(opts.mask) as maskfile:
         maskre = re.compile('\d+')
         for line in maskfile:
            if maskre.match(line):
               info = line.split()
               mask.add(int(info[0]), int(info[1]))
   if opts.mode.lower() == 'strip':
      opmode = ROOT.OpMode.STRIP_BASED
   elif opts.mode.lower() == 'apv':
      opmode = ROOT.OpMode.APV_BASED
   elif opts.mode.lower() == 'module':
      opmode = ROOT.OpMode.MODULE_BASED
   else:
      raise ValueError('allowed operation modes: strip, apv, module')
   ROOT.analyze_noise(tfilename, output_tfile, opts.gsim, opts.g1, opts.gratio, opts.gain, mask, opmode)
   for detlist in glob.glob('*.detlist'):
      base = os.path.basename(detlist)
      shutil.move(detlist, os.path.join(output_dir, base))

logging.info('done')
if opts.maps:
   for dlist in glob.glob(os.path.join(output_dir, '*.detlist')):
      os.system('print_TrackerMap %s "%s" %s' % (dlist, dlist.split('.')[0], dlist.replace('.detlist', '.png')))

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

def make_title(lines, xmin, ymin, xmax, ymax):
   title = ROOT.TPaveText(xmin,ymin,xmax,ymax, "brNDC")
   title.SetFillColor(0)
   title.SetBorderSize(1)
   title.SetMargin(0.)
   for line in lines:
      title.AddText(line)
   return title

def plot_dir(tfile, dirname, pngname, titletxt='', 
             yrange=(2, 8), xtitle='', ytitle='',
             xrange=(7, 21), showstat=True):
   c = ROOT.TCanvas()
   c.SetGridx()
   c.SetGridy()
   n_min = 1000
   n_max = 0
   keep = []
   i_am_legend = ROOT.TLegend(0.52,0.1,0.9,0.3)
   i_am_legend.SetFillColor(0)
   first = True
   graph_map = {}
   for region, attrs in drawattrs:
      graph = tfile.Get(
         os.path.join(
            dirname,
            region
            )
         )
      graph_map[region] = dict([
            (round(graph.GetX()[i],4),
             (graph.GetY()[i], graph.GetEY()[i]))
             for i in range(graph.GetN())
            ])

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
   title = make_title(lines, .001,1-0.04*len(lines),.8,.999)
   title.Draw('same')
   c.Update()

   i_am_legend.Draw()
   c.SaveAs(
      os.path.join(output_dir, pngname)
      )

   tdir = tfile.Get(dirname)
   keys = [i for i in tdir.GetListOfKeys()]
   regex= re.compile('G.+_T[A-Z]+_\d+\.?\d+')
   type_regex= re.compile('G.+_[A-Z0-9]+')
   c.SetLogy(True)
   for key in keys:
      lenght_based = bool(regex.match(key.GetName()))
      type_based   = bool(type_regex.match(key.GetName()))
      print key.GetName(), lenght_based, type_based
      if not type_based:
         continue
      subdet = None
      length = None
      if lenght_based:
         subdet = key.GetName().split('_')[1]
         length = float(key.GetName().split('_')[2])
      hist = key.ReadObj()
      hist.GetXaxis().SetTitle(ytitle)
      hist.GetYaxis().SetTitle('counts')
      hist.Draw('hist')
      y_min = 1-0.04*(len(lines)+1)
      new_lines = [key.GetName().replace('_',' ')]+lines
      title = make_title(new_lines, .2,y_min,.999,.999)
      title.Draw('same')

      stats = ROOT.TPaveText(.6,y_min-0.04*5,.999,y_min-0.04, "brNDC")
      if showstat and lenght_based:
         stats.SetFillColor(0)
         stats.SetBorderSize(1)
         stats.SetMargin(0.)
         stats.AddText('mean: %.2f, from hist: %.2f' % (graph_map[subdet][length][0], hist.GetMean()))
         stats.AddText('RMS : %.2f, from hist: %.2f' % (graph_map[subdet][length][1], hist.GetRMS() ))
         stats.AddText('overflow: %.0f' % (hist.GetBinContent(hist.GetNbinsX()+1)))
         stats.Draw('same')

      c.Update()
      c.SaveAs(
         os.path.join(output_dir, '%s.png' % key.GetName())
         )
   c.SetLogy(False)
   if dirname == 'Gain':
      hsum = {}
      for key in keys:
         if 'tdirectory' not in key.GetClassName().lower():
            continue
         #set_trace()
         tdir = key.ReadObj()
         regions = ['diagonal', 'overflow', 'underflow', 'above', 'below', 'masked']
         colors  = [ROOT.kBlue, ROOT.kRed, 8, 6, ROOT.kOrange+1, ROOT.kCyan]
         samples = []
         top = .999
         for region, color in zip(regions, colors):
            sam = ROOT.TPaveText(.7,top-0.04,.999,top, "brNDC")
            top -= 0.04
            sam.SetFillColor(0)
            sam.SetBorderSize(0)
            sam.SetMargin(0.)
            sam.SetTextColor(color)
            sam.AddText(region)
            samples.append(sam)
         
         subdet = key.GetName()
         keep = []
         first_2d=True
         for region, color in zip(regions, colors):
            hist = tdir.Get(region)
            hist.SetFillColor(color)
            hist.SetLineColor(color)
            hist.SetMaximum(1)
            draw_opt = 'box' if first_2d else 'box same'
            first_2d = False
            hist.Draw(draw_opt)
            hist.GetXaxis().SetTitle('gain')
            hist.GetYaxis().SetTitle('noise')
            if region not in hsum:
               hsum[region] = hist.Clone('%s_noise_vs_gain' % region)
            else:
               hsum[region].Add(hist)
            keep.append(hist)
            [i.Draw() for i in samples]
            c.Update()
         c.SaveAs(
            os.path.join(output_dir, '%s.png' % key.GetName())
            )
      first_2d = True
      for hregion in hsum.itervalues():
         hregion.SetMaximum(1)
         draw_opt = 'box' if first_2d else 'box same'
         first_2d = False
         hregion.Draw(draw_opt)
      #c.SetLogy()
      [i.Draw() for i in samples]
      c.Update()
      c.SaveAs(
         os.path.join(output_dir, 'noise_vs_gain.png')
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
if opts.gain:
   plots["Gain"] = {
      'titletxt' : 'APV Gain vs. stip length\nAPVGain: %s' % (tags['SiStripApvGainRcd']),
      'xtitle' : 'Layer',
      'ytitle' :'G1',
      'yrange' : (-0.5, 0.5),
      'xrange' : (-10, 10),
      'showstat': False,
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
