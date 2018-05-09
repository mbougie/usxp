import sys
import os
#import modules from other folders
sys.path.append('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\modules')
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



###NOTE STILL HAVE TO DEAL WITH YFC IN QUERY BELOW  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def createReclassifyList():
	cur = conn.cursor()
	
	query = "SELECT \"Value\", ytc, yfc from pre.{} as a JOIN pre.{} as b ON a.traj_array = b.traj_array WHERE ytc=2009 or yfc=2009".format(data['pre']['traj']['filename'], data['pre']['traj']['lookup_name'])
	# print 'query:', query

	cur.execute(query)
	#create empty list
	fulllist=[[0,0,"NODATA"]]

	# fetch all rows from table
	rows = cur.fetchall()
	# print rows
	# print 'number of records in lookup table', len(rows)
	return rows
	

##create global objects to reference through the script
# data = gen.getJSONfile()
# traj_list = createReclassifyList()
# print data




def execute_task(args):
	in_extentDict, data = args

	fc_count = in_extentDict[0]

	procExt = in_extentDict[1]
	# print procExt
	XMin = procExt[0]
	YMin = procExt[1]
	XMax = procExt[2]
	YMax = procExt[3]

	#set environments
	arcpy.env.snapRaster = data['pre']['traj']['path']
	arcpy.env.cellsize = data['pre']['traj']['path']
	arcpy.env.outputCoordinateSystem = data['pre']['traj']['path']	
	arcpy.env.extent = arcpy.Extent(XMin, YMin, XMax, YMax)

	cls = 21973
	rws = 13789

	# outData = numpy.zeros((rows,cols), numpy.int16)
	outData = np.zeros((13789, 21973), dtype=np.int)
    
    ### create numpy arrays for input datasets nlcds and traj
    # arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\binaries.gdb\\cdl30_b_2007_resampled', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
	cdls = {2007:arcpy.RasterToNumPyArray(in_raster='C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\ancillary\\raster\\binaries.gdb\\cdl30_b_2007', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973, nodata_to_value=255)}
	
	arr_traj = arcpy.RasterToNumPyArray(in_raster=data['pre']['traj']['path'], lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973)

	#### find the location of each pixel labeled with specific arbitray value in the rows list  
	#### note the traj_list is derived from the sql query above
	for row in traj_list:
		#trajectory value
		traj = row[0]
		#conversion year ytc
		ytc = row[1]
		# print 'ytc', ytc

		yfc = row[2]
		# print 'yfc', yfc

		#Return the indices of the pixels that have values of the ytc arbitray values of the traj.
		indices = (arr_traj == row[0]).nonzero()

		#stack the indices variable above so easier to work with
		stacked_indices=np.column_stack((indices[0],indices[1]))
        
        #get the x and y location of each pixel that has been selected from above
		for pixel_location in stacked_indices:
			row = pixel_location[0] 
			col = pixel_location[1]


			if ytc==2009 and cdls[2007][row][col]==1:
				# print cdls[2007][row][col]
				outData[row,col] = data['refine']['arbitrary_crop']


			elif yfc==2009 and cdls[2007][row][col]==0:
				# print cdls[2007][row][col]
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
	arcpy.MosaicToNewRaster_management(tilelist, data['refine']['gdb'], data['refine']['mask_2007']['filename'], inTraj.spatialReference, "16_BIT_UNSIGNED", 30, "1", "LAST","FIRST")


	#Overwrite the existing attribute table file
	arcpy.BuildRasterAttributeTable_management(data['refine']['mask_2007']['path'], "Overwrite")

	# Overwrite pyramids
	gen.buildPyramids(data['refine']['mask_2007']['path'])





def run(data):

	tiles = glob.glob("C:/Users/Bougie/Desktop/Gibbs/tiles/*")
	for tile in tiles:
		os.remove(tile)

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
	pool = Pool(processes=5)
	pool.map(execute_task, [(ed, data) for ed in extDict.items()])
	pool.close()
	pool.join

	mosiacRasters(data)


if __name__ == '__main__':
	run(data)
   

   
