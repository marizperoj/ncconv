from shapely import wkt
import datetime
from in_memory_oo_multi_core import multipolygon_multicore_operation


ocgOpts = {'colbnds_name': u'bounds_longitude',
           'calendar': u'proleptic_gregorian',
           'time_name': u'time',
           'time_units': u'days since 1950-01-01 00:00:00',
           'rowbnds_name': u'bounds_latitude'}
dataset = 'http://cida.usgs.gov/qa/thredds/dodsC/maurer/monthly'
variable = 'sresa1b_miroc3-2-medres_2_Prcp'
polyint = wkt.loads('POLYGON ((-96.2500000000000000 38.7000000000000028, -95.7800000000000011 38.1000000000000014, -95.9000000000000057 39.1000000000000014, -96.2300000000000040 39.7999999999999972, -96.2500000000000000 38.7000000000000028))')
time_range = [datetime.datetime(2010, 3, 1, 0, 0), datetime.datetime(2010, 4, 30, 0, 0)]
clip = True
dissolve = False
levels = None
subdivide = True


elements = multipolygon_multicore_operation(
               dataset,
               variable,
               [polyint],
               time_range=time_range,
               clip=clip,
               dissolve=dissolve,
               levels=levels,
               ocgOpts=ocgOpts,
               subdivide=subdivide
             )