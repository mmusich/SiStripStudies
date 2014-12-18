import FWCore.ParameterSet.Config as cms

import FWCore.ParameterSet.VarParsing as VarParsing

process = cms.Process("Reader")

options = VarParsing.VarParsing("analysis")

options.register ('outputRootFile',
                  "",
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "output root file")
options.register ('connectionString',
                  "",
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "connection string")
options.register ('recordName',
                  "",
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "record name")
options.register ('recordForQualityName',
                  "SiStripDetCablingRcd",
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "record name")
options.register ('tagName',
                  "",
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "tag name")
options.register ('runNumber',
                  0,
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



if options.GlobalTag:
    print "using global tag: %s" %options.GlobalTag
    process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
    process.GlobalTag.globaltag = '%s::All' % options.GlobalTag
else:
    process.poolDBESSource = cms.ESSource(
        "PoolDBESSource",
        BlobStreamerName = cms.untracked.string('TBufferBlobStreamingService'),
        DBParameters = cms.PSet(
            messageLevel = cms.untracked.int32(1),  # it used to be 2
            authenticationPath = cms.untracked.string('/afs/cern.ch/cms/DB/conddb')
            ),
        timetype = cms.untracked.string('runnumber'),
        connect = cms.string(options.connectionString),
        toGet = cms.VPSet(cms.PSet(
                record = cms.string(options.recordName),
                tag = cms.string(options.tagName)
                ))
        )

process.TFileService = cms.Service(
    "TFileService",
    fileName = cms.string(options.outputRootFile)
)
process.treeDump = cms.EDAnalyzer('DB2Tree')
process.p = cms.Path(process.treeDump)

