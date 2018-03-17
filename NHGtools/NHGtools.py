
import os, sys
import numpy as np
from . import fishnet as fn

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
        # assign defaults
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
   
        delr = [self.__cellsize for x in range(self.__irow)]
        delc = [self.__cellsize for x in range(self.__icol)]
        theta = 0.0

        print('new cols and rows', self.__icol, self.__irow)
        # irow and icol are ....
        fn.mkGrid(self.fc, self.__newext['ll'], delc, delr, self.__icol,
                  self.__irow, theta, self.__proj, self.fctype,
                  ngcolNum=self.__ngcolNum)

    def mkNationalGrid(self): #fc, fctype='gpkg'):

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


        # number of rows and cols of new grid
        self.__irow, self.__icol = fn.calcRowCol(self.__newext['ll'], self.__newext['lr'], 
                                   self.__newext['ur'], self.__cellsize) 
        print('number of rows, columns, and cellsize of new grid')
        print(self.__irow, self.__icol, self.__cellsize)


    def readGrid(self, grid):
        from osgeo import gdal

        g = gdal.Open(grid)
        gt = g.GetGeoTransform()
        rsize = (g.RasterXSize, g.RasterYSize)
        a = g.GetRasterBand(1).ReadAsArray()

        return(gt, rsize, a)

    def rasterizeGrid(self, fc=None, rasterName='mygrid.tif',
                      lyrName='modelgrid', 
                      attribute='cellnum', 
                      wkt='', raster=None):
        """
        rasterize modelgrid - use cellnum as value
        """
        if fc == None:
            fc = '{}.{}'.format(self.fc, self.fctype)

        from osgeo import gdal, osr, ogr

        # steal geotransform from existing grid
        if raster != None:
            gt, rsize, a = self.readGrid(raster)
        else:
            gt = (self.__newext['ul'][0],
                  self.__cellsize,
                  0.0,
                  self.__newext['ul'][1],
                  0.0,
                  -self.__cellsize)

            rsize = (self.__icol, self.__irow)

        ds = ogr.Open(fc)
        if lyrName != None:
            lyr = ds.GetLayerByName(lyrName)
        else:
            lyr = ds.GetLayer(0)

        proj = lyr.GetSpatialRef() #.ExportToProj4()
        proj = proj.ExportToProj4()
        srs = osr.SpatialReference()
        srs.ImportFromProj4(proj)

        driver = gdal.GetDriverByName('GTiff')

        rvds = driver.Create(rasterName, rsize[0], rsize[1], 1, gdal.GDT_Int32)
        rvds.SetGeoTransform(gt)
        rvds.SetProjection(srs.ExportToWkt())
        gdal.RasterizeLayer(rvds, [1], lyr, None, None, [1], ['ATTRIBUTE={}'.format(attribute)])

        print('Rasterizification complete')


    def makeCellNumRaster(self):

        # delrTot = 0. 
        # delcTot = self.__cellsize
        # delc1 = 0.

        # create grid cells
        # for i,c in enumerate(delc):
        cells = []

        # for i in range(self.__icol):
        for j in range(self.__irow):

            # sys.stdout.write('\r{} of {} cols'.format(i+1, self.__icol))
            # sys.stdout.flush()

            # for j,r in enumerate(delr):
            # for j in range(self.__irow):
            for i in range(self.__icol):

                # delrTot = delrTot + r

                # ngrow = irow + self.__irow - (j + 1)
                # ngcol = icol + i
                # natlCellNum = (ngrow - 1) * ngcolNum + ngcol

                irow = self.__irow - j
                icol = i + 1
                # cellNum = (len(delr) - j - 1) * len(delc) + i + 1
                cellNum = (self.__irow - j - 1) * self.__icol + i + 1
                cells.append(cellNum)

        cells = np.array(cells)
        cells = cells.reshape((self.__irow, self.__icol))
        self.__grid = cells

