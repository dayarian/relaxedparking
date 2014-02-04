relaxedparking.com is a web app that recommends parking spots for locations in San Francisco. The goal is to avoid parking tickets (by checking tow away times and street cleaning schedule) and to avoid car-related crimes. This app was built during the Insight Data Science Program Jan-2014 Session. 

The input data consists of street cleaning schedules, tow away times and crime data, all obtained from the city of San Francisco database:  https://data.sfgov.org/

The data is processed with Python and Pandas library, and stored in a mysql database. Using crime data, I developed a probabilistic model which assigns a risk score to each street block. This model was developed using Python and Pandas. The app was deployed using Flask, Google Maps API, jQuery and AWS. 


Repository Layout:

/parsing_input_data : Python scripts for parsing the SF data and storing it in SQL

/risk_model : Scripts for exploring the crime data

/web : The Flask-based application which serves up the app


