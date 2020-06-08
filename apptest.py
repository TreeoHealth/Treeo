from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from flask import Flask, jsonify
import boto3
from boto3.dynamodb.conditions import Key, Attr
import aws_controller
from botocore.exceptions import ClientError
from zoomtest_post import createMtg, getMtgsFromUserID,getUserFromEmail,deleteMtgFromID

app = Flask(__name__)

dynamo_client = boto3.client('dynamodb')

@app.route('/get-items')
def get_items():
    return jsonify(aws_controller.get_items())

@app.route('/')
def home():
    if not (session.get('logged_in') or session.get('logged_in_a')):
        return render_template('login.html')
    elif session.get('logged_in'):
        return 'Hello Boss! <a href="/logout">Logout</a>'
    else:
        return 'Hello Boss!  <a href="/get-items">Get table</a> <a href="/logout">Logout</a>'

@app.route('/loginadmin', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in_a'] = True
    else:
        print('wrong password admin!')
    return home()

@app.route('/login', methods=['POST'])
def check_login():
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:4000")

    table = dynamodb.Table('YourTestTable')
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in_a'] = True
        session['logged_in'] = False
        return home()
    else:
        print('wrong password admin!')
    
    try:
        print('before')
        response = dynamo_client.get_item(TableName= 'YourTestTable',
            Key={
                'username': {"S":request.form['username']},
                'password': {"S":request.form['password']}
            }
        )
        print('after')
        session['logged_in'] = True
        session['logged_in_a'] = False
    except ClientError as e:
        print(e.response['Error']['Message'])
    return home()

@app.route('/registerrender', methods=['POST'])
def regPg():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def new_register():
    
#register new user
    response = dynamo_client.put_item(TableName= 'YourTestTable',
       Item={
            'username': {"S":request.form['username']},
            'password': {"S":request.form['password']}
        }
       )
    return home()

@app.route('/createrender', methods=['POST'])
def createPg():
    return render_template('create_mtg.html')

@app.route('/createmtg', methods=['POST'])
def create_mtg():
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00'
    jsonResp = createMtg(str(request.form['mtgname']), time,str(request.form['password']))

    finalStr = ""
    strTmp = "Meeting Title: "+str(jsonResp.get("topic"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting Time: "+str(jsonResp.get("start_time"))+" <br>"
    finalStr+=strTmp
    strTmp = "Join URL: "+str(jsonResp.get("join_url"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting ID: "+str(jsonResp.get("id"))+" <br>"
    finalStr+=strTmp
    finalStr = finalStr+"<a href='/'>Home</a><br>"
    
    return finalStr#jsonResp

@app.route('/showallmtgs', methods=['POST'])
def show_mtg():
    #jsonResp = getUserFromEmail('cq7614@gmail.com')#getMtgsFromUserID(78851018678);
    jsonResp = getMtgsFromUserID('HE1A37EjRIiGjh_wekf90A');
    #return jsonResp
#---------------- needs work below  vvvv
    #TODO how to make a button for each mtg that when pushed will delet the mtg by sending /deletemtg and the mtgID
    
    arrOfMtgs = []
    mtgList = jsonResp.get("meetings")
    finalStr = ""
    for item in mtgList:
        temp = []
        strTmp = "Meeting Title: "+str(item.get("topic"))+" <br>"
        temp.append(strTmp)
        finalStr+=strTmp
        strTmp = "Meeting Time: "+str(item.get("start_time"))+" <br>"
        temp.append(strTmp)
        finalStr+=strTmp
        strTmp = "Join URL: "+str(item.get("join_url"))+" <br>"
        temp.append(strTmp)
        finalStr+=strTmp
        strTmp = "Meeting ID: "+str(item.get("id"))+" <br>"
        temp.append(strTmp)
        finalStr+=strTmp
        arrOfMtgs.append(temp)
        finalStr = finalStr+"<a href='/'>Home</a><br>"
    #for each mtg, make an array of strs with host name, join URL, date and mtgID
    return finalStr #tuple(arrOfMtgs) --> wrong format (not sure how to format it to display but it can't be a list)

@app.route("/deleterender", methods=['POST'])
def deletePg():
    return render_template('delete.html')


#TODO!!! the delete goes through and removes the meeting correctly
#BUT it has an incorrect JSON response (regardless of wherther the data from the delete function is returned to the flask page or not.
#Need to figure out how to catch that, the below try except is not enough
@app.route("/deletemtg", methods=['POST'])
def deleteMtg():
    try:
        x=jsonResp.get("code")
        return "That is a bad meeting ID, please go back and try again<br><a href='/'>Home</a>"
#TODO!!! cannot link to any page that has a [POST] method, not sure how to make them able to be navigated to ? Nav bar?
    except:
        deleteMtgFromID(str(request.form['mtgID']))
        return "Successfully deleted meeting "+str(request.form['mtgID'])+"<br><a href='/'>Home</a>"

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['logged_in_a'] = False
    return home()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
