# -*- coding: utf-8 -*-
"""
Created on Thu Mar 02 17:54:49 2017

@author: jrbrad
"""

import math
import MySQLdb as mySQL
from ftplib import FTP

R = 6371.0 * 0.621371

""" global MySQL settings """
mysql_user_name = 'my_username'
mysql_password = 'my_sql_password'
mysql_ip = '127.0.0.1'
mysql_db = 'tsp'

def tsp_value(dist,tsp):
    value = 0
    for i in range(1,len(tsp)):
        if tsp[i] < tsp[i-1]:
            value += dist[(tsp[i],tsp[i-1])]
        else:
            value += dist[(tsp[i-1],tsp[i])]
        
    if tsp[len(tsp)-1] < tsp[0]:
        value += dist[(tsp[len(tsp)-1],tsp[0])]
    else:
        value += dist[(tsp[0],tsp[len(tsp)-1])]
    return value

def tsp_feasible(locs,tsp):
    # tsp is a list of integer elements each corresponding with  a lcoation key/index
    error = False
    
    if not len(tsp) == len(locs):
        error = True
    for loc in locs:
        if not len([x for x in tsp if x==loc]) == 1:
            error = True
    return error
        
def getDBDataList(commandString):
    cnx = db_connect()
    cursor = cnx.cursor()
    cursor.execute(commandString)
    items = []
    x = cursor.fetchall()
    for item in x:
        new_row = []
        for i in range(len(item)):
            new_row.append(item[i])
        items.append(new_row)
    cursor.close()
    cnx.close()
    return items
    
def getDBDataList1(commandString):
    cnx = db_connect()
    cursor = cnx.cursor()
    cursor.execute(commandString)
    items = []
    x = cursor.fetchall()
    for item in x:
        items.append(item[0])
    cursor.close()
    cnx.close()
    return items

def db_connect():
    cnx = mySQL.connect(user=mysql_user_name, passwd=mysql_password,
                        host=mysql_ip, db=mysql_db)                        
    return cnx
        
def hav_dist(lat1, lon1, lat2, lon2):
    """ latitude and longitude inputs are in degrees """
    
    """ convert latitude and longitude to radians """
    lat1 = lat1 * math.pi /180.0
    lon1 = lon1 * math.pi /180.0
    lat2 = lat2 * math.pi /180.0
    lon2 = lon2 * math.pi /180.0
    
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1) * math.cos(lat2) * (math.sin((lon2-lon1)/2))**2
    return R * 2 * math.atan2(math.sqrt(a),math.sqrt(1-a))
    
def db_insert_results(problem_id,participant,result,valid):
    cnx = db_connect()                       
    cursor = cnx.cursor()
    cursor.execute("CALL spInsertResults(%s, %s, %s, %s);" , (problem_id,participant,result,valid))
    cursor.close()
    cnx.commit()
    cnx.close
    
def tsp_algo(locs,dist):
    name_or_team = 'Section X, Team Y'
    
    """    
    Write your program here to determine your TSP solution, which you place in the list variable tsp
    """
    
    return name_or_team, tsp
    
problems = getDBDataList1('CALL spGetProblemIds();')
silent_mode = False    # use this variable to turn on/off appropriate messaging depending on student or instructor use
filename_post = 'leaderboard.html'
update = False
""" Error Messages """
error_locid = """ 
An element in the tsp solution list from tsp_algo() was received which was an integer, although it did not correspond with a valid location id.
"""
error_not_int = """ 
An element in the tsp solution list from tsp_algo() was received which was not an integer.   
"""
error_response_not_list = """
tsp_algo() returned a response whose outer data type was not a list.  Scoring will be terminated   """

for problem_id in problems:
    locs = getDBDataList('CALL spGetProbData(%s);' % (str(problem_id)))
    loc_ids = [x[0] for x in locs]
    
    """ Compute Haversine distances between all location pairs """
    dist = {}
    for loc1 in range(len(locs)):
        for loc2 in range(len(locs)):
            dist[(locs[loc1][0],locs[loc2][0])] = hav_dist(locs[loc1][2],locs[loc1][3],locs[loc2][2],locs[loc2][3])
            
    errors = False
    # The tsp solution is expected in the form of a list in the order of visitation
    name_or_team, tsp = tsp_algo(locs,dist)
    
    if isinstance(tsp,list):
        for loc in tsp:
            if not (isinstance(loc,long) or isinstance(loc,int)):
                errors = True
                if silent_mode:
                    status = "bad_elements_in_list"
                else:
                    print error_not_int
                break
            else:
                if not loc in loc_ids:
                    errors = True
                    if silent_mode:
                        status = "bad_loc_id_"
                    else:
                        print error_locid
                    break
    else:
        if silent_mode:
            status = "P"+str(problem_id)+"_not_list_"
        else:
            print error_response_not_list    
    
    if errors == False:
        tsp_ok = tsp_feasible(locs,tsp)
        if tsp_ok:
            tsp_obj = tsp_value(dist,tsp)
        else:
            tsp_obj = 99999999999999999
        
        if tsp_ok:
            if silent_mode:
                status = "P"+str(problem_id)+"tsp_valid_"
            else:
                print "TSP Problem ", str(problem_id)," solution valid, distance =", tsp_obj
        else:
            if silent_mode:
                status = "P"+str(problem_id)+"tsp_invalid_"
            else:
                print "TSP Problem ", str(problem_id)," solution invalid ...."
        
        
        if tsp_ok:
            db_insert_results(problem_id,str(name_or_team),tsp_obj,str(1))
            update = True
        else:
            db_insert_results(problem_id,str(name_or_team),tsp_obj,str(0))
            
    print
    print "========================================"
    print "TSP Problem", str(problem_id)
    print name_or_team+': Route = '+ str(tsp)+';  Length = ',str(tsp_value(dist,tsp))+' miles'
    print "TSP feasible?", tsp_feasible(locs,tsp)
    print