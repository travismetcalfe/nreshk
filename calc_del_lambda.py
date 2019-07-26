

def import_lab_frame_spectra(fluxdir, minwl=None, maxwl=None, resolution=1, residual=False):
    import numpy as np
    import matplotlib as mpl
    from matplotlib import pyplot as plt
    import os
    import os.path
    import re
    import scipy
    import scipy.signal
    import scipy.ndimage.filters
    import helpers as h#for constants
    
    
    wavelength = []
    res_flux = []
    irradiance = []
    
    for f in os.listdir(fluxdir):
        if not re.match('^lm', f): continue
        fpath = os.path.join(fluxdir, f)
        d = np.genfromtxt(fpath, unpack=True)
        wavelength = np.append(wavelength, d[0]) # in nm
        res_flux = np.append(res_flux, d[1]) # from a normalized spectra
        irradiance = np.append(irradiance, d[2]) # from a regular spectra; mu-W / cm^2 / nm
        
    wavelength = np.array(wavelength)
    res_flux = np.array(res_flux)
    irradiance = np.array(irradiance)
    sort = np.argsort(wavelength)
    wavelength = wavelength[sort]
    res_flux = res_flux[sort]
    irradiance = irradiance[sort]

    angstroms = wavelength * 10 # in Angstroms
    
    
    
    if minwl is None:
        minwl = angstroms[0]
    if maxwl is None:
        maxwl = angstroms[-1]
    sel = (angstroms >= minwl) & (angstroms <= maxwl)
    dw = angstroms[1] - angstroms[0]
    if not residual:
        series = irradiance / 10. # nm^-1 => Ang.^-1
    else:
        series = res_flux

    if resolution > 0:
        series = scipy.ndimage.filters.gaussian_filter(series, resolution/dw)

    #print('degrading source: ' + str(resolution/dw))
    
    return angstroms[sel], series[sel]
    
    
#############################################
#TODO DESCPT
def tmp_find_del_lam(labGrid, lab, tarGrid, targ, smooth) :

    #TODO DO WE NEED ALL THESE
    import scipy as sc
    #import astropy.io.fits
    import numpy as np
    import helpers as h#for constants
    #import os
    #from calc_shk import calc_shk
    #from calc_shk import calc_targOlapf
    #from mk_flatolap import mk_flatolap
    from matplotlib import pyplot as plt
    from astropy.convolution import convolve, Box1DKernel
    from scipy import interpolate
    
    tmpGridScale = 1
    dLam = tarGrid[1] - tarGrid[0]
    #print(np.shape(targ))
    gausdTarg = sc.ndimage.filters.gaussian_filter(targ,smooth/dLam/2)
    
    dLabLam = labGrid[1] - labGrid[0]
    
    #TODO SHOULD 2.55 be h.sigToFWHM?
    gausedLab = sc.ndimage.filters.gaussian_filter(lab,(dLam/dLabLam)/2.55)

    #get the lab spectrum into angs div by 10 on angstrom grid for our purposes
    interpfunc = interpolate.interp1d(labGrid, gausedLab, kind='linear')#,fill_value='extrapolate')
    labInterp=interpfunc(tarGrid)



    #ZERO OUT THE EDGES OF OUR LAB SPECTRA
    #TODO do this with strict values to remove edge errors affecting correlation
    #from 0 to first nonzero element of targolap
    labInterp[:targ.nonzero()[0][0]]=0
    #from last nonzero element to end
    labInterp[targ.nonzero()[0][-1]:]=0


    #tmp = np.convolve(targOlapf,pikapika,'same')
    #plt.figure(figsize=(12,6))
    #plt.title('convolution function')
    #plt.plot(range(len(tmp)), tmp, 'k-', color='blue')
    #plt.xlabel('delta lamda?')
    #plt.xlabel('f * g')

    #plt.figure(figsize=(12,6))
    #plt.plot(tarGrid, targ, 'k-', color='blue')
    #plt.plot(lamGrid, tmpTarg1, 'k-', color="green")
    #plt.plot(lamGrid, tmpTarg2, 'k-',color='red')
    #plt.plot(tarGrid, labInterp*tmpGridScale, 'k-')
    #plt.axvline(x=393.4, color='red')
    #plt.axvline(x=396.9, color='red')

    #plt.xlabel('wavelength')
    #plt.ylabel('smoothed spectras')

    #do not consider 0's while taking mean
    labInterp[labInterp==0]=np.nan
    targ[targ==0]=np.nan
    
    rmsx = np.nanmean(labInterp)
    rmsy =  np.nanmean(targ)

    #place the 0's back
    labInterp[np.isnan(labInterp)]=0
    targ[np.isnan(targ)]=0




    #plt.figure(figsize=(12,6))
    #plt.plot(1000*labInterp[targ!=0]-rmsx,'k-')
    #plt.plot(targ[targ!=0]-rmsy,'g-')
    #plt.show()
    #plt.close()
    
    #THIS IS THE CROSS CORRELATION SECTION
    ##
    ##correlate must have same sized arrays input
    correlation = np.correlate(targ[targ!=0]-rmsy,(labInterp[targ!=0]-rmsx),'full')
    #length of the correlation array is length input array times 2 plus 1
    #if the two arrays are already aligned then the peak of correlation function should be middle
    middle = int((len(correlation)-1)/2)
    
    
    #width is used for local maximum finding
    #1 is a number that worked here for smarts and NRES data. MAY NEED TO BE ADJUSTED
    width = int(1/dLam)#TODO needs to be a grid based setting

    

    
    #max value is the index of the maximum value(local max around middle of array if width used)
    mval = middle-width+np.argmax(correlation[middle-width:middle+width])
    
    
    ##PRE VACAY
#want to make a quadratic to be more precise with 'peak' of correlation
#need to do poly only in certain range around center because wings will take over the fit
    fitWidth = 5
    import numpy.polynomial.polynomial as poly
    xRange = mval + np.arange(2*fitWidth)- fitWidth
    polyFunc = np.polyfit(xRange, correlation[mval-fitWidth:mval+fitWidth],2)
    #print(polyFunc)
    #f=a*x^2 +b*x+c
    #f' = 2*a*x+b = 0 -> x = -b/2a 
    xVal = -polyFunc[1]/(2*polyFunc[0])
    
    #print(xVal)
    #ffit = np.polyval(polyFunc,xRange)
    #plt.figure()
    #plt.xlim(mval-fitWidth*3,mval+fitWidth*3)
    #plt.plot(xRange, ffit,'g-')
    #plt.plot(range(len(correlation)), correlation, 'k-')
    #plt.show()
    #plt.close()
    
    #mval= np.argmax(ffit)
    #the actual lamda offset is how far from middle we are in pixel space times the pixel to grid ratio
    #
    offset = (xVal-middle)*(tarGrid[1]-tarGrid[0])
    #print('offset: ' + str(offset))
    ##


    
    scale = np.mean(gausdTarg)/np.mean(labInterp)


   # #tmpMax = np.argmax(out)
    #print('index of maximum: ' + str(tmpMax) + ' and adjusted delLam: ' + str(tmpMax/len(out)))
    #print(out)
    #fig, ax = plt.subplots(figsize=(25,5))
    #ax.ticklabel_format(useOffset=False)
    #plt.title("Unadjusted stellar spectra over reference spectra")
    #plt.xlabel("Wavelength (nm)")
    #plt.ylabel("Scaled irradiance")
    #plt.xlim([392,398])
    #plt.ylim([0,2200])
    #plt.plot(tarGrid, gausdTarg, 'g-')
    #plt.axvline(x=393.369, color='red')
    #plt.axvline(x=396.85, color='red')
    #plt.plot(tarGrid-offset, gausdTarg, 'k-',color='green')
    #SCALE JUST FOR VIEWING
    #plt.plot(tarGrid,labInterp*scale, 'k-')
    #plt.show()
    #plt.close()
    
    
    
    #fig, ax = plt.subplots(figsize=(25,5))
    #ax.ticklabel_format(useOffset=False)
    #plt.title("Correlated stellar spectra over reference spectra")
    #plt.xlabel("Wavelength (nm)")
    #plt.ylabel("Scaled irradiance")
    
    #plt.xlim([392,398])
    #plt.ylim([0,2200])
    
    #plt.plot(tarGrid-offset, gausdTarg, 'g-')
    #plt.axvline(x=393.369, color='red')
    #plt.axvline(x=396.85, color='red')

    #plt.plot(tarGrid-offset, gausdTarg, 'k-',color='green')
    #SCALE JUST FOR VIEWING
    #plt.plot(tarGrid,labInterp*scale, 'k-')
    #plt.show()
    #plt.close()
    
    
    
    return offset,targ,labInterp,gausdTarg
   
    
    
##
##TODO descripts
def pdf_from_data(bGrid, base, oGrid, obs, windows, title, path, descript, flat='', width=1):
    import numpy as np
    from matplotlib import pyplot as plt
    from helpers import mkdir_p
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.gridspec as gridspec
    import scipy as sc
    import helpers as h#for constants
    
    
    calH = h.cahLam#396.847#TODO and make global
    calK = h.cakLam#393.366
    #center of red continuum band (nm, vacuum)
    
    lamR=h.lamR#400.2204-.116#TODO TAKE FROM VAUGHAN 1978 subtraction is the offset from our lab values 
    
    #if flat was passed as empty, fill it with nans
    if len(flat) == 0:
        flat = np.full(len(bGrid),0)
        
    flatMax = max(flat)    
    
    if flatMax != 0:
        #create a bool array which describes in our grid sections of the flat which higher than .4th of flat max
        #print(flatMax)
        flatSection = flat/flatMax >= .4

        #used to set axis bounds
        mini = min(bGrid[flatSection])
        maxi = max(bGrid[flatSection])
    
    smooth = .01
    
    #colors for hk lines in each plot
    hColor = 'dodgerblue'
    kColor = 'turquoise'
    
    
    fig, ax = plt.subplots(figsize=(10,10))
    plt.suptitle(title)
    plt.ticklabel_format(useOffset=False)
    with PdfPages(path+descript+"_report.pdf") as curPdf:
        gs = gridspec.GridSpec(4, 3)
        
        targPlt = plt.subplot(gs[2,:])
        smoothedPlt = plt.subplot(gs[1,:])
        flatPlt = plt.subplot(gs[3,:])
        kPlt = plt.subplot(gs[0,0])
        hPlt = plt.subplot(gs[0,1])
        rPlt =plt.subplot(gs[0,2])
        
        #please matplotlib don't make my stuff hard to read!
        hPlt.ticklabel_format(useOffset=False)
        kPlt.ticklabel_format(useOffset=False)
        rPlt.ticklabel_format(useOffset=False)
        targPlt.ticklabel_format(useOffset=False)
        flatPlt.ticklabel_format(useOffset=False)
        smoothedPlt.ticklabel_format(useOffset=False)
        
        hPlt.tick_params(axis='both',which= 'major', labelsize=7)
        kPlt.tick_params(axis='both',which= 'major', labelsize=7)
        rPlt.tick_params(axis='both',which= 'major', labelsize=7)
        targPlt.tick_params(axis='both',which= 'major', labelsize=7)
        flatPlt.tick_params(axis='both',which= 'major', labelsize=7)
        smoothedPlt.tick_params(axis='both',which= 'major', labelsize=7)
        
        #titles 
        kPlt.set_xlabel("Wavelength(nm)")
        hPlt.set_ylabel("Irradiance")
        
        hPlt.set_title("Ca-H window")
        kPlt.set_title("Ca-K window")
        rPlt.set_title("Red band window")
        
        targPlt.set_title("Target overlap shifted over reference spectra")
        targPlt.set_xlabel("Wavelength(nm)")
        targPlt.set_ylabel("Irradiance scaled")
        
        smoothedPlt.set_title("Reference and target smoothed by " + str(smooth*h.sigToFWHM) + " nm Kernel")
        smoothedPlt.set_xlabel("Wavelength(nm)")
        smoothedPlt.set_ylabel("Irradiance scaled")
        
        flatPlt.set_title("Flat plot for target")
        flatPlt.set_xlabel("Wavelength(nm)")
        flatPlt.set_ylabel("Irradiance")
        
        #H/K/Red band plots zoomed
        #use exactly the windows that are gotten from hk_windows plus small buffer
        cur=windows[:,0]
        hkWidth=h.lineWid + .005
        rWidth =h.conWid/2 +.05
        
        hPlt.axvline(x=calH,color=hColor)
        hPlt.plot(oGrid[cur!=0],obs[cur!=0],'b-')
        hPlt.set_xlim(calH-hkWidth,calH+hkWidth)
        
        cur=windows[:,1]
        kPlt.axvline(x=calK,color=kColor)
        kPlt.plot(oGrid[cur!=0],obs[cur!=0],'b-')
        kPlt.set_xlim(calK-hkWidth,calK+hkWidth)

        cur=windows[:,2]
        rPlt.plot(oGrid[cur!=0],obs[cur!=0])
        rPlt.set_xlim(lamR-rWidth, lamR+rWidth)
        
        
        #Targolapf plot 
        #get red lines from windows funct too
        rMin = oGrid[cur!=0][0]
        rMax = oGrid[cur!=0][-1]
       #print('rmin: ' + str(rMin) + ' rMax: ' + str(rMax))
        #terrrrible way to get scale fixxxxxxx
        scale = obs[cur!=0]/base[cur!=0]
        avgS = np.mean(scale)
        
        targPlt.axvline(x=calH,color=hColor)
        targPlt.axvline(x=calK,color=kColor)
        targPlt.axvline(x=rMin, color='red')
        targPlt.axvline(x=rMax, color='red')
        
        
        if flatMax != 0:
            targPlt.set_xlim([mini,maxi])
            targPlt.plot(bGrid[flatSection],base[flatSection]*avgS,color='lightgray')
            targPlt.plot(oGrid[flatSection],obs[flatSection],'b-')
        else:
            targPlt.set_xlim([391.5,407])
            targPlt.plot(bGrid[base!=0],base[base!=0]*avgS,color='lightgray')
            targPlt.plot(oGrid[obs!=0],obs[obs!=0],'b-')
        
        #smoothed target and lab plot
        dOLam = oGrid[1]-oGrid[0]
        dBLam = bGrid[1]-bGrid[0]
        gdObs = sc.ndimage.filters.gaussian_filter(obs,smooth/dOLam)
        gdBase =  sc.ndimage.filters.gaussian_filter(base,smooth/dBLam)
        
        scale = obs[cur!=0]/base[cur!=0]
        avgS = np.mean(scale)
        
        
        
        smoothedPlt.axvline(x=calH,color=hColor)
        smoothedPlt.axvline(x=calK,color=kColor)
        smoothedPlt.axvline(x=rMin, color='red')
        smoothedPlt.axvline(x=rMax, color='red')
        
        if flatMax != 0:
            
            smoothedPlt.set_xlim([mini,maxi])
            smoothedPlt.plot(bGrid[flatSection],gdBase[flatSection]*avgS,color='lightgray')
            smoothedPlt.plot(oGrid[flatSection],gdObs[flatSection],'b-')
        else:
            smoothedPlt.set_xlim([391.5,407])
            smoothedPlt.plot(bGrid[gdBase!=0],gdBase[gdBase!=0]*avgS,color='lightgray')
            smoothedPlt.plot(oGrid[gdObs!=0],gdObs[gdObs!=0],'b-')
        
        #flat/other plot
        flatPlt.plot(bGrid[flat!=0], flat[flat!=0], 'k-')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        #plt.show()
        plt.close()
        
        curPdf.savefig(fig)