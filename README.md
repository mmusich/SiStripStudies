SiStripStudies
==============

#Installation

Inside a CMSSW src directory

```
git clone https://github.com/mverzett/SiStripStudies.git
```

Then compile

```
cmsenv
scram b
```

#Usage

Before starting working with the scripts it is better to source the envinronment.

```
source SiStripStudies/environment.sh
```

There are two main macros:
  - **db_tree_dump.sh**: It dumps the content of several interesting DB payloads into a ROOT tree
  - **noise_plot.py**: Besides its name it does much more. It analyzes the content of the ROOT tree produced by the previous macro

Both macros have to be configure through CLI and have help messages.
**N.B.:** To access the help message of db_tree_dump.sh, please call db_tree_dump.py, as I am still trying to expose the help message though bash

