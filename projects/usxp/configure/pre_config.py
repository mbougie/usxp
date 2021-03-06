from sqlalchemy import create_engine
import numpy as np, sys, os
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


'''######## DEFINE THESE EACH TIME ##########'''
#Note: need to change this each time on different machine
case=['Bougie','Gibbs']

try:
    conn = psycopg2.connect("dbname='usxp' user='mbougie' host='144.92.235.105' password='Mend0ta!'")
except:
    print "I am unable to connect to the database"


# def getInfo(directory):
#     return directory


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
            # print dirnames
            gdbmatches = os.path.join(root, dirnames)
    # print gdbmatches
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
    



def getTemplatefile(directory):
    with open('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\config\\template.json'.format(directory)) as json_data:
        template = json.load(json_data)
        return template


def getKernelfile(args_list):
    directory = args_list[0]

    if directory == 'series':
        filename = args_list[1]

        with open('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\config\\{}\\{}.json'.format(directory, filename)) as json_data:
            template = json.load(json_data)
            return template, directory, filename
    
    elif directory == 'routes':
        route = args_list[1]
        filename = args_list[2]

        with open('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\config\\{}\\{}\\{}.json'.format(directory, route, filename)) as json_data:
            template = json.load(json_data)
            return template, directory, filename      





def getArbitraryCropValue(table, years, croptype):
    #def this is a sub function for createMask_nlcdtraj()
    #this is to return the arbitrary value assocaited with full crop over entire years span
    cropdict = {'crop':'1', 'noncrop':'0'}

    lc_series = cropdict[croptype] * len(years)
    print croptype, lc_series
    columnList = ','.join(str(e) for e in lc_series)
    print 'columnlist', columnList

    cur = conn.cursor()
   
    cur.execute("SELECT \"Value\" FROM pre."+table+" Where traj_array = '{" + columnList + "}' ")

    # fetch all rows from table
    rows = cur.fetchall()
    print 'arbitrary value', rows[0][0]
    return rows[0][0]




class ProcessingObject(object):

    def __init__(self, args):
        kernel = args[0]
        print 'kernel', kernel
        directory = args[1]
        instance = args[2]
        print instance

        ##get the template json
        self.data = getTemplatefile(directory)
        print self.data

        #call the methods in order to modifiy the tempalte json
        self.updateKernel = self.updateKernel(kernel, instance)
        self.updatePreObject = self.updatePreObject(kernel)
        self.updateRefineObject = self.updateRefineObject(kernel)
        self.updateCoreObject = self.updateCoreObject(kernel)
        self.updatePostObject = self.updatePostObject(kernel)
        
        #export modified object to json file
        self.exportObject = self.exportObject(directory)
    


    def updateKernel(self, kernel, instance):
        #add kenel object to json 
        self.data['global']=kernel['global']

        self.data['global']['instance'] = kernel['global']['instance']
        self.data['global']['years'] = range(kernel['global']['years'][0], kernel['global']['years'][1]+1)
        self.data['global']['years_conv'] = range(kernel['global']['conv_years'][0], kernel['global']['conv_years'][1]+1)
        self.data['global']['datarange'] = '{}to{}'.format(str(self.data['global']['years'][0]), str(self.data['global']['years'][-1]))


 



    def updatePreObject(self, kernel):
        print '###############    updatePreObject()   #############################'

        ###update traj
        self.data['pre']['traj']['version'] = kernel['pre']['version']['traj']
        self.data['pre']['traj']['gdb'] = getGDBpath('{}_traj'.format(self.data['pre']['traj']['version']))
        self.data['pre']['traj']['filename'] = '_'.join([self.data['pre']['traj']['version'], 'traj', 'cdl'+self.data['global']['res'], 'b', self.data['global']['datarange']])
        self.data['pre']['traj']['lookup'] = 'lookup_{}'.format(self.data['global']['datarange'])
        self.data['pre']['traj']['lookup_version'] = kernel['pre']['version']['lookup_version']
        self.data['pre']['traj']['path']  = '\\'.join([self.data['pre']['traj']['gdb'], self.data['pre']['traj']['filename']]) 

        ### update traj rfnd
        self.data['pre']['traj_rfnd']['version'] = kernel['pre']['version']['traj_rfnd']
        self.data['pre']['traj_rfnd']['gdb'] = getGDBpath('{}_traj_rfnd'.format(self.data['pre']['traj_rfnd']['version']))
        self.data['pre']['traj_rfnd']['filename'] = '_'.join([self.data['pre']['traj']['filename'],'rfnd', self.data['pre']['traj_rfnd']['version']])
        self.data['pre']['traj_rfnd']['path']  = '\\'.join([self.data['pre']['traj_rfnd']['gdb'], self.data['pre']['traj_rfnd']['filename']])  





    def updateRefineObject(self, kernel):
        print '###############    updateRefineObject()   #############################'
        self.data['refine']['version'] = kernel['refine']['version']
        self.data['refine']['gdb'] = getGDBpath('{}_masks'.format(self.data['refine']['version']))
        
        self.data['refine']['mask_nlcd']['years_nlcd'] = kernel['refine']['years_nlcd']
        self.data['refine']['mask_nlcd']['operator'] = kernel['refine']['operator']
        self.data['refine']['mask_nlcd']['arbitrary'] = getArbitraryCropValue(self.data['pre']['traj']['filename'], self.data['global']['years'], 'crop')
        self.data['refine']['mask_nlcd']['filename'] = '{}_mask_nlcd_{}_{}'.format(self.data['refine']['version'], 'and'.join(str(e) for e in self.data['refine']['mask_nlcd']['years_nlcd']), self.data['global']['datarange'])
        self.data['refine']['mask_nlcd']['path'] = '\\'.join([self.data['refine']['gdb'], self.data['refine']['mask_nlcd']['filename']])
        
        
        
        
        
        self.data['refine']['mask_dev_alfalfa_fallow']['filename'] = '{}_mask_dev_alfalfa_fallow_{}'.format(self.data['refine']['version'], self.data['global']['datarange'])
        self.data['refine']['mask_dev_alfalfa_fallow']['path'] = '\\'.join([self.data['refine']['gdb'], self.data['refine']['mask_dev_alfalfa_fallow']['filename']])
        self.data['refine']['mask_dev_alfalfa_fallow']['arbitrary'] = getArbitraryCropValue(self.data['pre']['traj']['filename'], self.data['global']['years'], 'noncrop')
        


 
    #####   core functions  ################################################################################
    def updateCoreObject(self, kernel):
        print '###############    updateCoreObject()   #############################'
        
        self.data['core']['gdb'] = getGDBpath('core_{}'.format(self.data['global']['instance']))
        print "self.data['core']['gdb']-----------------------", self.data['core']['gdb']
        self.data['core']['filter'] = kernel['core']['filter']
        self.data['core']['route'] = kernel['core']['route']
        self.data['core']['rg'] = kernel['core']['rg']
        self.data['core']['mmu'] = kernel['core']['mmu']

        if self.data['core']['route'] == 'r2':
            self.data['core']['filename'] = '{}_{}_{}_mtr_mmu{}'.format(self.data['global']['instance'], self.data['pre']['traj_rfnd']['filename'], self.data['core']['filter'], self.data['core']['mmu'])
            self.data['core']['path'] = '\\'.join([self.data['core']['gdb'], self.data['core']['filename']])
            print "self.data['core']['path']----------------------", self.data['core']['path']

        elif self.data['core']['route'] == 'r3':
            self.data['core']['filename'] = '{}_{}_{}_mmu{}_mtr'.format(self.data['global']['instance'], self.data['pre']['traj_rfnd']['filename'], self.data['core']['filter'], self.data['core']['mmu'])
            self.data['core']['path'] = '\\'.join([self.data['core']['gdb'], self.data['core']['filename']])
            print "self.data['core']['path']----------------------", self.data['core']['path']




    #####   post functions  ################################################################################
    

    def updatePostObject(self, kernel):
        print '###############    updatePostObject()   #############################'
        def getvalues():
            ytc_dict = {}

            ytc_dict['gdb'] = getGDBpath('ytc_{}'.format(self.data['global']['instance']))
            ytc_dict['filename'] = '{}_ytc{}_{}_mmu{}'.format(self.data['global']['instance'], self.data['global']['res'], self.data['global']['datarange'], str(self.data['core']['mmu']))
            ytc_dict['path']  = '\\'.join([ytc_dict['gdb'], ytc_dict['filename']]) 
            ytc_dict['fc'] = self.createCDLdict('fc', self.data['global']['years_conv'])
            ytc_dict['bfc'] = self.createCDLdict('bfc', self.data['global']['years_conv'])
            return ytc_dict


        self.data['post']['ytc'] = getvalues()

    def createCDLdict(self, subtype, years):

        def getCDLpathsDict(years):
            #this is an aux function for attachCDL() function to get correct cdl for the attachCDL() function
            dict = {}
            for year in years:
                if subtype == 'fc' or subtype == 'fnc':
                    cdl_file = '{}{}cdl30_{}'.format(getGDBpath('cdl'), '\\', str(year))
                    dict[str(year)]=cdl_file
                elif subtype == 'bfc' or subtype == 'bfnc':
                    cdl_file = '{}{}cdl30_{}'.format(getGDBpath('cdl'), '\\', str(year-1))
                    dict[str(year)]=cdl_file
            return dict

        definedfilename = '{}_ytc{}_{}_mmu{}_{}'.format(self.data['global']['instance'], self.data['global']['res'], self.data['global']['datarange'], str(self.data['core']['mmu']), subtype)
        definedpath = '{}\\{}'.format(getGDBpath('ytc'), definedfilename)
        dictpath={"cdlpaths":getCDLpathsDict(years),"filename":definedfilename, "path":definedpath}
        print dictpath
        return dictpath




    ####  attach cdl ########################################################################################





     #####   export objects  ################################################################################
    def exportObject(self, directory):
        with open('C:\\Users\\Bougie\\Desktop\\Gibbs\\scripts\\config\\current_instance.json'.format(directory), 'w') as outfile:
            json.dump(self.data, outfile, indent=4)




###########  create instance of class ################################################
def run(arg_list):
    ProcessingObject(getKernelfile(arg_list))
    # ProcessingObject(getKernelfile(['series','s14']))

# ['routes','r2','r2_4']
if __name__ == '__main__':
    run(arg_list)

