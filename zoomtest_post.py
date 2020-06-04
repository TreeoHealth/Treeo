
import http.client
import json
from OpenSSL import SSL
conn = http.client.HTTPSConnection("api.zoom.us")#, context = ssl._create_unverified_context())

def addParticipant(mtgID, firstName, lastName, email):
    #conn = http.client.HTTPSConnection("api.zoom.us", context = ssl._create_unverified_context())

    payload = "{\"email\":\"myemail@mycompany.com\",\"first_name\":\"Mike\",\"last_name\":\"Brown\",\"address\":\"123 Main ST\",\"city\":\"San Jose\",\"country\":\"US\",\"zip\":\"95550\",\"state\":\"CA\",\"phone\":\"111-444-4444\",\"industry\":\"Tech\",\"org\":\"IT\",\"job_title\":\"DA\",\"purchasing_time_frame\":\"More Than 6 Months\",\"role_in_purchase_process\":\"Influencer\",\"no_of_employees\":\"1-20\",\"comments\":\"Excited to host you.\",\"custom_questions\":[{\"title\":\"Favorite thing about Zoom\",\"value\":\"Meet Happy\"}]}"

    headers = {
        'content-type': "application/json",
        'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTA5OTgwODEsImlhdCI6MTU5MDM5MzI4MX0.YOkr0BEfcgDd6gNk2lAfuWqGF0yYQphqI_MQDQUw79o"
        }

    conn.request("POST", "/v2/meetings/"+str(mtgID)+"/registrants", payload, headers)

    res = conn.getresponse()
    data = res.read()

    print(data.decode("utf-8"))

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
        'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTE2MjI4ODIsImlhdCI6MTU5MTAxODA4NH0.jpITACB91xADqzpSlu4BgYWf5LDx79DuGHasDZ5HK1Y"
        }

    conn.request("POST", "/v2/users/HE1A37EjRIiGjh_wekf90A/meetings", json.dumps(payload), headers)##HE1A37EjRIiGjh_wekf90A
    ##urllib.request.urlopen({api_url}, data=bytes(json.dumps(headers), encoding="utf-8"))
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data
    #print(data.decode("utf-8"))

def getMtgsFromUserID(userID):
    headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTE2MjI4ODIsImlhdCI6MTU5MTAxODA4NH0.jpITACB91xADqzpSlu4BgYWf5LDx79DuGHasDZ5HK1Y" }

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
    #conn = http.client.HTTPSConnection("api.zoom.us", context = ssl._create_unverified_context())
    ##
    headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTE2MjI4ODIsImlhdCI6MTU5MTAxODA4NH0.jpITACB91xADqzpSlu4BgYWf5LDx79DuGHasDZ5HK1Y" }
    ##
    conn.request("GET", "/v2/meetings/"+str(info), headers=headers)
    ##
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data
##    print(data.get('topic'))
##    print(data.get('start_time'))

def getUserFromEmail(email):
    headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTE2MjI4ODIsImlhdCI6MTU5MTAxODA4NH0.jpITACB91xADqzpSlu4BgYWf5LDx79DuGHasDZ5HK1Y" }
    ##
    conn.request("GET", "/v2/users/"+str(email), headers=headers)
    res = conn.getresponse()
    raw_data = res.read()
    data = json.loads(raw_data.decode("utf-8"))
    return data

print(getMtgsFromUserID('HE1A37EjRIiGjh_wekf90A'))#78851018678))
