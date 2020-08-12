#search for patient users
#when the create mtg is called in zoomtest_post, make it call a function here
    #search for patient user to add to this appt by both name and username
    #insert an item into the appt table that has dr name (un), patient name (un), appt time/day, join url
#invite a user to an already created appt? make this a part of edit functionality
#query all appts involving a user by username (dr and patient)
#query user's name from username

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json

def returnAllPatients():
    #dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:4000")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')
    response = table.scan()
    #print( response)

    patientList = []
    for i in response['Items']:
        if i['docStatus']=="patient":
            patientList.append(i['username'])
    
    return patientList    

def getAcctFromUsername(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('apptsTable')
    response = table.scan()
    #print(response)
    response = dynamo_client.get_item(TableName= 'users',
            Key={
                'username': {"S":username}
            }
        )
    return response


#TODO improve this implementation (increase efficiency)
def getAllApptsFromUsername(username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('apptsTable')
    response = table.scan()
    #print(response)

    apptList = []
    for i in response['Items']:
        if i['doctor'] == username or i['patient']==username:
            apptList.append(i)
    return apptList

dynamo_client = boto3.client('dynamodb')

def getApptFromMtgId(mtgid):
    mtgid=str(mtgid)
    try:
        response = dynamo_client.get_item(TableName= 'apptsTable',
            Key={
                'mtgid': {"S":mtgid}
            }
        )
        return response
    except ClientError as e:
        print(e.response['Error']['Message'])


def createApptAWS(mtgName, mtgid, doctor, patient, start_time, joinURL):

    dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:4000")

    table = dynamodb.Table('YourTestTable')
    dError = True
    pError = True
    try:
        response = dynamo_client.get_item(TableName= 'users',
            Key={
                'username': {"S":doctor}
            }
        )
        isDoc=response.get('Item').get('docStatus').get('S')
        if isDoc!="doctor":
            return "The doctor username sent was not a doctor account."
        dError = False
        response = dynamo_client.get_item(TableName= 'users',
            Key={
                'username': {"S":patient}
            }
        )
        try:
            isPat=response.get('Item').get('docStatus').get('S')
        except:
            return "The patient username sent was not a patient account."
        pError = False
    except ClientError as e:
        print(e.response['Error']['Message'])
        if dError:
            print("INVALID DOCTOR NAME.")
            return "You are not valid to create a meeting."
        else:
            print("INVALID PATIENT NAME.")
            return "Error retrieving the account information for patient account."
    #if the doctor and patient are both valid
    
    response = dynamo_client.put_item(TableName= 'apptsTable',
       Item={
            'mtgName':{"S":mtgName},
            'mtgid':{'S':str(mtgid)},
            'doctor': {"S":doctor},
            'patient': {"S":patient},
            'start_time': {"S":start_time},
            'joinurl':{"S":joinURL}
        }
       )
    return "Successfully inserted the appt into the database."

def deleteApptAWS(mtgid):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('apptsTable')
    mtgID = str(mtgid)
    try:
        response = table.delete_item(TableName= 'apptsTable',
            Key={
                'mtgid': mtgID
            }
            )
        return "Successfully deleted the meeting."
    except ClientError as e:
        print(e.response['Error']['Message'])
        return "ERROR. Could not delete the meeting."

def updateApptAWS(mtgName, mtgid,start_time): #dr, pat and joinurl will not change
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('apptsTable')
    try:
        response = table.update_item(
            Key={
                'mtgid': mtgid
            },
            UpdateExpression="set info.mtgName=:m, info.start_time=:s",
            ExpressionAttributeValues={
                ':m': mtgName,
                ':s': start_time
            },
            ReturnValues="UPDATED_NEW"
        )
        return "Successfully updated the appt in the database."
    except ClientError as e:
        print(e.response['Error']['Message'])
        return "ERROR. Could not update the meeting."
    

##print(createApptAWS('test','72261254435',"doc","pat", "2020-06-30T12:30:00Z",'https://us04web.zoom.us/j/72892071916?pwd=V2hHcUphUlBlZG5iQlN1YmQ4R3BZUT09'))
##print(getAllApptsFromUsername("doc"))
##returnAllPatients()
##print(deleteApptAWS(79347554325))
##print(getApptFromMtgId(74286081472))
##print(getAcctFromUsername('patient1'))
