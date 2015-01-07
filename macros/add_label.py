#! /bin/env python

import ROOT
import sys

#print sys.argv, len(sys.argv)
if len(sys.argv) != 4 or '--help' in sys.argv or '-h' in sys.argv:
   print "Usage add_label.py rootfile name content"
   retcode = 0 if '--help' in sys.argv or '-h' in sys.argv else 1
   sys.exit(retcode)

tf = ROOT.TFile.Open(sys.argv[1],'UPDATE')
text = ROOT.TText(0,0,sys.argv[3])
text.SetName(sys.argv[2])
#text.SetTitle(sys.argv[2])
text.Write()
#tf.Write()
tf.Close()

