from sqlalchemy import create_engine
import numpy as np, sys, os
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
import general as gen 
import pprint


'''######## DEFINE THESE EACH TIME ##########'''
#Note: need to change this each time on different machine
case=['Bougie','Gibbs']

try:
    conn = psycopg2.connect("dbname='usxp' user='mbougie' host='144.92.235.105' password='Mend0ta!'")
except:
    print "I am unable to connect to the database"


###################  Define the environment  #######################################################
#establish root path for this the main project (i.e. usxp)
rootpath = 'C:/Users/'+case[0]+'/Desktop/'+case[1]+'/data/usxp/'

### establish gdb path  ####
def defineGDBpath(args_list):
    gdb_path = '{}{}/{}/{}.gdb/'.format(rootpath,args_list[0],args_list[1],args_list[2])
    # print 'gdb path: ', gdb_path 
    return gdb_path





#################### class to create yxc object  ####################################################



    #     if self.name == 'ytc':
    #         self.mtr = 3
    #     elif self.name == 'yfc':
    #         self.mtr = 4
    
    # #function for to get correct cdl for the attachCDL() function
    # def getAssociatedCDL(self, year):
    #     if self.subname == 'bfc' or  self.subname == 'bfnc':
    #         # subtract 1 from every year in list
    #         cdl_file = defineGDBpath(['ancillary','cdl'])+'cdl_'+ str(year - 1)
    #         return cdl_file

    #     elif self.subname == 'fc' or  self.subname == 'fnc':
    #         # subtract 1 from every year in list
    #         cdl_file = defineGDBpath(['ancillary','cdl'])+'cdl_'+ str(year)
    #         return cdl_file

        


def createYearbinaries(data):
        # DESCRIPTION:attach the appropriate cdl value to each year binary dataset
    print "-----------------  createYearbinaries()  -------------------------------"
    def createReclassifyList():
        #this is a sub function for createYearbinaries_better().  references the mtr value in psotgres to create a list containing arbitray trajectory value and associated new mtr value

        engine = create_engine('postgresql://mbougie:Mend0ta!@144.92.235.105:5432/usxp')
        query = 'SELECT * FROM {} as a JOIN {} as b ON a.traj_array = b.traj_array WHERE {} IS NOT NULL'.format(data['paths_global']['traj'], data['paths_global']['traj_lookup'], data['paths_global']['name'])
        print 'query:', query
        df = pd.read_sql_query(query, con=engine)
        print df
        fulllist=[[0,0,"NODATA"]]
        for index, row in df.iterrows():
            templist=[]
            value=row['Value'] 
            yxc=row[data['paths_global']['name']]  
            templist.append(int(value))
            templist.append(int(yxc))
            fulllist.append(templist)
        print 'fulllist: ', fulllist
        return fulllist


    ## replace the arbitrary values in the trajectories dataset with the yxc values.
    # raster = Raster(defineGDBpath(['pre', 'v2', 'traj_refined'])+post.traj_dataset)
    raster = Raster(data['paths_post']['createYearbinaries']['input'])
    print 'raster:', raster

    # output = defineGDBpath(['s14', 'post', post.name])+post.yxc_dataset
    output = Raster(data['paths_post']['createYearbinaries']['output'])
    print 'output: ', output

    reclassArray = createReclassifyList() 

    outReclass = Reclassify(raster, "Value", RemapRange(reclassArray), "NODATA")
    
    outReclass.save(output)

    gen.buildPyramids(output)


# #####  NOTE!!  ACTUALLY CREATE THE MASK FIRST ANFD THEN CREATE THE MMU DATASET

def createMask():
    print "-----------------createMask() function-------------------------------"
    path_mtr = Raster(defineGDBpath(['s14', 'core','core'])+post.mtr_dataset)
    print 'path_mtr', path_mtr
    path_yxc = Raster(defineGDBpath(['s14', 'post', post.name])+post.yxc_dataset)
    print 'path_yxc', path_yxc

    # outCon = Con((mtr == 3) & (ytc < 2008), 3, Con((mtr == 3) & (ytc >= 2008), ytc))
    outCon = Con((path_mtr == post.mtr) & (path_yxc >= 2008), path_yxc)
    output = defineGDBpath(['s14', 'post', post.name])+post.yxc_mask_dataset
    outCon.save(output)
    gen.buildPyramids(output)



def clipByMMU():
    print "-----------------clipByMMU() function-------------------------------"
    path_mtr = Raster(defineGDBpath(['s14','core','core'])+post.mtr_dataset)
    path_yxc_msk = Raster(defineGDBpath(['s14','post',post.name])+post.yxc_mask_dataset)

    outCon = Con((path_mtr == post.mtr) & (IsNull(path_yxc_msk)), post.mtr, Con((path_mtr == post.mtr) & (path_yxc_msk >= 2008), path_yxc_msk))
    output = defineGDBpath(['s14','post',post.name])+post.yxc_mmu_dataset
    outCon.save(output)
    gen.buildPyramids(output)





def attachCDL(gdb_argss_in):
    # DESCRIPTION:attach the appropriate cdl value to each year binary dataset
    arcpy.env.workspace=defineGDBpath(gdb_argss_in)
    
    # arcpy.env.rasterStatistics = 'STATISTICS'
    # # Set the cell size environment using a raster dataset.
    # arcpy.env.cellSize = "ytc_years_traj_cdl_b_n8h_mtr_8w_msk23_nbl"

    # # Set Snap Raster environment
    # arcpy.env.snapRaster = "ytc_years_traj_cdl_b_n8h_mtr_8w_msk23_nbl"

    # # #copy raster
    # arcpy.CopyRaster_management("ytc_years_traj_cdl_b_n8h_mtr_8w_msk23_nbl", "ytc_years_traj_cdl_b_n8h_mtr_8w_msk23_nbl_"+post.subname)
    
    wc = '*'+post.subname
    print wc

    for raster in arcpy.ListDatasets(wc, "Raster"): 
      
        for year in  post.conversionyears:
            print 'raster: ', raster
            print 'year: ', year

            # allow raster to be overwritten
            arcpy.env.overwriteOutput = True
            print "overwrite on? ", arcpy.env.overwriteOutput
        
            #establish the condition
            cond = "Value = " + str(year)
            print 'cond: ', cond

            cdl_file= post.getAssociatedCDL(year)
            print 'associated cdl file: ', cdl_file
            
            # # set everthing not equal to the unique trajectory value to null label this abitray value equal to conversion year
            OutRas = Con(raster, cdl_file, raster, cond)
       
            OutRas.save(raster)



def addGDBTable2postgres():
    print 'running addGDBTable2postgres() function....'
    ####description: adds tables in geodatabse to postgres
    # set the engine.....
    engine = create_engine('postgresql://mbougie:Mend0ta!@144.92.235.105:5432/usxp')

    arcpy.env.workspace = defineGDBpath(['s14','post','ytc'])
    
    # wc = '*'+core.res+'*'+core.datarange+'*'+core.filter+'*_msk5_nbl'
    wc = 's14_ytc30_2008to2016_mmu5_nbl'
    print wc


    for raster in arcpy.ListDatasets(wc, "Raster"): 

    # for table in arcpy.ListTables(wc): 
        print 'raster: ', raster
        
        # Execute AddField twice for two new fields
        fields = [f.name for f in arcpy.ListFields(raster)]
        print fields

        # converts a table to NumPy structured array.
        arr = arcpy.da.TableToNumPyArray(raster,fields)
        print arr

        # convert numpy array to pandas dataframe
        df = pd.DataFrame(data=arr)

        print df

        df.columns = map(str.lower, df.columns)

        # use pandas method to import table into psotgres
        df.to_sql(raster, engine, schema='counts')

        #add trajectory field to table
        addAcresField(raster, 'counts')





def addAcresField(tablename, schema):
    #this is a sub function for addGDBTable2postgres()
    
    cur = conn.cursor()
    
    #DDL: add column to hold arrays
    cur.execute('ALTER TABLE ' + schema + '.' + tablename + ' ADD COLUMN acres bigint;');
    
    #DML: insert values into new array column
    cur.execute('UPDATE '+ schema + '.' + tablename + ' SET acres = count * ' + gen.getPixelConversion2Acres(post.res));
    
    conn.commit()
    print "Records created successfully";
    conn.close()



def createSpecificLUCMask():
    # Description: reclass cdl rasters based on the specific arc_reclassify_table 

        #     self.series = series
        # self.name = name
        # self.subname = subname
        # self.res = str(res)
        # self.mmu = str(mmu)
        # self.years = years

    # Set environment settings
    arcpy.env.workspace = defineGDBpath(['post', post.name])
    
    cond =  post.series+'_'+post.name+post.res+'_'+post.datarange+'_mmu'+post.mmu+'_nbl_'+post.subname
    print 'cond:', cond
    # print cond
    # #loop through each of the cdl rasters
    for raster in arcpy.ListDatasets(cond, "Raster"): 
        
        print 'raster: ',raster

        outraster = raster+'_msk'
        print 'outraster: ', outraster
       
        myRemapVal = RemapValue(getReclassifyValuesString())

        outReclassRV = Reclassify(raster, "VALUE", myRemapVal, "")

        # Save the output 
        outReclassRV.save(outraster)

        #create pyraminds
        gen.buildPyramids(outraster)



def getReclassifyValuesString():
    #Note: this is a aux function that the reclassifyRaster() function references
     
    cur = conn.cursor() 
    
    # NOTE BFC AND FNC ARE GETTING RID OF 1's!!!!
    def getbValue():
        if post.subname == 'bfc' or post.subname == 'fnc':
            return "'1'"
        else:
            return "'0'"

    query = "SELECT value::text,b FROM misc.lookup_cdl WHERE b = "+getbValue()+" ORDER BY value"
    print 'query----', query
    #DDL: add column to hold arrays
    cur.execute(query);
    
    #create empty list
    reclassifylist=[]

    # fetch all rows from table
    rows = cur.fetchall()
    
    # interate through rows tuple to format the values into an array that is is then appended to the reclassifylist
    for row in rows:
        ww = [int(row[0]),'NODATA']
        reclassifylist.append(ww)
    
    print reclassifylist
    return reclassifylist



def run(data): 
    print data
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data['paths_global'])

    
    # post = data['paths_global']
    # print 'post', post
    # data['paths_global']
    # print post['createYearbinaries']
    # # print post[]
    # createYearbinaries(data)
    # # createMask()
    # # clipByMMU()






