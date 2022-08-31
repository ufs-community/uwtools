&amip_interp_nml
    interp_oi_sst = .true.
    use_ncep_sst = .true.
    use_ncep_ice = .false.
    no_anom_sst = .false.
    data_set = 'reynolds_oi'
    date_out_of_range = 'climo'
/

&atmos_model_nml
    blocksize = 32
    chksum_debug = .false.
    dycore_only = .false.
    fdiag = 6
/

&diag_manager_nml
    prepend_date = .false.
/

&fms_io_nml
    checksum_required = .false.
    max_files_r = 100
    max_files_w = 100
/

&fms_nml
    clock_grain = 'ROUTINE'
    domains_stack_size = 3000000
    print_memory_usage = .false.
/

&fv_grid_nml
    grid_file = 'INPUT/grid_spec.nc'
/

&fv_core_nml
    layout = 3, 8
    io_layout = 1, 1
    npx = 97
    npy = 97
    ntiles = 6
    npz = 64
    grid_type = -1
    make_nh = .true.
    fv_debug = .false.
    range_warn = .false.
    reset_eta = .false.
    n_sponge = 24
    nudge_qv = .true.
    tau = 5.0
    rf_cutoff = 750.0
    d2_bg_k1 = 0.15
    d2_bg_k2 = 0.02
    kord_tm = -9
    kord_mt = 9
    kord_wz = 9
    kord_tr = 9
    hydrostatic = .false.
    phys_hydrostatic = .false.
    use_hydro_pressure = .false.
    beta = 0.0
    a_imp = 1.0
    p_fac = 0.1
    k_split = 2
    n_split = 6
    nwat = 2
    na_init = 1
    d_ext = 0.0
    dnats = 0
    fv_sg_adj = 450
    d2_bg = 0.0
    nord = 2
    dddmp = 0.1
    d4_bg = 0.12
    vtdm4 = 0.02
    delt_max = 0.002
    ke_bg = 0.0
    do_vort_damp = .true.
    external_ic = .true.
    external_eta = .true.
    gfs_phil = .false.
    nggps_ic = .true.
    mountain = .false.
    ncep_ic = .false.
    d_con = 1.0
    hord_mt = 6
    hord_vt = 6
    hord_tm = 6
    hord_dp = 6
    hord_tr = 8
    adjust_dry_mass = .false.
    consv_te = 1.0
    consv_am = .false.
    fill = .true.
    dwind_2d = .false.
    print_freq = 6
    warm_start = .false.
    no_dycore = .false.
    z_tracer = .true.
    read_increment = .false.
    res_latlon_dynamics = 'fv3_increment.nc'
/

&coupler_nml
    months = 0, '#'
    days = 1, '#'
    hours = 0, '#'
    dt_atmos = 225, '#'
    dt_ocean = 225, '#'
    current_date = 2016, 10, 3, 0, 0, 0, '#'
    calendar = 'julian', '#'
    memuse_verbose = .false., '#'
    atmos_nthreads = 1, '#'
    use_hyper_thread = .false., '#'
    ncores_per_node = 24, '#'
/

&external_ic_nml
    filtered_terrain = .true.
    levp = 65
    gfs_dwinds = .true.
    checker_tr = .false.
    nt_checker = 0
/

&gfs_physics_nml
    fhzero = 6.0
    ldiag3d = .false.
    fhcyc = 24.0
    nst_anl = .true.
    use_ufo = .true.
    pre_rad = .false.
    ncld = 1
    imp_physics = 99
    pdfcld = .false.
    fhswr = 3600.0
    fhlwr = 3600.0
    ialb = 1
    iems = 1
    iaer = 111
    ico2 = 2
    isubc_sw = 2
    isubc_lw = 2
    isol = 2
    lwhtr = .true.
    swhtr = .true.
    cnvgwd = .true.
    shal_cnv = .true.
    cal_pre = .true.
    redrag = .true.
    dspheat = .true.
    hybedmf = .true.
    random_clds = .true.
    trans_trac = .true.
    cnvcld = .true.
    imfshalcnv = 2
    imfdeepcnv = 2
    cdmbgwd = 3.5, 0.25
    prslrd0 = 0.0
    ivegsrc = 1
    isot = 1
    debug = .false.
    nstf_name = 0, 1, 1, 0, 5
    iau_delthrs = 6
    iaufhrs = 30
    iau_inc_files = 'placeholder.txt'
/

&interpolator_nml
    interp_method = 'conserve_great_circle'
/

&namsfc
    fnglac = 'global_glacier.2x2.grb'
    fnmxic = 'global_maxice.2x2.grb'
    fntsfc = 'RTGSST.1982.2012.monthly.clim.grb'
    fnsnoc = 'global_snoclim.1.875.grb'
    fnzorc = 'igbp'
    fnalbc = 'global_snowfree_albedo.bosu.t126.384.190.rg.grb'
    fnalbc2 = 'global_albedo4.1x1.grb'
    fnaisc = 'CFSR.SEAICE.1982.2012.monthly.clim.grb'
    fntg3c = 'global_tg3clim.2.6x1.5.grb'
    fnvegc = 'global_vegfrac.0.144.decpercent.grb'
    fnvetc = 'global_vegtype.igbp.t126.384.190.rg.grb'
    fnsotc = 'global_soiltype.statsgo.t126.384.190.rg.grb'
    fnsmcc = 'global_soilmgldas.t126.384.190.grb'
    fnmskh = 'seaice_newland.grb'
    fntsfa = ''
    fnacna = ''
    fnsnoa = ''
    fnvmnc = 'global_shdmin.0.144x0.144.grb'
    fnvmxc = 'global_shdmax.0.144x0.144.grb'
    fnslpc = 'global_slope.1x1.grb'
    fnabsc = 'global_mxsnoalb.uariz.t126.384.190.rg.grb'
    ldebug = .false.
    fsmcl(2:4) = 99999, 99999, 99999
    ftsfs = 90
    faiss = 99999
    fsnol = 99999
    fsicl = 99999
    ftsfl = 99999
    faisl = 99999
    fvetl = 99999
    fsotl = 99999
    fvmnl = 99999
    fvmxl = 99999
    fslpl = 99999
    fabsl = 99999
    fsnos = 99999
    fsics = 99999
/

&nam_stochy
    lon_s = 768
    lat_s = 384
    ntrunc = 382
    skebnorm = 1
    skeb_npass = 30
    skeb_vdof = 5
    skeb = 999
    skeb_tau = 21600.0
    skeb_lscale = 1000000.0
    shum = -99.0
    shum_tau = 21600
    shum_lscale = 500000
    sppt = -979.0
    sppt_tau = 21600
    sppt_lscale = 500000
    sppt_logit = .true.
    sppt_sfclimit = .true.
    iseed_shum = 1
    iseed_skeb = 2
    iseed_sppt = 3
/
