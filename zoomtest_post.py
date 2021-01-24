#https://marketplace.zoom.us/develop/apps/_ZCj-XJeSXuT8Dbv1bcZ6A/credentials

import http.client
import json
import jwt   # pip install pyjwt
from pytz import timezone
import datetime
from datetime import date, datetime, timedelta
import mySQL_apptDB

#global connection/jwt objects
conn = http.client.HTTPSConnection("api.zoom.us")

api_key = 'oURxTkQkTL6USazzprxmuw'
api_sec = 'aN9ShhzoaxLX0BCJwLpjNOpAK1pd8lkVWkax'

# generate JWT
payload = {
'iss': api_key,
'exp': datetime.now() + timedelta(hours=7)
}
jwt_encoded = jwt.encode(payload, api_sec)

headerKey = str(jwt_encoded)[2:-1]#'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE2MDk3MzQyNTksImlhdCI6MTYwOTEyOTQ1N30.j_v2lfEWoOSlcTLVTEhbfXE00oJUzrHmWGqq3R2ZCg4'

headers = {
'authorization': "Bearer "+str(jwt_encoded)[2:-1],
'content-type': "application/json"
}

#Purpose: adds another participant to the zoom meeting
def addParticipant(mtgID, firstName, lastName, email):
    conn = http.client.HTTPSConnection("api.zoom.us")
    payload = {
        "email":str(email),
        "first_name":str(firstName),
        "last_name":str(lastName)
        }
    headers = { #post needs this different headers definition, get doesn't
        'content-type': "application/json",
        'authorization': "Bearer "+headerKey
        }

    conn = http.client.HTTPSConnection("api.zoom.us")
#https://api.zoom.us/v2/meetings/{meetingId}/registrants
    conn.request("POST", "/v2/meetings/"+str(mtgID)+"/registrants", json.dumps(payload), headers)
    res = conn.getresponse()
    raw_data = res.read()
    conn.close()

#Purpose: converts a given date string from 1 timezome to another (takes care of edge cases)
def convert_datetime_timezone(dt, tz1, tz2):
    tz1 = timezone(tz1)
    tz2 = timezone(tz2)

    dtO = datetime.strptime(dt,"%Y-%m-%dT%H:%M:%S")
    dtO = tz1.localize(dtO)
    dtO = dtO.astimezone(tz2)
    dtO = dtO.strftime("%Y-%m-%dT%H:%M:%S")

    return dtO

#Purpose: creates a meeting through the zoom api and adds the appt to the database through a call
def createMtg(time, password, doctor, patient, cursor, cnx):
    #add 5 hrs to time
    conn = http.client.HTTPSConnection("api.zoom.us")
    topic = doctor+" + "+patient+" appt"
    payload={
      "topic":topic,
      "type": 2,
      "start_time": time, #zoom automatically adds 5 hrs to time (EST->UTC)
      "duration": 40,
      "timezone": "Eastern Time (US and Canada)",
      "password": password,
      "settings": {
        "host_video": 'true',
        "mute_upon_entry": 'true',
        "approval_type": 0,
        "enforce_login": 'true'
      }
    }
    
    headers = {
        'content-type': "application/json",
        'authorization': "Bearer "+headerKey
        }

    #HE1A37EjRIiGjh_wekf90A is my zoom account
    conn.request("POST", "/v2/users/HE1A37EjRIiGjh_wekf90A/meetings", json.dumps(payload), headers)
    
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    
    #change time to zoom time-5h (UTC->EST) but take off the 'z' to match the format
    zoomAdjustedTime = convert_datetime_timezone(data.get("start_time")[:-1], 'UTC',"US/Eastern")
    mySQL_apptDB.createAppt(topic, str(data.get("id")), doctor, patient, zoomAdjustedTime, str(data.get("join_url")), cursor, cnx)
    conn.close()
    return data

#Purpose: look at all zoom meetings through call return from Zoom API and cancel each one
def cancelAllMeetings():
    conn = http.client.HTTPSConnection("api.zoom.us")
    
    for i in getMtgsFromUserID("HE1A37EjRIiGjh_wekf90A").get("meetings"):
        conn.request("DELETE", "/v2/meetings/"+str(i.get("id")), headers=headers)
        res = conn.getresponse()
    conn.close()

#Purpose: delete zoom meeting from both Zoom API and database (through call)
def deleteMtgFromID(mtgID, cursor, cnx):
    conn = http.client.HTTPSConnection("api.zoom.us")
    conn.request("DELETE", "/v2/meetings/"+str(mtgID), headers=headers)
    res = conn.getresponse()
    mySQL_apptDB.deleteAppt(mtgID, cursor, cnx)
    raw_data = res.read()
    print("DELETE",raw_data)
    conn.close()
    #response is not JSON like the rest

#Purpose: returns info about a meeting in json format
def getMtgFromMtgID(info):
    conn = http.client.HTTPSConnection("api.zoom.us")
    conn.request("GET", "/v2/meetings/"+str(info), headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    conn.close()
    return data

#Purpose: returns all meetings that a user is a part of 
#   #(does not work with username bc it only works with the zoom user)
def getMtgsFromUserID(userID):
    conn = http.client.HTTPSConnection("api.zoom.us")
    conn.request("GET", "/v2/users/"+str(userID)+"/meetings?page_number=1&page_size=30&type=upcoming", headers=headers)
        #this request gets ALL past meetings as well, not as useful, a lot of bogged down info
            #conn.request("GET", "/v2/users/"+str(userID)+"/meetings", headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    conn.close()
    return data;

#Purpose: returns all active users (only 1 for now and doesn't filter on email value atm)
def getUserFromEmail(email):
    conn = http.client.HTTPSConnection("api.zoom.us")
    conn.request("GET", "/v2/users?page_number=1&page_size=30&status=active", headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    conn.close()
    return data

#Purpose: update meeting details (time is the only one they can change)
def updateMtg(mtgid, topic, time, cursor, cnx):
    zoomResp = getMtgFromMtgID(mtgid)
    payload={
      "topic": topic,
      "type": 2,
      "start_time":time, #zoom automatically sends +5, don't convert
      "duration": 40,
      "timezone": "Eastern Time (US and Canada)",
      "password": zoomResp.get('password'), #keep the password the same by querying what it already is
      "settings": {
        "host_video": 'true',
        "mute_upon_entry": 'true',
        "approval_type": 0,
        "enforce_login": 'true'
      }
    }
    headers = {
        'content-type': "application/json",
        'authorization': "Bearer "+headerKey
        }

    conn.request("PATCH", "/v2/meetings/"+str(mtgid), json.dumps(payload), headers)
    
    res = conn.getresponse()
    raw_data = res.read()
    
    #convert the UTC time to -5 for storing (UTC->EST)
    data = getMtgFromMtgID(mtgid)
    zoomAdjustedTime = convert_datetime_timezone(str(data.get("start_time"))[:-1], 'UTC',"US/Eastern")
    mySQL_apptDB.updateAppt(topic, mtgid,zoomAdjustedTime, cursor, cnx)
    conn.close()
    return getMtgFromMtgID(mtgid)


# for i in getMtgsFromUserID("HE1A37EjRIiGjh_wekf90A").get("meetings"):
#     print(i.get("id"))

#cancelAllMeetings()
# print("AFTER CANCEL")
# for i in getMtgsFromUserID("HE1A37EjRIiGjh_wekf90A").get("meetings"):
#     print(i.get("id"))

    