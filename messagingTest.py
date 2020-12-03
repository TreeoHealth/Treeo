from flask import Flask, render_template, request
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import datetime
from datetime import date, datetime,timezone

app = Flask(__name__)
dynamo_client = boto3.client('dynamodb')

@app.route('/submitEmail', methods=['POST','GET'])
def formatEmail():
    insertMessage(request.form['sender_username'],
        request.form['reciever_username'],
        request.form['subject'],
        request.form['email_body'])
    return render_template("messageInbox.html",
                           msgList = getAllMessages("gvhhhh"))

@app.route('/sentFolder', methods=['POST','GET'])
def sentFolder():
    return render_template("sentBox.html",
                           msgList = getAllMessagesSent("from_user"));

@app.route('/trashFolder', methods=['POST','GET'])
def trashFolder():
    return render_template("trashBox.html",
                           msgList = getAllTrashMessages("from_user"));

@app.route('/selectOption', methods=['POST','GET'])
def selectOption():
    listObj = []
    #print(request.form)
    for check in request.form:
        print(check)
        moveToTrash(str(check), "from_user")
    return index()

def insertMessage(sender, reciever, subject,body):
    
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:4000")

    table = dynamodb.Table('MessageDB')
    messageID = ""
    messageID= messageID+str(datetime.now().strftime('%H%M%S'))
    messageID= messageID+str(datetime.now()).split(".")[1]
    try:
        response = dynamo_client.put_item(TableName= 'MessageDB',
           Item={
            'messageID':{"N":messageID},
            'sender':{"S":sender},
            'reciever': {"S":reciever},
            'subject': {"S":subject},
            'msgbody':{"S":body},
            'send_time': {"S":str(datetime.now().strftime('%H:%M:%S'))},
            'send_date':{"S":str(date.today().strftime("%B %d, %Y"))},
            'read_status':{"S":"unread"},
            'sender_loc':{"S":"sent_folder"}, #sent_folder, deleted (in trash), [tbd - draft]
            'reciever_loc':{"S":"inbox"}, #inbox (in inbox), deleted (in trash)
            'perm_del':{"S":"n"} #n = neither, r = reciever, s = sender, sr = delete from database
            }
           )
    except:
        return

@app.route('/newEmail', methods=['POST','GET'])
def newEmail():
    return render_template("newEmail.html",
                           sender_username = "from_user",
                           reciever_username="",
                           subject = "",
                           email_body = "")

def countUnread(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    response = table.scan()

    unreadNum = 0
    for i in response['Items']:
        if(i['reciever']==username and i['read_status']=="unread"):
            print(i)

def markAsRead(msgID):
    try:
        read_status='read'   
        response = dynamo_client.update_item(TableName= 'MessageDB',
            Key={
                'messageID': {"N":str(msgID)}
            },
        UpdateExpression="SET #read_status = :r",
        ExpressionAttributeNames= {
        '#read_status' : 'read_status'
    },
    ExpressionAttributeValues= {
        ':r' : {'S':read_status}
    },
            ReturnValues="UPDATED_NEW"
        )
        return "Successfully marked as read."
    except ClientError as e:
        print(e.response['Error']['Message'])
        return "ERROR. Could not mark as read."

def permenantDel(msgID, del_username):
    response = dynamo_client.get_item(TableName= 'MessageDB',
            Key={
                'messageID': {"N":msgID}
            }
        )
        
    perm_del = "n"
    if response.get('Item').get('sender').get('S') == del_username and response.get('Item').get('perm_del').get('S')=='n': 
        perm_del = 's'
    elif response.get('Item').get('sender').get('S') == del_username and response.get('Item').get('perm_del').get('S')=='r':
        perm_del = 'sr'
    elif response.get('Item').get('reciever').get('S') == del_username and response.get('Item').get('perm_del').get('S')=='s':
        perm_del = 'sr'
    elif response.get('Item').get('reciever').get('S') == del_username and response.get('Item').get('perm_del').get('S')=='n': 
        perm_del = 'r'
    else:
        perm_del = 'n'

    if perm_del != 'sr':
        response = dynamo_client.update_item(TableName= 'MessageDB',
			Key={
				'messageID': {"N":str(msgID)}
			},
			UpdateExpression="SET #perm_del = :p",
			ExpressionAttributeNames= {
                            "#perm_del":"perm_del"
			},
			ExpressionAttributeValues= {
                                ':p' : {'S':perm_del}
                                
			},
			ReturnValues="UPDATED_NEW"
                             )
        return "Successfully deleted from view."
    else: #if they both said to permenantly delete it, remove it from the database
        response = dynamo_client.delete_item(TableName= 'MessageDB',
            Key={
                'messageID':{'N':msgID}
            }
            )
        return "successfully deleted from database"
		

def moveToTrash(msgID, del_username):
    try:
        response = dynamo_client.get_item(TableName= 'MessageDB',
            Key={
                'messageID': {"N":msgID}
            }
        )
        
        if (response.get('Item').get('sender').get('S'))==del_username: 
            try:
                sender_loc = 'trash'
                response = dynamo_client.update_item(TableName= 'MessageDB',
			Key={
				'messageID': {"N":str(msgID)}
			},
			UpdateExpression="SET #sender_loc = :s",
			ExpressionAttributeNames= {
			'#sender_loc' : 'sender_loc'
			},
			ExpressionAttributeValues= {
				':s' : {'S':sender_loc}
			},
			ReturnValues="UPDATED_NEW"
                             )
                return "Successfully moved to trash."

            except ClientError as e:
                print(e.response['Error']['Message'])
                return "ERROR. Could not move to trash."
        else:
            try:
                reciever_loc = 'trash'
                response = dynamo_client.update_item(TableName= 'MessageDB',
			Key={
				'messageID': {"N":str(msgID)}
			},
			UpdateExpression="SET #reciever_loc = :r",
			ExpressionAttributeNames= {
			'#reciever_loc' : 'reciever_loc'
			},
			ExpressionAttributeValues= {
				':r' : {'S':reciever_loc}
			},
			ReturnValues="UPDATED_NEW"
		 )
                return "Successfully moved to trash."

            except ClientError as e:
                print(e.response['Error']['Message'])
                return "ERROR. Could not move to trash."
    except:
        return "Bad message ID "

    #to do a "trash empty" change the username of whoever moved it to the trash so it does not show up in their scans any more
    #if both sender and reciever have permenantly deleted it, remove it from the database
    
def getAllTrashMessages(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    response = table.scan()
#TODO -- filter out messages that they have marked for permenant deletion
    trashList = []
    for i in response['Items']:
        if (i['reciever']==username and i['reciever_loc']=='trash') or (i['sender']==username and i['sender_loc']=='trash'):
            trashList.append([i['messageID'],i['sender'],i['send_date'],i['subject']])
    
    return trashList #make into class object later

def getAllUnreadMessages(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    response = table.scan()

    unreadList = []
    for i in response['Items']:
        if i['reciever']==username and i['read_status']=='unread'and i['reciever_loc']=='inbox':
            unreadList.append(i['messageID'])
    
    return unreadList #make into class object later


def getAllMessages(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    response = table.scan()

    msgList = []
    for i in response['Items']:
        if i['reciever']==username and i['reciever_loc']=='inbox':
            msgList.append([i['messageID'],i['sender'],i['send_date'],i['subject']])
    
    return msgList #make into class object later


def getAllMessagesSent(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    response = table.scan()

    msgList = []
    for i in response['Items']:
        if i['sender']==username and i['sender_loc']=='sent_folder':
            msgList.append([i['messageID'],i['reciever'],i['send_date'],i['subject']])
    
    return msgList #make into class object later




@app.route('/')
def index():
    return render_template("messageInbox.html",
                           msgList = getAllMessages("gvhhhh"))


#make a front page with 2 buttons - 1 = log in as user1, 2 = log in as user2
    #(interact with each one's inbox/sent/trash/etc. separately
#- DONE :) - trash (from inbox or sent) 1
#-- move to inbox or sent from (from trash) 3
#-- mark read/unread 2

#eventually
#--convert scan+filter -> query
#--put character limit on subject line
#--message for if user has nothing in a folder
#--conditional formatting for read/unread emails in inbox
#--change words to icons 

if __name__ == '__main__':
   app.run(debug=True)
