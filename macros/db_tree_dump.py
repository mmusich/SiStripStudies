import FWCore.ParameterSet.Config as cms
from fnmatch import fnmatch
import FWCore.ParameterSet.VarParsing as VarParsing
from pdb import set_trace

process = cms.Process("Reader")

options = VarParsing.VarParsing("analysis")

options.register ('outputRootFile',
                  "",
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "output root file")
options.register ('records',
                  [],
                  VarParsing.VarParsing.multiplicity.list, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "record:tag names to be used/changed from GT")
options.register ('external',
                  [],
                  VarParsing.VarParsing.multiplicity.list, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "record:fle.db picks the following record from this external file")
options.register ('runNumber',
                  1,
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.int,          # string, int, or float
                  "run number")
options.register ('GlobalTag',
                  '',
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "Correct noise for APV gain?")

options.parseArguments()


process.MessageLogger = cms.Service(
    "MessageLogger",
    debugModules = cms.untracked.vstring(''),
    #    cout = cms.untracked.PSet(
    #        threshold = cms.untracked.string('INFO')
)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
    )

process.source = cms.Source("EmptyIOVSource",
    firstValue = cms.uint64(options.runNumber),
    lastValue = cms.uint64(options.runNumber),
    timetype = cms.string('runnumber'),
    interval = cms.uint64(1)
)

connection_map = [
    # OLD DB version
    #('SiStrip*', 'frontier://FrontierProd/CMS_COND_31X_STRIP'), #one for everything in strips
    ('SiStrip*', 'frontier://PromptProd/CMS_CONDITIONS'),
]
if options.external:
    connection_map.extend(
        (i.split(':')[0], 'sqlite_file:%s' % i.split(':')[1]) for i in options.external
        )

connection_map.sort(key=lambda x: -1*len(x[0]))
def best_match(rcd):
    print rcd
    for pattern, string in connection_map:
        print pattern, fnmatch(rcd, pattern)
        if fnmatch(rcd, pattern):
            return string
records = []
if options.records:
    for record in options.records:
        rcd, tag = tuple(record.split(':'))
        records.append(
            cms.PSet(
                record = cms.string(rcd),
                tag    = cms.string(tag),
                connect = cms.untracked.string(best_match(rcd))
                )
            )

if options.GlobalTag:
    print "using global tag: %s" %options.GlobalTag
    process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
    process.GlobalTag.globaltag = '%s::All' % options.GlobalTag
    process.GlobalTag.DumpStat = cms.untracked.bool(True)
    process.GlobalTag.toGet = cms.VPSet(*records)
else:
    process.poolDBESSource = cms.ESSource(
        "PoolDBESSource",
        BlobStreamerName = cms.untracked.string('TBufferBlobStreamingService'),
        DBParameters = cms.PSet(
            messageLevel = cms.untracked.int32(1),  # it used to be 2
            authenticationPath = cms.untracked.string('/afs/cern.ch/cms/DB/conddb')
            ),
        DumpStat = cms.untracked.bool(True),
        timetype = cms.untracked.string('runnumber'),
        toGet = cms.VPSet(records),
        connect = cms.string('frontier://FrontierProd/CMS_COND_31X_STRIP')
        )

process.TFileService = cms.Service(
    "TFileService",
    fileName = cms.string(options.outputRootFile)
)
process.treeDump = cms.EDAnalyzer('DB2Tree')
process.p = cms.Path(process.treeDump)

