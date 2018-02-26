import os, sys, cmath
import time
from osgeo import ogr,osr,gdal
from math import radians, atan, degrees


def mkGrid(fcBase,origin,delc,delr,icol,irow,theta,proj,
           fctype='shp',lyr='modelgrid',targsrs=None,
           mkpoints=False):
    """
    fcBase: string, shapefile path and name or sqlite database name, 
         or name of geopackage, depending on value of fctype 
    origin: list,  lower left x and y coordinates of model grid
    delc and delr: lists, cell dimensions of rows and cols
    theta: float, angle of rotation
    proj: string or integer, proj4 projection string or EPSG code
    fctype: string, determines output format. options are
        - shp
        - sqlite
        - gpkg
    lyr: string, layer name
    targsrs: string or integer, proj4 projection string or EPSG code
        used to reproject the input to a different system if desired
    mkpoints: boolean, optional flag to create point features of
        cell centers
    should delc and delr should be switched.?
    """

    # start grid cell envelope
    x = origin[0]
    y = origin[1]

    def rotatePt(dX,dY,theta):
        pol = cmath.polar(complex(dX,dY))
        newTheta = radians(theta) + pol[1]
        newxy = cmath.rect(pol[0],newTheta)
        return(newxy.real, newxy.imag)

    projinfo = osr.SpatialReference()

    if isinstance(proj, str):
        if 'us-ft' in proj:
            proj = proj.replace('us-ft', 'm')
            projinfo.ImportFromProj4(proj)
            projinfo.SetLinearUnits('us-ft', 0.3048)
        else:
            projinfo.ImportFromProj4(proj)
    else:        
        projinfo.ImportFromEPSG(proj)

    if targsrs != None:
        targproj = osr.SpatialReference()
        if isinstance(targproj, str):
            targproj.ImportFromProj4(targsrs)
        else:
            targproj.ImportFromEPSG(targsrs)
        transform = osr.CoordinateTransformation(projinfo,targproj) 
    else:
        targproj = projinfo

    # create output file
    if fctype == 'shp': 
        outDriver = ogr.GetDriverByName('ESRI Shapefile')
        outDriver.DeleteDataSource(fcBase + 'pt.shp')
        outDriver.DeleteDataSource(fcBase + '.shp')
        outDataSource = outDriver.CreateDataSource(fcBase + 'pt.shp')
        outPolyDataSource = outDriver.CreateDataSource(fcBase + '.shp')
        outLayer = outPolyDataSource.CreateLayer(fcBase,geom_type=ogr.wkbPolygon25D, srs=projinfo)
        ptLayer = outDataSource.CreateLayer(fcBase, geom_type=ogr.wkbPoint, srs=projinfo)
    elif fctype == 'sqlite':
        outDriver = ogr.GetDriverByName('SQLite')
        if not os.path.exists(fcBase + '.sqlite'):
            outDriver.CreateDataSource(fcBase + '.sqlite', options=['SPATIALITE=yes']) 
        outDataSource = outDriver.Open(fcBase + '.sqlite', True)
        outLayer = outDataSource.CreateLayer(lyr, geom_type=ogr.wkbPolygon25D, srs=targproj, options=['OVERWRITE=YES'])
        if mkpoints:
            ptLayer = outDataSource.CreateLayer(lyr + '_label', geom_type=ogr.wkbPoint, srs=targproj, options=['OVERWRITE=YES'])
    else:
        outDriver = ogr.GetDriverByName('GPKG')
        if not os.path.exists(fcBase + '.gpkg'):
            outDriver.CreateDataSource(fcBase + '.gpkg')
        outDataSource = outDriver.Open(fcBase + '.gpkg', True)
        outLayer = outDataSource.CreateLayer(lyr, geom_type=ogr.wkbPolygon25D, srs=targproj, options=['OVERWRITE=YES'])

    featureDefn = outLayer.GetLayerDefn()
    if mkpoints:
        ptfeatureDefn = ptLayer.GetLayerDefn()

    fields = ['irow', 'icol', 'cellnum', 'rc', 'Xcoord', 'Ycoord']

    for field in fields:
        fieldDef = ogr.FieldDefn(field,ogr.OFTInteger)
        outLayer.CreateField(fieldDef)
        if mkpoints:
            ptLayer.CreateField(fieldDef)


    delrTot = 0. # delr[0]
    delcTot = delc[0]
    delc1 = 0.
    ringXlefttop,ringYlefttop = rotatePt(0,delrTot,theta)
    ringXrightbot,ringYrightbot = rotatePt(delcTot,0,theta)
    ringXrighttop,ringYrighttop = rotatePt(delcTot,delrTot,theta)
    # create grid cells
    for i,c in enumerate(delc):
        sys.stdout.write('\r{} of {} cols'.format(i+1,len(delc)))
        sys.stdout.flush()
        for j,r in enumerate(delr):

            ringXleftbot,ringYleftbot = rotatePt(delc1,delrTot,theta)
            ringXrightbot,ringYrightbot = rotatePt(delcTot,delrTot,theta)
            delrTot = delrTot + r
            ringXlefttop,ringYlefttop = rotatePt(delc1,delrTot,theta)
            ringXrighttop,ringYrighttop = rotatePt(delcTot,delrTot,theta)

            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(ringXlefttop+x, ringYlefttop+y)
            ring.AddPoint(ringXrighttop+x, ringYrighttop+y)
            ring.AddPoint(ringXrightbot+x, ringYrightbot+y)
            ring.AddPoint(ringXleftbot+x, ringYleftbot+y)
            ring.AddPoint(ringXlefttop+x, ringYlefttop+y)
            poly = ogr.Geometry(ogr.wkbPolygon25D)

            poly.AddGeometry(ring)
            if targproj != projinfo:
                poly.Transform(transform)

            # add new geom to layer
            outFeature = ogr.Feature(featureDefn)
            outFeature.SetGeometry(poly)
            # outFeature.SetField('irow',len(delr)-irow)
            outFeature.SetField('irow', irow + len(delr) - (j+1))
            # outFeature.SetField('icol',icol+1)
            outFeature.SetField('icol', icol + i)
            outFeature.SetField('cellnum',(len(delr)-irow-1)*len(delc)+icol+1)
            outFeature.SetField('rc',((len(delr)-irow)*1000+icol+1))
            outLayer.CreateFeature(outFeature)
            outFeature = None

            # cell centers
            if mkpoints:
                ptFeature = ogr.Feature(ptfeatureDefn)
                ptFeature.SetGeometry(poly.Centroid())
                ptFeature.SetField('irow',len(delr)-irow)
                ptFeature.SetField('icol',icol+1)
                ptFeature.SetField('cellnum',(len(delr)-irow-1)*len(delc)+icol+1)
                ptFeature.SetField('rc',((len(delr)-irow)*1000+icol+1))
                ptLayer.CreateFeature(ptFeature)
                ptFeature = None

        # new envelope for next poly
        delc1 = delcTot
        delcTot = delcTot + c
        delrTot = 0.

    # Close DataSources   
    outDataSource=None

def calcAngle(corners):
    '''
    corners: list of lower left (x,y) and
    lower right (x,y)
    '''

    xorig = corners[0][0]
    xupper = corners[1][0]
    # yorig = corners[0][1]
    dx = corners[0][0] - corners[1][0]
    dy = corners[0][1] - corners[1][1]
    theta = degrees(atan(dy / dx)) #- 90
    if xupper < xorig: #quad 1
        theta = 90 - (theta * -1)
    return(theta)

def calcRowCol(lowerLeft,lowerRight,upperRight,size):
    pt1 = ogr.Geometry(ogr.wkbPoint)
    pt2 = ogr.Geometry(ogr.wkbPoint)
    pt3 = ogr.Geometry(ogr.wkbPoint)
    pt1.AddPoint(lowerLeft[0],lowerLeft[1])
    pt2.AddPoint(lowerRight[0],lowerRight[1])
    pt3.AddPoint(upperRight[0],upperRight[1])

    ncol = int(round(pt1.Distance(pt2)/size, 0))
    nrow = int(round(pt2.Distance(pt3)/size, 0))

    return(nrow,ncol)
