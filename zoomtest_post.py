#set up selenium to go to the page that has the oauth key of the jwt app on it
#https://marketplace.zoom.us/develop/apps/_ZCj-XJeSXuT8Dbv1bcZ6A/credentials
#overwrite a txt that hold the key every week (timer tracks weeks/checks if key is valid)
#at the start of the code, read in the txt and sent it as a param to each function


##TO CREATE A TABLE:::
#aws dynamodb create-table --table-name tableName --attribute-definitions AttributeName=___,AttributeType=S AttributeName=____,AttributeType=S --key-schema AttributeName=____,KeyType=___ AttributeName=___,KeyType=___ --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
#AttributeType S
#KeyType RANGE, HASH (pk)

#eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTg5MzI3NDAsImlhdCI6MTU5MzU2OTYzMn0.kDAekzXUdjRsAiD9Aarmll_8FKozf9NLCWpQkzmyp48

import http.client
import json
#from OpenSSL import SSL
import jwt   # pip install pyjwt
import datetime
from datetime import date, datetime,timezone, timedelta
from pytz import timezone

import mySQL_apptDB
#from aws_appt import getAllApptsFromUsername,createApptAWS, deleteApptAWS,getApptFromMtgId #updateApptAWS,
conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())

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

def addParticipant(mtgID, firstName, lastName, email):
    #conn = http.client.HTTPSConnection("api.zoom.us", context = ssl._create_unverified_context())
    conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
    payload = {
        "email":str(email),
        "first_name":str(firstName),
        "last_name":str(lastName)
        }
    headers = { #post needs this different headers definition, get doesn't
        'content-type': "application/json",
        'authorization': "Bearer "+headerKey
        }

    conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
#https://api.zoom.us/v2/meetings/{meetingId}/registrants
    conn.request("POST", "/v2/meetings/"+str(mtgID)+"/registrants", json.dumps(payload), headers)
    res = conn.getresponse()
    raw_data = res.read()
    #data = json.loads(raw_data.decode("utf-8"))
    conn.close()
    #return data

def convert_datetime_timezone(dt, tz1, tz2):
    tz1 = timezone(tz1)
    tz2 = timezone(tz2)

    dt = datetime.strptime(dt,"%Y-%m-%dT%H:%M:%S")
    dt = tz1.localize(dt)
    dt = dt.astimezone(tz2)
    dt = dt.strftime("%Y-%m-%dT%H:%M:%S")

    return dt

#----post below
def createMtg(time, password, doctor, patient, cursor, cnx):
    #add 5 hrs to time
    #zoomAdjustedTime = convert_datetime_timezone(time, "US/Eastern",'UTC')
    #'2021-01-16T02:56:53Z'
    #print("adjusted create time (UTC) ->", zoomAdjustedTime)
    conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
    topic = doctor+" + "+patient+" appt"
    payload={
      "topic":topic,
      "type": 2,
      "start_time": time, #zoom automatically adds 5 hrs to time
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
#CALL createMtg  in aws_appt -> pass dr and patient
    #getAllApptsFromUsername,
    
    
    headers = {
        'content-type': "application/json",
        'authorization': "Bearer "+headerKey
        }

    conn.request("POST", "/v2/users/HE1A37EjRIiGjh_wekf90A/meetings", json.dumps(payload), headers)##HE1A37EjRIiGjh_wekf90A
    ##urllib.request.urlopen({api_url}, data=bytes(json.dumps(headers), encoding="utf-8"))
    
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    
    #createAppt(mtgName, mtgid, doctor, patient, start_time, joinURL, cursor, cnx)
    #change time to zoom time -5h but take off the 'z' to match the format
    zoomAdjustedTime = convert_datetime_timezone(str(data.get("start_time"))[:-1], 'UTC',"US/Eastern")
    print("zoom time:",str(data.get("start_time"))[:-1])
    print("adjusted create time -5 (EST) ->", zoomAdjustedTime)
    mySQL_apptDB.createAppt(topic, str(data.get("id")), doctor, patient, zoomAdjustedTime, str(data.get("join_url")), cursor, cnx)
    print("CREATE" , data)
    conn.close()
    return data

def updateMtg(mtgid, topic, time, cursor, cnx):
    zoomResp = getMtgFromMtgID(mtgid)
    print("Time before adjust = ", time)
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
    #TODO -- send zoom time -5h here
    #change time to zoom time -5h but take off the 'z' to match the format
    
    res = conn.getresponse()
    raw_data = res.read()
    #convert the UTC time to -5 for storing
    data = getMtgFromMtgID(mtgid)
    print("Time after update (UTC) = ",str(data.get("start_time"))[:-1])
    zoomAdjustedTime = convert_datetime_timezone(str(data.get("start_time"))[:-1], 'UTC',"US/Eastern")
    print("Time after update (EST) = ",zoomAdjustedTime)
    mySQL_apptDB.updateAppt(topic, mtgid,zoomAdjustedTime, cursor, cnx)
    conn.close()
    return getMtgFromMtgID(mtgid)

def deleteMtgFromID(mtgID, cursor, cnx):
    conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
    conn.request("DELETE", "/v2/meetings/"+str(mtgID), headers=headers)
    res = conn.getresponse()
    mySQL_apptDB.deleteAppt(mtgID, cursor, cnx)
    raw_data = res.read()
    print("DELETE",raw_data)
    conn.close()
    #response is not JSON like the rest

def getMtgsFromUserID(userID):
    conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
    conn.request("GET", "/v2/users/"+str(userID)+"/meetings?page_number=1&page_size=30&type=upcoming", headers=headers)
#this request gets ALL past meetings as well, not as useful, a lot of bogged down info
    #conn.request("GET", "/v2/users/"+str(userID)+"/meetings", headers=headers)#78851018678
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    conn.close()
    return data;

#gets info about a meeting --------------------------------
def getMtgFromMtgID(info):
    conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
    conn.request("GET", "/v2/meetings/"+str(info), headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    conn.close()
    return data

def getUserFromEmail(email):
    conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
    conn.request("GET", "/v2/users?page_number=1&page_size=30&status=active", headers=headers)
    #conn.request("GET", "/v2/users/"+str(email), headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    conn.close()
    return data

def mtgInfoToJSON():
    jsonResp = getMtgsFromUserID('HE1A37EjRIiGjh_wekf90A');
    arrOfMtgs = []
    #[{ "title": "Meeting",
    #"start": "2014-09-12T10:30:00-05:00",
    #"end": "2014-09-12T12:30:00-05:00Z"},{...}]
    
    mtgList = jsonResp.get("meetings")
    finalStr = ""
    for item in mtgList:
        time = str(item.get("start_time"))
        time = time[:-1]
        end_time = ((int(time[11:13])+1)%24)
        strend = time[:11]+str(end_time)+time[13:]
        mtgObj = {"title":str(item.get("topic")), "start": time, "end":strend}
        arrOfMtgs.append(mtgObj)


#print(createMtg("topic", "2020-12-31T10:30:00Z", "abc", "doctor", "patient"))
#print(getMtgFromMtgID(77580648369))
##addParticipant(72261254435,'isha', 'naik', 'inaik4000@gmail.com')
#jsonResp = getMtgFromMtgID(72261254435)
#jsonResp = updateMtg(77588267056, "Updated", "2020-07-30T12:30:00Z", "newp")
#print(jsonResp)
##print(createUser('inaik4000@gmail.com','isha', 'naik'))
