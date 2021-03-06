import os, sys, cmath
import time
from osgeo import ogr,osr,gdal
from math import radians, atan, degrees

# def getNational():
#     import NHGtools as nt
#     return(nt.NHGextent())


def mkGrid(fcBase,origin,delc,delr,icol,irow,theta,proj,
           fctype='gpkg',lyr='modelgrid',targsrs=None, ngcols=1):

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
    x1, y1 = rotatePt(0, len(delr) * delr[0], theta)
    # upper left
    x = x1 + x
    y = y1 + y

    if isinstance(proj, str):
        if 'us-ft' in proj:
            proj = proj.replace('us-ft', 'm')
            projinfo.ImportFromProj4(proj)
            projinfo.SetLinearUnits('us-ft', 0.3048)
        else:
            projinfo.ImportFromWkt(proj)
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
        outDataSource = outDriver.CreateDataSource(fcBase + '.shp')
        outLayer = outDataSource.CreateLayer(fcBase,geom_type=ogr.wkbPolygon25D, srs=projinfo)
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

    fields = ['natlRow', 'natlCol', 'natCellNum',
              'irow', 'icol', 'cellnum']

    for field in fields:
        fieldDef = ogr.FieldDefn(field,ogr.OFTInteger)
        outLayer.CreateField(fieldDef)


    delrTot = -delr[0]
    delcTot = delc[0]
    delc1 = 0.
    delr1 = 0.

    # create grid cells
    for j,r in enumerate(delr):
        sys.stdout.write('\r{} of {} rows'.format(j+1,len(delr)))
        sys.stdout.flush()
        outDataSource.StartTransaction()

        for i,c in enumerate(delc):

            ringXlefttop,ringYlefttop = rotatePt(delc1,delr1,theta)
            ringXrighttop,ringYrighttop = rotatePt(delcTot,delr1,theta)
            ringXleftbot,ringYleftbot = rotatePt(delc1,delrTot,theta)
            ringXrightbot,ringYrightbot = rotatePt(delcTot,delrTot,theta)
            delc1 = delcTot
            delcTot = delcTot + c

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

            ngrow = irow + j
            ngcol = icol + i
            outFeature.SetField('natlRow', ngrow)
            outFeature.SetField('natlCol', ngcol)
            outFeature.SetField('natCellNum',(ngrow -1) * ngcols + ngcol)

            outFeature.SetField('irow', j+1)
            outFeature.SetField('icol', i+1)
            outFeature.SetField('cellNum', j * len(delc) + i + 1)

            outLayer.CreateFeature(outFeature)
            outFeature = None

        outDataSource.CommitTransaction()

        # new envelope for next poly
        # delc1 = delcTot
        delc1 = 0
        delr1 = delrTot

        # delcTot = delcTot + c
        delrTot = (delrTot - r)

        # delrTot = 0.
        delcTot = delc[0]

    # Close DataSources
    outDataSource = None

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
