import sys
import os
#import modules from other folders
sys.path.append('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\usxp\\misc\\')
import arcpy
from arcpy import env
from arcpy.sa import *
import glob

from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import psycopg2
from itertools import groupby
import general as gen
import json
import fnmatch
from multiprocessing import Process, Queue, Pool, cpu_count, current_process, Manager
import multiprocessing




arcpy.CheckOutExtension("Spatial")


try:
    conn = psycopg2.connect("dbname='usxp' user='mbougie' host='144.92.235.105' password='Mend0ta!'")
except:
    print "I am unable to connect to the database"



arcpy.env.overwriteOutput = True
arcpy.env.scratchWorkspace = "in_memory" 




def createReclassifyList(data):
	cur = conn.cursor()

	query = "SELECT \"Value\", mtr from pre_imw.{} as a JOIN pre_imw.{} as b ON a.traj_array = b.traj_array WHERE mtr = 3".format(data['pre']['traj']['filename'], data['pre']['traj']['lookup'])
	print 'query:', query

	cur.execute(query)
	#create empty list
	fulllist=[[0,0,"NODATA"]]

	# fetch all rows from table
	rows = cur.fetchall()
	print rows
	print 'number of records in lookup table', len(rows)
	return rows


def getNonCropList():
	cur = conn.cursor()

	query = "SELECT value FROM misc.lookup_cdl WHERE b = '0'"

	cur.execute(query)

	# fetch all rows from table
	rows = cur.fetchall()
	#use list comprehension to convert list of tuples to list
	noncrop_list = [i[0] for i in rows]

	##add 36 and 61 to noncrop list!!!
	return noncrop_list + [36,61]




def execute_task(args):
	in_extentDict, data, nc_list = args

	fc_count = in_extentDict[0]
	
	procExt = in_extentDict[1]
	# print procExt
	XMin = procExt[0]
	YMin = procExt[1]
	XMax = procExt[2]
	YMax = procExt[3]

	#set environments
	#The brilliant thing here is that using the extents with the full dataset!!!!!!   DONT EVEN NEED TO CLIP THE FULL RASTER TO THE FISHNET BECASUE 
	arcpy.env.snapRaster = data['pre']['traj']['path']
	arcpy.env.cellsize = data['pre']['traj']['path']
	arcpy.env.outputCoordinateSystem = data['pre']['traj']['path']	
	arcpy.env.extent = arcpy.Extent(XMin, YMin, XMax, YMax)

	cls = 21973
	rws = 13789


	# outData = numpy.zeros((rows,cols), numpy.int16)
	outData = np.zeros((13789, 21973), dtype=np.int)
    
    ### create numpy arrays for input datasets cdls and traj
	cdls = {
			2008:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2008', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2009:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2009', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2010:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2010', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2011:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2011', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2012:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2012', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2013:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2013', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2014:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2014', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2015:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2015', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2016:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2016', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2017:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\cdl.gdb\\cdl30_2017', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973)
	       }
	
	arr_traj = arcpy.RasterToNumPyArray(in_raster=data['pre']['traj']['path'], lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973)

	# find the location of each pixel labeled with specific arbitray value in the rows list  
	for row in createReclassifyList(data):
		#year of conversion for either expansion or abandonment
		fc = data['global']['years_conv']
		print 'fc', fc
		
		#year before conversion for either expansion or abandonment
		bfc = data['global']['years_conv']-1
		print 'bfc', bfc

		#Return the indices of the pixels that have values of the fc arbitrsy values of the traj.
		indices = (arr_traj == row[0]).nonzero()

		#stack indices so easier to work with
		stacked_indices=np.column_stack((indices[0],indices[1]))
        
        #get the x and y location of each pixel that has been selected from above
		for pixel_location in stacked_indices:
			row = pixel_location[0] 
			col = pixel_location[1]
            
            #get the pixel value for fc
			pixel_value_fc =  cdls[fc][row][col]
			#get the pixel value for bfc
			pixel_value_bfc =  cdls[bfc][row][col]

			#####  create dev mask  ##################################################################################
			if pixel_value_bfc in [122,123,124]:
				outData[row,col] = data['refine']['arbitrary_noncrop']

	        #####  create 36_61 mask  ################################################################################
			if pixel_value_fc in [36,61]:
				#find the years still left in the time series for this pixel location
				yearsleft = [i for i in data['global']['years'] if i > fc]
				#create templist to hold the rest of the cld values for the time series.  initiaite it with the first cdl value
				templist = [pixel_value_fc]
				for year in yearsleft:
					templist.append(cdls[year][row][col])

				#if the templist values are esentailly all "noncrop" then realbel as noncrop
				if len(set(np.isin(templist, nc_list))) == 1:
					outData[row,col] = data['refine']['arbitrary_noncrop']




	arcpy.ClearEnvironment("extent")

	outname = "tile_" + str(fc_count) +'.tif'

	# #create
	outpath = os.path.join("C:/Users/Bougie/Desktop/Gibbs/", r"tiles", outname)

	# NumPyArrayToRaster (in_array, {lower_left_corner}, {x_cell_size}, {y_cell_size}, {value_to_nodata})
	myRaster = arcpy.NumPyArrayToRaster(outData, lower_left_corner=arcpy.Point(XMin, YMin), x_cell_size=30, y_cell_size=30, value_to_nodata=0)
	

	myRaster.save(outpath)





def mosiacRasters(data):
	######Description: mosiac tiles together into a new raster
	tilelist = glob.glob("C:/Users/Bougie/Desktop/Gibbs/tiles/*.tif")
	print 'tilelist:', tilelist 

	#### need to wrap these paths with Raster() fct or complains about the paths being a string
	inTraj=Raster(data['pre']['traj']['path'])
	print 'inTraj:', inTraj


	######mosiac tiles together into a new raster
	arcpy.MosaicToNewRaster_management(tilelist, data['refine']['gdb'], data['refine']['mask_dev_alfalfa_fallow']['filename'], inTraj.spatialReference, "16_BIT_UNSIGNED", 30, "1", "LAST","FIRST")


	#Overwrite the existing attribute table file
	arcpy.BuildRasterAttributeTable_management(data['refine']['mask_dev_alfalfa_fallow']['path'], "Overwrite")

	# Overwrite pyramids
	gen.buildPyramids(data['refine']['mask_dev_alfalfa_fallow']['path'])



    





def run(data):

	tiles = glob.glob("C:/Users/Bougie/Desktop/Gibbs/tiles/*")
	for tile in tiles:
		os.remove(tile)

	nc_list = getNonCropList()

	#get extents of individual features and add it to a dictionary
	extDict = {}

	for row in arcpy.da.SearchCursor(data['ancillary']['vector']['shapefiles']['fishnet_mtr'], ["oid","SHAPE@"]):
		atlas_stco = row[0]
		print atlas_stco
		extent_curr = row[1].extent
		ls = []
		ls.append(extent_curr.XMin)
		ls.append(extent_curr.YMin)
		ls.append(extent_curr.XMax)
		ls.append(extent_curr.YMax)
		extDict[atlas_stco] = ls

	print 'extDict', extDict
	print'extDict.items',  extDict.items()

	#######create a process and pass dictionary of extent to execute task
	pool = Pool(processes=3)
	pool.map(execute_task, [(ed, data, nc_list) for ed in extDict.items()])
	pool.close()
	pool.join

	mosiacRasters(data)


if __name__ == '__main__':
	run(data)
    
   
