from sqlalchemy import create_engine
import numpy as np, sys, os, errno
sys.path.append('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\usxp\\misc')
import general as gen 
import pandas as pd
import collections
from collections import namedtuple
# import openpyxl
import arcpy
from arcpy import env
from arcpy.sa import *
import glob
import fnmatch
import psycopg2

import pprint
import json
import shutil
import stat

'''######## DEFINE THESE EACH TIME ##########'''
#Note: need to change this each time on different machine
case=['Bougie','Gibbs']

try:
    conn = psycopg2.connect("dbname='usxp' user='mbougie' host='144.92.235.105' password='Mend0ta!'")
except:
    print "I am unable to connect to the database"



###################  create classes ######################################################



def getSeriesParams(series):
    engine = create_engine('postgresql://mbougie:Mend0ta!@144.92.235.105:5432/usxp')
    query = """SELECT * FROM series.series FULL JOIN series.core USING(series) LEFT OUTER JOIN series.routes USING(route) FULL JOIN series.post USING(series) WHERE series = '{}'""".format(series)
    print 'query:-getSeries-', query
    df = pd.read_sql_query(query, con=engine)
    # print df
    for index, row in df.iterrows():
        print row
        return row


def getObjectValues(row):
    engine = create_engine('postgresql://mbougie:Mend0ta!@144.92.235.105:5432/usxp')
    query = "SELECT * FROM series.objects where object = '{}'".format(row)
    print 'query:-getPaths-', query
    df = pd.read_sql_query(query, con=engine)
    # print df
    # return df
    for index, row in df.iterrows():
        # print row
        return row



def getGDBpath(wc):
    for root, dirnames, filenames in os.walk("C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\"):
        for dirnames in fnmatch.filter(dirnames, '*{}*.gdb'.format(wc)):
            print dirnames
            gdbmatches = os.path.join(root, dirnames)
    print gdbmatches
    # return json.dumps(gdbmatches)
    return gdbmatches


def insertGDBpaths(subpath, gdb):
    #get gdb list
    gdblist = getGDBpath(subpath)
    gdbstring = ','.join(gdblist)
    print 'sdsd', gdbstring

    #insert list into table
    query = "UPDATE series.objects SET gdb_path='{}' WHERE gdb='{}'".format(gdbstring, gdb);
    print query
    
    gen.commitQuery(query)
    




# def getJSONfile():
#     with open('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\config\\test\\series_test4.json') as json_data:
#         template = json.load(json_data)
#         # print(template)
#         # print type(template)
#         return template



# data = getJSONfile()
# # print data


# print data['global']['series']

def moveDir():
    shutil.move('C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\series', 'D:\\projects\\usxp\\series')

def renameDir():
    os.rename('D:\\projects\\usxp\\series', data['global']['series'])

def createDirectory(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise



# instance_directory = 'E:\\projects\\usxp\\sa\\{}\\{}'.format('r2','r2_4')
# dict_dirs = {'instance':'r2_4', 'core':'core', 'post':'post'}
# # moveDir()
# createDirectory(directory)





def getJSONfile():
    with open('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\config\\routes\\r2\\r2_2.json') as json_data:
        template = json.load(json_data)
        # print(template)
        # print type(template)
        return template



data = getJSONfile()
print data







def mainCreate():
    # create the instance
    instance_directory = 'C:\\Users\\Bougie\\Desktop\\Gibbs\\data\\usxp\\sa\\{}\\{}'.format(data['core']['route'],data['global']['instance'])
    createDirectory(instance_directory)
    
    
    for stage in ['core','post','sf', 'plots']:
        subdir = '{}\\{}'.format(instance_directory, stage)
        #create subdir
        createDirectory(subdir)
        
        if stage == 'core' or stage == 'post':
            #create geodatabse
            if stage == 'post':
                arcpy.CreateFileGDB_management(subdir, "{}_{}.gdb".format('ytc',data['global']['instance']))
            else:
                arcpy.CreateFileGDB_management(subdir, "{}_{}.gdb".format(stage,data['global']['instance']))







mainCreate()