
import os, sys
import numpy as np

def NHGextent():
    # coordinates of each corner of the NHG
    natlExt  = {'ll': [-2553045.0, -92715.0],
                'lr': [2426955.0, -92715.0],
                'ur': [2426955.0, 3907285.0],
                'ul': [-2553045.0, 3907285.0]}
    return(natlExt)

def gcGrid(ll, lr, ur, size, icol, irow, grd, proj=5070, fctype='gpkg'):
    """
    creates a polygon grid from given spatial location
    and dimensions.
    can write shapefile, sqlite, or geopackage feature class
    """
    import fishnet as fn

    nrow, ncol = fn.calcRowCol(ll, lr, ur, size)    
    delr = [size for x in range(nrow)]
    delc = [size for x in range(ncol)]
    print(len(delc), len(delr))
    print(ncol, nrow)
    fn.mkGrid(grd,ll,delc,delr,icol,irow,0.0,proj,fctype=fctype, mkpoints=False)

def convertCoords(xy, src='', targ=''):
    """
    self explanatory?
    """

    from osgeo import ogr, osr

    srcproj = osr.SpatialReference()
    if isinstance(src, str):
        srcproj.ImportFromProj4(src)
    else:
        srcproj.ImportFromEPSG(src)

    targproj = osr.SpatialReference()
    if isinstance(targ, str):
        targproj.ImportFromProj4(targ)
    else:
        targproj.ImportFromEPSG(targ)

    transform = osr.CoordinateTransformation(srcproj,targproj)

    pt = ogr.Geometry(ogr.wkbPoint)
    pt.AddPoint(xy[0], xy[1])
    pt.Transform(transform)
    return(pt.GetX(), pt.GetY())

def lcc2albers(exts, wktsrc, wkttarg):
    nexts = {}
    nexts['ul'] = convertCoords(exts['ul'], wktsrc, wkttarg)
    nexts['ll'] = convertCoords(exts['ll'], wktsrc, wkttarg)
    nexts['ur'] = convertCoords(exts['ur'], wktsrc, wkttarg)
    nexts['lr'] = convertCoords(exts['lr'], wktsrc, wkttarg)

    return(nexts)

def calcCorners(noaa, lulc, res=30, newgridres=10000):
    """
    use northern extent of NOAA model and
    eastern extent of LULC to calculate a new
    lower left for national albers grid
    """
    import math

    westDiff = ((noaa['ul'][0] - lulc['ul'][0]) / res)
    l = math.modf(math.log10(abs(westDiff)))[1]
    if l > 3: l = 3 
    wxoff = round(westDiff / 10**l) * 10**l * res

    southDiff = ((noaa['lr'][1] - lulc['lr'][1]) / res)
    l = math.modf(math.log10(abs(southDiff)))[1]
    if l > 3: l = 3 
    syoff = math.floor(southDiff / 10**l) * 10**l * res

    eastDiff = ((noaa['ur'][0] - lulc['ur'][0]) / res)
    l = math.modf(math.log10(abs(eastDiff)))[1]
    if l > 3: l = 3 
    exoff = math.ceil(eastDiff / 10**l) * 10**l * res 

    northDiff = ((noaa['ur'][1] - lulc['ur'][1]) / res)
    l = math.modf(math.log10(abs(northDiff)))[1]
    nyoff = math.ceil(northDiff / 10**l) * 10**l * res 

    newll = [lulc['ll'][0] + wxoff, lulc['ll'][1] + syoff]
    newur = [lulc['ur'][0] + exoff, lulc['ur'][1] + nyoff]
    
    # round for clean bounds
    diff = (newur[1] - newll[1]) / newgridres 
    print(diff)
    diff = int(diff)
    newur[1] = newll[1] + (diff * newgridres)
    print('rows', diff)

    diff = (newur[0] - newll[0]) / newgridres
    diff = int(diff)
    newur[0] = newll[0] + (diff * newgridres)
    print('cols', diff)


    newlr = [newur[0], newll[1]]
    newul = [newll[0], newur[1]]

    newext = {'ll':newll,
               'lr':newlr,
               'ur':newur,
               'ul':newul} 

    return(newext)

def maxExtent(box1, box2):
    """
    return maximum extent of two different
    bounding boxes
    """
    ll = min(box1['ll'][0], box2['ll'][0]), min(box1['ll'][1], box2['ll'][1])
    ur = max(box1['ur'][0], box2['ur'][0]), max(box1['ur'][1], box2['ur'][1])

    newext = {'ll':ll,
              'lr':[ur[0], ll[1]],
               'ur':ur,
               'ul':[ur[0], ll[1]]} 
    return(newext)

def fit2national(grid, fac=1, natl=None):
    #why would natl ever not be None?
    if natl == None:
        natl = NHGextent()
    
    print('national grid')
    print(natl)
    natres = 1000
    # print(type(fac))

    if isinstance(fac, int):
        if fac == 1:
            res = natres
        else:
            print('this is where grid would get bigger')
    elif isinstance(fac, str):
        if fac == '1/2':
            res = natres/2
        elif fac == '1/4':
            res = natres/4
        elif fac == '1/8':
            res = natres/8
        else:
            res = 0
            print('this aint gonna work')
    else:
        res = 0
        print('this also aint gonna work')
    print('resolution',res)

    newext = {}

    syoff = (grid['ll'][1] - natl['ll'][1]) / res
    y = natl['ll'][1] + int(syoff) * res
    sxoff = (grid['ll'][0] - natl['ll'][0]) / res
    x = natl['ll'][0] + (int(sxoff)) * res

    newext['ll'] = [x, y]

    syoff = (grid['ur'][1] - natl['ll'][1]) / res
    y = natl['ll'][1] + int(syoff) * res + res

    sxoff = (grid['ur'][0] - natl['ll'][0]) / res
    x = natl['ll'][0] + (int(sxoff) + 1) * res 

    newext['ur'] = [x, y]
    newext['lr'] = [x, newext['ll'][1]]
    newext['ul'] = [newext['ll'][0], y]
    print('new local extent')
    print(newext)

    icol = (abs(natl['ul'][0] - newext['ul'][0]) / res ) + 1
    irow = (abs(natl['ul'][1] - newext['ul'][1]) / res) + 1
    print(icol,irow)

    return(res, newext, icol, irow)

def readGrid(grid):
    from osgeo import gdal

    g = gdal.Open(grid)
    gt = g.GetGeoTransform()
    rsize = (g.RasterXSize, g.RasterYSize)
    a = g.GetRasterBand(1).ReadAsArray()

    return(gt, rsize, a)

def rasterizeGrid(shp, gridOut, lyrName='modelgrid', cellsize=1000.,
                  nrow=4000, ncol=4980, attribute='cellnum', 
                  upperleft=None, wkt='', grid=None):
    """
    rasterize modelgrid - use cellnum as value
    """

    from osgeo import gdal, osr, ogr

    # steal geotransform from existing grid
    if grid != None:
        gt, rsize, a = readGrid(grid)
    else:
        # assumes national grid corner
        # gt = (-2553045.0, cellsize, 0.0, 3907285.0, 0.0, -cellsize)
        gt = (upperleft[0], cellsize, 0.0, upperleft[1], 0.0, -cellsize)
        rsize = (ncol, nrow)

    ds = ogr.Open(shp)
    if lyrName != None:
        lyr = ds.GetLayerByName(lyrName)
    else:
        lyr = ds.GetLayer(0)

    proj = lyr.GetSpatialRef() #.ExportToProj4()
    # print(proj.ExportToWkt())
    # proj = osr.SpatialReference()
    # proj.ImportFromEPSG(5070)
    # proj.ImportFromProj4(5070)
    # print(proj.ExportToWkt())

    driver = gdal.GetDriverByName('GTiff')

    rvds = driver.Create(gridOut, rsize[0], rsize[1], 1, gdal.GDT_Int32)
    rvds.SetGeoTransform(gt)
    rvds.SetProjection(proj.ExportToWkt())
    gdal.RasterizeLayer(rvds, [1], lyr, None, None, [1], ['ATTRIBUTE={}'.format(attribute)])

