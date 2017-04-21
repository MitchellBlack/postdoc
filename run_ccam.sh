#!/bin/bash
#SBATCH --job-name=ccam
#SBATCH --mem=50gb
#SBATCH --nodes=5
#SBATCH --ntasks-per-node=20
#SBATCH --time=02:00:00

###############################################################
# PEARCEY MODULES

module unload openmpi
module load openmpi/1.8.8-mellanox
#module load mpt
module load netcdf/4.3.3.1
module load python



# RAIJIN MODULES
#module load python/2.7.5
#module load python/2.7.5-matplotlib
#module load hdf5
#module load netcdf

#NETCDF4_DIR=$NETCDF_ROOT pip install --user --build $TMPDIR/pip_build netcdf4

###############################################################
# This is the CCAM run script

# set -xv

# Example grid sizes and processor numbers
# C48  nproc = 1, 2, 3, 6, 12, 24, 48, 72, 96, 144, 192, 216
# C72  nproc = 6, 12, 24, 48, 72, 96, 144, 192, 216, 288, 384
# C96  nproc = 48, 72, 96, 144, 192, 216, 288, 384, 432, 768, 864
# C144 nproc = 96, 144, 192, 216, 288, 384, 432, 768, 864, 1536, 1728
# C192 nproc = 192, 216, 288, 384, 432. 768, 864, 1536, 1728, 3072, 3456
# C288 nproc = 384, 432. 768, 864, 1536, 1728, 3072, 3456, 6144, 6912
# C384 nproc = 768, 864, 1536, 1728, 3072, 3456, 6144, 6912, 12288, 13824
# C576 nproc = 1536, 1728, 3072, 3456, 6144, 6912, 12288, 13824, 24576, 27648
# C768 nproc = 3072, 3456, 6144, 6912, 12288, 13824, 24576, 27648, 49152, 55296

###############################################################
# Specify parameters

nproc=96                                     ;# number of processors

midlon=135.5                                  ;# central longitude of domain
midlat=-34.5                                  ;# central latitude of domain
gridres=1.0                                  ;# required resolution (km) of domain
gridsize=144                                  ;# cubic grid size 

name=ccam_${gridres}km                       ;# run name

mlev=27                                      ;# number of model levels (27, 35, 54, 72, 108 or 144)
iys=2005                                     ;# start year
ims=01                                       ;# start month
iye=2005                                     ;# end year
ime=01                                       ;# end month
leap=1                                       ;# Use leap days (0=off, 1=on)
ncountmax=12                                 ;# Number of months before resubmit

ktc=360                                                  ;# standard output period (mins)
minlat=$(bc -l <<< "( $midlat - $gridres * 1./112. * $gridsize / 2.)") ;# output min latitude (degrees)
maxlat=$(bc -l <<< "( $midlat + $gridres * 1./112. * $gridsize / 2.)") ;# output max latitude (degrees)
minlon=$(bc -l <<< "( $midlon - $gridres * 1./112. * $gridsize / 2.)") ;# output min longitude (degrees)
maxlon=$(bc -l <<< "( $midlon + $gridres * 1./112. * $gridsize / 2.)") ;# output max longitude (degrees)
echo $minlat, $maxlat, $minlon, $maxlon
reqres=-1.                                   ;# required output resolution (degrees) (-1.=automatic)
plevs="1000, 850, 700, 500, 300"             ;# output pressure levels (hPa)

dmode=0                                      ;# downscaling (0=spectral(GCM), 1=SST-only, 2=spectral(CCAM) )
nstrength=0                                  ;# nudging strength (0=normal, 1=strong)
sib=1                                        ;# land surface (1=CABLE, 2=MODIS)
aero=1                                       ;# aerosols (0=off, 1=prognostic)
conv=1                                       ;# convection (0=2014, 1=2015a, 2=2015b)
cloud=2                                      ;# cloud microphysics (0=liq+ice, 1=liq+ice+rain, 2=liq+ice+rain+snow+graupel)
bmix=0                                       ;# boundary layer (0=Ri, 1=TKE-eps)
river=1                                      ;# river (0=off, 1=on)
mlo=0                                        ;# ocean (0=Interpolated SSTs, 1=Dynamical ocean)
casa=0                                       ;# CASA-CNP carbon cycle with prognostic LAI (0=off 1=on)

ncout=1                                      ;# standard output format (0=none, 1=CCAM, 2=CORDEX, 3=CTM)
nctar=1                                      ;# TAR output files in OUTPUT directory (0=off, 1=on)
ncsurf=0                                     ;# High-freq output (0=none, 1=lat/lon, 2=raw)
ktc_surf=5                                   ;# High-freq file output period (mins)

bcdom=ccam_eraint_                            ;# host file prefix for dmode=0 or dmode=2

###############################################################
# Specify directories

cmip=cmip5                    ;# CMIP scenario
rcp=historic                  ;# RCP scenario
excdir=/home/bla375/ccam_code ;# code directory
insdir=$HOME/ccaminstall      ;# install directory
hdir=$FLUSHDIR/ccam/wangery   ;# script directory
bcdir=$insdir/erain            ;# host atmospheric data (for dmode=0 or dmode=2)
sstdir=$insdir/gcmsst         ;# SST data (for dmode=1)
stdat=$insdir/ccamdata        ;# eigen and radiation datafiles
vegca=$hdir/vegdata         ;# topographic datasets

sstfile=ACCESS1-0_RCP45_bcvc_osc_ots_santop96_18_0.0_0.0_1.0.nc ;# sst file for dmode=1
sstinit=$bcdir/$bcdom$iys$ims.nc          ;# initial conditions file for dmode=1



###############################################################
# Specify executables and scripts

aeroemiss=$insdir/src/bin/aeroemiss
model=$insdir/src/bin/globpea
pcc2hist=$insdir/src/bin/pcc2hist

terread=$insdir/src/bin/terread
igbpveg=$insdir/src/bin/igbpveg
ocnbath=$insdir/src/bin/ocnbath
casafield=$insdir/src/bin/casafield

###############################################################

python $excdir/run_ccam.py --name $name --nproc $nproc --midlon " $midlon" --midlat " $midlat" --gridres $gridres \
                   --gridsize $gridsize --mlev $mlev --iys $iys --ims $ims --iye $iye --ime $ime --leap $leap \
                   --ncountmax $ncountmax --ktc $ktc --minlat " $minlat" --maxlat " $maxlat" --minlon $minlon \
                   --maxlon $maxlon --reqres " $reqres" --plevs ${plevs// /} --dmode $dmode --nstrength $nstrength \
                   --sib $sib --aero $aero --conv $conv --cloud $cloud --bmix $bmix --river $river --mlo $mlo \
                   --casa $casa --ncout $ncout --nctar $nctar --ncsurf $ncsurf --ktc_surf $ktc_surf --bcdom $bcdom \
                   --sstfile $sstfile --sstinit $sstinit --cmip $cmip --rcp $rcp --insdir $insdir --hdir $hdir \
                   --bcdir $bcdir --sstdir $sstdir --stdat $stdat --vegca $vegca \
                   --aeroemiss $aeroemiss --model $model --pcc2hist $pcc2hist --terread $terread --igbpveg $igbpveg \
                   --ocnbath $ocnbath --casafield $casafield

if [ "`cat $hdir/year.qw`" != "Complete" ] && [ "`cat $hdir/restart.qw`" == "True" ]; then
  echo 'Restarting script'
  sbatch $excdir/run_ccam.sh
fi
