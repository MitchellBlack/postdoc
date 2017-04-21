# **run_ccam.py**: a python script for automating CCAM

Author: [Mitchell Black](mailto:mitchell.black@csiro.au)

The following describes a python script that has been developed for automating the Conformal Cubic Atmospheric Model (CCAM).


## Overview
------

A new user can start using CCAM in a few simple steps:

1. [Install CCAM](https://bitbucket.csiro.au/users/bla375/repos/ccam_code/browse/ccam_install.md)
2. [Download the scripts **run_ccam.py**](https://bitbucket.csiro.au/users/bla375/repos/ccam_code/browse/run_ccam.py)
3. [Execute **run_ccam.py** from the command line or using the shell script **run_ccam.sh**](https://bitbucket.csiro.au/users/bla375/repos/ccam_code/browse/run_ccam.sh)
4. For an example of how to downscale ERA-Interim reanalysis data for SPARK or SWIFT, see [here](https://bitbucket.csiro.au/users/bla375/repos/ccam_code/browse/downscaling_example.md).

## run_ccam.py
------

An up-to-date version of **run_ccam.py** is available [here](https://bitbucket.csiro.au/users/bla375/repos/ccam_code/browse/run_ccam.py).

There is no need for the user to make changes to this code. All input arguments are provided via the command line.

To read a manual page for **run_ccam.py**, a user can type the following on the comand line:

`python run_ccam.py -h`

An example manual page is provided below.

```
usage: run_ccam.py [-h] [--name NAME] [--nproc NPROC] [--midlon MIDLON]
                   [--midlat MIDLAT] [--gridres GRIDRES]
                   [--gridsize {48,72,96,144,192,288,384,576,768}]
                   [--domain DOMAIN] [--mlev {27,35,54,72,108,144}]
                   [--iys IYS] [--ims {1,2,3,4,5,6,7,8,9,10,11,12}]
                   [--iye IYE] [--ime {1,2,3,4,5,6,7,8,9,10,11,12}]
                   [--leap {0,1}] [--ncountmax NCOUNTMAX] [--ktc KTC]
                   [--minlat MINLAT] [--maxlat MAXLAT] [--minlon MINLON]
                   [--maxlon MAXLON] [--reqres REQRES] [--plevs PLEVS]
                   [--dmode {0,1,2}] [--nstrength {0,1}] [--sib {1,2}]
                   [--aero {0,1}] [--conv {0,1,2}] [--cloud {0,1,2}]
                   [--bmix {0,1}] [--river {0,1}] [--mlo {0,1}] [--casa {0,1}]
                   [--ncout {0,1,2,3}] [--nctar {0,1}] [--ncsurf {0,1,2}]
                   [--ktc_surf KTC_SURF] [--bcdom BCDOM] [--sstfile SSTFILE]
                   [--sstinit SSTINIT] [--cmip {cmip5}]
                   [--rcp {historic,RCP26,RCP45,RCP85}] [--insdir INSDIR]
                   [--hdir HDIR] [--bcdir BCDIR] [--sstdir SSTDIR]
                   [--stdat STDAT] [--vegca VEGCA] [--aeroemiss AEROEMISS]
                   [--model MODEL] [--pcc2hist PCC2HIST] [--terread TERREAD]
                   [--igbpveg IGBPVEG] [--ocnbath OCNBATH]
                   [--casafield CASAFIELD]

Run the CCAM model

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           run name
  --nproc NPROC         number of processors
  --midlon MIDLON       central longitude of domain
  --midlat MIDLAT       central latitude of domain
  --gridres GRIDRES     required resolution (km) of domain
  --gridsize {48,72,96,144,192,288,384,576,768}
                        cubic grid size
  --domain DOMAIN       domain of topographic files
  --mlev {27,35,54,72,108,144}
                        number of model levels (27, 35, 54, 72, 108 or 144)
  --iys IYS             start year [YYYY]
  --ims {1,2,3,4,5,6,7,8,9,10,11,12}
                        start month [MM]
  --iye IYE             end year [YYYY]
  --ime {1,2,3,4,5,6,7,8,9,10,11,12}
                        end month [MM]
  --leap {0,1}          Use leap days (0=off, 1=on)
  --ncountmax NCOUNTMAX
                        Number of months before resubmit
  --ktc KTC             standard output period (mins)
  --minlat MINLAT       output min latitude (degrees)
  --maxlat MAXLAT       output max latitude (degrees)
  --minlon MINLON       output min longitude (degrees)
  --maxlon MAXLON       output max longitude (degrees)
  --reqres REQRES       required output resolution (degrees) (-1.=automatic)
  --plevs PLEVS         output pressure levels (hPa)
  --dmode {0,1,2}       downscaling (0=spectral(GCM), 1=SST-only,
                        2=spectral(CCAM) )
  --nstrength {0,1}     nudging strength (0=normal, 1=strong)
  --sib {1,2}           land surface (1=CABLE, 2=MODIS)
  --aero {0,1}          aerosols (0=off, 1=prognostic)
  --conv {0,1,2}        convection (0=2014, 1=2015a, 2=2015b)
  --cloud {0,1,2}       cloud microphysics (0=liq+ice, 1=liq+ice+rain,
                        2=liq+ice+rain+snow+graupel)
  --bmix {0,1}          boundary layer (0=Ri, 1=TKE-eps)
  --river {0,1}         river (0=off, 1=on)
  --mlo {0,1}           ocean (0=Interpolated SSTs, 1=Dynamical ocean)
  --casa {0,1}          CASA-CNP carbon cycle with prognostic LAI (0=off 1=on)
  --ncout {0,1,2,3}     standard output format (0=none, 1=CCAM, 2=CORDEX,
                        3=CTM)
  --nctar {0,1}         TAR output files in OUTPUT directory (0=off, 1=on)
  --ncsurf {0,1,2}      High-freq output (0=none, 1=lat/lon, 2=raw)
  --ktc_surf KTC_SURF   High-freq file output period (mins)
  --bcdom BCDOM         host file prefix for dmode=0 or dmode=2
  --sstfile SSTFILE     sst file for dmode=1
  --sstinit SSTINIT     initial conditions file for dmode=1
  --cmip {cmip5}        CMIP scenario
  --rcp {historic,RCP26,RCP45,RCP85}
                        RCP scenario
  --insdir INSDIR       install directory
  --hdir HDIR           script directory
  --bcdir BCDIR         host atmospheric data (for dmode=0 or dmode=2)
  --sstdir SSTDIR       SST data (for dmode=1)
  --stdat STDAT         eigen and radiation datafiles
  --vegca VEGCA         topographic datasets
  --aeroemiss AEROEMISS
                        path of aeroemiss executable
  --model MODEL         path of globpea executable
  --pcc2hist PCC2HIST   path of pcc2hist executable
  --terread TERREAD     path of terread executable
  --igbpveg IGBPVEG     path of igbpveg executable
  --ocnbath OCNBATH     path of ocnbath executable
  --casafield CASAFIELD
                        path of casafield executable

    Usage:
        python run_ccam.py [-h]

    Author:
        Mitchell Black, mitchell.black@csiro.au
```


## run_ccam.sh
------

Previously, the CCAM model has been automated using a bash script similar to [pd60_run.sh](http://www.hpc.csiro.au/users/244528/ccaminstall/scripts/clim/pd60_run.sh).

Existing CCAM users who are familiar with this shell environment can use the new script **run_ccam.sh** as a shell interface for **run_ccam.py**.

An up-to-date version of **run_ccam.sh** is available [here](https://bitbucket.csiro.au/users/bla375/repos/ccam_code/browse/run_ccam.sh).

To run CCAM, the user simply needs to change the arguments within **run_ccam.sh** and then submit the job for processing. For example,

`sbatch run_ccam.sh`


