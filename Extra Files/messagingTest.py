from flask import Flask, render_template, request,session, jsonify
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import datetime
from datetime import date, datetime,timezone
import time
import aws_appt

app = Flask(__name__)
dynamo_client = boto3.client('dynamodb')

@app.route('/submitEmail', methods=['POST','GET'])
def formatEmail():

    query = request.form['reciever_username']
    actualUsername = (query.split(" - "))[0] #username - last name, first name
    response = aws_appt.getAcctFromUsername(actualUsername)
    if(len(query.split(" - "))==2 and len(response)==2):
        insertMessage(request.form['sender_username'],
            request.form['reciever_username'],
            request.form['subject'],
            request.form['email_body'],
                  "0"
                  )
    elif(len(aws_appt.getAcctFromUsername(query))==2):
        insertMessage(request.form['sender_username'],
            request.form['reciever_username'],
            request.form['subject'],
            request.form['email_body'],
                  "0"
                  )
    else:
        return render_template("newEmail.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           sender_username = session['username'],
                           errorMsg="Please enter a valid user ID",
                           reciever_username="",
                           subject = request.form['subject'],
                           email_body = request.form['email_body'])
    msgListObj = getAllMessages(session['username'])
    if(len(msgListObj)==0):
        return render_template("emptyInbox.html",
                           inboxUnread ="",
                           trashUnread = countUnreadInTrash(session['username'])
                           )
    else:
        return render_template("messageInbox.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           msgList = msgListObj)

@app.route('/submitReplyEmail', methods=['POST','GET'])
def formatReplyEmail():
    insertMessage(request.form['sender_username'],
        request.form['reciever_username'],
        request.form['subject'],
        request.form['email_body'],
        request.form['headMsgID']
                  )
    msgListObj = getAllMessages(session['username'])
    if(len(msgListObj)==0):
        return render_template("emptyInbox.html",
                           inboxUnread ="",
                           trashUnread = countUnreadInTrash(session['username'])
                           )
    else:
        return render_template("messageInbox.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           msgList = msgListObj)

@app.route('/sentFolder', methods=['POST','GET'])
def sentFolder():
    msgListObj = getAllMessagesSent(session['username'])
    if(len(msgListObj)==0):
        return render_template("emptySent.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username'])
                           );
    else:
        return render_template("sentBox.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           msgList=msgListObj);

@app.route('/trashFolder', methods=['POST','GET'])
def trashFolder():
    msgListObj = getAllTrashMessages(session['username'])
    if(len(msgListObj)==0):
        return render_template("emptyTrash.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = ""
                           );
    else:
        return render_template("trashBox.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           msgList=msgListObj);


@app.route('/selectOption', methods=['POST','GET'])
def selectOption():
    x = ""
    try:
        x = str(request.form['trash.x'])
        for check in request.form:
            if(str(check)!='trash.x' and str(check)!='trash.y' and str(check)!='selectAll'):
                moveToTrash(str(check), session['username'])
    except:
        try:
            x = str(request.form['mar.x'])
            for check in request.form:
                if(str(check)!='mar.x' and str(check)!='mar.y' and str(check)!='selectAll'):
                    markAsRead(str(check))
        except:
            x = str(request.form['mau.x'])
            for check in request.form:
                if(str(check)!='mau.x' and str(check)!='mau.y' and str(check)!='selectAll'):
                    markAsUnread(str(check))

    return openInbox()

@app.route('/selectSent', methods=['POST','GET'])
def selectSent():
    try:
        x = str(request.form['trash.x'])
        for check in request.form:
            print(check)
            if(str(check)!='trash.x' and str(check)!='trash.y'and str(check)!='selectAll'):
                moveToTrash(str(check), session['username'])
        return sentFolder()
    except:
        return sentFolder()


@app.route("/search/<string:box>")
def process(box):
    jsonSuggest = []
    query = request.args.get('query')
    listPatients= aws_appt.searchPatientList()
    for username in listPatients:
        if(query in username):
            jsonSuggest.append({'value':username,'data':username})
    return jsonify({"suggestions":jsonSuggest})

@app.route('/subjWordCheck', methods=['POST','GET'])
def subjCheck():
    text = str(len(request.args.get('jsdata')))
    text = text + "/50"
    print(text)
    return text

@app.route('/bodyWordCheck', methods=['POST','GET'])
def bodyCheck():
    text = str(len(request.args.get('jsdata')))
    text = text + "/600"
    print(text)
    return text


@app.route('/permTrash', methods=['POST','GET'])
def emptyTrash():
    x=""
    try:
        x = str(request.form['permdel.x'])
        for check in request.form:
            if(str(check)!='permdel.x' and str(check)!='permdel.y' and str(check)!='selectAll'):
                permenantDel(str(check), session['username'])
    except:
            x = str(request.form['undotrash.x'])
            for check in request.form:
                if(str(check)!='undotrash.x' and str(check)!='undotrash.y' and str(check)!='selectAll'):
                    undoTrash(str(check))

    return trashFolder()
    
##    try:
##        x = str(request.form['undotrash'])
##        for check in request.form:
##            undoTrash(str(check))
##        return trashFolder()
##    except:
##       # try:
##            x = str(request.form['permdel'])
##            for check in request.form:
##                permenantDel(str(check), session['username'])
##            return trashFolder()
##       # except:
##           #return trashFolder() 
##    return trashFolder()
    

def undoTrash(msgID):
    #if it is in the trash and the sender == current username -> move it to sent folder
    #else move it to inbox
    try:
        sender_loc='sent_folder'
        reciever_loc='inbox'
        response = dynamo_client.get_item(TableName= 'MessageDB',
            Key={
                'messageID': {"N":msgID}
            }
        )
        if (response.get('Item').get('sender').get('S')==session['username']):
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
            return "Successfully marked as read."
        else:
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
            return "Successfully marked as read."
        
    except ClientError as e:
        print(e.response['Error']['Message'])
        return "ERROR. Could not mark as read."

def insertMessage(sender, reciever, subject,body, convoID):
    #print((sender, reciever, subject,body, convoID))
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:4000")
    table = dynamodb.Table('MessageDB')
    messageID = ""
    messageID= messageID+str(datetime.now().strftime('%H%M%S'))
    messageID= messageID+str(datetime.now()).split(".")[1]
    try:
        if(convoID =="0"): #if it is the only message
            response = dynamo_client.put_item(TableName= 'MessageDB',
		   Item={
			'messageID':{"N":messageID},
			'sender':{"S":sender},
			'reciever': {"S":reciever},
			'subject': {"S":subject},
			'msgbody':{"S":body},
			'convoID': {"N":messageID},
			'send_time': {"S":str(datetime.now().strftime('%H:%M:%S'))},
			'send_date':{"S":str(date.today().strftime("%B %d, %Y"))},
			'read_status':{"S":"unread"},
			'sender_loc':{"S":"sent_folder"}, #sent_folder, deleted (in trash), [tbd - draft]
			'reciever_loc':{"S":"inbox"}, #inbox (in inbox), deleted (in trash)
			'perm_del':{"S":"n"} #n = neither, r = reciever, s = sender, sr = delete from database
			}
		   )
        else: #replying to a msg and this is the last
            response = dynamo_client.put_item(TableName= 'MessageDB',
		   Item={
			'messageID':{"N":messageID},
			'sender':{"S":sender},
			'reciever': {"S":reciever},
			'subject': {"S":subject},
			'msgbody':{"S":body},
			'convoID': {"N":convoID},
			'send_time': {"S":str(datetime.now().strftime('%H:%M:%S'))},
			'send_date':{"S":str(date.today().strftime("%B %d, %Y"))},
			'read_status':{"S":"unread"},
			'sender_loc':{"S":"sent_folder"}, #sent_folder, deleted (in trash), [tbd - draft]
			'reciever_loc':{"S":"inbox"}, #inbox (in inbox), deleted (in trash)
			'perm_del':{"S":"n"} #n = neither, r = reciever, s = sender, sr = delete from database
			}
		   )  
    except:
        return "COULD NOT INSERT."

@app.route('/newEmail', methods=['POST','GET'])
def newEmail():
    return render_template("newEmail.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           sender_username = session['username'],
                           errorMsg="",
                           reciever_username="",
                           subject = "",
                           email_body = "")

def countUnreadInInbox(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    scan_kwargs = {
        'FilterExpression': Key('reciever').eq(username)&Key('read_status').eq("unread")&Key('reciever_loc').eq("inbox"),
        'ProjectionExpression': "messageID"
    }
    
    done = False
    start_key = None

    msgList = []
    unreadNum = 0
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)     
        unreadNum=unreadNum+len(response['Items'])
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    if(unreadNum == 0):
        return ""
    else:
        return "("+str(unreadNum)+")"
##    dynamodb = boto3.resource('dynamodb')
##    table = dynamodb.Table('MessageDB')
##    response = table.scan()
##
##    unreadNum = 0
##    for i in response['Items']:
##        if(i['reciever']==username and i['read_status']=="unread" and i['reciever_loc']=="inbox"):
##            unreadNum = unreadNum +1
##    if(unreadNum == 0):
##        return ""
##    else:
##        return "("+str(unreadNum)+")"
    
    
def countUnreadInTrash(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    scan_kwargs = {
        'FilterExpression': Key('reciever').eq(username)&Key('read_status').eq("unread")&Key('reciever_loc').eq("trash"),
        'ProjectionExpression': "messageID"
    }
    
    done = False
    start_key = None

    msgList = []
    unreadNum = 0
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)     
        unreadNum=unreadNum+len(response['Items'])
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    if(unreadNum == 0):
        return ""
    else:
        return "("+str(unreadNum)+")"
##    dynamodb = boto3.resource('dynamodb')
##    table = dynamodb.Table('MessageDB')
##    response = table.scan()
##
##    unreadNum = 0
##    for i in response['Items']:
##        if i['read_status']=="unread" and (i['reciever']==session['username'] and i['reciever_loc']=="trash"):
##            unreadNum = unreadNum +1
##    if(unreadNum == 0):
##        return ""
##    else:
##        return "("+str(unreadNum)+")"

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

def markAsUnread(msgID):
    try:
        read_status='unread'   
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
        return "Successfully marked as unread."
    except ClientError as e:
        print(e.response['Error']['Message'])
        return "ERROR. Could not mark as unread."

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

    if perm_del == 'sr':
        response = dynamo_client.delete_item(TableName= 'MessageDB',
            Key={
                'messageID':{'N':msgID}
            }
            )
        return "successfully deleted from database"
    else:
        try:
            response = dynamo_client.update_item(TableName= 'MessageDB',
                Key={
                    'messageID': {"N":str(msgID)}
                },
                UpdateExpression="SET #perm_del = :p",
                ExpressionAttributeNames= {
                    '#perm_del' : 'perm_del'
                },
                ExpressionAttributeValues= {
                    ':p' : {'S':perm_del}
                },
                ReturnValues="UPDATED_NEW"
                )
            return "did not delete bc not perm"
        except ClientError as e:
            print(e.response['Error']['Message'])
            return "ERROR. Could not update permdel."
		

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


    
##def getAllTrashMessagesQuery(username):
##    dynamodb = boto3.resource('dynamodb')
##    table = dynamodb.Table('MessageDB')
##    scan_kwargs = { #.eq is ==, ????? is !=
##        'FilterExpression': (Key('reciever').eq(username)&Key('reciever_loc').eq("trash")&(!(Key('perm_del').eq('r'))& !(Key('perm_del').eq('sr'))))|(Key('sender').eq(username)&Key('sender_loc').eq("trash")&(!(Key('perm_del').eq('s'))& !(Key('perm_del').eq('sr')))),
##        'ProjectionExpression': "messageID, reciever, read_status,sender, send_date, subject"
##    }
##    
##    done = False
##    start_key = None
##
##    trashList = []
##    
##    while not done:
##        if start_key:
##            scan_kwargs['ExclusiveStartKey'] = start_key
##        response = table.scan(**scan_kwargs)
##        #trashList = [[i['messageID'],"*"+str(i['sender'])+"*",i['send_date'],i['subject']] if i['read_status']=='unread' else [i['messageID'],i['sender'],i['send_date'],i['subject']] for i in response['Items']]
##        for i in response['Items']:
##            if(i['reciever']==username and i['read_status']=='unread'):
##                trashList.append([i['messageID'],str("*"+str(i['sender'])+"*"),i['send_date'],i['subject']])
##            elif(i['sender']==username):
##                trashList.append([i['messageID'],str("To:"+str(i['reciever'])),i['send_date'],i['subject']])
##            else:
##                trashList.append([i['messageID'],i['sender'],i['send_date'],i['subject']])
##        
##        start_key = response.get('LastEvaluatedKey', None)
##        done = start_key is None
##
##    return trashList

def getAllTrashMessages(username):   
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    response = table.scan()
#TODO -- filter out messages that they have marked for permenant deletion
    trashList = []
    for i in response['Items']:
        dateWhole = str(i['send_date'] + " - " +i['send_time'])
        if (i['reciever']==username and i['reciever_loc']=='trash' and (i['perm_del']!='r' and i['perm_del']!='sr')) or (i['sender']==username and i['sender_loc']=='trash' and (i['perm_del']!='s' and i['perm_del']!='sr')):
            if(i['reciever']==username and i['read_status']=='unread'):
                trashList.append([dateWhole,i['messageID'],"",i['sender'],i['send_date'],i['subject'],True])
            elif(i['sender']==username):
                trashList.append([dateWhole, i['messageID'],"To:",i['reciever'],i['send_date'],i['subject'],False])
            else:
                trashList.append([dateWhole,i['messageID'],"",i['sender'],i['send_date'],i['subject'],False])


    trashList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
#if x do1
#elif y do 2
#else (z) do 3
#(_do 1_ if x else (_do 2_ if y else do 3) )

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


def getAllMessages(username, pageNum):
    #Limit, Select, ReturnConsumedCapacity, TotalSegments, Segment,
    #ScanFilter, ConditionalOperator, ExclusiveStartKey, TableName, IndexName, AttributesToGet, ProjectionExpression, FilterExpression, ExpressionAttributeNames, ExpressionAttributeValues, ConsistentRead
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    scan_kwargs = {
        'FilterExpression': Key('reciever').eq(username)&Key('reciever_loc').eq("inbox"),
        'ProjectionExpression': "messageID, read_status,sender,send_time, send_date, subject",
        'Segment': 5,
        'TotalSegments':1
    }
    
    done = False
    start_key = None

    msgList = []
    numPg = 0
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        print(numPg, response)
        numPg = numPg+1
        msgList = [[str(i['send_date'] + " - " +i['send_time']),i['messageID'],i['sender'],i['send_date'],i['subject'],True] if i['read_status']=='unread' else [str(i['send_date'] + " - " +i['send_time']),i['messageID'],i['sender'],i['send_date'],i['subject'],False] for i in response['Items']]
        
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))

    pageSize = 5
    return msgList[pageNum*pageSize:pageSize+(pageNum*pageSize)]
##    dynamodb = boto3.resource('dynamodb')
##    table = dynamodb.Table('MessageDB')
##    response = table.scan()
##
##    msgList = []
##    for i in response['Items']:
##        if i['reciever']==username and i['reciever_loc']=='inbox':
##            if(i['read_status']=='unread'):
##                msgList.append([i['messageID'],str("*"+str(i['sender'])+"*"),i['send_date'],i['subject']])
##            else:
##                msgList.append([i['messageID'],i['sender'],i['send_date'],i['subject']])
##
##    return msgList #make into class object later

def insertTest():
    for i in range(0,10):
        insertMessage("second_user", "first_user", "bt","rter", "0")





def getAllMessagesSent(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    scan_kwargs = {
        'FilterExpression': Key('sender').eq(username)&Key('sender_loc').eq("sent_folder"),
        'ProjectionExpression': "messageID, read_status,sender,send_time, send_date, subject"
    }
    
    done = False
    start_key = None

    msgList = []
    
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        msgList = [[ str(i['send_date'] + " - " +i['send_time']),i['messageID'],i['sender'],i['send_date'],i['subject']] for i in response['Items']]
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))

    return msgList
##
##    dynamodb = boto3.resource('dynamodb')
##    table = dynamodb.Table('MessageDB')
##    response = table.scan()
##
##    msgList = []
##    for i in response['Items']:
##        if i['sender']==username and i['sender_loc']=='sent_folder':
##            msgList.append([i['messageID'],i['reciever'],i['send_date'],i['subject']])
##                
##    
##    return msgList #make into class object later
##

def getAllMsgsInConvo(convoID):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('MessageDB')
    scan_kwargs = {
        'FilterExpression': Key('convoID').eq(int(convoID)),
        'ProjectionExpression': "messageID, sender,reciever,send_time,send_date, subject,msgbody"
    }
    
    done = False
    start_key = None

    convoList = []
    
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        for i in response['Items']:
            dateWhole = str(i['send_date'] + "   " +i['send_time'])
            convoList.append([dateWhole,
                             i['messageID'],
                               i['sender'],
                               i['reciever'],
                               i['subject'],
                               i['msgbody']])
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    convoList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y   %H:%M:%S"))
    return convoList #make into class object later

##    dynamodb = boto3.resource('dynamodb')
##    table = dynamodb.Table('MessageDB')
##    response = table.scan()
##    
##    convoList = []
##    for i in response['Items']:
##        if i['convoID']==int(convoID):
##            print("MATCH", i['messageID'])
##            dateWhole = str(i['send_time'] + " " +i['send_date'])
##            convoList.append([dateWhole,
##                               i['sender'],
##                               i['reciever'],
##                               i['subject'],
##                               i['msgbody']])
##                


def testSort():
    my_dates = [['05:30:25 25-Nov-18',"c"], ['05:31:09 25-Mar-17', "a"], ['05:30:25 25-Mar-17', "b"], ['05:30:25 7-Mar-18', "d"]]
    my_dates.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%H:%M:%S %d-%b-%y"))
    print(my_dates)


@app.route('/msg/<msgid>', methods=['POST','GET'])
def openMsg(msgid):
        response = dynamo_client.get_item(TableName= 'MessageDB',
            Key={
                'messageID': {"N":msgid}
            }
        )
        if(session['username']==response.get('Item').get('reciever').get('S')):
            markAsRead(msgid)
            #need to refresh the response item bc we update it to be read
            response = dynamo_client.get_item(TableName= 'MessageDB',
                Key={
                    'messageID': {"N":msgid}
                }
                )
        convoList=getAllMsgsInConvo(response.get('Item').get('convoID').get('N'))
        if(session['username']==response.get('Item').get('reciever').get('S') and response.get('Item').get('reciever_loc').get('S')=="inbox"):
            return render_template("msgInfo.html",
                                   inbox = True,sent = False,trashbox=False,
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                               headMsgID = response.get('Item').get('convoID').get('N'),
                               msgList=convoList,
                                   targetmId = str(msgid)
                               )
        elif(session['username']==response.get('Item').get('reciever').get('S') and response.get('Item').get('reciever_loc').get('S')=="trash") or (session['username']==response.get('Item').get('sender').get('S') and response.get('Item').get('sender_loc').get('S')=="trash"):
            return render_template("msgInfo.html",
                                   inbox = False,sent = False,trashbox=True,
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                               headMsgID = response.get('Item').get('convoID').get('N'),
                               msgList=convoList,
                                   targetmId = str(msgid)
                               )
        else:
            return render_template("msgInfo.html",
                                   inbox = False,sent = True,trashbox=False,
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                               headMsgID = response.get('Item').get('convoID').get('N'),
                               msgList=convoList,
                                   targetmId = str(msgid)
                               )
            

@app.route('/reply', methods=['POST','GET'])
def reply():
    convoID =request.form['headMsgID']
    response = dynamo_client.get_item(TableName= 'MessageDB',
            Key={
                'messageID': {"N":convoID}
            }
        )
    subj = ""
    if("re: " in response.get('Item').get('subject').get('S')):
        subj = response.get('Item').get('subject').get('S')
    else:
        subj = "re: "+response.get('Item').get('subject').get('S')
    print(subj)
    originalReciever = response.get('Item').get('reciever').get('S')
    originalSender = response.get('Item').get('sender').get('S')
    return render_template("replyEmail.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           headMsgID=convoID,
                           sender_username = session['username'],
                           reciever_username=(originalReciever if originalSender == session['username'] else originalSender),
                           subject = subj,
                           email_body = "")


    
    #get the sender from this to be the reciever of the reply
    #get current username to be sender
    #replying subject tack on a re:  (if one is not already on there)

@app.route('/inbox')
def openInbox():
    msgListObj = getAllMessages(session['username'])
    if(len(msgListObj)==0):
        return render_template("emptyInbox.html",
                           inboxUnread ="",
                           trashUnread = countUnreadInTrash(session['username'])
                           )
    else:
        return render_template("messageInbox.html",
                           inboxUnread =countUnreadInInbox(session['username']),
                           trashUnread = countUnreadInTrash(session['username']),
                           msgList=msgListObj)


@app.route('/u1')
def user1():
    session['username'] = "first_user"
    return openInbox()

@app.route('/u2')
def user2():
    session['username'] = "second_user"
    return openInbox()

@app.route('/u3')
def user3():
    session['username'] = "third_user"
    return openInbox()


@app.route('/')
def index():
    session['username']=""
    return render_template("messageHome.html")


# - DONE :) - make a front page with 2 buttons - 1 = log in as user1, 2 = log in as user2
    #(interact with each one's inbox/sent/trash/etc. separately)
#- DONE :) - trash (from inbox or sent) 1
#- DONE :) -make a "trash empty" change the username of whoever moved it to the trash so it does not show up in their scans any more
#- DONE :) -if both sender and reciever have permenantly deleted it, remove it from the database
#- DONE :) -make a top row with blank values with a check that checks all messages in that folder
#- DONE :) -make a limit to the size of the message and make that the max/fixed size of the textarea
#- DONE :) -put character limit on subject line
#- DONE :) -make a dynamically updating character count for subject line and body
#- DONE :) - mark read/unread 2
#- DONE :) - make an "empty trash" button
#- DONE :) - make messages clickable (extend for body and mark as read if unread)
#- DONE :) -make the whole msg bar the <a> click (not just subject)
#- DONE :) -make an inicator of the # of unread msgs in inbox or trash in nav label
#*- DONE :) -allow users to reply
#- DONE :) -make all checkbox implemented in js (no reloading the page)
#- DONE :) -make the select all checkboxes centered/correct (like inbox)

#*- DONE :) -convert scan+filter -> query (MUCH FASTER)
    #Note: the getAllTrashMessages(username) function has 2 inefficient parts that I left in bc they are too hard to replace
    #1 -> there is a 3 way if that turening into a ternary operator for the comprehensive list would be too hard
    #2 -> there is a scan+filter bc it uses not and or as parts of its query logic and python's aws does not support those??

#- DONE :) -figure out how to display a conversation aesthetcially (allow longer messages?)
#- DONE :) -move to inbox or sent from (from trash) 3
#   - DONE :) -Add the time and day
#FORMATTING TO FIX
#   - DONE :) -Fix positioning of the character counter (full screen)
#- DONE :) -change the styling of the new email page to match the msg info page
#- DONE :) -change styling of reply email page
#- DONE :) -order all folders by the time they were recieved/sent
#- DONE :) -message for if user has nothing in a folder
#- DONE :) -FIX PERMENANT DELETE (SMTG WITH BTN STATES??)
#- DONE :) -add unread # updates to unread trash/inbox on reply and new email pages
#- DONE :) -add time to the message in inbox line
#- DONE :) -conditional formatting for read/unread emails in inbox
    #- DONE :) -send the unread value in the message array for each item
    #- DONE :) -do the css for the conditional classes (and change styling for message class)
    #- DONE :) -replicate all in trash folder
#- DONE :) -when you open a message from the trash/sent, the active should shift to trash/sent instead of inbox
#*- DONE :) -when you click a message, have the first thing you see is that message (snap to that message in the convo)
#- DONE :) -fix whitespace in span (after To:)
#- DONE :) -change button/action words to icons
    #- DONE :) -do the deescription on hover
#*- DONE :) -make autocomplete for usernames (user cannot enter an invalid username)

#- DONE :) -in the sent folder, change the sender to who the recipient is

#WRITE QUERY FOR SELECTIVE RETURNS
    #when they are a patient user, the dropdown should only have doctors
    #when they are a doctor user, the dropdown should only be doctors/patients

#*--read up on if AWS can support paged queries (only query for items on that page?)


#eventually
#*--make pages for inbox




if __name__ == '__main__':
   app.secret_key = os.urandom(12)
   app.run(debug=True)
