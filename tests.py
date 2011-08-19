import unittest
from shapely.geometry.polygon import Polygon
from util.ncwrite import NcSpatial, NcTime, NcVariable, NcWrite
import datetime
import os
from netCDF4 import Dataset
import in_memory_oo_multi_core as ncconv


class TestSimpleNc(unittest.TestCase):

    def get_uri(self,bounds=Polygon(((0,0),(10,0),(10,15),(0,15))),rng=[datetime.datetime(2007,10,1),datetime.datetime(2007,10,3)],res=5,constant=5,nlevels=1,path=None,bnds=True):
        """
        constant=5 -- provides a constant value when generating data to fill
            a NC variable. set to None to generate random values.
        nlevels=1 -- a value greater than 1 will create a NC with a fourth level
            dimension. the input values determines the number of levels.
        """
        ncspatial = NcSpatial(bounds,res,add_bounds=bnds)
        
        interval = datetime.timedelta(days=1)
        nctime = NcTime(rng,interval)
        
        ncvariable = NcVariable("Prcp","mm",constant=constant)
        
        ncw = NcWrite(ncvariable,ncspatial,nctime,nlevels=nlevels)
        uri = ncw.write(path)
        return(uri)

    def test_get_uri(self):
        uri = self.get_uri(bnds=False)
        self.assertTrue(os.path.exists(uri))
        d = Dataset(uri,'r')
        sh = d.variables["Prcp"].shape
        self.assertEqual(sh,(3,3,2))
        d.close()



    def _getCtrd(element):
        g = element['geometry']
        return (g.centroid.x,g.centroid.y)


    def setUp(self):
        self.singleLayer = self.get_uri(bounds=Polygon(((0,0),(20,0),(20,20),(0,20))),rng=[datetime.datetime(2000,1,1),datetime.datetime(2000,1,10)],res=10)
        self.multiLayer = self.get_uri(nlevels=4)
        self.randomized = self.get_uri(constant=None,nlevels=4)

    def _access(self,uri,polygons,temporal,dissolve,clip,levels,subdivide,subres):
        POLYINT = polygons
        
        dataset = uri

        TEMPORAL = temporal
        DISSOLVE = dissolve
        CLIP = clip
        VAR = 'Prcp'
        kwds = {
            'rowbnds_name': 'bounds_latitude', 
            'colbnds_name': 'bounds_longitude',
            'time_units': 'days since 1800-01-01 00:00:00 0:00',
            'level_name': 'level',
            'calendar': 'gregorian'
        }
        ## open the dataset for reading
        ## make iterable if only a single polygon requested
        if type(POLYINT) not in (list,tuple): POLYINT = [POLYINT]
        ## convenience function for multiple polygons
        elements = ncconv.multipolygon_multicore_operation(dataset,
                                        VAR,
                                        POLYINT,
                                        time_range=TEMPORAL,
                                        clip=CLIP,
                                        dissolve=DISSOLVE,
                                        levels = levels,
                                        ocgOpts=kwds,
                                        subdivide=subdivide,
                                        subres = subres
                                        )

        return elements

    def test_LSSlSdRcd(self):
        layer = self.singleLayer
        poly = Polygon(((0,0),(10,0),(10,10),(0,10))) 
        time = [datetime.datetime(2000,1,1),datetime.datetime(2000,1,1)]
        levels = None
        subdivide = False
        subres = 'Detect'
        elements = self._access(layer,poly,time,False,False,levels,subdivide,subres)
        print elements
        self.assertEqual(len(elements),1)
        self.assertEqual(self._getCtrd(elements[0]),(5,5))
        
        poly = Polygon(((0,0),(20,0),(20,10),(0,10)))
        elements = self.access(layer,poly,time,False,False,levels,subdivide,subres)
        self.assertEqual(len(elements),2)

        c = [self._getCtrd(x) for x in elements]
        self.assertTrue((5,5) in c and (10,5) in c)

        poly = Polygon(((0,0),(20,0),(20,20),(0,20)))
        elements = self.access(layer,poly,time,False,False,levels,subdivide,subres)
        self.assertEqual(len(elements),4)
        c = [self._getCtrd(x) for x in elements]
        self.assertTrue((5,5) in c and (10,5) in c and (10,10) in c and (5,10) in c)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()