import mysql.connector
import sys
from mysql.connector import errorcode
from math import cos,sin
import time

class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


def input_sweeping_sched_from_csv(in_f,data_container):
    # this inputs the street cleaning data in in_f into data_container        
	##
	# reading the street cleaning schedule, downloaded from the sf database 
	##
	# description of the columns
	# line[0] : week_3
	# line[1] : weekday, 
	# line[2] : week_2
	# line[3] : end of R side
	# line[4] : cnn variable, unique section identifier
	# line[5] : street name
	# line[7] : start of L side
	# line[10] : end of L side
	# line[11] : week_1
	# line[12] : start of R side
	# line[13] : R or L flag
	# line[14] : from hour
	# line[17] : block sweep 
	# line[18] : to hour
	# line[19] : week_5
	# line[21] : week_4
	# line[22] : lat
	# line[23] : lon

    verbose=0
    weekdays=['Mon','Tues','Wed','Thu','Fri','Sat','Sun','Holiday']
    
    File=open(in_f, mode='r'); line = File.readline(); line = File.readline();    
    while line:	
        line=line.replace("Octavia St, Frontage", "Octavia St") # specific to this particular file
        line=line.rstrip(); line=line.split(',')    
        if len(line) != 24 : print "wrong length ", line; break;
            
        startn_R = line[12] # start street address number for the R side 
        endn_R = line[3]; startn_L = line[7]; endn_L = line[10]
        
        if startn_R == '0' and endn_R == '0' and startn_L == '0' and endn_L == '0':
            #print "skipping the line ", line; 
            line = File.readline();  continue
        
        if line[4] not in data_container:
            data_container[line[4]]['street'] = line[5].lower() 
            data_container[line[4]]['startn_L'] = startn_L
            data_container[line[4]]['endn_L'] = endn_L 
            data_container[line[4]]['startn_R'] = startn_R  
            data_container[line[4]]['endn_R'] = endn_R
            
            data_container[line[4]]['lat'] = line[22] 
            data_container[line[4]]['lon'] = line[23] 
            
            # check which weeks in the month that day is schedules, e.g. YYYYY means all weeks
            week_flags=line[11]+line[2]+line[0]+line[21]+line[19]
            
            # hierarchy of indicies in data_container identifier - day (line[1]) - R/L (line[13]) : data_container[cnn_id][day][R/L]['end_hrs'] 
            
            data_container[line[4]][line[1]][line[13]]['week_flags'] = week_flags           
            data_container[line[4]][line[1]][line[13]]['start_hrs'] = line[14]                      
            data_container[line[4]][line[1]][line[13]]['end_hrs'] = line[18]     
            
        else:
            # resolve duplicate records
            if line[13] in data_container[line[4]][line[1]]: 
                week_flags=line[11]+line[2]+line[0]+line[21]+line[19]
                
                if  data_container[line[4]][line[1]][line[13]]['start_hrs'] != line[14] or \
                    data_container[line[4]][line[1]][line[13]]['end_hrs'] != line[18]:            
                    if data_container[line[4]][line[1]][line[13]]['week_flags'] == week_flags:
                        line = File.readline(); continue 
                    elif verbose == 1:    
                        print 
                        print "already have the record with conflicting time", \
                         data_container[line[4]]['street_add'] , line[5].lower()
                        
                        print data_container[line[4]][line[1]][line[13]]['week_flags'] ,  week_flags , " ", \
                        data_container[line[4]][line[1]][line[13]]['start_hrs'] , line[14] , " ", \
                         data_container[line[4]][line[1]][line[13]]['end_hrs'] , line[18]
                    
                    #print data_container[line[4]][line[1]][line[13]]
                else:                    
                    if data_container[line[4]][line[1]][line[13]]['week_flags'] != week_flags:
                        newflag=''
                        for i in range(len(week_flags)):
                            if week_flags[i] == 'Y' or data_container[line[4]][line[1]][line[13]]['week_flags'][i] == 'Y':
                                newflag+='Y'
                            else:
                                newflag='N'                                
                        #print "corrected duplicate", data_container[line[4]][line[1]][line[13]]['week_flags'] , week_flags,                        
                        data_container[line[4]][line[1]][line[13]]['week_flags'] = newflag                    
                        #print data_container[line[4]][line[1]][line[13]]['week_flags']

            if line[1] not in weekdays: 
                print 
                print line[1], " not in weekdays ", line; 
                print             
            
            # check which weeks in the month that days is scheduled 
            week_flags=line[11]+line[2]+line[0]+line[21]+line[19]
            
            # hierarchy of indicies in data_container identifier - day (line[1]) - R/L (line[13])
            
            data_container[line[4]][line[1]][line[13]]['week_flags'] = week_flags           
            data_container[line[4]][line[1]][line[13]]['start_hrs'] = line[14]                      
            data_container[line[4]][line[1]][line[13]]['end_hrs'] = line[18]   
            
            #print line[4], data_container[line[4]]['street_add'], line[1], "  ",\
             #start_num_on_L_side, end_num_on_L_side,  start_num_on_R_side , end_num_on_R_side
                
        line = File.readline();  
    File.close()
    return data_container    
	
	

def input_tow_sched_from_csv(in_f,data_container):
    ##
    # reading the tow away schedule, downloaded from the sf database 
    ##
    # this inputs the data in in_f into data_container
    verbose=0
    weekdays=['Mon','Tues','Wed','Thu','Fri','Sat','Sun','Holiday']
    
    File=open(in_f, mode='r'); line = File.readline(); line = File.readline();    
    while line:  
        line=line.replace("street, from Guerrer", "street from Guerrer") # specific to this particular file   
        line=line.replace("6 am,", "6 am") # specific to this particular file   
        line=line.replace("everyday,", "everyday") # specific to this particular file   
        line=line.replace("Mo,Tu,We,Th,Fr,Sa,Su,Ho", "Mon-Tues-Wed-Thu-Fri-Sat-Sun-Holiday") # specific to this particular file        
        line=line.replace("Mo,Tu,We,Th,Fr,Sa,Su", "Mon-Tues-Wed-Thu-Fri-Sat-Sun") # specific to this particular file                
        line=line.replace("Mo,Tu,We,Th,Fr,Sa", "Mon-Tues-Wed-Thu-Fri-Sat") # specific to this particular file                
        line=line.replace("Mo,Tu,We,Th,Fr", "Mon-Tues-Wed-Thu-Fri") # specific to this particular file                
        line=line.replace("Fr,Sa,Su", "Fri-Sat-Sun") # specific to this particular file                
        line=line.replace("Th,Fr,Sa", "Thu-Fri-Sat") # specific to this particular file                        
        line=line.replace("Fr,Sa", "Fri-Sat") # specific to this particular file                
        line=line.replace("Sa,Su", "Sat-Sun") # specific to this particular file                
        
        original=line
        
        line=line.rstrip(); line=line.split(',')    
        if len(line) != 25 : print "wrong length ", original; break;
            
        cnn_id = line[9]     
        
        if cnn_id in data_container:
            if line[12] == 'Left':
                side='L'
            elif line[12] == 'Right':
                side='R'                
            else:
                print "problematic side", line[12] ; break
            
            if side in data_container[cnn_id]:
                
                print "why side already in the towaway?"; break 
            else:
                                                    # days , start time, end time
                if len(line[1]) < 2: line[1] =  '000'  
                data_container[cnn_id]['tow'][side]=[[line[3],line[1][:-2],line[2][:-2]]]                
                
                if len(line[4]) > 2:
                    data_container[cnn_id]['tow'][side].append([line[6],line[4][:-2],line[5][:-2]])
                
        line = File.readline();  
    File.close()
    return data_container    

	
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
# startn_L and endn_L are the starting and the ending number on the corresponding street
# the format in the day columns: YYYY-L-starttime_endtime|YYYY-R-starttime_endtime	
##
TABLES = {}
TABLES['schedules_for_cleaning'] = (
    "CREATE TABLE cleaning_sch ("    
    "  `cnn_id` int(4) NOT NULL,"
    "  `street` varchar(50) NOT NULL,"
    "  `startn_L` int(4) NOT NULL,"
    "  `endn_L` int(4) NOT NULL,"
    "  `startn_R` int(4) NOT NULL,"
    "  `endn_R` int(4) NOT NULL,"    
    "  `lon` FLOAT(12,7) NOT NULL,"
    "  `lat` FLOAT(12,7) NOT NULL,"    
    "  `Mon` varchar(50),"
    "  `Tues` varchar(50)," 
    "  `Wed` varchar(50),"
    "  `Thu` varchar(50),"
    "  `Fri` varchar(50)," 
    "  `Sat` varchar(50),"  
    "  `Sun` varchar(50),"
    "  `Holiday` varchar(50)," 
    "  `Tow_L` varchar(250),"
    "  `Tow_R` varchar(250),"
    "  `x_c` DECIMAL(20,12) NOT NULL,"
    "  `y_c` DECIMAL(20,12) NOT NULL,"  
    "  `z_c` DECIMAL(20,12) NOT NULL, "
    "  PRIMARY KEY (`cnn_id`)"
    ") ENGINE=InnoDB")
          




#All_headers_in_sweep_db='street, startn_R, endn_L, startn_R, endn_R, lon, lat, Mon, Tues, Wed, Thu, Fri, Sat, Sun, Holiday'
Primary_headers_in_sweep_db='street, startn_L, endn_L, startn_R, endn_R, lon, lat, x_c, y_c, z_c'
weekdays=['Mon','Tues','Wed','Thu','Fri','Sat','Sun','Holiday']

##
# For populating the table
##
add_series_primaries = ("INSERT INTO cleaning_sch "
               " (" + 'cnn_id,' + Primary_headers_in_sweep_db +") "
               " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")

#add_series = ("INSERT INTO cleaning_sch "
#               " (" + All_headers_in_sweep_db +") "
#               " VALUES (%s, %s, %s, %s, %s) ")

add_series_days = ("UPDATE cleaning_sch SET {} = %s WHERE cnn_id = %s ")

add_series_tow = ("UPDATE cleaning_sch SET Tow_{} = %s WHERE cnn_id = %s ")

#cursor.execute(add_series, data_series)
#emp_no = cursor.lastrowid    


	
if __name__ == '__main__':	
    # we will dump the data in the variable data_container. the keys are going to be cnn variable
    # which uniqly identifies the considered street section
    #    subkeys are street_address, latitude and longitude and days of the week. 
    #        for each day the subkeys are R/L side. 
    #            for each R/L side, subkeys are start_hrs and end_hrs, and which 
    #            weeks in the month that schedule applies. 

    data_container=AutoVivification() 
    data_container= input_sweeping_sched_from_csv("datasets/street_sweep/sfsweeproutes.csv",data_container)

    # adding the towaway schedule
    data_container = input_tow_sched_from_csv("datasets/TowAway/TowAway.csv",data_container)

    # connect to sql and create the database
    cnx = db_connect()
    dbase_name_street_sweep = 'sf_street_sweep'
    cursor = create_database(cnx, dbase_name_street_sweep)
    cursor.execute('DROP DATABASE '+ dbase_name_street_sweep)


    cursor = create_database(cnx, dbase_name_street_sweep)

    create_tables(cursor, TABLES)
    
    radius = 3959; pi_n=3.14159265358979323/180

    for cnn in data_container:    
        data_series_primaries=(cnn,data_container[cnn]['street'],data_container[cnn]['startn_L'])
        data_series_primaries+=(data_container[cnn]['endn_L'],data_container[cnn]['startn_R'],data_container[cnn]['endn_R'])
        data_series_primaries+=(data_container[cnn]['lon'],data_container[cnn]['lat'])

        lat = float(data_container[cnn]['lat']); lon = float(data_container[cnn]['lon'])

        x=radius*cos(lat * pi_n)*cos(lon * pi_n);
        y=radius*cos(lat * pi_n)*sin(lon * pi_n);
        z=radius*sin(lat * pi_n)
        data_series_primaries+=(str(x),str(y),str(z))


        cursor.execute(add_series_primaries, data_series_primaries)

    cnx.commit()    

    for cnn_id in data_container:
        for day in weekdays:
        	if day in data_container[cnn_id]:   
        		a=''
        		for side in ['L','R']:
        			if side in data_container[cnn_id][day]:
        				a += data_container[cnn_id][day][side]['week_flags'] + "_" + side + "_" \
        				 + data_container[cnn_id][day][side]['start_hrs'] + "_" \
        				 + data_container[cnn_id][day][side]['end_hrs'] 
        			a+= "|"                 
        		data_series_days=(a[:-1] , cnn_id)
        		cursor.execute(add_series_days.format(day), data_series_days)

	cnx.commit()            

    for cnn_id in data_container:
        if 'tow' in data_container[cnn_id]:
            for side in ['L','R']:
                if side in data_container[cnn_id]['tow']:
                    a=''
                    for el in data_container[cnn_id]['tow'][side]:
                        a+= el[0]+"_"+el[1]+"_"+el[2]+"|"                
                    data_series_tow = (a[:-1] , cnn_id)                
                    cursor.execute(add_series_tow.format(side), data_series_tow)

    cnx.commit()      

    cursor.close()
    cnx.close()


""" 
use sf_street_sweep;
 
select distinct street from cleaning_sch where lon >-122.44291 and lon < -122.43591 and lat >37.77 and lat < 37.78;


select Mon,Tues,Wed,Thu,Fri,Sat,Sun,Holiday from cleaning_sch where cnn_id='9865000';


"""