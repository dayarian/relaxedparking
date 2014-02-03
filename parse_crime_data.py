import mysql.connector
import sys
from mysql.connector import errorcode
from math import cos,sin
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
from re import search


def input_data_from_csv(data_thf, data_lar, data_van, yr):
    a=pd.read_csv('datasets/sfpd_incident_all_csv/sfpd_incident_'+ yr +'.csv', encoding="utf-8")
    c=a.Descript.map(lambda x:  1 if ('VEHICLE' in x or 'LOCKED AUTO'in x) else 0)
    
    data_thf=a[(a.Category == 'VEHICLE THEFT') & (a.Descript != 'STOLEN AND RECOVERED VEHICLE')]
    data_lar=a[ (a.Category == 'LARCENY/THEFT') & ( c == 1 )]
    data_van=a[ (a.Category == 'VANDALISM') & ( c == 1 )]
    return data_thf, data_lar, data_van

def cleanup_crim_date(data):
    data=data[['Category','Date','Time','X','Y','Descript']]
    data['year']=data.Date.map(lambda x: x[-4:]); data['month']=data.Date.map(lambda x: x[:2])
    data=data.drop('Date', 1)
    return data

def dump_crime_to_sql(data, cnx, cursor):
    radius = 3959; pi_n=3.14159265358979323/180 
    for index, row in data.iterrows():
        data_crime_vals=()
        
        for col in headers_in_crime:
            data_crime_vals+=(row[col],) 
        data_crime_vals+=(int(index),)
           
        lon = float(row['X']); lat = float(row['Y'])
        
        x=radius*cos(lat * pi_n)*cos(lon * pi_n);
        y=radius*cos(lat * pi_n)*sin(lon * pi_n);
        z=radius*sin(lat * pi_n)
        
        data_crime_vals+=(str(x),str(y),str(z)) 
        
        cursor.execute(add_incident, data_crime_vals)
        
    cnx.commit()  
    return

##
# Connect to DB, return connection object
##
def db_connect(db_name=None):
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
##
# Create database
##
def create_database(cursor, db_name):
    cursor = cnx.cursor()
    try:
        cnx.database = db_name    
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            try:
                cursor.execute(
                    "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
                #cursor.execute(
                 #   "GRANT ALL ON {}.* TO 'adel'@'localhost'".format(db_name))
            except mysql.connector.Error as err:
                print("Failed creating database: {}".format(err))
                exit(1)
            cnx.database = db_name
        else:
            print(err)
            exit(1)
    return cursor
##
# Create tables
##
def create_tables(cursor, TABLES):
    for name, ddl in TABLES.iteritems():
        try:
            print("Creating table {}: ".format(name))
            cursor.execute(ddl)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err)
        else:
            print("OK")   
##
# Declare tables
##

crime_table='crime';
TABLES = {}
TABLES['crime'] = (
    "CREATE TABLE "+ crime_table +" ("    
    "  ID int NOT NULL AUTO_INCREMENT,"
    "  category varchar(50) NOT NULL,"
    "  time varchar(6) NOT NULL,"
    "  lon FLOAT(12,8) NOT NULL,"
    "  lat FLOAT(12,8) NOT NULL,"  
    "  year int(4) NOT NULL,"
    "  month int(4) NOT NULL,"
    "  description varchar(50) NOT NULL,"    
    "  inc_index int(4) NOT NULL,"
    "  `x_c` DECIMAL(20,12) NOT NULL,"
    "  `y_c` DECIMAL(20,12) NOT NULL,"  
    "  `z_c` DECIMAL(20,12) NOT NULL," 
    "  PRIMARY KEY (ID) "
    ") ENGINE=InnoDB")

all_headers_in_crime= 'category, time, lon, lat, year, month, description, inc_index, x_c, y_c, z_c' 

headers_in_crime=['Category','Time','X','Y','year','month','Descript']

##
# Populate crime table
##
add_incident = ("INSERT INTO "+ crime_table +" (" + all_headers_in_crime +") "
               " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")


if __name__ == '__main__':  

    # connect to sql and create the database/table

    cnx = db_connect()
    dbase_name_street_sweep = 'sf_street_sweep' 
    cursor = create_database(cnx, dbase_name_street_sweep)
    create_tables(cursor, TABLES); cursor.execute('DROP TABLE '+ crime_table);
    create_tables(cursor, TABLES)

    
    for yr in ['2011','2012','2013']:
        # we will dump the crime data in variables data_thf, data_lar, data_van
        data_thf=[]; data_lar=[]; data_van=[]
        data_thf, data_lar, data_van = input_data_from_csv(data_thf, data_lar, data_van, yr)
        data_thf=cleanup_crim_date(data_thf); data_lar=cleanup_crim_date(data_lar); data_van=cleanup_crim_date(data_van)
        
        dump_crime_to_sql(data_thf, cnx, cursor); dump_crime_to_sql(data_lar, cnx, cursor); dump_crime_to_sql(data_van, cnx, cursor); 

    cnx.close()


    
