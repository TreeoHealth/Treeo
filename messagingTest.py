from flask import Flask, render_template, request
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import datetime
from datetime import date, datetime,timezone

app = Flask(__name__)
dynamo_client = boto3.client('dynamodb')


def insertMessage(sender, reciever, body):
    
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
            'msgbody':{"S":body},
            'send_time': {"S":str(datetime.now().strftime('%H:%M:%S'))},
            'send_date':{"S":str(date.today().strftime("%B %d, %Y"))},
            'read_status':{"S":"unread"}
            }
           )
    except:
        return


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

def getAllUnreadMessages(username):
    return

def getAllMessages(username):
    return

def getAllMessagesSent(username):
    return

def openInbox(username):
    return render_template()


@app.route('/')
def index():
    return render_template("messageInbox.html")

if __name__ == '__main__':
    app.run(debug=True)
