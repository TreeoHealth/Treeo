from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from flask import Flask, jsonify
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import aws_controller
from botocore.exceptions import ClientError
from zoomtest_post import updateMtg,createMtg,getMtgFromMtgID, getMtgsFromUserID,getUserFromEmail,deleteMtgFromID

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
        return 'Hello '+str(session['zoomID'])+' '+str(session['username'])+'<br><a href="/showallmtgs">Calendar</a><br> <a href="/logout">Logout</a> '
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
        response = dynamo_client.get_item(TableName= 'YourTestTable',
            Key={
                'username': {"S":request.form['username']},
                'password': {"S":request.form['password']}
            }
        )
        formEmail = response.get('Item').get('email').get('S')
        session['logged_in'] = True
        session['username'] = request.form['username']
        session['zoomID'] = getUserFromEmail(str(formEmail)).get('id')
        session['logged_in_a'] = False
    except ClientError as e:
        print(e.response['Error']['Message'])
    return home()

@app.route('/registerrender', methods=['POST','GET'])
def regPg():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def new_register():
    
#register new user
    response = dynamo_client.put_item(TableName= 'YourTestTable',
       Item={
            'username': {"S":request.form['username']},
            'password': {"S":request.form['password']},
            'email': {"S":request.form['email']},
            'name':{"S":request.form['name']}
        }
       )
    #TODO figure out how to display an error message while they're entering the form data
    try:
        formEmail = request.form['email']
        emailAdd = getUserFromEmail(str(formEmail)).get('id')
        if(emailAdd==None):
            raise
        session['zoomID']=emailAdd
        session['logged_in'] = True
        session['username'] = request.form['username']
    except:
        print("invalid zoom email!")
        return regPg()
    return home()

#things to implement
###session constant of username and zoom-affiliated email
###validation of zoom acct on creation
###change all of this to the info of the logged in user, not hard coded userid
###add a nav bar
###make calendar, and meeting create/delete behind the login wall
###once the user logs in, make a home page
###form integration
###meeting -- update

###how to invite a user to the meeting who doesn't own it
###how to make sub users under the main admin acct -- are they in the secret/encrypted in the JWT key??
#####will the same key have the ability to query all of the sub users+CRUD their meetings?
###TODO -- how to get the meetings that the patients have been invited to without them being owners of the JWT app/not being encrypted in the key?

##TODO -- radio buttons for recurring meetings (how to line up recurring mtgs)
##how to fill in a form with already existing mtg info for meeting info to be updated


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
    
    return finalStr

@app.route('/data')
def return_data():
#TODO --- eventually we are going to need to get the userID from WHO IS LOGGED IN
    jsonResp = getMtgsFromUserID('HE1A37EjRIiGjh_wekf90A');
    arrOfMtgs = []
    #[{ "title": "Meeting",
    #"start": "2014-09-12T10:30:00-05:00",
    #"end": "2014-09-12T12:30:00-05:00",
    #"url":"absolute or relative?"},{...}]
    
    mtgList = jsonResp.get("meetings")
    finalStr = ""
    for item in mtgList:
        time = str(item.get("start_time"))
        mtgid = str(item.get("id"))
        time = time[:-1]
        end_time = ((int(time[11:13])+1)%24)
        strend = time[:11]+str(end_time)+time[13:]
        mtgObj = {"title":str(item.get("topic")), "start": time, "end":strend, "url":("/showmtgdetail/"+mtgid)}
        arrOfMtgs.append(mtgObj)
    #BADDDD (change this)
    with open('appts.json', 'w') as outfile:
        json.dump(arrOfMtgs, outfile)
    with open('appts.json', "r") as input_data:
        return input_data.read()    


#
@app.route('/showmtgdetail/<mtgid>', methods=['POST','GET'])
def show_mtgdetail(mtgid):     # TODO ---(make this calendar) Or when the calendar is clicked, have it call the show mtgs and format each mtg to show up correctly
    jsonResp = getMtgFromMtgID(str(mtgid))
    finalStr = ""
    strTmp = "Meeting Title: "+str(jsonResp.get("topic"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting Time: "+str(jsonResp.get("start_time"))+" <br>"
    finalStr+=strTmp
    strTmp = "Join URL: "+str(jsonResp.get("join_url"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting ID: "+mtgid+" <br>"
    finalStr+=strTmp
    finalStr = finalStr+"<a href='/deleterender/"+mtgid+"'>Delete</a><br><a href='/'>Home</a><br><a href='/editrender/"+mtgid+"'>Edit</a><br><br>"

    return finalStr

@app.route("/editrender/<mtgid>", methods=['POST','GET'])
def editPgFromID(mtgid):
    jsonResp = getMtgFromMtgID(str(mtgid))
    #mtgname, pword, mtgtime, mtgdate
    time=str(jsonResp.get("start_time"))
    #split and display
    date=time[:10]
    
    return render_template('edit.html',
                           mtgnum=mtgid,
                           mtgname=str(jsonResp.get("topic")),
                           pword=str(jsonResp.get("password")),
                           mtgtime=str(time[11:-1]),
                           mtgdate=str(date))

@app.route("/editmtg", methods=['POST','GET'])
def editSubmit():
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00'
    jsonResp = updateMtg(str(request.form['mtgnum']),str(request.form['mtgname']), time,str(request.form['password']))

    finalStr = "UPDATED MTG "+str(request.form['mtgnum'])+"<br>"
    strTmp = "Meeting Title: "+str(jsonResp.get("topic"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting Time: "+str(jsonResp.get("start_time"))+" <br>"
    finalStr+=strTmp
    strTmp = "Join URL: "+str(jsonResp.get("join_url"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting ID: "+str(jsonResp.get("id"))+" <br>"
    finalStr+=strTmp
    finalStr = finalStr+"<a href='/'>Home</a><br>"
    
    return finalStr

    



    
#TODO ---> delete is a little unreliable?
    #It said it was deleted but it was still on the schedule??

#TODO -- FIX TIME ZONE MANAGEMENT (it is registering all time stamps as 4hrs in the future)
    #even the time creation is wrong but it is still seeing the time zone as EST so ??????
#TODO -- make a link in each entry to an EDITABLE/EXTENDED appt description
    #in this area, make a button for each mtg that when pushed will delet the mtg by sending /deletemtg and the mtgID
#*****************************************************************************************
@app.route('/showallmtgs', methods=['POST','GET'])
def show_mtg():     # TODO ---(make this calendar) Or when the calendar is clicked, have it call the show mtgs and format each mtg to show up correctly
    return render_template("calendar.html")

#This is what is needed to be able to link to this page
#make a get method a part of the route
@app.route("/deleterender", methods=['POST','GET'])
def deletePg():
    #if ???:
    #(if it came from the showallmtgs list instead of the home page, expect a mtg # along with it)
        #return render_template('delete.html', mtg=str(???))
    #else:
    return render_template('delete.html', mtg="")

#This will render the delete with the mtgID in the box filled in already
#doesn't work currently
@app.route("/deleterender/<mtgid>", methods=['POST','GET'])
def deletePgFromID(mtgid):
    return render_template('delete.html', mtg=str(mtgid))

#TODO -- make a function+page that allows you to view/edit specific mtg details?
#TODO -- figure out why the info transfers to the other page but the mtgID is not seen as valid?? ALL deletions are not working??
#     -- fix the "blank" render (no 'placeholder' in the box)

#TODOOOOOO (again) the delete goes through? but doesn't go through?
@app.route("/deletemtg", methods=['POST'])
def deleteMtg():
    jsonResp = getMtgFromMtgID(str(request.form['mtgID']))
    try:
        x=jsonResp.get("start_time")
        print(deleteMtgFromID(str(request.form['mtgID'])))
        return "Successfully deleted meeting "+str(request.form['mtgID'])+"<br><a href='/showallmtgs'>Calendar</a>"
#DONE cannot link to any page that has a [POST] method, not sure how to make them able to be navigated to ? Nav bar?
    except:
        return "That is a bad meeting ID, please go back and try again<br><a href='/deleterender/"+str(request.form['mtgID'])+"'>Delete</a>"
        

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['logged_in_a'] = False
    return home()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
