##import http.client
##
##conn = http.client.HTTPSConnection("api.zoom.us")
##
##payload ={"topic":string,"type":integer,"start_time":string [date-time],"duration":"integer","schedule_for":"string","timezone":"string","password":"string","agenda":"string","recurrence":{"type":"integer","repeat_interval":"integer","weekly_days":"string","monthly_day":"integer","monthly_week":"integer","monthly_week_day":"integer","end_times":"integer","end_date_time":"string [date-time]"},"settings":{"host_video":"boolean","participant_video":"boolean","cn_meeting":"boolean","in_meeting":"boolean","join_before_host":"boolean","mute_upon_entry":"boolean","watermark":"boolean","use_pmi":"boolean","approval_type":"integer","registration_type":"integer","audio":"string","auto_recording":"string","enforce_login":"boolean","enforce_login_domains":"string","alternative_hosts":"string","global_dial_in_countries":["string"],"registrants_email_notification":"boolean"}}
##
##headers = {
##    'content-type': "application/json",
##    'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTA5OTgwODEsImlhdCI6MTU5MDM5MzI4MX0.YOkr0BEfcgDd6gNk2lAfuWqGF0yYQphqI_MQDQUw79o"
##    }
##
##conn.request("POST", "/v2/users/cq7614/meetings", payload, headers)
##
##res = conn.getresponse()
##data = res.read()
##
##print(data.decode("utf-8"))


import http.client

conn = http.client.HTTPSConnection("api.zoom.us")

headers = { 'authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6Im9VUnhUa1FrVEw2VVNhenpwcnhtdXciLCJleHAiOjE1OTA5OTgwODEsImlhdCI6MTU5MDM5MzI4MX0.YOkr0BEfcgDd6gNk2lAfuWqGF0yYQphqI_MQDQUw79o" }

conn.request("GET", "/v2/meetings/72951983398", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
