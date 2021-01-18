import jwt   # pip install pyjwt
import http.client
import datetime
import json

api_key = 'oURxTkQkTL6USazzprxmuw'
api_sec = 'aN9ShhzoaxLX0BCJwLpjNOpAK1pd8lkVWkax'


# generate JWT
payload = {
'iss': api_key,
'exp': datetime.datetime.now() + datetime.timedelta(hours=7)
}
jwt_encoded = jwt.encode(payload, api_sec)

# call API: get user list
conn = http.client.HTTPSConnection("api.zoom.us")
headers = {
'authorization': "Bearer "+str(jwt_encoded)[2:-1],
'content-type': "application/json"
}
# conn.request("GET", "/v2/users?status=active", headers=headers)
# res = conn.getresponse()
# response_string = res.read().decode('utf-8')
# response_obj = json.loads(response_string)

payload={
      "topic": "topic",
      "type": 2,
      "start_time": "2021-12-31T10:30:00Z",
      "duration": 40,
      "timezone": "Eastern Time (US and Canada)",
      "password": "password",
      "settings": {
        "host_video": 'true',
        "mute_upon_entry": 'true',
        "approval_type": 0,
        "enforce_login": 'true'
      }
    }

conn.request("POST", "/v2/users/HE1A37EjRIiGjh_wekf90A/meetings", json.dumps(payload), headers)##HE1A37EjRIiGjh_wekf90A
res = conn.getresponse()
raw_data = res.read()
data = json.loads(raw_data.decode("utf-8"))
print(data)
conn.close()
