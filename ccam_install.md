# CCAM installation

### Source code and initial condition model fields

* Markus Thatcher has a copy of all of the CCAM files on his home directory (Pearcey): `/datastore/tha051/ccaminstall`

* The model files are available under version control from the project's bitbucket repo: https://bitbucket.csiro.au/projects/CCAM

### Building the model

The model can be built on the Pearcey machine from the source code:

Parent directory `/home/bla375/ccaminstall/src`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/aeroemiss.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/casafield.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/ccam.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/cdfvidar.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/g2n.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/igbpveg.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/ocnbath.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/pcc2hist.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/sibveg.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/smclim.git`

  `git clone https://bla375@bitbucket.csiro.au/scm/~bla375/terread.git`

Clone the directories listed above into the directory `/home/bla375/ccaminstall/src`

Within this directory, run the following script: [ccam_compile.sh](https://bitbucket.csiro.au/users/bla375/repos/ccam_code/browse/ccam_compile.sh)

`bash ccam_compile.sh`

> This will compile all of the required code. NOTE: for Ruby, build the code using mpt (`module load mpt`). On Raijin and Pearcey, buld the code using openmpi (`module load mpi`).

### Additional data fields required for running CCAM

You will be required to copy/link additional files from Marcus' account:

Example working directory: `/home/bla375/ccaminstall/`

```
ln -s /datastore/tha051/ccaminstall/ccamdata 

ln -s /datastore/tha051/ccaminstall/erai

ln -s /datastore/tha051/ccaminstall/vegin

```


