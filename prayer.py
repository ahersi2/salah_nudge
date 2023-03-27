

from builtins import breakpoint
import os
from re import L
import random
from urllib.error import HTTPError
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime, timezone, timedelta
import requests
import json
import pytz
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder

import firebase_admin
from firebase_admin import firestore, credentials

class Salah:
    # Need to add Newfound land
    timezone_offsets = {'ADT':3,'AST':4,'EDT':4,'EST':5,'CDT':5,'CST':6,'MDT':6,
                        'MST':7,'PDT':7,'PST':8,'ASDT':8,'AKST':9,'HDT':9,'HST':10}

    PRAYERS = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']

    def __init__(self,locations, users):
        self.users = users
        self.locations = locations
    
    def geocode_helper(self, loc, attempts):

        while attempts >0:
            geolocator = Nominatim(user_agent="http")
                
            try:
                return(geolocator.geocode(' '.join(loc))[1])
            except GeocoderTimedOut as e:
                if attempts == 1:
                    raise e #I will log this instead

                time.sleep(5)
                attempts -= 1


    
    def get_prayer_times(self):

        #run application 5 different times for the different timezones
        #use this: datetime.now(pytz.timezone('America/Toronto')).strftime('%z')
        #'-0500'
        #put each of these numbers in the .json file before each city, and have
        #the offset correspond to timezone. So the smallest offset/timezone will
        #execute first. The rest will follow. Maybe have env variable used here
        #or have it put in the databse as another column. The databse query will
        # have the offset included, which will correspond to 
        #or just simply have offset beside city name in json, and only send 

        

        

        prayer_times = {}
        for loc in self.locations:
            lat, lng = self.geocode_helper(loc, 5)

            #Get timezone for location
            tf = TimezoneFinder()
            #lng is index[1], lat is index [0]

            current_timezone = tf.timezone_at(lng=lng,lat=lat)

            #Get current UTC time
            timezone_key = datetime.now(pytz.timezone(current_timezone)).strftime("%Z")

            url = "http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2".\
                        format(city=loc[0],country=loc[1:])

            r = requests.get(url = url)

            data = r.json()
            
            cur_date = (data['data'].get("date").get("gregorian").get("date")).replace('-','/')

            fajr_time = cur_date + ' ' +data['data'].get("timings").get("Fajr")
            dhuhr_time = cur_date + ' ' +data['data'].get("timings").get("Dhuhr")
            asr_time = cur_date + ' ' +data['data'].get("timings").get("Asr")
            maghrib_time = cur_date + ' ' +data['data'].get("timings").get("Maghrib")
            isha_time = cur_date + ' ' +data['data'].get("timings").get("Isha")

            # The time below minus the offset will be the scheduled time of the message we send
            fajr_time_date_time = datetime.strptime(fajr_time, '%d/%m/%Y %H:%M')
            dhuhr_time_date_time = datetime.strptime(dhuhr_time, '%d/%m/%Y %H:%M')
            asr_time_date_time = datetime.strptime(asr_time, '%d/%m/%Y %H:%M')
            maghrib_time_date_time = datetime.strptime(maghrib_time, '%d/%m/%Y %H:%M')
            isha_time_date_time = datetime.strptime(isha_time, '%d/%m/%Y %H:%M')

            if timezone_key not in prayer_times:
                prayer_times[timezone_key] = {}


            if loc[2]:
                prayer_times[timezone_key].update({
                    loc[0]+'-'+loc[1]+loc[2]:{
                        "Fajr": (fajr_time_date_time, self.timezone_offsets[timezone_key]),
                        "Dhuhr": (dhuhr_time_date_time, self.timezone_offsets[timezone_key]),
                        "Asr": (asr_time_date_time, self.timezone_offsets[timezone_key]),
                        "Maghrib": (maghrib_time_date_time, self.timezone_offsets[timezone_key]),
                        "Isha": (isha_time_date_time, self.timezone_offsets[timezone_key])
                    }
                })
            else:
                prayer_times[timezone_key].update({
                    loc[0]+'-'+loc[1]:{
                        "Fajr": (fajr_time_date_time, self.timezone_offsets[timezone_key]),
                        "Dhuhr": (dhuhr_time_date_time, self.timezone_offsets[timezone_key]),
                        "Asr": (asr_time_date_time, self.timezone_offsets[timezone_key]),
                        "Maghrib": (maghrib_time_date_time, self.timezone_offsets[timezone_key]),
                        "Isha": (isha_time_date_time, self.timezone_offsets[timezone_key])
                    }
                })
        
        
        with open("prayer_times.json", "w") as write_file:
            json.dump(prayer_times, write_file, indent=4, default=str)

        print("PRAYER_TIMES.JSON FILE CREATED SUCCESSFULLY")
    def send_sms(self,time_zone_prefix):
        print("HERE IS THE TIMEZONES: {timezones}".format(timezones= time_zone_prefix))
        account_sid = os.environ["ACCOUNT_SID"]
        auth_token = os.environ["AUTH_TOKEN"]
        client = Client(account_sid, auth_token) 
        
        # message = client.messages.create(
        # body=fajr,
        # from_="+13852933323",
        # to="+17802223914"
        # )
        
        #Get lat and lng for city
        with open('prayer_times.json', 'r') as openfile:
            # Reading from json file
            json_object = json.load(openfile)
        

        for user in self.users:

            users_country = user[0]
            users_city = user[1]
            users_phone = user[3]

            if user[2]:
                users_state = user[0]
                city_country_index = users_city+'-'+users_country+'-'+users_state

            else:
                city_country_index = users_city+'-'+users_country


            #check if city_countr_index == json_object['EST'][key]
            # for example portaland-oregan-usa vs portland-maryland-usa
            # if portland oregan is in EST but the other is in MST
            # if were running script for EST, and were in user whose 
            # in marlyand, we'll skip this iteration
            
            cities_in_current_timezone = []
            
            for cur_time_zone_prefix in time_zone_prefix:
                if cur_time_zone_prefix not in json_object:
                    continue
                temp = [k for k, v in json_object[cur_time_zone_prefix].items()]
                cities_in_current_timezone.extend(temp)

            #cities_in_current_timezone = [k for k, v in json_object[time_zone_prefix].items()]
            
            #if current users location, doesn't exist in list of json
            #locations for current timezone, skip this user
            #
            if city_country_index not in cities_in_current_timezone:
                continue

            users_prayers_today = ''
            for tz in time_zone_prefix:
                if tz in json_object and city_country_index in json_object[tz]:
                    users_prayers_today = json_object[tz][city_country_index]
            
            for prayer, date in users_prayers_today.items():

                with open('messages.json', 'r') as openfile:
                    f = json.load(openfile)
                    try:
                        body = random.choice(f['messages']).format(prayer=prayer)
                    except KeyError as e:
                        print("Key error")
                        body = "Friendly reminder that {prayer} prayer is in roughly 15 minutes".format(prayer=prayer)

                date_to_send = datetime.strptime(date[0], '%Y-%m-%d %H:%M:%S') + timedelta(hours = date[1])
                print("HERE IS THE BODY MESSAGE: {body} ".format(body=body))
                
                try:
                    message = client.messages \
                    .create(
                    messaging_service_sid='MG0b425562b3e558bd579517caf5043e73',
                    body=body,
                    send_at=date_to_send,
                    schedule_type='fixed',
                    to=users_phone
                    )
                    print(message.sid)
                    print("MESSAGE SENT SUCCESSFULLY")
                except TwilioRestException as e:
                    print(repr(e))

        

def main(time_zone_prefix):
    #first query all the citys and coutries
    #pass that in get_prayer_times to create json file

    #then query the entire database in temp memory for all users
    #pass that in send_sms()
    #use prayers = data['EST'].get('city-country'), the 'EST' will come 
    #from global var in heroku
    # if prayers then you know its the correct time zone
    
    my_credentials = {
        u"type": "service_account",
        u"project_id": "prayer-app-5e55c",
        u"private_key_id": os.environ.get("PRIVATE_KEY_ID"),
        u"private_key": os.environ["PRIVATE_KEY"].replace("\\n", "\n"),
        u"client_email": os.environ.get("CLIENT_EMAIL"),
        u"client_id": os.environ.get("CLIENT_ID"),
        u"auth_uri": "https://accounts.google.com/o/oauth2/auth",
        u"token_uri": "https://oauth2.googleapis.com/token",
        u"auth_provider_x509_cert_url": os.environ.get("AUTH_PROVIDER_X509_CERT_URL"),
        u"client_x509_cert_url": os.environ.get("CLIENT_X509_CERT_URL")
    }

    

    if not firebase_admin._apps:
        #cred = credentials.Certificate(my_credentials)
        cred = credentials.Certificate(json.loads(os.environ["TEST_CONFIG"]))
        
        app = firebase_admin.initialize_app(cred)

    db = firestore.client()
    # Get the data from the user and location collection
    location_tuple = db.collection(u'locations').stream()
    users = db.collection(u'users').stream()

    # Documents for user collection and location collection
    # will be stored here
    countries_and_cities = []
    users_data = []
    
    print("before location tuple loop")
    for location in location_tuple:
        location = location.to_dict()
        countries_and_cities.append((location['city'], \
        location['country'], location['state']))

    for user in users:
        user = user.to_dict()
        users_data.append((user['country'], user['city'], \
        user['state'], user['phone']))


    #Create the json file on once a day, so AST time comes first
    salah_object = Salah(countries_and_cities, users_data)

    salah_object.get_prayer_times()

    salah_object.send_sms(time_zone_prefix)

#main(['MDT'])