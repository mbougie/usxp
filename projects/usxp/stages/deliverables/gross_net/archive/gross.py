import arcpy
from arcpy import env
from arcpy.sa import *
import multiprocessing
from sqlalchemy import create_engine
import pandas as pd
import psycopg2
import os
import glob
import sys
import time
import logging
from multiprocessing import Process, Queue, Pool, cpu_count, current_process, Manager
sys.path.append('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\modules\\')
import general as gen
import json
# import general_deliverables as gen_dev

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")






def processingCluster(instance, inraster, outraster, reclasslist):
    outReclass = Reclassify(inraster, "Value", RemapValue(reclasslist), "NODATA")
    print 'finished outReclass..............'
  
    for key, value in instance['scale'].iteritems():

        nbr = NbrRectangle(value, value, "CELL")
        outBlockStat = BlockStatistics(outReclass, nbr, "SUM", "DATA")
        print 'finished block stats.............'
        outBlockStat.save(outraster)

        ## add percent column  ###
        addField(outraster, value)


        gen.buildPyramids_new(outraster, 'NEAREST')





def addField(raster, value):
    normalizer = value*value
    ##AddField_management (in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
    arcpy.AddField_management(in_table=raster, field_name='percent', field_type='FLOAT')

    cur = arcpy.UpdateCursor(raster)

    for row in cur:
        row.setValue('percent', ((float(row.getValue('Value'))/normalizer)*100))
        cur.updateRow(row)







def run(instance):
    inraster = Raster('D:\\projects\\usxp\\deliverables\\{0}\\{0}.gdb\\{0}_mtr'.format(instance['series']))
    print inraster


    for mtr, reclasslist in instance['yxc'].iteritems():
        pass
        for scale in instance['scale'].keys():
            outraster = 'D:\\projects\\usxp\\deliverables\\{0}\\maps\\gross\\gross.gdb\\{0}_{1}_{2}'.format(instance['series'], scale, mtr)
            print outraster

            processingCluster(instance, inraster, outraster, reclasslist)





#####  call main function  ###########################################################################
instance = { 'scale':{'3km':100}, 'series':'s27', 'yxc':{'mtr3':[[3,1]], 'mtr4':[[4,1]]} }
run(instance)











