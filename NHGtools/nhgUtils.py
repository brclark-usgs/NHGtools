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