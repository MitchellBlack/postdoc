# Downscaling from ERA-Interim - Wangary fire

The following provides an application of running CCAM for integration with Spark. The Wangary fire (January 2005) will be used as a case study.

## 1. Install the CCAM model

Instructions on how to download the CCAM model are available [here](). Note that these may differ slightly for different computers (the current example was performed on the CSIRO HPC Pearcey machine).


## 2. Downscaling from ERA-Interim reanalysis

In this example we will downscale the ERA-Interim (~125km resolution, multi-hour timestep) over the Wangary region (final output ~1km resolution, 5 min timestep).

In order to downscale from 125km to 1km, we perform 'downscaling steps'. That is to say, we first downscale the ERA-Interim data to 60km; the output from this simulation is then downscaled to 8km, which in turn is downscaled to 1km.


### Specifying CCAM parameters

#### Downscaling step 1: 125km to 60km grid.

Within the file **run_ccam.sh** set the following:

```bash
nproc=96               ;# number of processors (change as required)
midlon=135.5           ;# central longitude of domain
midlat=-34.5           ;# central latitude of domain
gridres=60.0           ;# required resolution (km) of domain
gridsize=144           ;# cubic grid size (change as required) 
name=ccam_eraint_      ;# run name
iys=2005               ;# start year
ims=01                 ;# start month
iye=2005               ;# end year
ime=01                 ;# end month (note the current model simulation is for 1 month only; change as required)
dmode=0                ;# set to 0 when downscaling from ERA-Interim. Set to 2 when downscaling from an existing CCAM run.
ncsurf=0               ;# no output high frequency for this resolution.

```

Run the model: `sbatch run_ccam.sh`

#### Downscaling step 2: 60km to 8km grid.

Within the file **run_ccam.sh** change the following:

```bash
gridres=8.0                   ;# required resolution (km) of domain
dmode=2                       ;# downscaling (0=spectral(GCM), 1=SST-only, 2=spectral(CCAM) )
bcdir=$hdir/OUTPUT            ;# host atmospheric data (for dmode=0 or dmode=2)
bcdom=ccam_60.0km             ;# host file prefix

```

*As we are downscaling from a previous CCAM simulation, remove the file *year.qm* file. Failure to do so will result in the model crashing as it will be looking for the parent/host simulation for the following time period. That is to say, year.qm indicates the starting date for the simulation. This needs to be the same as for the parent (host) simulation.*

After deleting year.qm from working directory ($hdir), run the model again with the new 8km parameters: `sbatch run_ccam.sh`

#### Downscaling step 3: 8km to 1km grid.

Within the file **run_ccam.sh** change the following:

```bash
gridres=1.0                   ;# required resolution (km) of domain
dmode=2                       ;# downscaling (0=spectral(GCM), 1=SST-only, 2=spectral(CCAM) )
bcdir=$hdir/OUTPUT            ;# host atmospheric data (for dmode=0 or dmode=2)
bcdom=ccam_8.0km              ;# host file prefix

ncsurf=1                      ;# Output high-frequency data
ktc_surf=5                    ;# High-frequency file output period (5 mins in this example) 

```

After deleting year.qm from working directory ($hdir), run the model again with the new 1km parameters: `sbatch run_ccam.sh`

#### Preparing the output for integrating with SPARK.

CCAM will produce a file called **surf.ccam_1.0km.200501.nc** within the directory `$hdir/daily`. This is the file containing the 1km fields at 5 minute timesteps. This file will need to be post-processed before it can be read in with spark.

First, all of the meteorological variables are within the one file. They can be separated into individual files using the [NCO](http://nco.sourceforge.net/nco.html) package, using the following commands within a Linux environment:

```bash
ncks -v temp_scrn surf.ccam_1.0km.200501.nc surfccam_1km200501_temp_scrn.nc
ncks -v RH_scrn surf.ccam_1.0km.200501.nc surfccam_1km200501_RH_scrn.nc
ncks -v wspeed10m surf.ccam_1.0km.200501.nc surfccam_1km200501_wspeed10m.nc
ncks -v wdir10m surf.ccam_1.0km.200501.nc surfccam_1km200501_wdir10m.nc
```

Also, the NetCDF files will be in 'NetCDF-4/HDF5' format, which currently cannot be read by Workspace. To convert the files into NetCDF3/Classic format, use the [nccopy](http://www.unidata.ucar.edu/software/netcdf/docs/netcdf_utilities_guide.html#guide_nccopy) package commands:

```
nccopy -k classic {filenetcdf4}.nc {filenetcdf3}.nc

```

Where you change the above file names as appropriate. Now, the files will be ready for integrating into SPARK/SWIFT.


