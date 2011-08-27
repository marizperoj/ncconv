import os
import numpy as np
from netCDF4 import date2num, Dataset
import datetime
from shapely.geometry import Polygon
from helpers import get_temp_path
from pdb import set_trace


#PATH = os.path.join(os.path.split(climatedata.__file__)[0],'fixtures','trivial_grid.json')
#
#
### collect data objects
#cells = []
#with open(PATH,'r') as f:
#    for obj in serializers.deserialize("json",f):
#        if isinstance(obj.object,SpatialGridCell):
#            cells.append(obj.object)
#        elif isinstance(obj.object,SpatialGrid):
#            grid = obj.object
#        else:
#            raise ValueError('db model not recognized')
        
## organize cells into lat/lon objects

class NcSpatial(object):
    """
    bounds -- shapely Polygon objects
    res -- float
    
    >>> bounds = Polygon(((0,0),(10,0),(10,15),(0,15)))
    >>> res = 5
    >>> n = NcSpatial(bounds,res)
    >>> n._check_partition_(0,10,5)
    True
    >>> n._check_partition_(0,3,15)
    Traceback (most recent call last):
        ...
    ValueError: selected interval must yield an equal number of partitions.
    >>> n.get_dimension()
    {'row_bnds': array([[  0.,   5.],
           [  5.,  10.],
           [ 10.,  15.]]), 'col': array([ 2.5,  7.5]), 'col_bnds': array([[  0.,   5.],
           [  5.,  10.]]), 'row': array([  2.5,   7.5,  12.5])}
    """
    
    def __init__(self,bounds,res,add_bounds=True):
        self.bounds = bounds
        self.res = float(res)
        self.add_bounds = add_bounds
        
    def get_dimension(self):
        self._partition_()
        ret = dict(row=self.dim_row,
                   col=self.dim_col)
        if self.add_bounds:
            ret.update(dict(row_bnds=self.dim_rowbnds,
                            col_bnds=self.dim_colbnds))
        return(ret)
        
    def _partition_(self):
        min_x,min_y,max_x,max_y = self.bounds.envelope.bounds
        self.dim_row = self._do_partition_(min_y,max_y,self.res)
        self.dim_col = self._do_partition_(min_x,max_x,self.res)
        if self.add_bounds:
            self.dim_rowbnds = self._make_bounds_(self.dim_row)
            self.dim_colbnds = self._make_bounds_(self.dim_col)
        
    def _make_bounds_(self,centroid):
        l = (centroid - 0.5*self.res).reshape(-1,1)
        u = (centroid + 0.5*self.res).reshape(-1,1)
        return(np.hstack((l,u)))
        
    def _check_partition_(self,lower,upper,interval):
        if (upper-lower)%interval != 0:
            raise ValueError('selected interval must yield an equal number of partitions.')
        else:
            return(True)
        
    def _do_partition_(self,lower,upper,interval):
        self._check_partition_(lower,upper,interval)
        return(np.arange(lower,upper,interval)+(0.5*interval))
    
    
class NcTime(object):
    """
    >>> rng = [datetime.datetime(2007,10,1),datetime.datetime(2007,10,3)]
    >>> interval = datetime.timedelta(days=1)
    >>> n = NcTime(rng,interval)
    >>> n._get_dates_()
    [datetime.datetime(2007, 10, 1, 0, 0), datetime.datetime(2007, 10, 2, 0, 0), datetime.datetime(2007, 10, 3, 0, 0)]
    >>> n.get_dimension()
    array([ 75878.,  75879.,  75880.])
    >>> overload = [datetime.datetime(2007,10,15),datetime.datetime(2007,11,15)]
    >>> n = NcTime(overload=overload)
    >>> n.get_dimension()
    array([ 75892.,  75923.])
    """
    
    def __init__(self,rng=None,interval=None,overload=None,
                      units='days since 1800-01-01 00:00:00 0:00',
                      calendar='gregorian'):
        self.rng = rng
        self.interval = interval
        self.units = units
        self.calendar = calendar
        self.overload = overload
        
    def get_dimension(self):
        return(date2num(self._get_dates_(),self.units,self.calendar))
    
    def _get_dates_(self):
        if self.overload != None:
            ret = self.overload
        else:
            dtimes = []
            curr = self.rng[0]
            while curr <= self.rng[1]:
                dtimes.append(curr)
                curr += self.interval
            ret = dtimes
        return(ret)
    
    
class NcVariable(object):
    """
    >>> n = NcVariable("Prcp","mm",constant=5)
    >>> n.get_values((2,2))
    array([[ 5.,  5.],
           [ 5.,  5.]])
    >>> n = NcVariable("Prcp","mm",seed=1)
    >>> n.get_values((2,2))
    array([[ 1.62434536, -0.61175641],
           [-0.52817175, -1.07296862]])
    """
    
    def __init__(self,name,units,constant=None,seed=None):
        self.name = name
        self.units = units
        self.constant = constant
        self.seed = seed
        
    def get_values(self,shape):
        if self.constant is not None:
            v = np.ones(shape)*self.constant
        else:
            if self.seed != None: np.random.seed(self.seed)
            v = abs(np.random.normal(size=shape))
            #np.set_printoptions(precision=10)
            #print repr(v)
        return(v)
        
    

class NcWrite(object):
    """
    >>> ncvariable = NcVariable("Prcp","mm",constant=5)
    >>> bounds = Polygon(((0,0),(10,0),(10,15),(0,15)))
    >>> res = 5
    >>> ncspatial = NcSpatial(bounds,res)
    >>> rng = [datetime.datetime(2007,10,1),datetime.datetime(2007,10,3)]
    >>> interval = datetime.timedelta(days=1)
    >>> nctime = NcTime(rng,interval)
    >>> ncw = NcWrite(ncvariable,ncspatial,nctime)
    >>> path = get_temp_path(suffix='.nc')
    >>> rootgrp = ncw.get_rootgrp(path)
    >>> rootgrp.variables["Prcp"][:].shape
    (3, 3, 2)
    >>> ncw = NcWrite(ncvariable,ncspatial,nctime,nlevels=4)
    >>> path = get_temp_path(suffix='.nc')
    >>> rootgrp = ncw.get_rootgrp(path)
    >>> rootgrp.variables["Prcp"][:].shape
    (3, 4, 3, 2)
    >>> rootgrp.variables["bounds_latitude"][:].shape
    (3, 2)
    """
    
    def __init__(self,ncvariable,ncspatial,nctime,nlevels=1):
        self.ncvariable = ncvariable
        self.ncspatial = ncspatial
        self.nctime = nctime
        self.nlevels = nlevels
        
        self._dt = self.nctime.get_dimension()
        self._dsp = self.ncspatial.get_dimension()
        
    def write(self,path=None):
        if path is None:
            path = get_temp_path('.nc')
        rootgrp = self.get_rootgrp(path)
        rootgrp.close()
        return(path)
            
    def get_rootgrp(self,path):
        rootgrp = Dataset(path,'w',format='NETCDF4')
        
        rootgrp.createDimension('time',len(self._dt))
        rootgrp.createDimension('lon',len(self._dsp['col']))
        rootgrp.createDimension('lat',len(self._dsp['row']))
        
        times = rootgrp.createVariable('time','f8',('time',))
        latitudes = rootgrp.createVariable('latitude','f4',('lat',))
        longitudes = rootgrp.createVariable('longitude','f4',('lon',))
        
        bdim = ['time','lat','lon']
        if self.nlevels > 1:
            bdim.insert(1,'lvl')
            rootgrp.createDimension('lvl',self.nlevels)
            levels = rootgrp.createVariable('level','u1',('lvl',))
            levels[:] = np.arange(1,self.nlevels+1)
        var = rootgrp.createVariable(self.ncvariable.name,'f4',bdim)
        
        times.units = self.nctime.units
        times.calendar = self.nctime.calendar
        var.units = self.ncvariable.units
        
        latitudes[:] = self._dsp['row']
        longitudes[:] = self._dsp['col']
        times[:] = self._dt
        
        values = self.ncvariable.get_values(var.shape)
        if self.nlevels > 1:
            var[:,:,:,:] = values
        else:
            var[:,:,:] = values
            
        if self.ncspatial.add_bounds:
            rootgrp.createDimension('bound',2)
            blats = rootgrp.createVariable('bounds_latitude','f4',('lat','bound'))
            blons = rootgrp.createVariable('bounds_longitude','f4',('lon','bound'))
            blats[:,:] = self._dsp['row_bnds']
            blons[:,:] = self._dsp['col_bnds']
        
        return(rootgrp)

def NcSubset(path,ocg,Var,poly,time_range,Levels=None,lat_name='latitude',lon_name='longitude'):
    'subset a netCDF4 file'

    npd = ocg._get_numpy_data_(Var,polygon=poly,time_range=time_range,levels=Levels)

    rootgrp = Dataset(path,'w',format='NETCDF4')
    
    rootgrp.createDimension('time',len(ocg._idxtime))
    rootgrp.createDimension('lon',len(ocg._idxcol))
    rootgrp.createDimension('lat',len(ocg._idxrow))

    times = rootgrp.createVariable(ocg.time_name,'f8',('time',))
    latitudes = rootgrp.createVariable('latitude','f4',('lat',))
    longitudes = rootgrp.createVariable('longitude','f4',('lon',))

    bdim = ['time','lat','lon']
    if not(Levels==None):
        bdim.insert(1,'lvl')
        rootgrp.createDimension('lvl',len(Levels))
        levels = rootgrp.createVariable(ocg.level_name,'u1',('lvl',))
        #print '>>',ocg.levels[np.array(Levels)]
        levels[:] = list(x for x in ocg.levels[np.array(Levels)])
    var = rootgrp.createVariable(Var,'f4',bdim)

    times.units = ocg.time_units
    times.calendar = ocg.calendar
    var.units = ocg.dataset.variables[Var].units

    #print ocg.dataset.variables.keys()
    latitudes[:] = ocg.dataset.variables[lat_name][ocg._idxrow]
    longitudes[:] = ocg.dataset.variables[lon_name][ocg._idxcol]
    times[:] = ocg.dataset.variables[ocg.time_name][ocg._idxtime]

    if hasattr(npd,'mask'):
        npdma = np.ma.array(npd,mask=np.invert(ocg._mask*np.invert(npd.mask)))
    else:
        mask=np.invert(ocg._mask)
        if not(Levels==None):
            mask = np.zeros((len(ocg._idxtime),len(levels),len(ocg._idxrow),len(ocg._idxcol)),dtype=bool)
        else:
            mask = np.zeros((len(ocg._idxtime),len(ocg._idxrow),len(ocg._idxcol)),dtype=bool)

        mask = np.invert(ocg._mask*np.invert(mask))
        #print mask

        npdma = np.ma.masked_array(npd,mask=mask)

    #print ">>>>>>>>",hasattr(npdma,'mask')
    #print npdma.mask

    if not(Levels==None):
        var[:,:,:,:] = npdma
    else:
        var[:,:,:] = npdma

    #print ">>>>>>>>",hasattr(var,'mask')
    #print npdma.mask

    #print ocg.min_row.shape
    #print ocg._idxrow
    #print ocg._idxcol
    #print ocg._idxrow.shape
    #print ocg._idxcol.shape
    #print
    mr  = ocg.min_row[ocg._idxrow,:][:,ocg._idxcol]
    mxr = ocg.max_row[ocg._idxrow,:][:,ocg._idxcol]
    mc  = ocg.min_col[ocg._idxrow,:][:,ocg._idxcol]
    mxc = ocg.max_col[ocg._idxrow,:][:,ocg._idxcol]

    #print ocg.min_row
    #print ocg.min_col
    #print
    #print mr
    #print mxr

    #print mc
    #print mc.shape
    #print mxc

    #mr  = ocg.min_row[ocg._idxrow,ocg._idxcol]
    #mxr = ocg.max_row[ocg._idxrow,ocg._idxcol]
    #mc  = ocg.min_col[ocg._idxrow,ocg._idxcol]
    #mxc = ocg.max_col[ocg._idxrow,ocg._idxcol]

    #print mr
    #print mxr

    #print mc
    #print mxc
    #print ocg.row_bnds
    #print ocg.col_bnds

    rootgrp.createDimension('bound',2)
    blats = rootgrp.createVariable(ocg.rowbnds_name,'f4',('lat','bound'))
    blons = rootgrp.createVariable(ocg.colbnds_name,'f4',('lon','bound'))
    #print [ [mr[x,0],mxr[x,0]] for x in xrange(mr.shape[0])]
    #print [ [mc[0,x],mxc[0,x]] for x in xrange(mc.shape[1])]
    blats[:,:] = [ [mr[x,0],mxr[x,0]] for x in xrange(mr.shape[0])]
    blons[:,:] = [ [mc[0,x],mxc[0,x]] for x in xrange(mc.shape[1])]
        

if __name__ == '__main__':
    import doctest
    doctest.testmod()