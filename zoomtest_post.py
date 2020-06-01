import http.client
import json
conn = http.client.HTTPSConnection("api.zoom.us")

headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTE2MjI4ODIsImlhdCI6MTU5MTAxODA4NH0.jpITACB91xADqzpSlu4BgYWf5LDx79DuGHasDZ5HK1Y" }

conn.request("GET", "/v2/users?page_number=1&page_size=30&status=active", headers=headers)

res = conn.getresponse()
data = res.read()

#print(data.decode("utf-8"))


#----post below
payload={
  "topic": "Sophia Test",
  "type": 8,
  "start_time": "2020-06-14T10:21:57",
  "duration": 40,
  "timezone": "Eastern Time (US and Canada)",
  "password": "abc123",
"recurrence": {
"type": 1,
"repeat_interval": 1,
"end_date_time": "2020-06-14T10:21:57"
},
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

conn.request("POST", "/v2/users/HE1A37EjRIiGjh_wekf90A/meetings", json.dumps(payload), headers)
##urllib.request.urlopen({api_url}, data=bytes(json.dumps(headers), encoding="utf-8"))
res = conn.getresponse()
data = res.read()
#print(data.decode("utf-8"))

headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTE2MjI4ODIsImlhdCI6MTU5MTAxODA4NH0.jpITACB91xADqzpSlu4BgYWf5LDx79DuGHasDZ5HK1Y" }

conn.request("GET", "/v2/meetings/78851018678", headers=headers)
res = conn.getresponse()
raw_data = res.read()
data = json.loads(raw_data.decode("utf-8"))
print(data)
print(data.get('join_url'))
info=data.get('id')
print(info)
print(data.get('start_time'))

#gets info about a meeting --------------------------------
##
##import http.client
##
conn = http.client.HTTPSConnection("api.zoom.us")
##
headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTE2MjI4ODIsImlhdCI6MTU5MTAxODA4NH0.jpITACB91xADqzpSlu4BgYWf5LDx79DuGHasDZ5HK1Y" }
##
conn.request("GET", "/v2/meetings/"+str(info), headers=headers)
##
res = conn.getresponse()
raw_data = res.read()
data = json.loads(raw_data.decode("utf-8"))
print(data.get('topic'))
print(data.get('start_time'))
