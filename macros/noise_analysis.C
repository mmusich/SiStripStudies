#include <iostream>
#include "TTree.h"
#include "TMath.h"
#include <string>
#include <map>
#include <vector>
#include "TFile.h"
#include "TText.h"
#include "TGraphErrors.h"
#include "TH1F.h"
#include "TH2F.h"
#include "TUUID.h"
#include <sstream>
#include <fstream>
#include <set>

using namespace std;

class Mask {
public:
	Mask():
		container_(){}
	void add(unsigned int id, int apv) { container_.insert(make_pair(id, apv)); }
	bool has(unsigned int id, int apv) { return container_.find(make_pair(id, apv)) != container_.end(); }
private:
	set<pair<unsigned int, int> > container_;
};

class Entry{
public:
  Entry():
    entries(0),
    sum(0),
    sq_sum(0){}

  double mean() {return sum / entries;}
  double std_dev() {
    double tmean = mean();
    return TMath::Sqrt((sq_sum - entries*tmean*tmean)/(entries-1));
  }
	double mean_rms() { return std_dev()/TMath::Sqrt(entries); }

  void add(double val){
    entries++;
    sum += val;
    sq_sum += val*val;
  }

	void reset() {
    entries = 0;
    sum = 0;
    sq_sum = 0;
	}
private:
  long int entries;
  double sum, sq_sum;
};

typedef map<double, Entry> EntryMap;
typedef EntryMap::iterator EntryMapIT;

typedef map<double, TH1F>  HMap;
typedef HMap::iterator HMapIT;

/*void initMap(map<int, map<double, Entry> > &toinit){
  map<double, Entry> dummy;
  for(int i=0; i<4; i++)
    toinit.insert(make_pair<int, map<double, Entry> >(i, dummy));
    }*/

void loadGraph(EntryMap &input_map, TGraphErrors* graph){
  int ipoint = 0;
  for(EntryMapIT it = input_map.begin(); it != input_map.end(); ++it){
    //cout << ipoint << " " << it->first << " " << it->second.mean() << endl;
    graph->SetPoint(ipoint, it->first, it->second.mean());
    graph->SetPointError(ipoint, 0., it->second.std_dev());
    ipoint++;
  }
}

void makeGraphs(TFile* file, string dirname, EntryMap *input_map){
  TDirectory * dir =file->mkdir(dirname.c_str());
  dir->cd();
  string regions[4] = {"TIB", "TID", "TOB", "TEC"};
  
  for(int i=0; i<4; i++){
    TGraphErrors *graph = new TGraphErrors();
    graph->SetName(regions[i].c_str());
    //cout << regions[i] << endl;
    loadGraph(input_map[i], graph);
    graph->Write();
  }
}

enum OpMode {STRIP_BASED, APV_BASED, MODULE_BASED};

class Monitor2D {
public:
	Monitor2D(OpMode mode, const char* name, int nbinsx, double xmin, double xmax, int nbinsy, double ymin, double ymax):
		entryx_(),
		entryy_(),
		mode_(mode),
		obj_(name, "", nbinsx, xmin, xmax, nbinsy, ymin, ymax) {}

	Monitor2D():
		entryx_(),
		entryy_(),
		mode_(OpMode::STRIP_BASED),
		obj_() {}

	~Monitor2D() {}

	void Fill(int apv, int det, double vx, double vy) {
		switch(mode_) {
    case (OpMode::APV_BASED):
			// cout << "time to flush? " << !((apv == prev_apv_ && det == prev_det_) || prev_apv_ == 0) << 
			// 	" apv: " << apv << " prev_apv: " << prev_apv_ << " det: " << det << " prev_det: " << prev_det_ << endl;
      if(!((apv == prev_apv_ && det == prev_det_) || prev_apv_ == 0)){
				flush();
			}
				prev_apv_ = apv;
				prev_det_ = det;
      break;
    case (OpMode::MODULE_BASED):
      if(!(det == prev_det_ || prev_det_ == 0)){
				flush();
      }
			prev_det_ = det;
      break;
    case (OpMode::STRIP_BASED):
			flush();
			break;
		}
		entryx_.add(vx);
		entryy_.add(vy);
	}

	void flush() {
		//cout << "Monitor2D::flush" << endl;
		obj_.Fill(entryx_.mean(), entryy_.mean());
		entryx_.reset();
		entryy_.reset();
	}

	TH2F& hist() {
		flush();
		return obj_;
	}
private:
	int prev_apv_=0, prev_det_=0;
	Entry entryx_, entryy_;
	OpMode mode_;
	TH2F obj_;
};

class Filler {
public:
	Filler(string prefix, double hmax=20):
		emap_(),
		hmap_(),
		prefix_(prefix),
		hmax_(hmax) {}

	~Filler() {};

	void add(int idx, double length, double val){
		//cout << "Filler::add(" << prefix_ << ", " << op_mode_ << ")"<<endl;
		EntryMapIT found = emap_[idx].find(length);
		if(found == emap_[idx].end()){
			//cout << "adding new entry in map"<<endl;
			emap_[idx][length] = Entry();
			stringstream ss;
			ss << prefix_ << regions[idx] << "_" << length;
			hmap_[idx].insert(
				make_pair(
					length, 
					TH1F(ss.str().c_str(),"",100, 0, hmax_)
					)
				);
		}

		emap_[idx][length].add( val);
		hmap_[idx][length].Fill(val);
	}

	EntryMap* emap(){return emap_;}
	HMap* hmap(){return hmap_;}
	
private:
	EntryMap emap_[4];
	HMap hmap_[4];
	string prefix_;
	const string regions[4] = {"TIB", "TID", "TOB", "TEC"}; 
	double hmax_;
};

class TkMap {
public:
	TkMap(string name):
		detid_(0),
		counts_(0),
		file_(name) {}
	~TkMap() {file_.close();}
	
	void add(unsigned int det) {
		if(detid_ && detid_ != det) flush();
		detid_ = det;
		counts_++;
	}

	void flush() {
		file_ << detid_ << " " << counts_ << endl;
		counts_ = 0;
	}
private:
	unsigned int detid_, counts_;
	ofstream file_;
};

void analyze_noise(string input_file, string output_file, bool gsim_, bool g1_, bool gratio_, bool gain_=false, Mask mask_ = Mask(), OpMode op_mode_ = OpMode::STRIP_BASED){
  //region, strip length, Entries
	cout << "Running opts: " << endl <<
		"   input:  " << input_file << endl <<
		"   output: " << output_file << endl <<
		"   gsim:   " << gsim_ 		 << endl << 
		"   g1:     " << g1_ 			 << endl << 
		"   gratio  " << gratio_ 	 << endl << 
		"   gain    " << gain_ << endl << 
		"   op_mode:" << op_mode_ << endl;
  string regions[4] = {"TIB", "TID", "TOB", "TEC"};

	Filler fill_gsim("GSim_");
	Filler fill_g1("G1_");
	Filler fill_gratio("GRatio_");
	Filler fill_gain("GAIN_", 2);
	string det_types[] = {"UNKNOWN", "IB1", "IB2", "OB1", 
												"OB2", "W1A", "W2A", "W3A", "W1B", "W2B", 
												"W3B", "W4", "W5", "W6", "W7"};
	Monitor2D noise_vs_gain[15];
	string base("_noise_vs_gain");
	for(size_t i =0; i < 15; i++){
		noise_vs_gain[i] = Monitor2D(op_mode_, (det_types[i]+base).c_str(), 100, 0, 2, 208, 0, 52);
	}

	TkMap wrong_gain("wrong_gain.detlist"), no_noise("no_noise.detlist"), 
		saturated_noise("saturated_noise.detlist");

  unsigned int detId, ring, istrip, dtype; 
  Int_t layer;
  float noise, gsim, g1, g2, length; 
  bool isTIB, isTOB, isTEC, isTID;

  TFile *infile = TFile::Open(input_file.c_str());
  TTree *tree = (TTree*) infile->Get("treeDump/StripDBTree");

  //book branches (I know, hand-made, I hate it)
  tree->SetBranchAddress("detId/i", &detId); 
  tree->SetBranchAddress("noise/F", &noise); 
  tree->SetBranchAddress("istrip/i", &istrip);
  tree->SetBranchAddress("detType/i", &dtype); 
  tree->SetBranchAddress("gsim/F", &gsim); 
  tree->SetBranchAddress("g1/F", &g1); 
  tree->SetBranchAddress("g2/F", &g2); 
  tree->SetBranchAddress("layer/I", &layer); 
  //tree->SetBranchAddress("ring/i", &ring); 
  tree->SetBranchAddress("length/F", &length); 
  tree->SetBranchAddress("isTIB/O", &isTIB); 
  tree->SetBranchAddress("isTOB/O", &isTOB); 
  tree->SetBranchAddress("isTEC/O", &isTEC); 
  tree->SetBranchAddress("isTID/O", &isTID); 

  unsigned long int entries = tree->GetEntries();
  int cent = entries / 10;
	TH1::AddDirectory(kFALSE);

	unsigned int prev_det=0, prev_apv=0;
	int prev_subdet=-1, prev_type=-1; 
	double prev_length=-1;
	Entry enoise, eg1, egsim, eg2;

  for(unsigned long int ientry=0; ientry <= entries; ientry++){
		if(ientry < entries) tree->GetEntry(ientry);
		else {
			//on last event force flushing
			detId = 0;
			istrip = prev_apv*128+100;
		}
    if(ientry % cent == 0){ 
      cout << "reading entry " << ientry 
	   <<" of "<< entries <<" ("
	   <<float(ientry)/entries << ")" << endl;
    }
    unsigned int idx=0;
		if( mask_.has(detId, istrip/128) ) continue;

		bool flush = false;
		switch(op_mode_) {
		case (OpMode::APV_BASED):
			flush = (prev_det != 0 && prev_apv != istrip/128);
			break;
		case (OpMode::MODULE_BASED):
			flush = (prev_det != 0 && prev_det != detId);
			break;
		case (OpMode::STRIP_BASED):
			flush = (ientry != 0);
			break;
		}

		if(flush) {
			if(eg1.mean() > 0.8 && eg1.mean() < 1.3 && enoise.mean() < 1.9)
				no_noise.add(prev_det);
			else if(eg1.mean() > 0.2 && eg1.mean() < 0.42 && enoise.mean() > 2 && enoise.mean() < 10)
				wrong_gain.add(prev_det);
			else if(eg1.mean() > 0.8 && eg1.mean() < 1.4 && enoise.mean() > 2 && enoise.mean() > 40)
				saturated_noise.add(prev_det);
			
			if(gain_){
				fill_gain.add(prev_subdet, prev_length, eg1.mean());
				noise_vs_gain[prev_type].Fill(prev_apv, prev_det, eg1.mean(), enoise.mean());
			}
			if(gsim_){
				fill_gsim.add(prev_subdet, prev_length, enoise.mean()/egsim.mean());
			}
			if(g1_){
				fill_g1.add(prev_subdet, prev_length, enoise.mean()/eg1.mean());
			}
			if(gratio_){
				fill_gratio.add(prev_subdet, prev_length, (eg1.mean()*eg2.mean()/egsim.mean()) -1);
			}
			enoise.reset(); 
			eg1.reset();
			egsim.reset();
			eg2.reset();
		}
		if(ientry < entries) {
			if(isTOB){idx=2;}
			else if(isTEC){idx=3;}
			else if(isTID){idx=1;}
			
			enoise.add(noise);
			eg1.add(g1);
			egsim.add(gsim);
			eg2.add(g2);
			
			prev_det = detId;
			prev_apv = istrip/128;
			prev_subdet = idx; 
			prev_length = length;
			prev_type = dtype;
		}
  }
	cout << "loop done" << endl;
  TText* info = (TText*) infile->Get("DBTags");
	cout << "Got DB Info" << endl;
  //TText* clone_info = (TText*) info->Clone("DBTags");
  //clone_info->

	cout << "Opening output: " << output_file << endl;
  TFile *outfile = TFile::Open(output_file.c_str(),"RECREATE");
	
	if(gain_) {
		cout << "Saving Gain" << endl;
		makeGraphs(outfile, "Gain"  , fill_gain.emap());
		HMap* hmap = fill_gain.hmap();
		for(int i=0; i<4; i++){
			for(HMapIT it = hmap[i].begin(); it != hmap[i].end(); ++it){
				cout << "saving " << it->second.GetName() << endl;
				it->second.Write();
			}			
		}
		for(size_t i =0; i < 15; i++){
			noise_vs_gain[i].hist().Write();
		}
	}	
  if(gsim_) {   
		cout << "Saving GSim" << endl;
		makeGraphs(outfile, "GSim"  , fill_gsim.emap());
		HMap* hmap = fill_gsim.hmap();
		for(int i=0; i<4; i++){
			for(HMapIT it = hmap[i].begin(); it != hmap[i].end(); ++it){
				cout << "saving " << it->second.GetName() << endl;
				it->second.Write();
			}			
		}
	}
	if(g1_) {    
		cout << "Saving G1" << endl;
		makeGraphs(outfile, "G1"    , fill_g1.emap());
		HMap* hmap = fill_g1.hmap();
		for(int i=0; i<4; i++){
			for(HMapIT it = hmap[i].begin(); it != hmap[i].end(); ++it){
				cout << "saving " << it->second.GetName() << endl;
				it->second.Write();
			}			
		}
	}
	if(gratio_) {
		cout << "Saving GRatio" << endl;
		makeGraphs(outfile, "GRatio", fill_gratio.emap());
		HMap* hmap = fill_gratio.hmap();
		for(int i=0; i<4; i++){
			for(HMapIT it = hmap[i].begin(); it != hmap[i].end(); ++it){
				cout << "saving " << it->second.GetName() << endl;
				it->second.Write();
			}			
		}
	}
  outfile->Write();
  outfile->Close();
  infile->Close();
}
