#! /bin/env bash

set -o errexit

#rm labels.txt tags.txt
outputRootFile=`for i; do echo $i; shift; done| grep outputRootFile | awk -F= '{print $2}'`
cmsRun $CMSSW_BASE/src/SiStripStudies/macros/db_tree_dump.py $@ > tags.txt
echo "{" > labels.txt
grep -E 'SiStrip.*Rcd' tags.txt | awk '{print "\""$1"\" : \""$5"\","}' >> labels.txt
echo "}" >> labels.txt

$CMSSW_BASE/src/SiStripStudies/macros/add_label.py $outputRootFile DBTags "`cat labels.txt`"

rm labels.txt tags.txt
