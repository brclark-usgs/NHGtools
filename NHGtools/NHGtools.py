
import os, sys
import numpy as np

class nhg(object):
    """
    Parameters
    -----------------------
    ext: dictionary of four keys and values for 'll':lowerleft,
           'lr':lowerright, 'ur': upper right, 'ul': upper left'
           of desired extent
    fc: string, output file name
    fctype: string, output format, may be 'gpkg' or ...
    fac: float, mult or division factor to resize grid

    __icol: int, columns of desired grid aligned to NHG
    __irow: int, rows of desired grid aligned to NHG

    """

    def __init__(self, ext, fac=1, proj=5070, fctype='gpkg',
                 fc='mygrid'):

        self.ext = ext
        self.fctype = fctype
        self.fac = fac
        self.fc = fc

        self.__proj = proj

        self.NHGextent()
        self.__cellsize = self.__natCellsize
        self.__icol = self.__ngcols
        self.__irow = self.__ngrows


    def NHGextent(self):
        # coordinates of each corner of the NHG
        self.__natlExt  = {'ll': [-2553045.0, -92715.0],
                    'lr': [2426955.0, -92715.0],
                    'ur': [2426955.0, 3907285.0],
                    'ul': [-2553045.0, 3907285.0]}

        self.__ngrows = 4000
        self.__ngcols = 4980
        self.__natCellsize = 1000

    def createGrid(self):
        #ext, cellsize, icol, irow, grd, proj=5070, fctype='gpkg'):
        """
        creates a polygon grid from given spatial location
        and dimensions.
        can write shapefile, sqlite, or geopackage feature class
        """
        from . import fishnet as fn

        # number of rows and cols of new grid
        self.__irow, self.__icol = fn.calcRowCol(self.ext['ll'], self.ext['lr'], 
                                   self.ext['ur'], self.__cellsize)    
        delr = [self.__cellsize for x in range(self.__irow)]
        delc = [self.__cellsize for x in range(self.__icol)]
        theta = 0.0
        print(len(delc), len(delr))
        print('new cols and rows', self.__icol, self.__irow)
        # irow and icol are ....
        fn.mkGrid(self.fc, self.ext['ll'], delc, delr, self.__icol,
                  self.__irow, theta, self.__proj, self.fctype,
                  ngcolNum=self.__ngcolNum)

    def mkNationalGrid(self): #fc, fctype='gpkg'):
        import fishnet as fn

        # nrow, ncol = fn.calcRowCol(ne['ll'], ne['lr'], ne['ur'], cellsize)
        delr = [self.__natCellsize for x in range(self.__ngrows)]
        delc = [self.__natCellsize for x in range(self.__ngcols)]
        icol = 1
        irow = 1
        theta = 0.

        fn.mkGrid(self.fc, self.__netlExt['ll'], delc, delr,
                  icol, irow, theta, self.__proj, fctype=fctype)


    def fit2national(self):
        
        print('national grid')
        print(self.__natlExt)

        if isinstance(self.fac, int):
            # if fac == 1:
            res = self.__natCellsize * self.fac
            # if fac != 1:
                # raise Exception('expecting factor of 1')
            # else:
                # print('this is where grid would get bigger')

        elif isinstance(self.fac, str):
            if self.fac == '1/2':
                res = self.__natCellsize / 2
            elif self.fac == '1/4':
                res = self.__natCellsize / 4
            elif self.fac == '1/8':
                res = self.__natCellsize / 8
            else:
                res = 0
                print('this aint gonna work')
        else:
            res = 0
            print('this also aint gonna work')
        print('resolution',res)

        newext = {}

        syoff = (self.ext['ll'][1] - self.__natlExt['ll'][1]) / res
        y = self.__natlExt['ll'][1] + int(syoff) * res
        sxoff = (self.ext['ll'][0] - self.__natlExt['ll'][0]) / res
        x = self.__natlExt['ll'][0] + (int(sxoff)) * res

        newext['ll'] = [x, y]

        syoff = (self.ext['ur'][1] - self.__natlExt['ll'][1]) / res
        y = self.__natlExt['ll'][1] + int(syoff) * res + res

        sxoff = (self.ext['ur'][0] - self.__natlExt['ll'][0]) / res
        x = self.__natlExt['ll'][0] + (int(sxoff) + 1) * res 

        newext['ur'] = [x, y]
        newext['lr'] = [x, newext['ll'][1]]
        newext['ul'] = [newext['ll'][0], y]
        print('new local extent')
        print(newext)

        self.__newext = newext
        self.__ngcolNum = int(abs(self.__natlExt['ul'][0] - newext['ul'][0]) / res ) + 1
        self.__ngrowNum = int(abs(self.__natlExt['ul'][1] - newext['ul'][1]) / res) + 1
        self.__cellsize = res

        print('starting row and col of national grid')
        print(self.__ngrowNum, self.__ngcolNum)
        print(self.__irow, self.__icol, self.__cellsize)


    def readGrid(self, grid):
        from osgeo import gdal

        g = gdal.Open(grid)
        gt = g.GetGeoTransform()
        rsize = (g.RasterXSize, g.RasterYSize)
        a = g.GetRasterBand(1).ReadAsArray()

        return(gt, rsize, a)

    def rasterizeGrid(self, shp, gridOut, lyrName='modelgrid', 
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
            gt = (upperleft[0], self.__cellsize, 0.0, upperleft[1], 0.0, -self.__cellsize)
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

