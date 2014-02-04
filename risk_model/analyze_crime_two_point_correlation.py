import mysql.connector
import sys
from mysql.connector import errorcode
import MySQLdb
from math import cos,sin
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
from re import search
  
"""
    we will look at different radii from each crime points to see how many other 
    crime points have happened at various radii. Basically we are going to calculate
    the two point correlation function. If crime events were random, the two point correlation
    would look flat as a function of radius. If it is not flat, then it means that crime locations 
    are correlated.
"""  


def db_connect(db_name=None):
    ##
    # Connect to DB, return connection object
    ##
    try:
        cnx = mysql.connector.connect(user='adel')#(user='*********', password='*********')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
            print(err)
        return
    else:  
        if db_name is not None:
            try:
                cnx.database = db_name 
            except mysql.connector.Error as err:
                print(err)
                exit(1)
        return cnx


def set_up_variables():
    """
        Set up 
        1) radiuses_larceny: the radii (in feet) at which we are going to explore crime events.
        2) event_count_larceny: a variable that will hold the number of events at each radius.
        3) bin_edges: It is basically the same as radiuses_larceny but in miles instead of feet.
                      This variable is used later to plot the historagm.   
        4) threshold_outmost: the maximum distance around each crime location that we will explore.
    """

    feet_in_mile = 5280.; # number of feets in one mile

    radiuses_larceny = [0,200]+range(500,3400,400) 
    event_count_larceny=zeros(len(radiuses_larceny)); areas_larceny=[0.1]; 
    for i in range(1,len(radiuses_larceny)):
        areas_larceny.append(pi*(radiuses_larceny[i]**2-radiuses_larceny[i-1]**2))

    bin_edges=np.array(radiuses_larceny)/feet_in_mile; 

    threshold_outmost = radiuses_larceny[-1]/feet_in_mile;

    return radiuses_larceny, event_count_larceny, bin_edges, threshold_outmost



def count_events(radiuses_larceny, event_count_larceny):

    E_radius = 3959; # earth_radius in miles
    feet_in_mile = 5280.; # number of feets in one mile
    pi=3.14159265358979323; pi_n=3.14159265358979323/180;  

    # get all the crime locations
    dbase_name_street_sweep = 'sf_street_sweep';     
    cnx = db_connect(dbase_name_street_sweep); cursor = cnx.cursor()

    query = ("SELECT x_c, y_c, z_c, lon, lat, year FROM crime WHERE \
                    year < 2013 AND category = 'LARCENY/THEFT';")
    cursor.execute(query)

    # set up another connection to sql database
    db = MySQLdb.connect(user="root", host="localhost", port=3306, db= dbase_name_street_sweep) 

    # go through each crime locations
    for (x_o, y_o, z_o, lon, lat, year) in cursor: 
        cnt+=1         
        if cnt % 1 != 0: # only look at a sub sample
            continue   

        # query all other crimes in the vicinity of the original crime 
        query_parking= db.query("SELECT POW(POW((x_c-"+str(x_o)+"),2)+POW((y_c-"+str(y_o)+"),2)+POW((z_c-"+str(z_o)+"),2),.5) AS dis \
                          FROM crime WHERE year = 2013 AND \
                          category = 'LARCENY/THEFT' AND \
                          POW(POW((x_c-"+str(x_o)+"),2)+POW((y_c-"+str(y_o)+"),2)+POW((z_c-"+str(z_o)+"),2),.5) <= "\
                          + str(threshold_outmost) +";")
        query_parking = db.store_result().fetch_row(maxrows=0)
        
        # see how many other crimes have happened at various radii
        if len(query_parking) > 0:    
            hist, bin_edges = np.histogram([q[0] for q in query_parking if q[0] > 0], bin_edges)
            event_count_larceny[1:]+=hist


    return event_count_larceny







 



if __name__ == '__main__':  

    # set up some variables
    radiuses_larceny, event_count_larceny, bin_edges, threshold_outmost = set_up_variables()


    event_count_larceny = count_events(radiuses_larceny, event_count_larceny)



    
