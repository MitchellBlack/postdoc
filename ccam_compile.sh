#!/bin/sh

# This script compiles all CCAM executables

module unload intel-fc
module unload openmpi
module unload netcdf

module load intel-fc/16.0.1.150
module load openmpi/1.8.8-mellanox
module load netcdf/4.3.3.1

#module load mpt # use mpt for Ruby

srcdir=$PWD

if [[ ! -d bin ]]; then
    echo $srcdir 
    echo mkdir bin 
    mkdir bin
fi

# ccam
if [[ -e $srcdir/bin/globpea ]]; then
   echo 'globpea is ready'
else
   cd $srcdir/ccam
   make clean
   make 
   mv globpea $srcdir/bin
   make clean
fi

# aeroemiss
if [[ -e $srcdir/bin/aeroemiss ]]; then
   echo 'aeroemiss is ready'
else
   cd $srcdir/aeroemiss
   make clean
   make
   mv aeroemiss $srcdir/bin
   make clean
fi

# pcc2hist
if [[ -e $srcdir/bin/pcc2hist ]]; then
   echo 'pcc2hist is ready'
else
   cd $srcdir/pcc2hist
   make clean
   make 
   mv pcc2hist $srcdir/bin
   make clean
fi

# cdfvidar
if [[ -e $srcdir/bin/cdfvidar ]]; then
   echo 'cdfvidar is ready'
else
   cd $srcdir/cdfvidar
   make clean
   make
   mv cdfvidar $srcdir/bin
   make clean
fi

# g2n
if [[ -e  $srcdir/bin/g2n ]]; then
   echo 'g2n is ready'
else
   cd $srcdir/g2n
   make clean
   make
   mv g2n $srcdir/bin
   make clean
fi

# igbpveg
if [[ -e $srcdir/bin/igbpveg ]]; then
   echo 'igbpveg is ready'
else
   cd $srcdir/igbpveg
   make clean
   make
   mv igbpveg $srcdir/bin
   make clean
fi

# terread
if [[ -e $srcdir/bin/terread ]]; then
   echo 'terread is ready'
else
   cd $srcdir/terread
   make clean
   make
   mv terread $srcdir/bin
   make clean
fi

#ocnbath
if [[ -e $srcdir/bin/ocnbath ]]; then
   echo 'ocnbath is ready'
else
   cd $srcdir/ocnbath
   make clean
   make
   mv ocnbath $srcdir/bin
   make clean
fi

# sibveg
if [[ -e $srcdir/bin/sibveg ]]; then
   echo 'sibveg is ready '
else
   cd $srcdir/sibveg
   make clean 
   make
   mv sibveg $srcdir/bin
   make clean
fi

# casafield
if [[ -e $srcdir/bin/casafield ]]; then
   echo 'casafield is ready '
else
   cd $srcdir/casafield
   make clean 
   make 
   mv casafield $srcdir/bin
   make clean
fi

# smclim
if [[ -e $srcdir/bin/smclim ]]; then
   echo 'smclim is ready '
else
   cd $srcdir/smclim
   make clean 
   make 
   mv smclim $srcdir/bin
   make clean
fi


echo "################################## compile is finish #####################################"
echo "######                                                                               #####"
echo "###### Please check on bin directory                                                 #####"
echo "###### on  srcdir/bin are :                                                          #####"
echo "######                     aeroemiss                                                 #####"
echo "######                     casafield                                                 #####"
echo "######                     cdfvidar                                                  #####"
echo "######                     g2n                                                       #####"
echo "######                     globpea                                                   #####"
echo "######                     igbpveg                                                   #####"
echo "######                     ocnbath                                                   #####"
echo "######                     pcc2hist                                                  #####"
echo "######                     sibveg                                                    #####" 
echo "######                     smclim                                                    #####"
echo "######                     terread                                                   #####"
echo "######                                                                               #####"
echo "##########################################################################################"
 
