
import json
from zoomus import ZoomClient

client = ZoomClient('oURxTkQkTL6USazzprxmuw', 'aN9ShhzoaxLX0BCJwLpjNOpAK1pd8lkVWkax')
#key/client id?? + secret --> must be jwt app*
#go to marketplace.zoom.us, sign in, hit manage, select the created project

user_list_response = client.user.list()
user_list = json.loads(user_list_response.content)
print(user_list)
for user in user_list['users']:
    user_id = user['id']
    print(user_id)
    print(json.loads(client.meeting.list(user_id=user_id).content))
