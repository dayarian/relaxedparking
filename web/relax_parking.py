from flask import Flask, render_template, request, jsonify

import MySQLdb
import json 
from re import search
import datetime as dt 
import colorsys


class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


def pseudoopacity(risk):
    """
        Set the opacity of the marker for the riskiest places (red) to be low. 
        Similarly, set the opacity for the safe places (green) to be high.
        This value is used for the circle-markers on the google map
    """
    return .4 + .6 * ( 1- min(80,risk) / 80.) 

def pseudosize(risk):
    """
        Set the size of the marker for the riskiest places (red) to be smaller. 
        Similarly, set the size for the safe places (green) to be larger.
        This value is used for the circle-markers on the google map
    """
    return 8 + 8 * ( 1- min(80,risk) / 80.) 


def pseudocolor(risk):
    """
        Set the color of the markers for the riskiest places to be redish. 
        Similarly, set the color for the safe places to be greenish.
        This value is used for the circle-markers on the google map
    """
    h = ( 1- min(100,risk) / 100.) * 180
    r, g, b = colorsys.hsv_to_rgb(h/360., 1., 1.)

    return '#%02x%02x%02x' % (255*r,255*g,255*b)

 
app = Flask(__name__)
app.debug = True
#db = MySQLdb.connect(user="root", host="localhost", port=3306, db="sf_street_sweep") 

@app.route("/")
def hello():
    return render_template('index.html') 

@app.route("/slides")
def slides():
    return render_template('slides.html')     

@app.route("/contact")
def contact():
    return render_template('contact.html') 

@app.route('/getGoodblocks')
def getGoodblocks():
    """
        It receives the destination, time of arrival and duration of stay.
        It returns whether one can park ine ach of the neighboring blocks,
        and how risky/safe it is to park at each block
    """
    # input and parse variables
    db = MySQLdb.connect(user="root", host="localhost", port=3306, db="sf_street_sweep") 

    lat_des = request.args.get('lat', ''); lon_des = request.args.get('lon', '') 
    num_days = request.args.get('num_days', '');num_hours = request.args.get('num_hours', ''); 
    zone = request.args.get('zone', ''); current_time = request.args.get('current_time', '');  

    lat_des=float(lat_des.encode('ascii','ignore')); lon_des=float(lon_des.encode('ascii','ignore'))
    num_days = num_days.encode('ascii','ignore');num_hours = num_hours.encode('ascii','ignore'); 
    zone = zone.encode('ascii','ignore'); current_time=current_time.encode('ascii','ignore');
      
    # extract number of days
    m=search(r'(\d+) day(.*)',num_days);  
    if m:   
        num_days=int(m.group(1)); 
    else:  
        return json.dumps([])

    # extract number of hours
    m=search(r'(\d+)hr:(\d+)min',num_hours);  
    if m:   
        num_hrs=int(m.group(1)); 
        num_min=int(m.group(2)); 
    else:  
        return json.dumps([])

    # extract current_time        2014/1/22 10:47 
    m=search(r'(\d+)/(\d+)/(\d+) (\d+):(\d+)',current_time);  
    if m:   
        current_year=int(m.group(1)); 
        current_month=int(m.group(2)); 
        current_day=int(m.group(3)); 
        current_hr=int(m.group(4)); 
        current_min=int(m.group(5)); 
    else:  
        return json.dumps([])


    weekdays=['Mon','Tues','Wed','Thu','Fri','Sat','Sun']

    # (dt.date(2014, 1, 18)+dt.timedelta(days=1)).month
    # (dt.date(2014, 1, 18)+dt.timedelta(days=1)).day  # d=8;  1+(d-1)/7     
    # lat, lon, num_days, num_hrs, num_min, zone, current_year, current_month, current_day, current_hr, current_min

    # determine which day the arrival day is, and also the follwoing days in case someone is staying for more than one day
    day_1=weekdays[dt.date(current_year, current_month, current_day).weekday()]
    day_2=weekdays[(dt.date(current_year, current_month, current_day)+dt.timedelta(days=1)).weekday()]
    day_3=weekdays[(dt.date(current_year, current_month, current_day)+dt.timedelta(days=2)).weekday()]
    day_4=weekdays[(dt.date(current_year, current_month, current_day)+dt.timedelta(days=3)).weekday()]

    delta_lon=.006; delta_lat=.005;

    # get the information about all the blocks in the neighborhood of the destination
    query_results= db.query("SELECT street, startn_L, endn_L, startn_R, endn_R, lat, lon, \
       "+ day_1 + ","+ day_2 +","+ day_3 +","+ day_4 +", Tow_L, Tow_R, Risk_2012_larceny, Risk_2013_larceny\
                            FROM cleaning_sch WHERE \
                            lon >" + str(lon_des-delta_lon) + " AND lon < " + str(lon_des+delta_lon) + " and \
                            lat >" + str(lat_des-delta_lat) + " AND lat < " + str(lat_des+delta_lat) + ";")

    query_results = db.store_result().fetch_row(maxrows=0)

    # For each block, we will store in the variable parsed_st
    # whether one can park there, what the risk is and what color/size/opacity to use for the marker
    parsed_st=[]

    # looping over the blocks in the neighborhood
    for result in query_results:        

        total_risk = float(result[13])+float(result[14])

        risk_col = pseudocolor(total_risk)
        circle_size = pseudosize(total_risk)
        opacity = pseudoopacity(total_risk) 

        # check if there is any conflict with cleaning schedule or tow away times 
        flag=check_availability(result[0], int(result[1]), int(result[2]), int(result[3]), int(result[4]),\
                               result[7], result[8], result[9], result[10], day_1,day_2,day_3,day_4, \
                               result[11], result[12], num_days,num_hrs,num_min, zone, \
                               current_year,current_month,current_day,current_hr,current_min)

        if flag == True:
            interval= max(int(result[2])-int(result[1]),int(result[4])-int(result[3]))
            if interval > 20:
                parsed_st.append( [result[0]+ ", San Francisco " , result[5], result[6],1,\
                        risk_col, total_risk, circle_size, opacity])
        else:
            interval= max(int(result[2])-int(result[1]),int(result[4])-int(result[3]))
            if interval > 20:
                parsed_st.append( [result[0]+ ", San Francisco " , result[5], result[6],0,\
                        risk_col, total_risk, circle_size, opacity])

    db.close()
    return json.dumps(parsed_st)

  
def check_availability(street, startn_L, endn_L, startn_R, endn_R,\
                            day_1_rule, day_2_rule, day_3_rule, day_4_rule, day_1,day_2,day_3,day_4, \
                            Tow_L, Tow_R, num_days,num_hrs,num_min, zone, \
                            current_year,current_month,current_day,current_hr,current_min):

    """
        Check whether the parking time conflicts with the cleaning schedule or tow away times.
    """

    # maximum allowed time to park in SF is 72 hrs
    # We divid the period of stay into different days (tody, tomorrow, etc)

    # different flags for different days (tody, tomorrow, etc)
    # value of the flag for each day: 2 if one can park on both sides of the street, 
    #                                 1 if possible to park at one side at least, 
    #                                 0 if not possible to park

    flag_1, flag_2, flag_3, flag_4 = 2, 2, 2, 2
    
    end_park_time = (current_hr+num_days*24+num_hrs)*60+current_min+num_min

    # for the first day
    flag_1 = find_compatibility_per_day(current_hr*60+current_min, min(1440,end_park_time), day_1_rule, day_1, Tow_L, Tow_R)

    # for the second day
    if end_park_time > 1440:
        flag_2 = find_compatibility_per_day(0,  min(1440,end_park_time-1440), day_2_rule, day_2, Tow_L, Tow_R)

    # for the third day
    if end_park_time > 2880:
        flag_3 = find_compatibility_per_day(0,  min(1440,end_park_time-2880), day_3_rule, day_3, Tow_L, Tow_R)

    # for the forth day
    if end_park_time > 4320:
        flag_4 = find_compatibility_per_day(0,  min(1440,end_park_time-4320), day_4_rule, day_4, Tow_L, Tow_R)


    if (startn_L == 0 or endn_L == 0) or (startn_R == 0 or endn_R == 0) :
        # if only one side of the street has cleaning schedule

        if (flag_1+flag_2+flag_3+flag_4) > 7 :
            return True
        else:
            return False 
    else:
        if (flag_1+flag_2+flag_3+flag_4) > 6 :
            return True
        else:
            return False 

def find_compatibility_per_day(park_start_time,park_end_time, day_rules, day, Tow_L, Tow_R):

    """
        For each day, check whether the parking time conflicts with the cleaning schedule or tow away times.

        return 2 if one can park on both sides of the street, 1 if possible to park at one side at least, 0 if not possible to park
    """

    # find compatibility with the tow away times

    flag_tow_l, flag_tow_r = find_tow_compatibility(park_start_time,park_end_time, day, Tow_L, Tow_R)

    if day_rules == None:
        if flag_tow_l == True and flag_tow_r == True:
            return 2
        elif flag_tow_l == False and flag_tow_r == False:
            return 0
        else:
            return 2             

    # find compatibility with cleaning schedules 

    # left_rule corresponds to the odd side of the street, right_rule corresponds to the even side of the street 
    left_rule,right_rule=day_rules.split('|'); 

    if ("_R_" not in day_rules):
        hr_field = left_rule[8:]
    elif("_L_" not in day_rules):    
        hr_field = right_rule[8:]        
    else:    
        hr_field = left_rule[8:]

    m=search(r'(\d+):(\d+)_(\d+):(\d+)',hr_field);  
    
    if m:   
        start_hr=int(m.group(1)); start_min=int(m.group(2)); 
        end_hr=int(m.group(3)); end_min=int(m.group(4)); 
    else:  
        return 2

    start = start_hr * 60 + start_min;  end = end_hr * 60 + end_min


    if ("_L_" not in day_rules):
        # if no cleaning schedule for the odd side
        if park_start_time > end or park_end_time < start and flag_tow_r == True:
            return 2
        else:
            if flag_tow_l == True:
                return 1
            else:
                return 0    

    elif ("_R_" not in day_rules):
        # if no cleaning schedule for the right side

        if park_start_time > end or park_end_time < start  and flag_tow_l == True:
            return 2
        else:
            if flag_tow_r == True:
                return 1
            else:
                return 0 

    else:
        if park_start_time > end or park_end_time < start:

            if flag_tow_l == True or flag_tow_r == True:
                return 2
            else:
                return 0

        else:
            return 0


def find_tow_compatibility(park_start_time,park_end_time, day, Tow_L, Tow_R):
    """
        For each day, check whether the parking time conflicts with the tow away times.
    """
    
    # flag_tow_l, flag_tow_r correspond to the odd, even side of the street respectively

    flag_tow_l, flag_tow_r = True, True

    if Tow_L == None or day not in Tow_L:
        flag_tow_l = True
    else:
        Tow_L=Tow_L.split("|")
        
        for el in Tow_L:
            if day in el:
                m=search(r'(.*)_(\d+)_(\d+)',el);  
                
                if m:   
                    start_hr=int(m.group(2)); 
                    end_hr=int(m.group(3)); 

                    start = start_hr * 60;  end = end_hr * 60 

                    if park_start_time > end or park_end_time < start :
                        flag_tow_l = True
                    else:
                        flag_tow_l = False

    if Tow_R == None or day not in Tow_R:
        flag_tow_r = True
    else:
        Tow_R=Tow_R.split("|")
        
        for el in Tow_R:
            if day in el:
                m=search(r'(.*)_(\d+)_(\d+)',el);  
                
                if m:   
                    start_hr=int(m.group(2)); 
                    end_hr=int(m.group(3)); 

                    start = start_hr * 60;  end = end_hr * 60 

                    if park_start_time > end or park_end_time < start :
                        flag_tow_r = True
                    else:
                        flag_tow_r = False

    return flag_tow_l, flag_tow_r 



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
#    app.run(debug=True, host='0.0.0.0', port=80)