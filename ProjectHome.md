Allows you to extract data from a netCDF file and save the results as either geoJSON or shapefile.

Allows you to specify multiple geographical regions, time ranges, and/or spatial levels in the case of multi-level data.

Two operation parameters:

Dissolve -

True: geometry is dissolved into a single feature, data values are averaged over the entire area.

False: Each data point in the file is output as a separate geographical feature.


Clip -

True: feature geometries are clipped so only data points lying within the Area of Interest are included. Features that lie on the edge are intersected with the AoI, but the value at that location is unmodified.

False: all features within the bounding envelope of the AoI are included, features are not intersected with the AoI.


Supports multi-core systems

Can access netCDF files through a web URL