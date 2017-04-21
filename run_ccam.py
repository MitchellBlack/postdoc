import os
import argparse
import sys
import commands
from netCDF4 import Dataset
from calendar import monthrange

def main(inargs):
    "Run the CCAM model"

    global d
    d = vars(inargs)
    check_inargs()
    create_directories()
    check_surface_files()
    calc_dt_out()
    read_inv_schmidt()
    calc_res()
    set_ktc_surf()
    calc_dt_mod()

    for mth in xrange(0,d['ncountmax']):
        get_datetime()
        prep_iofiles()
        set_mlev_params()
        config_initconds()
        set_nudging()
        set_downscaling()
        set_cloud()
        set_river()
        set_ocean()
        set_atmos()
        set_surfc()
        set_aeros()
        create_aeroemiss_file()
        create_sulffile_file()
        create_input_file()
        prepare_ccam_infiles()
        check_correct_host()
        check_correct_landuse()
        run_model()
        post_process_output()
        update_yearqm()

    restart_flag()

def check_inargs():
    "Check all inargs are specified and are internally consistent"

    args2check = ['name','nproc','midlon','midlat','gridres','gridsize','mlev','iys',
                  'ims','iye','ime','leap','ncountmax','ktc','minlat','maxlat',
                  'minlon','maxlon','reqres','plevs','dmode','nstrength',
                  'sib','aero','conv','cloud','bmix','river','mlo','casa',
                  'ncout','nctar','ncsurf','ktc_surf','bcdom','sstfile',
                  'sstinit','cmip','insdir','hdir','bcdir','sstdir','stdat',
                  'vegca','aeroemiss','model','pcc2hist','terread','igbpveg','ocnbath','casafield']

    for i in args2check:
     if not( i in d.keys() ):
         print 'Missing input argument --'+i
         sys.exit(1)

    if d['ncout'] == 3 and d['sib'] != 2:
        raise ValueError, "sib=2 is required for ctm output"
        # I could simply hard-wire this here

    if d['ncout'] == 3 and d['nstrength'] != 1:
        raise ValueError, "nstrength=1 is required for ctm output"

    d['plevs'] = d['plevs'].replace(',',', ')

def check_surface_files():
    "Ensure surface datasets exist"

    d['domain'] = dict2str('{gridsize}_{midlon}_{midlat}_{gridres}km')

    for fname in ['topout','bath','casa']:
        if not(os.path.exists(dict2str('{vegca}/'+fname+'{domain}'))):        
            run_cable()

    for mon in xrange(1,13):
        if not(os.path.exists(dict2str('{vegca}/veg{domain}.'+mon_2digit(mon)))):
            run_cable()

def run_cable():
    "Generate topography and land-use files for CCAM"

    print "Generating topography file"
    d['inv_schmidt'] = float(d['gridres']) * float(d['gridsize']) / (112. * 90.)
    write2file('top.nml',top_template(),mode='w+')
    run_cmdline('ulimit -s unlimited && {terread} < top.nml')

    print "Generating MODIS land-use data"
    write2file('igbpveg.nml',igbpveg_template(),mode='w+')
    run_cmdline('ulimit -s unlimited && {igbpveg} -s 1000 < igbpveg.nml')
    run_cmdline('mv -f topsib{domain} topout{domain}')

    print "Processing bathymetry data"
    run_cmdline('ln -s {insdir}/vegin/*.bil .')
    write2file('ocnbath.nml',ocnbath_template(),mode='w+')
    run_cmdline('ulimit -s unlimited && {ocnbath} -s 1000 < ocnbath.nml')
    run_cmdline('rm -f *.bil')

    print "Processing CASA data"
    run_cmdline('ulimit -s unlimited && {casafield} -t topout{domain} -i {insdir}/vegin/casaNP_gridinfo_1dx1d.nc -o casa{domain}')

    run_cmdline('mv -f topout{domain} {vegca}')
    run_cmdline('mv -f veg{domain}* {vegca}')
    run_cmdline('mv -f bath{domain} {vegca}')
    run_cmdline('mv -f casa{domain} {vegca}')

def create_directories():
    "Create output directories and go to working directory"

    os.chdir(dict2str('{hdir}'))
    
    for dirname in ['daily','OUTPUT','RESTART','vegdata','wdir']:
        if not(os.path.isdir(dirname)):
            os.mkdir(dirname)
   
    run_cmdline('rm -f {hdir}/restart.qm')

    os.chdir('wdir')

def calc_dt_out():
    "Calculate model output timestep"

    d['dtout']=360  # raw cc output frequency (mins)

    if d['ncout'] == 3:
        d['dtout'] = 60 # need hourly output for CTM

    if d['ktc'] < d['dtout']:
        d['dtout'] = d['ktc']

def read_inv_schmidt():
    "Read inverse schmidt value from NetCDF topo file and calculate grid resolution"

    topofile = dict2str('{vegca}/topout{domain}')
    check_file_exists(topofile)
    d['topofile'] = topofile

    fread = Dataset(topofile,'r')
    d['inv_schmidt'] = fread.schmidt
    d['lon0'] = fread.lon0
    d['lat0'] = fread.lat0
    d['gridsize'] = len(fread.variables['longitude'])
    fread.close()

def calc_res():
    "Calculate resolution for high resolution area"

    gridres_m = d['gridres']*1000. # GRIDRES IN UNITS OF METERS

    res=d['reqres']
    if res == -1.:
        res = gridres_m/112000.

    d['gridres'] = gridres_m
    d['res'] = res

    # CHECK
    # 1. Should reqres be an input argument - how does this then relate to the pre-defind inv_schmidt?
    # 2. Note above I have divided by 112000. The original code had 100000.

def set_ktc_surf():
    "Set tstep for high-frequency output"

    if d['ncsurf'] == 0. :
        d['ktc_surf'] = d['dtout']

def calc_dt_mod():
    """Calculate model timestep.
     dt is a function of dx; dt out and ktc_surf must be integer multiples of dt"""

    # define dictionary of pre-defined dx (mtrs) : dt (sec) relationships
    d_dxdt = {60000:1200, 45000:900, 36000:720,
              30000:600, 18000:360, 15000:300,
              12000:240, 9000:180, 6000:120, 4500:90,
              4000:80, 3000:60, 2000:40, 1000:20,
              500:10, 200:4, 100:2, 50:1}

    # determine dt based on dx, dtout and ktc_surf
    for dx in sorted(d_dxdt):
        if ( d['gridres'] >= dx ) and ( 60 * d['dtout'] % d_dxdt[dx] == 0 ) and ( 60 * d['ktc_surf'] % d_dxdt[dx] == 0):
            d['dt'] = d_dxdt[dx]

    if d['gridres'] < 50:
        raise ValueError, "Minimum grid resolution of 50m has been exceeded"

    #if ( d['dtout'] % dt != 0 ):
    #    raise ValueError, "dtout must be a multiple of dt" # CHECK: Original code has dtout must be a multiple of dt/60
    #Is this not redundant code given that dt will be 1, above.

    if ( d['ktc'] % d['dtout'] != 0):
        raise ValueError, "ktc must be a multiple of dtout"

    if d['ncsurf'] != 0:
        if ( d['dtout'] % d['ktc_surf'] != 0): # This order is different to original code
            raise ValueError, "dtout must be a multiple of ktc_surf"

def get_datetime():
    "Determine relevant dates and timesteps for running model"

    # Load year.qm with current simulation year:
    fname=dict2str('{hdir}/year.qm')
    if (os.path.exists(fname)):
        yyyydd = open(fname).read()
        d['iyr']  = int(yyyydd[0:4])
        d['imth'] = int(yyyydd[4:6])
        print("ATTENTION:")
        print(dict2str("Simulation start date taken from {hdir}/year.qm"))
        print("Start date: "+str(d['iyr'])+mon_2digit(d['imth'])+'01')
        print("If this is the incorrect start date, please delete year.qm")
    else:
        d['iyr']  = d['iys']
        d['imth'] = d['ims']

    # Abort run at finish year:
    sdate = d['iyr']*100 +d['imth']
    edate = d['iye']*100 +d['ime']

    if sdate > edate:
        write2file(d['hdir']+'/year.qm',"Complete",mode='w+')
        raise ValueError, 'CCAM simulation completed normally'

    iyr = d['iyr']
    imth = d['imth']

    # Decade start and end:
    d['ddyear'] = iyr/10*10
    d['deyear'] = d['ddyear'] + 9

    # Calculate previous month:
    if imth == 1:
        d['imthlst'] = '12'
        d['iyrlst']  = iyr-1
    else:
        d['imthlst'] = imth-1
        d['iyrlst']  = iyr

    # Calculate the next month:
    if imth == 12:
        d['imthnxt'] = 1
        d['iyrnxt'] = iyr+1
    else:
        d['imthnxt'] = imth+1
        d['iyrnxt'] = iyr

    # Calculate the next next month (+2):
    if imth > 10:
        d['imthnxtb'] = imth-10
    else:
        d['imthnxtb'] = imth+2

    d['imthlst_2digit'] = mon_2digit(d['imthlst'])
    d['imth_2digit'] = mon_2digit(d['imth'])
    d['imthnxt_2digit'] = mon_2digit(d['imthnxt'])
    d['imthnxtb_2digit'] = mon_2digit(d['imthnxtb'])

   # Calculate number of days in current month:
    d['ndays']=monthrange(iyr,imth)[1]

    if (imth == 2) and (d['leap'] == 0):
        d['ndays']=28 #leap year turned off

    # Number of steps between output:
    d['nwt'] = d['dtout']*60/d['dt']

    # Number of steps in run:
    d['ntau'] = d['ndays']*86400/d['dt']

    # Start date string:
    d['kdates']=str(d['iyr']*10000 + d['imth']*100 + 01)

def prep_iofiles():
    "Prepare input and output files"

    # Define restart file:
    d['ifile'] = dict2str('Rest{name}.{iyrlst}{imthlst_2digit}')
    d['ofile'] = dict2str('{name}.{iyr}{imth_2digit}')

    # Define host model fields:
    d['mesonest'] = dict2str('{bcdom}.{iyr}{imth_2digit}')

    if d['bcdom'] == 'ccam_eraint_':
        d['mesonest'] = dict2str('{bcdom}{iyr}{imth_2digit}.nc')

    # Define restart file:
    d['restfile'] = dict2str('Rest{name}.{iyr}{imth_2digit}')

    # Define ozone infile:
    if d['rcp'] == "historic" or d['iyr'] < 2005 :
        d['ozone'] = dict2str('{stdat}/{cmip}/historic/pp.Ozone_CMIP5_ACC_SPARC_{ddyear}-{deyear}_historic_T3M_O3.nc')
    else:
        d['ozone'] = dict2str('{stdat}/{cmip}/{rcp}/pp.Ozone_CMIP5_ACC_SPARC_{ddyear}-{deyear}_{rcp}_T3M_O3.nc')

    # Define CO2 infile:
    d['co2file']= dict2str('{stdat}/{cmip}/{rcp}_MIDYR_CONC.DAT')

    for fname in [d['ozone'],d['co2file']]:
        check_file_exists(fname)

def set_mlev_params():
    "Set the parameters related to the number of model levels"

    d_mlev_eigenv = {27:"eigenv27-10.300", 35:"eigenv.35b", 54:"eigenv.54b", 72:"eigenv.72b", 108:"eigenv.108b", 144:"eigenv.144b"}
    d_mlev_modlolvl = {27:20, 35:30, 54:40, 72:60, 108:80, 144:100}

    d.update({'nmr': 1, 'acon': 0.00, 'bcon': 0.04, 'eigenv': d_mlev_eigenv[d['mlev']], 'mlolvl': d_mlev_modlolvl[d['mlev']]})

def config_initconds():
    "Configure initial condition file"

    d['nrungcm'] = 0

    if d['iyr'] == d['iys'] and d['imth'] == d['ims']:

        d['nrungcm'] = -1

        if d['dmode'] in [0,2]:
            d.update({'ifile': d['mesonest']})
        else:
            d.update({'ifile': d['sstinit']})

def set_nudging():
    "Set nudging strength parameters"

    if d['nstrength'] == 0:
        d.update({'mbd_base': 20, 'mbd_maxgrid': 999999, 'mbd_maxscale': 3000,
                'kbotdav': -900, 'sigramplow': 0.05})

    elif d['nstrength'] == 1:
        d.update({'mbd_base': 20, 'mbd_maxgrid': 24, 'mbd_maxscale': 500,
                'kbotdav': 1, 'sigramplow': 0.00})

def set_downscaling():
    "Set downscaling parameters"

    if d['dmode'] == 0:
        d.update({'dmode_meth': 0, 'nud_p': 1, 'nud_q': 0, 'nud_t': 1,
                'nud_uv': 1, 'mfix': 0, 'mfix_qg': 1, 'mfix_aero': 1,
                'nbd': 0, 'mbd': d['mbd_base'], 'namip': 0, 'nud_aero': 0})

    elif d['dmode'] == 1:
        d.update({'dmode_meth': 1, 'nud_p': 0, 'nud_q': 0, 'nud_t': 0,
                'nud_uv': 0, 'mfix': 1, 'mfix_qg': 1, 'mfix_aero': 1,
                'nbd': 0, 'mbd': 0, 'namip': 14, 'nud_aero': 0})

    elif d['dmode'] == 2:
        d.update({'dmode_meth': 0, 'nud_p': 1, 'nud_q': 1, 'nud_t': 1,
                'nud_uv': 1, 'mfix': 0, 'mfix_qg': 0, 'mfix_aero': 0,
                'nbd': 0, 'mbd': d['mbd_base'], 'namip': 0, 'nud_aero': 1})

def set_cloud():
    "Cloud microphysics settings"

    if d['cloud'] == 0:
        d.update({'ncloud': 0})

    elif d['cloud'] == 1:
        d.update({'ncloud': 2})

    elif d['cloud'] == 2:
        d.update({'ncloud': 3})

def set_river():
    "River physics settings"

    if d['river'] == 0:
        d.update({'nriver': 0})

    elif d['river'] == 1:
        d.update({'nriver': -1})

def set_ocean():
    "Ocean physics settings"

    if d['mlo'] == 0:
        #Interpolated SSTs
        d.update({'nmlo': 0, 'mbd_mlo': 0, 'nud_sst': 0,
                'nud_sss': 0, 'nud_ouv': 0, 'nud_sfh': 0,
                'kbotmlo': -1000})

    else:
        #Dynanical Ocean
        if d['river'] != 1:
            raise ValueError, 'river=1 is a requirement for ocean mlo=1'

        if d['dmode'] == 0 or d['dmode'] == 1:
            # Downscaling mode - GCM or SST-only:
            d.update({'nmlo': -3, 'mbd_mlo': 20, 'nud_sst': 1,
                    'nud_sss': 0, 'nud_ouv': 0, 'nud_sfh': 0,
                    'kbotmlo': -100})

        elif d['dmode'] == 2:
            # Downscaling CCAM:
            d.update({'nmlo': -3, 'mbd_mlo': 20, 'nud_sst': 1,
                    'nud_sss': 1, 'nud_ouv': 1, 'nud_sfh': 1,
                    'kbotmlo': -1000})

def set_atmos():
    "Atmospheric physics settings"
    if d['sib'] == 1:
        d.update({'nsib': 7})

        if d['casa'] == 0:
            d.update({'ccycle': 0, 'proglai': -1})

        elif d['casa'] == 1:
            d.update({'ccycle': 3, 'proglai': 1})

    elif d['sib'] == 2:
        d.update({'nsib': 5, 'ccycle': 0, 'proglai': -1})

        if d['casa'] == 1:
            raise ValueError, "casa=1 requires sib=1"

    d.update({ 'vegin': d['vegca'],
        'vegprev': dict2str('veg{domain}.{imthlst_2digit}'),
        'vegfile': dict2str('veg{domain}.{imth_2digit}'),
        'vegnext': dict2str('veg{domain}.{imthnxt_2digit}'),
        'vegnextb': dict2str('veg{domain}.{imthnxtb_2digit}') })

    if d['bmix'] == 0:
        d.update({'nvmix': 3, 'nlocal': 6})

    elif d['bmix'] == 1:
        d.update({'nvmix': 6, 'nlocal': 7})

    d.update({'ngwd': -5, 'helim': 800., 'fc2': 1., 'sigbot_gwd': 0., 'alphaj': '0.000001'})

    if d['conv'] == 2:
        d.update({'ngwd': -20, 'helim': 1600.,'fc2': -0.5, 'sigbot_gwd': 1., 'alphaj': '0.025'})

def set_surfc():
    "Prepare surface files"

    d.update({'tbave': 0, 'tblock': 0})

    if d['ncsurf'] in [1,2]:
        d.update({'tbave': d['ktc_surf'] * 60 / d['dt'],
                  'tblock': d['dtout'] / d['ktc_surf'] })

def set_aeros():
    "Prepare aerosol files"

    if d['aero'] == 0:
        # Aerosols turned off
        d.update({'iaero': 0, 'sulffile' : 'none'})

    if d['aero'] == 1:
        # Prognostic aerosols
        d.update({'iaero': -2, 'sulffile': 'aero.nc'})

        fpath_cmip =dict2str('{stdat}/{cmip}/{rcp}')

        if d['rcp'] == "historic":
            aero = {
                    'so2_anth': get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_SO2_anthropogenic_{ddyear}*.nc'),
                    'so2_ship': get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_SO2_ships_{ddyear}*.nc'),
                    'so2_biom': get_fpath('{stdat}/{cmip}/{rcp}/IPCC_GriddedBiomassBurningEmissions_SO2_decadalmonthlymean{ddyear}*.nc'),
                    'bc_anth':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_BC_anthropogenic_{ddyear}*.nc'),
                    'bc_ship':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_BC_ships_{ddyear}*.nc'),
                    'bc_biom':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_GriddedBiomassBurningEmissions_BC_decadalmonthlymean{ddyear}*.nc'),
                    'oc_anth':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_OC_anthropogenic_{ddyear}*.nc'),
                    'oc_ship':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_OC_ships_{ddyear}*.nc'),
                    'oc_biom':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_GriddedBiomassBurningEmissions_OC_decadalmonthlymean{ddyear}*.nc')}

        elif d['iyr'] >= 2010 :
            aero = {
                    'so2_anth': get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_SO2_anthropogenic_{ddyear}*.nc'),
                    'so2_ship': get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_SO2_ships_{ddyear}*.nc'),
                    'so2_biom': get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_SO2_biomassburning_{ddyear}*.nc'),
                    'bc_anth':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_BC_anthropogenic_{ddyear}*.nc'),
                    'bc_ship':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_BC_ships_{ddyear}*.nc'),
                    'bc_biom':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_BC_biomassburning_{ddyear}*.nc'),
                    'oc_anth':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_OC_anthropogenic_{ddyear}*.nc'),
                    'oc_ship':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_OC_ships_{ddyear}*.nc'),
                    'oc_biom':  get_fpath('{stdat}/{cmip}/{rcp}/IPCC_emissions_{rcp}_OC_biomassburning_{ddyear}*.nc')}
        else:
            aero = {
                    'so2_anth': get_fpath('{stdat}/{cmip}/historic/IPCC_emissions_SO2_anthropogenic_{ddyear}*.nc'),
                    'so2_ship': get_fpath('{stdat}/{cmip}/historic/IPCC_emissions_SO2_ships_{ddyear}*.nc'),
                    'so2_biom': get_fpath('{stdat}/{cmip}/historic/IPCC_GriddedBiomassBurningEmissions_SO2_decadalmonthlymean{ddyear}*.nc'),
                    'bc_anth':  get_fpath('{stdat}/{cmip}/historic/IPCC_emissions_BC_anthropogenic_{ddyear}*.nc'),
                    'bc_ship':  get_fpath('{stdat}/{cmip}/historic/IPCC_emissions_BC_ships_{ddyear}*.nc'),
                    'bc_biom':  get_fpath('{stdat}/{cmip}/historic/IPCC_GriddedBiomassBurningEmissions_BC_decadalmonthlymean{ddyear}*.nc'),
                    'oc_anth':  get_fpath('{stdat}/{cmip}/historic/IPCC_emissions_OC_anthropogenic_{ddyear}*.nc'),
                    'oc_ship':  get_fpath('{stdat}/{cmip}/historic/IPCC_emissions_OC_ships_{ddyear}*.nc'),
                    'oc_biom':  get_fpath('{stdat}/{cmip}/historic/IPCC_GriddedBiomassBurningEmissions_OC_decadalmonthlymean{ddyear}*.nc')}

        aero['volcano'] = dict2str('{stdat}/contineous_volc.nc')
        aero['dmsfile'] = dict2str('{stdat}/dmsemiss.nc')
        aero['dustfile'] = dict2str('{stdat}/ginoux.nc')     
        
        for fpath in aero.iterkeys():
            check_file_exists(aero[fpath])

        d.update(aero)

def create_aeroemiss_file():
    "Write arguments to 'aeroemiss' namelist file"

    if d['aero'] == 1:
        write2file('aeroemiss.nml',aeroemiss_template(),mode='w+')

def create_sulffile_file():
    "Create the aerosol forcing file"

    # Remove any existing sulffile:
    run_cmdline('rm -rf {sulffile}')

    # Create new sulffile:
    run_cmdline('{aeroemiss} -o {sulffile} < aeroemiss.nml > aero.log || exit')

def create_input_file():
    "Write arguments to the CCAM 'input' namelist file"

    write2file('input',input_template_1(),mode='w+')

    if d['conv'] == 0:
        write2file('input',input_template_2())

    elif d['conv'] == 1:
        write2file('input',input_template_3())

    elif d['conv'] == 2:
        write2file('input',input_template_4())

    write2file('input',input_template_5())

def prepare_ccam_infiles():
    "Prepare and check CCAM input data"

    if d['dmode'] == 0 or d['dmode'] == 2:
        fpath = dict2str('{bcdir}/{mesonest}')

        if d['bcdom'] == "ccam_eraint_":
            check_file_exists(fpath)
            run_cmdline('ln -s '+fpath+' .')

        elif os.path.exists(fpath+'.000000'):
            run_cmdline('ln -s '+fpath+'.?????? .')

        else:
            check_file_exists(fpath+'.tar')
            run_cmdline('tar xvf '+fpath+'.tar')

    if d['dmode'] == 1:
        check_file_exists(dict2str('{sstinit}'))
        run_cmdline('ln -s {sstinit} .')

    if not(os.path.exists(d['ifile'])) and not(os.path.exists(d['ifile']+'.000000')):
        raise ValueError(dict2str('Cannot locate {ifile} or {ifile}.000000. ')+
                         'If this is the start of a new run, please check that year.qm has been deleted')

    if d['dmode'] != 1:
        if not(os.path.exists(d['mesonest'])) and not(os.path.exists(d['mesonest']+'.000000')):
            raise ValueError(dict2str('Cannot locate {mesonest} or {mesonest}.000000'))

    for file in ['topout{domain}', '{vegprev}', '{vegfile}', '{vegnext}', '{vegnextb}']:
        check_file_exists(dict2str('{vegin}/'+file))

    if d['nmlo'] != 0 and not(os.path.exists(dict2str('{vegin}/bath{domain}'))):
        raise ValueError(dict2str('Cannot locate {vegin}/bath{domain}'))

    if d['aero'] != 0 and not(os.path.exists(d['sulffile'])):
        raise ValueError('Cannot locate '+d['sulffile'])

    if d['dmode'] == 1 and not(os.path.exists(dict2str('{sstdir}/{sstfile}'))):
        raise ValueError(dict2str('Cannot locate {sstdir}/{sstfile}'))

def check_correct_host():
    "Check if host is CCAM"

    if d['dmode'] in [0,2]:
        for fname in [d['mesonest'], d['mesonest']+'.000000']:
            if os.path.exists(fname):
                ccam_host = (commands.getoutput('ncdump -c '+fname+' | grep -o version') == "version")
                break
        if ccam_host == True and d['dmode'] == 0:
            raise ValueError('CCAM is the host model. Use dmode = 2')
        elif ccam_host == False and d['dmode'] == 2:
            raise ValueError('CCAM is not the host model. Use dmode = 0')

def check_correct_landuse():
    "Check that land-use data matches what the user wants"

    fname = dict2str('{vegin}/{vegfile}')

    cable_data = (commands.getoutput('ncdump -c '+fname+' | grep -o cableversion') == "cableversion")
    if d['sib'] == 2 and cable_data == True:
        raise ValueError('MODIS surface selected with sib=2, but CABLE data is in the input file')

    modis_data = (commands.getoutput('ncdump -c '+fname+' | grep -o sibvegversion') == "sibvegversion")
    if d['nsib'] == 1 and modis_data == True:
        raise ValueError('CABLE surface selected with sib=1, but MODIS data is in the input file')

def run_model():
    "Execute the CCAM model"

    run_cmdline('mpirun -np {nproc} {model} > prnew.{kdates}.{name} 2> err.{iyr} || exit')
    run_cmdline('rm {mesonest}.?????? {mesonest}')

def post_process_output():
    "Post-process the CCAM model output"

    if d['ncout'] == 1:
        write2file('cc.nml',cc_template_1(),mode='w+')
        run_cmdline('mpirun -np {nproc} {pcc2hist} > pcc2hist.log')

    if d['ncout'] == 2:
        write2file('cc.nml',cc_template_2(),mode='w+')
        run_cmdline('mpirun -np {nproc} {pcc2hist} --cordex > pcc2hist.log')

    if d['ncout'] == 3:
        if d['sib'] == 2:
            for iday in xrange(1,d['ndays']+1):
                d['cday'] = mon_2digit(iday)
                d['iend'] = iday*1440
                d['istart'] = (iday*1440)-1440
                d['outctmfile'] = dict2str('ctm_{iyr}{imth_2digit}{cday}.nc',d)
                write2file('cc.nml',cc_template_3(),mode='w+')
                run_cmdline('mpirun -np {nproc} {pcc2hist} > pcc2hist_ctm.log')

            run_cmdline('tar cvf {hdir}/daily/ctm_{iyr}{imth_2digit}.tar ctm_{iyr}{imth}_2digit??.nc')
            run_cmdline('rm ctm_{iyr}{imth_2digit}??.nc')

        else:
            raise ValueError(dict2str("Invalid land-use option for CTM sib={sib}. Please use sib=2 for CTM output",d))

    # surface files

    d['ktc_sec'] = d['ktc_surf']*60

    if d['ncsurf'] == 1:
        write2file('cc.nml',cc_template_4(),mode='w+')
        run_cmdline('mpirun -np {nproc} {pcc2hist} > surf.pcc2hist.log')
        #run_cmdline('rm surf.{ofile}.??????')

    if d['ncsurf'] == 2 and d['nctar'] == 1:
        write2file('cc.nml',cc_template_4(),mode='w+')
        run_cmdline('tar cvf {hdir}/OUTPUT/surf.{ofile}.tar surf.{ofile}.??????')
        #run_cmdline('rm surf.{ofile}.??????')

    # store output
    if d['nctar'] == 0:
        run_cmdline('mv {ofile}.?????? {hdir}/OUTPUT')

    elif d['nctar'] == 1:
        run_cmdline('tar cvf {hdir}/OUTPUT/{ofile}.tar {ofile}.??????')
        run_cmdline('rm {ofile}.??????')

    # update counter for next simulation month and remove old files
    d['imth'] = d['imth'] + 1

    if d['imth'] < 12:
        run_cmdline('rm Rest{name}.{iyr}12.??????')

    elif d['imth'] > 12:
        run_cmdline('tar cvf {hdir}/RESTART/Rest{name}.{iyr}12.tar Rest{name}.{iyr}12*')
        run_cmdline('rm Rest{name}.{iyr}0?.?????? Rest{name}.{iyr}10.?????? Rest{name}.{iyr}11.??????')
        run_cmdline('rm prnew.{iyr}*')
        run_cmdline('rm {name}*{iyr}??')
        run_cmdline('rm {name}*{iyr}??.nc')
        d['imth'] = 1
        d['iyr'] = d['iyr'] + 1

def update_yearqm():
    "Update the year.qm file"

    d['yyyymm'] = d['iyr'] * 100 + d['imth']
    write2file(d['hdir']+'/year.qm',"{yyyymm}",mode='w+')

def restart_flag():
    "Create restart.qm containing flag for restart. This flag signifies that CCAM completed previous month"

    write2file(d['hdir']+'/restart.qm',"True",mode='w+')


def run_cmdline(arg):
    "Run a command line argument from within python"

    os.system(dict2str(arg))

def dict2str(str_template):
    "Create a string that includes dictionary elements"

    return str_template.format(**d)

def write2file(fname,args_template,mode='a'):
    "Write arguments to namelist file"

    with open(fname,mode) as ofile:
        ofile.write(args_template.format(**d))

    ofile.close()

def get_fpath(fpath):
    "Get relevant file path(s)"
    return commands.getoutput(dict2str('ls -1tr '+fpath+' | tail -1'))

def check_file_exists(path):
    "Check that the specified file path exists"

    if not (os.path.exists(path)):
        raise ValueError('File not found: '+path)

def mon_2digit(imth):
    "Create 2-digit numerical string for given month"

    imth = int(imth)

    if imth < 10:
        return '0'+str(imth)
    else:
        return str(imth)

def top_template():
    "Template for writing top.nml namelist file"

    return """\
    &topnml
     il={gridsize}
     debug=t idia=29 jdia=48 id=2 jd=4
     fileout="topout{domain}" luout=50
     rlong0={midlon} rlat0={midlat} schmidt={inv_schmidt:0.4f}
     dosrtm=f do1km=t do250=t netout=t topfilt=t    
     filepath10km="{insdir}/vegin"
     filepath1km="{insdir}/vegin"
     filepath250m="{insdir}/vegin"
     filepathsrtm="{insdir}/vegin"
    &end"""

def igbpveg_template():
    "Template for writing igbpveg.nml namelist file"

    return """\
    &vegnml
     month=0
     topofile="topout{domain}"
     newtopofile="topsib{domain}"
     landtypeout="veg{domain}"
     veginput="{insdir}/vegin/gigbp2_0ll.img"
     soilinput="{insdir}/vegin/usda4.img"
     laiinput="{insdir}/vegin"
     albvisinput="{insdir}/vegin/salbvis223.img"
     albnirinput="{insdir}/vegin/salbnir223.img"
     fastigbp=t
     igbplsmask=t
     ozlaipatch=f
     binlimit=2
     tile=t
     outputmode="cablepft"
    &end"""

def ocnbath_template():
    "Template for writing ocnbath.nml namelist file"

    return """\
    &ocnnml
     topofile="topout{domain}"
     bathout="bath{domain}"
     bathdatafile="{insdir}/vegin/etopo1_ice_c.flt"
     fastocn=t
     bathfilt=t
     binlimit=4
    &end"""

def aeroemiss_template():
    "Template for writing aeroemiss.nml namelist file"

    return """\
    &aero
     month={imth_2digit}
     topofile='{vegin}/topout{domain}'
     so2_anth='{so2_anth}'
     so2_ship='{so2_ship}'
     so2_biom='{so2_biom}'
     bc_anth= '{bc_anth}'
     bc_ship= '{bc_ship}'
     bc_biom= '{bc_biom}'
     oc_anth= '{oc_anth}'
     oc_ship= '{oc_ship}'
     oc_biom= '{oc_biom}'
     volcano= '{stdat}/contineous_volc.nc'
     dmsfile= '{stdat}/dmsemiss.nc'
     dustfile='{stdat}/ginoux.nc'
    &end"""

def input_template_1():
    "First part of template for 'input' namelist file"

    template1= """\
    &defaults &end
    &cardin
     COMMENT='date and runlength'
     kdate_s={kdates} ktime_s=0000 leap={leap}
     dt={dt} nwt={nwt} ntau={ntau}
     nmaxpr=999999 newtop=1 nrungcm={nrungcm}
     namip={namip} rescrn=1

     COMMENT='dynamical core'
     epsp=0.1 epsu=0.1 precon=-10000 restol=2.e-7 nh=5 knh=9
     nstagu=1 khor=0 epsh=1.

     COMMENT='mass fixer'
     mfix_qg={mfix_qg} mfix={mfix} mfix_aero={mfix_aero}

     COMMENT='nudging'
     nbd={nbd} mbd={mbd} mbd_maxscale={mbd_maxscale} mbd_maxgrid={mbd_maxgrid}
     nud_p={nud_p} nud_q={nud_q} nud_t={nud_t} nud_uv={nud_uv}
     nud_aero={nud_aero} nud_hrs=1
     kbotdav={kbotdav} ktopdav=-10 sigramplow={sigramplow}
     mbd_maxscale_mlo=500 mbd_mlo={mbd_mlo}
     nud_sst={nud_sst} nud_sss={nud_sss} nud_ouv={nud_ouv} nud_sfh={nud_sfh}
     ktopmlo=1 kbotmlo={kbotmlo} mloalpha=0

     COMMENT='ocean, lakes and rivers'
     nmlo={nmlo} ol={mlolvl} tss_sh=0.3 nriver={nriver}

     COMMENT='land, urban and carbon'
     nsib={nsib} nurban=1 vmodmin=0.1 nsigmf=0 jalbfix=0

     COMMENT='radiation and aerosols'
     nrad=5 iaero={iaero}

     COMMENT='boundary layer'
     nvmix={nvmix} nlocal={nlocal}
     cgmap_offset=600. cgmap_scale=200.

     COMMENT='station'
     mstn=0 nstn=0

     COMMENT='file'
     localhist=.true. unlimitedhist=.true. synchist=.false.
     procformat=.true. compression=1
     tbave={tbave} tblock={tblock}
    &end
    &skyin
     mins_rad=-1 qgmin=2.E-7
     ch_dust=3.E-10
    &end
    &datafile
     ifile=      '{ifile}'
     mesonest=   '{mesonest}'
     topofile=   '{vegin}/topout{domain}'
     vegprev=    '{vegin}/{vegprev}'
     vegfile=    '{vegin}/{vegfile}'
     vegnext=    '{vegin}/{vegnext}'
     vegnext2=   '{vegin}/{vegnextb}'
     bathfile=   '{vegin}/bath{domain}'
     cnsdir=     '{stdat}'
     radfile=    '{co2file}'
     eigenv=     '{stdat}/{eigenv}'
     o3file=     '{ozone}'
     so4tfile=   '{sulffile}'
     oxidantfile='{stdat}/oxidants.nc'
     ofile=      '{ofile}'
     restfile=   'Rest{name}.{iyr}{imth_2digit}'
     sstfile=    '{sstdir}/{sstfile}'
     casafile=   '{vegin}/casa{domain}'
     phenfile=   '{stdat}/modis_phenology_csiro.txt'"""
     
    template2 = """  
     surfile=    'surf.{ofile}'"""

    template3 = """
    &end"""
    
    if d['ncsurf'] == 0:
        template = template1 + template3
    else:
        template = template1 + template2 + template3
    
    return template
    
def input_template_2():
    "Second part of template for 'input' namelist file"

    return """
    &kuonml
     alfsea=1.10 alflnd=1.25
     convfact=1.05 convtime=-2030.60
     tied_con=0.85 mdelay=0
     fldown=-0.3
     iterconv=3
     ksc=0 kscsea=0 kscmom=1 dsig2=0.1
     mbase=0 nbase=10
     methprec=5 detrain=0.15 methdetr=3
     ncvcloud=0
     nevapcc=0 entrain=0.1
     nuvconv=-3
     rhcv=0.1 rhmois=0. tied_over=-26.
     nmr={nmr}
     nevapls=0 ncloud={ncloud} acon={acon} bcon={bcon}
    &end"""

def input_template_3():
    "Third part of template for 'input' namelist file"

    return """
    &kuonml
     alfsea=1.05 alflnd=1.20
     convfact=1.05 convtime=-2030.60
     fldown=-0.3
     iterconv=3
     ksc=0 kscsea=0 kscmom=1 dsig2=0.1
     mbase=4 nbase=-2
     methprec=5 detrain=0.1 methdetr=-2
     mdelay=0
     ncvcloud=0
     nevapcc=0 entrain=-0.5
     nuvconv=-3
     rhmois=0. rhcv=0.1
     tied_con=0. tied_over=2626.
     nclddia=12
     nmr={nmr}
     nevapls=0 ncloud={ncloud} acon={acon} bcon={bcon}
    &end"""

def input_template_4():
    "Fourth part of template for 'input' namelist file"

    return """
    &kuonml
     nkuo=23 sig_ct=1. rhcv=0.1 rhmois=0. convfact=1.05 convtime=-2030.60
     alflnd=1.2 alfsea=1.10 fldown=-0.3 iterconv=3 ncvcloud=0 nevapcc=0
     nuvconv=-3
     mbase=4 mdelay=0 methprec=5 nbase=-10 detrain=0.1 entrain=-0.5
     methdetr=-1 detrainx=0. dsig2=0.1 dsig4=1.
     ksc=0 kscsea=0 sigkscb=0.95 sigksct=0.8 tied_con=0. tied_over=2626.
     ldr=1 nclddia=12 nstab_cld=0 nrhcrit=10 sigcll=0.95
     nmr={nmr}
     nevapls=0 ncloud={ncloud} acon={acon} bcon={bcon}
    &end"""

def input_template_5():
    "Fifth part of template for 'input' namelist file"

    return """
    &turbnml
     buoymeth=1 mineps=1.e-11 qcmf=1.e-4
     ngwd={ngwd} helim={helim} fc2={fc2}
     sigbot_gwd={sigbot_gwd} alphaj={alphaj}
    &end
    &landnml
     proglai={proglai} ccycle={ccycle}
    &end
    &mlonml
     mlodiff=1 mlomfix=2
     rivermd=1
    &end
    &tin &end
    &soilin &end"""

def cc_template_1():
    "First part of template for 'cc.nml' namelist file"

    return """\
    &input
     ifile = "{ofile}"
     ofile = "{hdir}/daily/{ofile}.nc"
     hres  = {res}
     kta={ktc}   ktb=999999  ktc={ktc}
     minlat = {minlat}, maxlat = {maxlat}, minlon = {minlon},  maxlon = {maxlon}
     use_plevs = T
     plevs = {plevs}
    &end
    &histnl
     htype="inst"
     hnames= "all"  hfreq = 1
    &end"""

def cc_template_2():
    "Second part of template for 'cc.nml' namelist file"

    return """\
    &input
     ifile = "{ofile}"
     ofile = "{hdir}/daily/{ofile}.nc"
     hres  = {res}
     kta={ktc}   ktb=999999  ktc={ktc}
     minlat = {minlat}, maxlat = {maxlat}, minlon = {minlon},  maxlon = {maxlon}
     use_plevs = T
     plevs = {plevs}
    &end
    &histnl
     htype="inst"
     hnames= "all"  hfreq = 1
    &end"""

def cc_template_3():
    "Third part of template for 'cc.nml' namelist file"

    return """\
    &input
     ifile = "{ofile}"
     ofile = "{outctmfile}"
     hres  = {res}
     kta={istart} ktb={iend} ktc=60
     minlat = {minlat}, maxlat = {maxlat}
     minlon = {minlon}, maxlon = {maxlon}
     use_plevs = F
    &end
    &histnl
     htype="inst"
     hnames="land_mask","vegt","soilt","lai","zolnd","zs","sigmf","tscr_ave",\
"temp","u","v","omega","mixr","qlg","qfg","ps","rnd","rnc","pblh","fg","eg",\
"taux","tauy","cld","qgscrn","tsu","wb1_ave","wb2_ave","wb3_ave","wb4_ave",\
"tgg1","tgg2","tgg3","tgg4","tgg5","tgg6","ustar","rsmin","cbas_ave","ctop_ave"
     hfreq = 1
    &end"""

def cc_template_4():
    "Fourth part of template for 'cc.nml' namelist file"

    return """\
    &input
     ifile = "surf.{ofile}"
     ofile = "{hdir}/daily/surf.{ofile}.nc"
     hres  = {res}
     kta={ktc_sec}   ktb=2999999  ktc={ktc_sec}
     minlat = {minlat}, maxlat = {maxlat}, minlon = {minlon},  maxlon = {maxlon}
    &end
    &histnl
     htype="inst"
     hnames= "uas","vas","tscrn","rhscrn","psl","rnd","sno","grpl","d10","u10"
     hfreq = 1
    &end"""

if __name__ == '__main__':

    extra_info="""
    Usage:
        python run_ccam.py [-h]

    Author:
        Mitchell Black, mitchell.black@csiro.au
    """
    description='Run the CCAM model'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info,
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", type=str, help=" run name")
    parser.add_argument("--nproc", type=int, help=" number of processors")
    parser.add_argument("--midlon", type=float, help=" central longitude of domain")
    parser.add_argument("--midlat", type=float, help=" central latitude of domain")
    parser.add_argument("--gridres", type=float, help=" required resolution (km) of domain")
    parser.add_argument("--gridsize", type=int, choices=[48,72,96,144,192,288,384,576,768], help="cubic grid size")
    
    parser.add_argument("--domain", type=str, help=" domain of topographic files")
    parser.add_argument("--mlev", type=int,choices=[27,35,54,72,108,144], help=" number of model levels (27, 35, 54, 72, 108 or 144)")
    parser.add_argument("--iys", type=int, help=" start year [YYYY]")
    parser.add_argument("--ims", type=int, choices=[1,2,3,4,5,6,7,8,9,10,11,12], help=" start month [MM]")
    parser.add_argument("--iye", type=int, help=" end year [YYYY]")
    parser.add_argument("--ime", type=int, choices=[1,2,3,4,5,6,7,8,9,10,11,12], help=" end month [MM]")
    parser.add_argument("--leap", type=int, choices=[0,1], help=" Use leap days (0=off, 1=on)")
    parser.add_argument("--ncountmax", type=int, help=" Number of months before resubmit")

    parser.add_argument("--ktc", type=int, help=" standard output period (mins)")
    parser.add_argument("--minlat", type=float, help=" output min latitude (degrees)")
    parser.add_argument("--maxlat", type=float, help=" output max latitude (degrees)")
    parser.add_argument("--minlon", type=float, help=" output min longitude (degrees)")
    parser.add_argument("--maxlon", type=float, help=" output max longitude (degrees)")
    parser.add_argument("--reqres", type=float, help=" required output resolution (degrees) (-1.=automatic)")
    parser.add_argument("--plevs", type=str, help=" output pressure levels (hPa)")

    parser.add_argument("--dmode", type=int, choices=[0,1,2], help=" downscaling (0=spectral(GCM), 1=SST-only, 2=spectral(CCAM) )")
    parser.add_argument("--nstrength", type=int, choices=[0,1], help=" nudging strength (0=normal, 1=strong)")
    parser.add_argument("--sib", type=int, choices=[1,2], help=" land surface (1=CABLE, 2=MODIS)")
    parser.add_argument("--aero", type=int, choices=[0,1], help=" aerosols (0=off, 1=prognostic)")
    parser.add_argument("--conv", type=int, choices=[0,1,2], help=" convection (0=2014, 1=2015a, 2=2015b)")
    parser.add_argument("--cloud", type=int, choices=[0,1,2], help=" cloud microphysics (0=liq+ice, 1=liq+ice+rain, 2=liq+ice+rain+snow+graupel)")
    parser.add_argument("--bmix", type=int, choices=[0,1], help=" boundary layer (0=Ri, 1=TKE-eps)")
    parser.add_argument("--river", type=int, choices=[0,1], help=" river (0=off, 1=on)")
    parser.add_argument("--mlo", type=int, choices=[0,1], help=" ocean (0=Interpolated SSTs, 1=Dynamical ocean)")
    parser.add_argument("--casa", type=int, choices=[0,1], help=" CASA-CNP carbon cycle with prognostic LAI (0=off 1=on)")

    parser.add_argument("--ncout", type=int, choices=[0,1,2,3], help=" standard output format (0=none, 1=CCAM, 2=CORDEX, 3=CTM)")
    parser.add_argument("--nctar", type=int, choices=[0,1], help=" TAR output files in OUTPUT directory (0=off, 1=on)")
    parser.add_argument("--ncsurf", type=int, choices=[0,1,2], help=" High-freq output (0=none, 1=lat/lon, 2=raw)")
    parser.add_argument("--ktc_surf", type=int, help=" High-freq file output period (mins)")

    parser.add_argument("--bcdom", type=str, help=" host file prefix for dmode=0 or dmode=2")

    parser.add_argument("--sstfile", type=str, help=" sst file for dmode=1")
    parser.add_argument("--sstinit", type=str, help=" initial conditions file for dmode=1")

    ###############################################################
    # Specify directories, datasets and executables

    parser.add_argument("--cmip", type=str, choices=['cmip5'], help=" CMIP scenario")
    parser.add_argument("--rcp", type=str, choices=['historic','RCP26','RCP45','RCP85'], help=" RCP scenario")
    parser.add_argument("--insdir", type=str, help=" install directory")
    parser.add_argument("--hdir", type=str, help=" script directory")
    parser.add_argument("--bcdir", type=str, help=" host atmospheric data (for dmode=0 or dmode=2)")
    parser.add_argument("--sstdir", type=str, help=" SST data (for dmode=1)")
    parser.add_argument("--stdat", type=str, help=" eigen and radiation datafiles")
    parser.add_argument("--vegca", type=str, help=" topographic datasets")
    parser.add_argument("--aeroemiss", type=str, help=" path of aeroemiss executable")
    parser.add_argument("--model", type=str, help=" path of globpea executable")
    parser.add_argument("--pcc2hist", type=str, help=" path of pcc2hist executable")
    parser.add_argument("--terread", type=str, help=" path of terread executable")
    parser.add_argument("--igbpveg", type=str, help=" path of igbpveg executable")
    parser.add_argument("--ocnbath", type=str, help=" path of ocnbath executable")
    parser.add_argument("--casafield", type=str, help=" path of casafield executable")

    args = parser.parse_args()

    main(args)
