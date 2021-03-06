import arcpy
from arcpy import env
from arcpy.sa import *
import pandas as pd
import numpy as np
import os
import glob
import sys
import psycopg2
from sqlalchemy import create_engine
from multiprocessing import Process, Queue, Pool, cpu_count, current_process, Manager
sys.path.append('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\modules\\')
import general as gen







try:
    conn = psycopg2.connect("dbname='usxp' user='mbougie' host='144.92.235.105' password='Mend0ta!'")
except:
    print "I am unable to connect to the database"





#import extension
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
arcpy.env.scratchWorkspace = "in_memory" 




def execute_task(args):
	#create region group tiles and add fields to raster after to define from which tile it came from
	#these tiles contain all mtr values (1-5)
	in_extentDict, data = args

	rg_combos = {'4w':["FOUR", "WITHIN"], '8w':["EIGHT", "WITHIN"], '4c':["FOUR", "CROSS"], '8c':["EIGHT", "CROSS"]}
	rg_instance = rg_combos['8w']


	fc_count = in_extentDict[0]
	# print fc_count
	procExt = in_extentDict[1]
	# print procExt
	XMin = procExt[0]
	YMin = procExt[1]
	XMax = procExt[2]
	YMax = procExt[3]

	#set environments
	arcpy.env.extent = arcpy.Extent(XMin, YMin, XMax, YMax)
    

	raster_in = Raster(data['core']['path'])
	raster_rg = RegionGroup(raster_in, rg_instance[0], rg_instance[1], "ADD_LINK")

	#clear out the extent for next time
	arcpy.ClearEnvironment("extent")

	outname = "tile_" + str(fc_count) +'.tif'

	outpath = os.path.join("C:/Users/Bougie/Desktop/Gibbs/data/", r"tiles", outname)

	raster_rg.save(outpath)


	arcpy.AddField_management(Raster(outpath), field_name='tile', field_type='TEXT')
	expression = "{}".format(str(fc_count))
	arcpy.CalculateField_management(outpath, "tile", expression, "PYTHON_9.3")






def createMergedTable():
	##import all tiles as tables into postgres where mtr3 or mtr4 and count >= 23
	##merge all tile tables into one table with a unique id primary key
	# set the engine.....
	engine = create_engine('postgresql://mbougie:Mend0ta!@144.92.235.105:5432/usxp')

	tilelist = glob.glob("C:/Users/Bougie/Desktop/Gibbs/data/tiles/*.tif")
	print 'tilelist:', tilelist 

	querylist=[]

	for tile in tilelist:

		print tile
		tile_split=tile.split("\\")
		table_name=tile_split[1].split(".")

		# Execute AddField twice for two new fields
		fields = [f.name for f in arcpy.ListFields(tile)]

		# converts a table to NumPy structured array.
		arr = arcpy.da.TableToNumPyArray(tile,fields)
		print arr

		# convert numpy array to pandas dataframe
		df = pd.DataFrame(data=arr)

		df.columns = map(str.lower, df.columns)

		print 'df-----------------------', df

		mtr3 = df['link'] == 3 
		mtr4 = df['link'] == 4 
        
		yo = df[mtr3 | mtr4]

		print 'df------- subset ---', yo
		# # # use pandas method to import table into psotgres
		### beusre to only select the pathces that have count 23 or greater
		yo.to_sql(table_name[0], engine, schema='eric')

		querylist.append("SELECT * FROM eric.{} WHERE count >= 23".format(table_name[0]))



	query = "CREATE TABLE eric.merged_table AS " + ' UNION '.join(querylist) + " ORDER BY tile; ALTER TABLE eric.merged_table ADD COLUMN id SERIAL PRIMARY KEY;"
	print '--- query ----', query
    
	cur = conn.cursor()
	cur.execute(query);

	conn.commit()
	print "Records created successfully";
	# conn.close()






def reclassTiles(data, field):
	tilelist = glob.glob("C:/Users/Bougie/Desktop/Gibbs/data/tiles/*.tif")
	print 'tilelist:', tilelist 

	for tile in tilelist:

		print tile
		tile_split=tile.split("\\")
		print tile_split[0], tile_split[1]
		output = '{}/mtr/{}'.format(tile_split[0], tile_split[1].replace(".tif", "_mtr_{}.tif".format(field)))
		print output

		table_name=tile_split[1].split(".")
		tile_num = table_name[0].split("_")

		return_string = getReclassifyValuesString(tile_num[1], field)
		arcpy.gp.Reclassify_sa(tile, "Value", return_string, output, "NODATA")

    #### mosiac all the mtr datasets
	mosiacRasters(data, field)






def getReclassifyValuesString(tile_num, field):
    #Note: this is a aux function that the reclassifyRaster() function references
    cur = conn.cursor()
    
    query = "SELECT value, {} FROM eric.merged_table WHERE tile='{}'".format(field, tile_num)
    print 'query:', query
    #DDL: add column to hold arrays
    cur.execute(query);
    
    #create empty list
    reclassifylist=[['0 NODATA']]

    # fetch all rows from table
    rows = cur.fetchall()
    
    # interate through rows tuple to format the values into an array that is is then appended to the reclassifylist
    for row in rows:
        ww = [str(row[0]) + ' ' + str(int(row[1]))]
        reclassifylist.append(ww)
    
    #flatten the nested array and then convert it to a string with a ";" separator to match arcgis format 
    columnList = ';'.join(sum(reclassifylist, []))
    print columnList
    
    #return list to reclassifyRaster() fct
    return columnList






def mosiacRasters(data, field):
	tilelist = glob.glob("C:/Users/Bougie/Desktop/Gibbs/data/tiles/mtr/*{}.tif".format(field))
	print tilelist 
	#### need to wrap these paths with Raster() fct or complains about the paths being a string
	inTraj=Raster(tilelist[0])

	gdb = 'C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\sa\\r2\\{0}\\core\\core_{0}.gdb'.format(data['global']['instance'])
	filename = '{}_mtr_{}'.format(data['global']['instance'], field)
	path = '{}\\{}'.format(gdb, filename)

	######mosiac tiles together into a new raster
	arcpy.MosaicToNewRaster_management(tilelist, gdb, filename, inTraj.spatialReference, "32_BIT_UNSIGNED", 30, "1", "LAST","FIRST")

	# #Overwrite the existing attribute table file
	arcpy.BuildRasterAttributeTable_management(path, "Overwrite")

	# # Overwrite pyramids
	gen.buildPyramids(path)







def run(data):


	# # # #####  remove a files in tiles directory
	# tiles = glob.glob("C:/Users/Bougie/Desktop/Gibbs/data/tiles/*")
	# for tile in tiles:
	# 	os.remove(tile)

	# #get extents of individual features and add it to a dictionary
	# extDict = {}

	# for row in arcpy.da.SearchCursor(data['ancillary']['vector']['shapefiles']['fishnet_mtr'], ["oid","SHAPE@"]):
	# 	atlas_stco = row[0]
	# 	print atlas_stco
	# 	extent_curr = row[1].extent
	# 	ls = []
	# 	ls.append(extent_curr.XMin)
	# 	ls.append(extent_curr.YMin)
	# 	ls.append(extent_curr.XMax)
	# 	ls.append(extent_curr.YMax)
	# 	extDict[atlas_stco] = ls

	# print 'extDict', extDict
	# print'extDict.items',  extDict.items()

	# ######create a process and pass dictionary of extent to execute task
	# pool = Pool(processes=1)
	# pool.map(execute_task, [(ed, data) for ed in extDict.items()])
	# pool.close()
	# pool.join


	print('---createMergedTable()----')
	# createMergedTable()
    
	reclassTiles(data, 'id')

if __name__ == '__main__':

	## NOTE: BERORE EACH NEW SERIES HAVE:
	## 1) eric schema in postgres
    ## 2) have mtr3 and mtr4 in the tiles folder 
	run(data)




