#include <iostream>
#include "TTree.h"
#include "TMath.h"
#include <string>
#include <map>
#include <vector>
#include "TFile.h"
#include "TText.h"
#include "TGraphErrors.h"

using namespace std;

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
  void add(double val){
    entries++;
    sum += val;
    sq_sum += val*val;
  }
private:
  long int entries;
  double sum, sq_sum;
};

typedef map<double, Entry> EntryMap;
typedef EntryMap::iterator EntryMapIT;

/*void initMap(map<int, map<double, Entry> > &toinit){
  map<double, Entry> dummy;
  for(int i=0; i<4; i++)
    toinit.insert(make_pair<int, map<double, Entry> >(i, dummy));
    }*/

void loadGraph(EntryMap &input_map, TGraphErrors* graph){
  int ipoint = 0;
  for(EntryMapIT it = input_map.begin(); it != input_map.end(); ++it){
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
    loadGraph(input_map[i], graph);
    graph->Write();
  }
}

void analyze_noise(string input_file, string output_file){
  //region, strip length, Entries
  EntryMap map_gsim[4];
  EntryMap map_g1[4];
  EntryMap map_gratio[4];

  unsigned long int detId, layer, ring, istrip; 
  float noise, gsim, g1, g2, lenght; 
  bool isTIB, isTOB, isTEC, isTID;
  
  TFile *infile = TFile::Open(input_file.c_str());
  TTree *tree = (TTree*) infile->Get("treeDump/StripDBTree");

  //book branches (I know, hand-made, I hate it)
  //tree->SetBranchAddress("detId/i", &detId); 
  tree->SetBranchAddress("noise/F", &noise); 
  //tree->SetBranchAddress("istrip/i", &istrip);
  tree->SetBranchAddress("gsim/F", &gsim); 
  tree->SetBranchAddress("g1/F", &g1); 
  tree->SetBranchAddress("g2/F", &g2); 
  //tree->SetBranchAddress("layer/i", &layer); 
  //tree->SetBranchAddress("ring/i", &ring); 
  tree->SetBranchAddress("length/F", &lenght); 
  tree->SetBranchAddress("isTIB/O", &isTIB); 
  tree->SetBranchAddress("isTOB/O", &isTOB); 
  tree->SetBranchAddress("isTEC/O", &isTEC); 
  tree->SetBranchAddress("isTID/O", &isTID); 

  unsigned long int entries = tree->GetEntries();
  int cent = entries / 100;
  for(unsigned long int ientry=0; ientry < entries; ientry++){
    tree->GetEntry(ientry);
    if(ientry % cent == 0){ 
      cout << "reading entry " << ientry 
	   <<" of "<< entries <<" ("
	   <<float(ientry)/entries << ")" << endl;
    }
    unsigned int idx=0;
    if(isTOB){idx=2;}
    else if(isTEC){idx=3;}
    else if(isTID){idx=1;}

    EntryMapIT found = map_gsim[idx].find(lenght);
    if(found == map_gsim[idx].end()) {
      map_gsim[idx].insert(make_pair<double, Entry>(lenght, Entry()));
      map_g1[idx].insert(make_pair<double, Entry>(lenght, Entry()));
      map_gratio[idx].insert(make_pair<double, Entry>(lenght, Entry()));
    }
    
    map_gsim  [idx][lenght].add(noise/gsim);
    map_g1    [idx][lenght].add(noise/g1);
    map_gratio[idx][lenght].add((g1*g2/gsim) -1);
  }
  TText* info = (TText*) infile->Get("DBTags");
  //TText* clone_info = (TText*) info->Clone("DBTags");
  //clone_info->
  infile->Close();

  TFile *outfile = TFile::Open(output_file.c_str(),"RECREATE");
  makeGraphs(outfile, "GSim"  , map_gsim  );
  makeGraphs(outfile, "G1"    , map_g1    );
  makeGraphs(outfile, "GRatio", map_gratio);

  outfile->Close();

}
