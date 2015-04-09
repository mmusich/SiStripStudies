#! /bin/env bash

set -o errexit

#rm labels.txt tags.txt

echo "{" > opts.txt
for opt in $@ 
do
		echo $opt | awk -F= '{print "\""$1"\" : \""$2"\","}' >> opts.txt
done
echo "}" >> opts.txt

outputRootFile=`for i; do echo $i; shift; done| grep outputRootFile | awk -F= '{print $2}'`
echo cmsRun $CMSSW_BASE/src/SiStripStudies/macros/db_tree_dump.py $@
cmsRun $CMSSW_BASE/src/SiStripStudies/macros/db_tree_dump.py $@ > tags.txt
echo "{" > labels.txt
grep -E 'SiStrip.*Rcd' tags.txt | awk '{print "\""$1"\" : \""$5"\","}' >> labels.txt
echo "}" >> labels.txt

$CMSSW_BASE/src/SiStripStudies/macros/add_label.py $outputRootFile DBTags "`cat labels.txt`"
$CMSSW_BASE/src/SiStripStudies/macros/add_label.py $outputRootFile Opts "`cat opts.txt`"

rm labels.txt tags.txt opts.txt
