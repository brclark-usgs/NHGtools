import os, sys, cmath
import time
from osgeo import ogr,osr,gdal
from math import radians, atan, degrees

# def getNational():
#     import NHGtools as nt
#     return(nt.NHGextent())


def mkGrid(fcBase,origin,delc,delr,icol,irow,theta,proj,
           fctype='gpkg',lyr='modelgrid',targsrs=None, ngcolNum=1):

    """
    fcBase: string, shapefile path and name or sqlite database name, 
         or name of geopackage, depending on value of fctype 
    origin: list,  lower left x and y coordinates of model grid
    delc and delr: lists, cell dimensions of rows and cols
    icol: int, corresponding first column of national grid
    irow: int, corresponding first row of national grid
    theta: float, angle of rotation
    proj: string or integer, proj4 projection string or EPSG code
    fctype: string, determines output format. options are
        - shp
        - sqlite
        - gpkg
    lyr: string, layer name
    targsrs: string or integer, proj4 projection string or EPSG code
        used to reproject the input to a different system if desired
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
        outDriver.DeleteDataSource(fcBase + '.shp')
        outPolyDataSource = outDriver.CreateDataSource(fcBase + '.shp')
        outLayer = outPolyDataSource.CreateLayer(fcBase,geom_type=ogr.wkbPolygon25D, srs=projinfo)
    elif fctype == 'sqlite':
        outDriver = ogr.GetDriverByName('SQLite')
        if not os.path.exists(fcBase + '.sqlite'):
            outDriver.CreateDataSource(fcBase + '.sqlite', options=['SPATIALITE=yes']) 
        outDataSource = outDriver.Open(fcBase + '.sqlite', True)
        outLayer = outDataSource.CreateLayer(lyr, geom_type=ogr.wkbPolygon25D, srs=targproj, options=['OVERWRITE=YES'])
    else:
        outDriver = ogr.GetDriverByName('GPKG')
        if not os.path.exists(fcBase + '.gpkg'):
            outDriver.CreateDataSource(fcBase + '.gpkg')
        outDataSource = outDriver.Open(fcBase + '.gpkg', True)
        outLayer = outDataSource.CreateLayer(lyr, geom_type=ogr.wkbPolygon25D, srs=targproj, options=['OVERWRITE=YES'])

    featureDefn = outLayer.GetLayerDefn()

    fields = ['natlRow', 'natlCol', 'natlCellNum',
              'irow', 'icol', 'cellnum']

    for field in fields:
        fieldDef = ogr.FieldDefn(field,ogr.OFTInteger)
        outLayer.CreateField(fieldDef)


    delrTot = 0. # delr[0]
    delcTot = delc[0]
    delc1 = 0.
    ringXlefttop,ringYlefttop = rotatePt(0,delrTot,theta)
    ringXrightbot,ringYrightbot = rotatePt(delcTot,0,theta)
    ringXrighttop,ringYrighttop = rotatePt(delcTot,delrTot,theta)
    # create grid cells
    outDataSource.StartTransaction()
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
            ring.AddPoint(ringXlefttop + x, ringYlefttop + y)
            ring.AddPoint(ringXrighttop + x, ringYrighttop + y)
            ring.AddPoint(ringXrightbot + x, ringYrightbot + y)
            ring.AddPoint(ringXleftbot + x, ringYleftbot + y)
            ring.AddPoint(ringXlefttop + x, ringYlefttop + y)
            poly = ogr.Geometry(ogr.wkbPolygon25D)

            poly.AddGeometry(ring)
            if targproj != projinfo:
                poly.Transform(transform)

            # add new geom to layer
            outFeature = ogr.Feature(featureDefn)
            outFeature.SetGeometry(poly)

            ngrow = irow + len(delr) - (j + 1)
            ngcol = icol + i
            outFeature.SetField('natlRow', ngrow)
            outFeature.SetField('natlCol', ngcol)
            # outFeature.SetField('natlCellNum',(len(delr)-irow-1)*len(delc)+icol+1)
            outFeature.SetField('natlCellNum',(ngrow - 1) * ngcolNum + ngcol)

            outFeature.SetField('irow',len(delr) - j)
            outFeature.SetField('icol', i + 1)
            outFeature.SetField('cellNum',(len(delr)-j-1)*len(delc)+i+1)

            outLayer.CreateFeature(outFeature)
            outFeature = None


        # new envelope for next poly
        delc1 = delcTot
        delcTot = delcTot + c
        delrTot = 0.

    # Close DataSources   
    outDataSource.CommitTransaction()
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
