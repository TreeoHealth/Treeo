#set up selenium to go to the page that has the oauth key of the jwt app on it
#https://marketplace.zoom.us/develop/apps/_ZCj-XJeSXuT8Dbv1bcZ6A/credentials
#overwrite a txt that hold the key every week (timer tracks weeks/checks if key is valid)
#at the start of the code, read in the txt and sent it as a param to each function

import http.client
import json
from OpenSSL import SSL
conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())
headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTM1MzI3NDAsImlhdCI6MTU5MTU4ODM1MX0.fC3ewzx3rvy-Fex6_zKX6mryW-d83WjTSILdHm-dMdg" }

def addParticipant(mtgID, firstName, lastName, email):
    #conn = http.client.HTTPSConnection("api.zoom.us", context = ssl._create_unverified_context())
    payload = {
        "email":str(email),
        "first_name":str(firstName),
        "last_name":str(lastName)
        }
    headers = { #post needs this different headers definition, get doesn't
        'content-type': "application/json",
        'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTM1MzI3NDAsImlhdCI6MTU5MTU4ODM1MX0.fC3ewzx3rvy-Fex6_zKX6mryW-d83WjTSILdHm-dMdg"
        }

    conn.request("POST", "/v2/meetings/"+str(mtgID)+"/registrants", payload, headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data;

#----post below
def createMtg(topic, time, password):

    payload={
      "topic": topic,
      "type": 2,
      "start_time": time,
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
        'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTM1MzI3NDAsImlhdCI6MTU5MTU4ODM1MX0.fC3ewzx3rvy-Fex6_zKX6mryW-d83WjTSILdHm-dMdg"
        }

    conn.request("POST", "/v2/users/HE1A37EjRIiGjh_wekf90A/meetings", json.dumps(payload), headers)##HE1A37EjRIiGjh_wekf90A
    ##urllib.request.urlopen({api_url}, data=bytes(json.dumps(headers), encoding="utf-8"))
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data

def deleteMtgFromID(mtgID):
    conn.request("DELETE", "/v2/meetings/"+str(mtgID), headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data

def getMtgsFromUserID(userID):

    conn.request("GET", "/v2/users/"+str(userID)+"/meetings", headers=headers)#78851018678
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data;
##    print(data)
##    print(data.get('join_url'))
##    info=data.get('id')
##    print(info)
##    print(data.get('start_time'))

#gets info about a meeting --------------------------------
def getMtgFromMtgID(info):
    conn.request("GET", "/v2/meetings/"+str(info), headers=headers)
    ##
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data
##    print(data.get('topic'))
##    print(data.get('start_time'))

def getUserFromEmail(email):
    conn.request("GET", "/v2/users/"+str(email), headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data
