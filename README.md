Code for paper<br>
_Structural complementarity and similarity:
linking relational principles to network motifs_
=================================================================

    Talaga, S., & Nowak, A. (2022).
    Structural complementarity and similarity:
    linking relational principles to network motifs.
    arXiv preprint arXiv:2201.03664.

This repository allows replication of all results presented in the 
[paper](https://arxiv.org/abs/2201.03664).
The code should run for Python 3.8+. Main dependencies are specified
in `requirements.txt`. The core methods including _PathCensus_ algorithms
and structural coefficients are implemented in `pathcensus` package
It will be distributed through PyPI upon publication and currently
can be accessed and installed directly from its
[Github repo](https://github.com/sztal/pathcensus).
It is a full-featured package with detailed documentation and an extensive
suite of unit tests.

Downloading data depends also on `graph-tool` package
(not listed in `requirements.txt`)
which cannot be installed via PIP. Thus, it is recommended to run the project
within an isolated [Conda](https://docs.conda.io/en/latest/) environment.
Furthermore, installing `graph-tool` on Windows machines is problematic
and the instructions described here do not handle this specific case.
However, the precomputed raw data for running the analyses is already bundled
with the repository. However, in order to recalculate the data the network
datasets have to be downloaded from the Netzschleuder repository and this
depends on `graph-tool`.

**NOTE**

    The replication pipeline assumes that Conda distribution of Python is used.
    Replication using a non-Conda distribution is possible but may require
    some additional tweaking of the Makefile commands.

The rest of the document outlines the project structure and describes
all the steps necessary for reproducing the analyses. All the steps are
defined as `Makefile` commands to facilitate a seemless reproduction.

**NOTE**

    The `Makefile` used here is Unix-compatible. Windows users may have to
    define their own `makefile.bat` or just run command by hand.
    However, this should be easy as implementation of all the steps is defined
    transparently in the original `Makefile`.

Project structure
-----------------

    ????????? analyses                      <- Scripts for downloading and preparing data and notebook presenting the analyses
    ???   ????????? 1-domains                 <- Analysis of real networks from different domains + degree correlations in the configuration model
    ???   ????????? 2-social                  <- Discrimination between friendship and health advice networks
    ???   ????????? 3-proteins                <- Structural diversity of interactomes across the tree of life
    ???   ????????? 4-descriptive             <- Tables with descriptive statistics
    ???   ????????? 5-performance             <- Experimental analysis of the computational complexity of the 'PathCensus' algorithm
    ????????? data                  <- Here downloaded network datasets are stored; created when needed
    ????????? figures               <- Figures folder; created when needed
    ????????? src                   <- Project-specific code; installed as local package
    ???   ????????? _ns.py            <- Downloader class for the Netzschleuder repostitory
    ???   ????????? _argparse.py      <- Unimportant utility; do not touch
    ???   ????????? utils.py          <- Custom utility functions
    ????????? LICENCE
    ????????? Makefile            <- Defines commands for replicating the analyses
    ????????? README.md
    ????????? requirements.txt    <- Main dependencies except `pathcensus` and `graph_tool`
    ????????? setup.py            <- Setup configuration for the local `src` package

Data
----

All data used in this study was obtained from the
[Netzschleuder repository](https://networks.skewed.de/).


Pipeline
--------

Below we discuss the pipeline for reproducing the analyses
presented in the paper.

1. Unpack the repository or clone from Github.
2. Enter the root directory.
3. At this point you can run `make help` to see an overview of the
   available commands.
4. Run `make env`. This sets up a Conda environment named `scs-paper`.
5. Run `conda activate scs-paper` to activate the environment.
6. Run `make install-gt`. This installs `graph-tool`. This step is required
   only for downloading the networks from the Netzschleuder repository,
   so usually may be skipped as the data is already bundled with the repo.
7. Run `make install`. This installs everything else, including the
   `pathcensus` package.
8. Run `make networks` to download the networks used in the analyses.
   This is not required is one only want to re-run the notebooks
   as the precomputed data for the analyses is bundled with the repo.
   However, if the goal is to repeat the analysis in full, that is, also
   reproduce the precomputed datasets, then the networks have to be downloaded.
9. Run `make data` to generate the data used in the analyses presented in the
   paper. This is not required as the data is distributed with the code.
   The data produced by this command must be available to run the notebooks
   in the `analyses` folder.
10. Use the notebooks in `analyses` to replicate the results.


Testing
-------

The `pathcensus` package has an extensive unit test suite which can be
run to check if everything works fine on your machine.

```bash
# It is recommended to first create a separate virtual environment for testing
# and use it to isolate test running
git clone git@github.com:sztal/pathcensus.git
cd pathcensus
pip install -r requirements.txt
pip install -r requirements-tests.txt
pip install tox
make test-all
```

One of the final outputs of the `make test-all` will include a table
with unit test coverage statistics.

Documentation
-------------

Documentation for the `pathcensus` package can also be built and opened easily.

```bash
cd pathcensus
pip install -r requirements-docs.txt
make docs
```
