from osgeo import osr


wkt = """
PROJCS["WGS_84_Alaska_Albers",
    GEOGCS["GCS_WGS_1984",
        DATUM["WGS_1984",
            SPHEROID["WGS_1984",6378137.0,298.257223563]],
        PRIMEM["Greenwich",0.0],
        UNIT["Degree",0.017453292519943295]],
    PROJECTION["Albers_Conic_Equal_Area"],
    PARAMETER["False_Easting",0.0],
    PARAMETER["False_Northing",0.0],
    PARAMETER["longitude_of_center",-154.0],
    PARAMETER["Standard_Parallel_1",55.0],
    PARAMETER["Standard_Parallel_2",65.0],
    PARAMETER["latitude_of_center",50.0],
    UNIT["Meter",1.0]]
"""

wkt = """
PROJCS["USA_Contiguous_Albers_Equal_Area_Conic_USGS_WGS84",
    GEOGCS["GCS_WGS_1984",
        DATUM["WGS_1984",
            SPHEROID["WGS_1984",6378137.0,298.257223563]],
        PRIMEM["Greenwich",0.0],
        UNIT["Degree",0.017453292519943295]],
    PROJECTION["Albers_Conic_Equal_Area"],
    PARAMETER["False_Easting",0.0],
    PARAMETER["False_Northing",0.0],
    PARAMETER["longitude_of_center",-96.0],
    PARAMETER["Standard_Parallel_1",29.5],
    PARAMETER["Standard_Parallel_2",45.5],
    PARAMETER["latitude_of_center",23.0],
    UNIT["Meter",1.0]]
"""

wkt = """
PROJCS["North_America_Equidistant_Conic",
    GEOGCS["GCS_North_American_1983",
        DATUM["North_American_Datum_1983",
            SPHEROID["GRS_1980",6378137.0,298.257222101]],
        PRIMEM["Greenwich",0.0],
        UNIT["Degree",0.0174532925199433]],
    PROJECTION["Equidistant_Conic"],
    PARAMETER["False_Easting",0.0],
    PARAMETER["False_Northing",0.0],
    PARAMETER["longitude_of_center",-96.0],
    PARAMETER["Standard_Parallel_1",20.0],
    PARAMETER["Standard_Parallel_2",60.0],
    PARAMETER["latitude_of_center",40.0],
    UNIT["Meter",1.0]]
"""


class PgSpatialReference(osr.SpatialReference):
    
    def ExportToPostGisInsertStatement(self,srid):
        sql = """INSERT INTO spatial_ref_sys (srid,auth_name,auth_srid,srtext,proj4text) VALUES ({0},'custom',{0},'{1}','{2}')""".format(srid,sr.ExportToWkt(),sr.ExportToProj4())
        return sql

#p = osr.ImportFromWKT(wkt)
sr = PgSpatialReference()
sr.ImportFromWkt(wkt)
print sr.AutoIdentifyEPSG()
print sr.ExportToProj4()
print sr.ExportToWkt()
print sr.ExportToPostGisInsertStatement(900007)