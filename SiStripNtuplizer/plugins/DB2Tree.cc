// -*- C++ -*-
//
// 
/**\class Convert noise and APVGain payload into a TTree

 Description: [one line class summary]

 Implementation:
     [Notes on implementation]
*/
//
// Original Author:  Mauro Verzetti
//
//


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/Framework/interface/EventSetup.h"

#include "CondFormats/SiStripObjects/interface/SiStripNoises.h"
#include "CondFormats/DataRecord/interface/SiStripNoisesRcd.h"
#include "CondFormats/SiStripObjects/interface/SiStripApvGain.h"
#include "CondFormats/DataRecord/interface/SiStripApvGainRcd.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "TTree.h"

#include "CalibTracker/SiStripCommon/interface/SiStripDetInfoFileReader.h"

#include "DataFormats/SiStripDetId/interface/TECDetId.h"
#include "DataFormats/SiStripDetId/interface/TIBDetId.h"
#include "DataFormats/SiStripDetId/interface/TIDDetId.h"
#include "DataFormats/SiStripDetId/interface/TOBDetId.h"

#include "DataFormats/Common/interface/DetSetNew.h"
#include "DataFormats/Common/interface/DetSetVectorNew.h"
#include <vector>
#include <unordered_map>
#include <map>
#include <string>

class DB2Tree : public edm::EDAnalyzer {
public:
  explicit DB2Tree(const edm::ParameterSet&);
  ~DB2Tree();

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);


private:
  virtual void beginJob() override;
  virtual void analyze(const edm::Event&, const edm::EventSetup&) override;
  virtual void endJob() override;
  void setTopoInfo(uint32_t detId);
  //virtual void beginRun(edm::Run const&, edm::EventSetup const&) override;
  //virtual void endRun(edm::Run const&, edm::EventSetup const&) override;
  //virtual void beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;
  //virtual void endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;

  // ----------member data ---------------------------
  TTree *tree_;
  SiStripDetInfoFileReader reader_; 


  //branches
  uint32_t detId_, layer_, ring_, istrip_; 
  float noise_, APVgain_, lenght_; 
  bool isTIB_, isTOB_, isTEC_, isTID_; 
};

//
// constants, enums and typedefs
//

//
// static data member definitions
//

//
// constructors and destructor
//
DB2Tree::DB2Tree(const edm::ParameterSet& iConfig):
  reader_(edm::FileInPath(std::string("CalibTracker/SiStripCommon/data/SiStripDetInfo.dat") ).fullPath()),
  detId_(0), layer_(0), ring_(0), istrip_(0),
  noise_(0), APVgain_(0), lenght_(0),
  isTIB_(0), isTOB_(0), isTEC_(0), isTID_(0)
{
  edm::Service<TFileService> fs;
   //now do what ever initialization is needed
  tree_ = fs->make<TTree>( "StripDBTree"  , "Tree with DB SiStrip info");

  //book branches (I know, hand-made, I hate it)
  tree_->Branch("detId/i", &detId_); 
  tree_->Branch("noise/F", &noise_); 
  tree_->Branch("istrip/i", &istrip_);
  tree_->Branch("APVgain/F", &APVgain_); 
  tree_->Branch("layer/i", &layer_); 
  tree_->Branch("ring/i", &ring_); 
  tree_->Branch("length/F", &lenght_); 
  tree_->Branch("isTIB/O", &isTIB_); 
  tree_->Branch("isTOB/O", &isTOB_); 
  tree_->Branch("isTEC/O", &isTEC_); 
  tree_->Branch("isTID/O", &isTID_); 
  //tree_->Branch("", &_); 

  //clusters cfg
  //edm::ParameterSet noise_label_ = iConfig.getParameter<edm::ParameterSet>("noiseLabel");
  //edm::ParameterSet gain_label = iConfig.getParameter<edm::ParameterSet>("gainLabel");
}



DB2Tree::~DB2Tree()
{
  // for(auto entry = functor_branches_.begin(); entry != functor_branches_.end(); ++entry)
  //   {
  //     delete entry->second.second;
  //   }
  // do anything here that needs to be done at desctruction time
  // (e.g. close files, deallocate resources etc.)

}


//
// member functions
//

void DB2Tree::setTopoInfo(uint32_t detId)
{
  int subDetId = ((detId>>25)&0x7);
  //because a central function would have been too easy
  //3->TIB 4->TID 5->TOB 6->TEC
  //maybe it's madness
  switch(subDetId){
  case 3: //TIB
    isTIB_=true; isTOB_=false; isTEC_=false; isTID_=false;
    layer_ = TIBDetId(detId).layer();
    ring_ =0;
    break;
  case 4: //TID
    isTIB_=false; isTOB_=false; isTEC_=false; isTID_=true;
    layer_ = -1*(2*TIDDetId(detId).side()-3)*TIDDetId(detId).wheel();
    ring_ = 0;
    break;
  case 5: //TOB
    isTIB_=false; isTOB_=true; isTEC_=false; isTID_=false;
    layer_ = TOBDetId(detId).layer();
    ring_ =0;
    break;
  case 6: //TEC    
    isTIB_=false; isTOB_=false; isTEC_=true; isTID_=false;
    layer_ = -1*(2*TECDetId(detId).side()-3)*TECDetId(detId).wheel();
    ring_ =0;
    break;
  }
  return;
}


// ------------ method called for each event  ------------
void
DB2Tree::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
  edm::ESHandle<SiStripNoises> noiseHandle;
  iSetup.get<SiStripNoisesRcd>().get(noiseHandle);

  edm::ESHandle<SiStripApvGain> gainHandle;
  iSetup.get<SiStripApvGainSimRcd>().get(gainHandle);
  
  std::vector<uint32_t> activeDetIds;
  noiseHandle->getDetIds(activeDetIds);
  
  int prev_subdetId = -1;
  for(uint32_t detid : activeDetIds){
      //std::vector<uint32_t>::const_iterator it = activeDetIds.cbegin(); it != activeDetIds.cend(); ++it){
    int subdetectorId = ((detid>>25)&0x7);
    if(subdetectorId != prev_subdetId){
      prev_subdetId = subdetectorId;
      setTopoInfo(detid);      
    }

    SiStripNoises::Range noiseRange = noiseHandle->getRange(detid);
    SiStripApvGain::Range gainRange = gainHandle->getRange(detid);
    unsigned int nStrip = reader_.getNumberOfApvsAndStripLength(detid).first*128;
    lenght_ = reader_.getNumberOfApvsAndStripLength(detid).second;
    detId_=detid;
    
    for(istrip_=0; istrip_<nStrip; ++istrip_){
      APVgain_ = gainHandle->getStripGain(istrip_, gainRange) ? gainHandle->getStripGain(istrip_, gainRange) : 1.;
      noise_ = noiseHandle->getNoise(istrip_, noiseRange);
      tree_->Fill();
    }
  }
}


// ------------ method called once each job just before starting event loop  ------------
void 
DB2Tree::beginJob()
{
}

// ------------ method called once each job just after ending the event loop  ------------
void 
DB2Tree::endJob() 
{
}

// ------------ method called when starting to processes a run  ------------
/*
void 
DB2Tree::beginRun(edm::Run const&, edm::EventSetup const&)
{
}
*/

// ------------ method called when ending the processing of a run  ------------
/*
void 
DB2Tree::endRun(edm::Run const&, edm::EventSetup const&)
{
}
*/

// ------------ method called when starting to processes a luminosity block  ------------
/*
void 
DB2Tree::beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/

// ------------ method called when ending the processing of a luminosity block  ------------
/*
void 
DB2Tree::endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void
DB2Tree::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}

//define this as a plug-in
#include "FWCore/PluginManager/interface/ModuleDef.h"
DEFINE_FWK_MODULE(DB2Tree);
