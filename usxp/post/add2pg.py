from sqlalchemy import create_engine
import numpy as np, sys, os
import fnmatch
# from osgeo import gdal
# from osgeo.gdalconst import *
import pandas as pd
import collections
from collections import namedtuple
# import openpyxl
import arcpy
from arcpy import env
from arcpy.sa import *
import glob
import psycopg2
sys.path.append('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\usxp\\misc\\')
import general as gen
import shutil
import matplotlib.pyplot as plt



#import extension
arcpy.CheckOutExtension("Spatial")
arcpy.env.parallelProcessingFactor = "95%"


try:
    conn = psycopg2.connect("dbname='usxp' user='mbougie' host='144.92.235.105' password='Mend0ta!'")
except:
    print "I am unable to connect to the database"







def addGDBTable2postgres(data,yxc):
    # set the engine.....
    engine = create_engine('postgresql://mbougie:Mend0ta!@144.92.235.105:5432/usxp')
    
    # # path to the table you want to import into postgres
    # input = 'C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\pre\\traj_rfnd\\v3\\v3_traj_rfnd.gdb\\v4_traj_cdl30_b_2008to2017_rfnd_v3'

    # Execute AddField twice for two new fields
    fields = [f.name for f in arcpy.ListFields(data['post'][yxc]['path'])]
   
    # converts a table to NumPy structured array.
    arr = arcpy.da.TableToNumPyArray(data['post'][yxc]['path'],fields)
    print arr
    
    # convert numpy array to pandas dataframe
    df = pd.DataFrame(data=arr)

    df.columns = map(str.lower, df.columns)

    print 'df-----------------------', df
    
    # # # use pandas method to import table into psotgres
    df.to_sql(data['post'][yxc]['filename'], engine, schema='counts')
    
    # #add trajectory field to table
    addAcresField('counts', data['post'][yxc]['filename'], yxc, '30')







def addAcresField(schema, tablename, yxc, res):
    #this is a sub function for addGDBTable2postgres()
    
    cur = conn.cursor()
    
    ####DDL: add column to hold arrays
    query1 = 'ALTER TABLE {}.{} ADD COLUMN acres bigint, ADD COLUMN series text, ADD COLUMN yxc text'.format(schema, tablename)
    print query1
    cur.execute(query1)

    #####DML: insert values into new array column
    cur.execute("UPDATE {0}.{1} SET acres=count*{2}, series='{3}', yxc='{4}'".format(schema, tablename, gen.getPixelConversion2Acres(res), tablename.split("_")[0], yxc))
    conn.commit() 




def createMergedTable():
  cur = conn.cursor()
  query="SELECT table_name FROM information_schema.tables WHERE table_schema = 'counts' AND SUBSTR(table_name, 1, 1) = 's';"
  cur.execute(query)
  rows = cur.fetchall()
  print rows
  
  table_list = []
  for row in rows:
    query_temp="SELECT * FROM counts.{}".format(row[0])
    table_list.append(query_temp)

  query_final = "DROP TABLE counts.merged_series; CREATE TABLE counts.merged_series AS {}".format(' UNION '.join(table_list))
  print query_final
  cur.execute(query_final)
  conn.commit()








def run(data,yxc):
  addGDBTable2postgres(data,yxc)
  createMergedTable()





if __name__ == '__main__':
  run(data,yxc)




