import http.client
import json
conn = http.client.HTTPSConnection("api.zoom.us")

headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTA5OTgwODEsImlhdCI6MTU5MDM5MzI4MX0.YOkr0BEfcgDd6gNk2lAfuWqGF0yYQphqI_MQDQUw79o" }

conn.request("GET", "/v2/users?page_number=1&page_size=30&status=active", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))


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
    'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTA5OTgwODEsImlhdCI6MTU5MDM5MzI4MX0.YOkr0BEfcgDd6gNk2lAfuWqGF0yYQphqI_MQDQUw79o"
    }

conn.request("POST", "/v2/users/HE1A37EjRIiGjh_wekf90A/meetings", bytes(json.dumps(payload), encoding="utf-8"), headers)
##urllib.request.urlopen({api_url}, data=bytes(json.dumps(headers), encoding="utf-8"))
res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTA5OTgwODEsImlhdCI6MTU5MDM5MzI4MX0.YOkr0BEfcgDd6gNk2lAfuWqGF0yYQphqI_MQDQUw79o" }

conn.request("GET", "/v2/meetings/78851018678", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

#gets info about a meeting --------------------------------
##
##import http.client
##
##conn = http.client.HTTPSConnection("api.zoom.us")
##
##headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTA5OTgwODEsImlhdCI6MTU5MDM5MzI4MX0.YOkr0BEfcgDd6gNk2lAfuWqGF0yYQphqI_MQDQUw79o" }
##
##conn.request("GET", "/v2/meetings/72951983398", headers=headers)
##
##res = conn.getresponse()
##data = res.read()
##
##print(data.decode("utf-8"))
