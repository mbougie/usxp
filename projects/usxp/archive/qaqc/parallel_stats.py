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



def getJSONfile():
    with open('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\config\\test\\series_test4.json') as json_data:
        template = json.load(json_data)
        # print(template)
        # print type(template)
        return template



def createReclassifyList():
	cur = conn.cursor()

	query = "SELECT \"Value\",ytc from pre.{} as a JOIN pre.{} as b ON a.traj_array = b.traj_array WHERE ytc IS NOT NULL AND version ='{}'".format(data['pre']['traj']['filename'], data['pre']['traj']['lookup'], data['pre']['traj']['version'])
	print 'query:', query

	cur.execute(query)
	#create empty list
	fulllist=[[0,0,"NODATA"]]

	# fetch all rows from table
	rows = cur.fetchall()
	print rows
	print 'number of records in lookup table', len(rows)
	return rows
	



##create global objects to reference through the script

data = getJSONfile()
# print data
# location_list = createReclassifyList()




def execute_task(in_extentDict):

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
	state = 'nd'
    ### create numpy arrays for input datasets cdls and traj
	conf = {
			2008:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\{}.gdb\\cdl_30m_r_{}_2008_albers_confidence'.format(state,state), lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2009:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\{}.gdb\\cdl_30m_r_{}_2009_albers_confidence'.format(state,state), lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			2010:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\{}.gdb\\cdl_30m_r_{}_2010_albers_confidence'.format(state,state), lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973)
			# 2011:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\al.gdb\\cdl30_2011', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			# 2012:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\al.gdb\\cdl30_2012', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			# 2013:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\al.gdb\\cdl30_2013', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			# 2014:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\al.gdb\\cdl30_2014', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			# 2015:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\al.gdb\\cdl30_2015', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973),
			# 2016:arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\qaqc\\al.gdb\\cdl30_2016', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973)
	       }
	
	arr_traj = arcpy.RasterToNumPyArray(in_raster='D:\\projects\\usxp\\series\\s14\\post\\ytc.gdb\\s14_ytc30_2008to2016_mmu5_nbl', lower_left_corner = arcpy.Point(XMin,YMin), nrows = 13789, ncols = 21973)

	# # find the location of each pixel labeled with specific arbitray value in the rows list  
	# for row in location_list:
	# #year of conversion for either expansion or abandonment
	# ytx = row[1]
	
	# #year before conversion for either expansion or abandonment
	# ybx = row[1]-1
	
	#Return the indices of the pixels that have values of the ytc arbitrsy values of the traj.
	indices = (arr_traj != 0).nonzero()
	print indices

	#stack indices so easier to work with
	stacked_indices=np.column_stack((indices[0],indices[1]))
    
    #get the x and y location of each pixel that has been selected from above
	for pixel_location in stacked_indices:
		row = pixel_location[0] 
		# print 'row', row
		col = pixel_location[1]
		# print 'col', col
        
  #       #get the pixel value for ytx
		pixel_value_ytx =  conf[2008][row][col]
		print 'pixel_value_ytx', pixel_value_ytx

		# #get the pixel value for ybx
		# pixel_value_ybx =  conf[ybx][row][col]






	# arcpy.ClearEnvironment("extent")

	# outname = "tile_" + str(fc_count) +'.tif'

	# # #create
	# outpath = os.path.join("C:/Users/Bougie/Desktop/Gibbs/", r"tiles", outname)

	# # NumPyArrayToRaster (in_array, {lower_left_corner}, {x_cell_size}, {y_cell_size}, {value_to_nodata})
	# myRaster = arcpy.NumPyArrayToRaster(outData, lower_left_corner=arcpy.Point(XMin, YMin), x_cell_size=30, y_cell_size=30, value_to_nodata=0)
	

	# myRaster.save(outpath)





def mosiacRasters():
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



    





# def run():  
if __name__ == '__main__':
    #######clear the tiles from directory
	tiles = glob.glob("C:/Users/Bougie/Desktop/Gibbs/tiles/*")
	for tile in tiles:
		os.remove(tile)

	#get extents of individual features and add it to a dictionary
	extDict = {}
	count = 1 

	for row in arcpy.da.SearchCursor(data['ancillary']['vector']['shapefiles']['counties_subset'], ["SHAPE@"]):
		extent_curr = row[0].extent
		ls = []
		ls.append(extent_curr.XMin)
		ls.append(extent_curr.YMin)
		ls.append(extent_curr.XMax)
		ls.append(extent_curr.YMax)
		extDict[count] = ls
		count+=1
    
	print 'extDict', extDict
	print'extDict.items',  extDict.items()

	#######create a process and pass dictionary of extent to execute task
	pool = Pool(processes=1)
	pool.map(execute_task, extDict.items())
	pool.close()
	pool.join

	mosiacRasters()


# run()
    
   
