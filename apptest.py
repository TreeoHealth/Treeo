from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from flask import Flask, jsonify
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import aws_controller
from botocore.exceptions import ClientError
import aws_appt
import zoomtest_post
#from aws_appt import getAllApptsFromUsername, returnAllPatients, getAcctFromUsername
#from zoomtest_post import updateMtg,createMtg,getMtgFromMtgID, getMtgsFromUserID,getUserFromEmail,deleteMtgFromID

app = Flask(__name__)

dynamo_client = boto3.client('dynamodb')

@app.route('/get-items')
def get_items():
    return jsonify(aws_controller.get_items())

@app.route('/')
def home():
    #opItem = [{'name':'a'}, {'name':'b'},{'name':'c'},{'name':'d'}]
    #return render_template('picture.html', options=opItem)
    if not (session.get('logged_in_p') or session.get('logged_in_d')):
        return render_template('login.html', errorMsg="")
    else:
        return displayLoggedInHome()

@app.route('/homepage')
def displayLoggedInHome():
    if(session.get('logged_in_d')):
        docStatus = 'doctor'
        return render_template('homePageDr.html',docStat = docStatus,name=session['name'])
    else:
        docStatus = 'patient'
        return render_template('homePage.html',docStat = docStatus,name=session['name'])

        #name of logged in person printed
        #doctor/patient

@app.route('/login', methods=['POST','GET'])
def check_login():
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:4000")

    table = dynamodb.Table('YourTestTable')

    try:
        response = dynamo_client.get_item(TableName= 'users',
            Key={
                'username': {"S":request.form['username']}                
            }
        )
        #print(response)
        try:
            test = response.get('Item').get('password')
        except:
            return render_template('login.html', errorMsg="Incorrect username or password.")
        if response.get('Item').get('password').get('S')!= request.form['password']:
            print("WRONG PASSWORD")
            return render_template('login.html', errorMsg="Incorrect username or password.")
            #return home()
        formEmail = response.get('Item').get('email').get('S')
        docStatus = str(response.get('Item').get('docStatus').get('S'))
        if(docStatus=='doctor'):
            session['logged_in_d']=True
            session['logged_in_p']=False
        else:
            session['logged_in_p'] = True
            session['logged_in_d']=False
        session['username'] = request.form['username']
        session['name'] = str(response.get('Item').get('name').get('S'))
    except ClientError as e:
        print(e.response['Error']['Message'])
    return home()

@app.route('/registerrender', methods=['POST','GET'])
def regPg():
    return render_template('register.html')

@app.route('/register', methods=['POST','GET'])
def new_register():
    response = dynamo_client.get_item(TableName= 'users',
        Key={
            'username': {"S":request.form['username']}                
        }
    )
    try:
        test = response.get('Item').get('password')
        return render_template('register.html', errorMsg="Username is already taken. Please use a different one.")
    except:
#register new user
        response = dynamo_client.put_item(TableName= 'users',
           Item={
                'username': {"S":request.form['username']},
                'password': {"S":request.form['password']},
                'email': {"S":request.form['email']},
                'name':{"S":request.form['name']},
                'docStatus':{"S":request.form['docStatus']}
            }
           )

        try:
            formEmail = request.form['email']
            if(request.form['docStatus']=='doctor'):
                session['logged_in_d']=True
                session['logged_in_p']=False
            else:
                session['logged_in_p'] = True
                session['logged_in_d']=False
            session['username'] = request.form['username']
            session['name'] = request.form['name']
        except:
            print("invalid zoom email!")
            return regPg()
        return displayLoggedInHome()
#note: relad page appears to wipe session values???

def accessDenied():
    return render_template('accessDenied.html')

@app.route('/createrender', methods=['POST','GET'])
def createPg():
##    if session['logged_in_p']:
##        return accessDenied()
    return render_template('create_mtg.html')

@app.route('/createmtg', methods=['POST','GET'])
def create_mtg():
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00Z'
    jsonResp, awsResp = zoomtest_post.createMtg(str(request.form['mtgname']), time,str(request.form['password']),session['username'], request.form['patientUser'])
    date=time[:10]
    finalStr = ""
    if awsResp!="Successfully inserted the appt into the database.":
        finalStr="ERROR CREATING APPOINTMENT. "+awsResp
#ADD PATIENT FIELD
    
    else:
        return render_template('apptDetail.html',
                               mtgnum=str(jsonResp.get("id")),
                               doctor =session['username'],
                               patient = request.form['patientUser'],
                               mtgname=str(jsonResp.get("topic")),
                               mtgtime=str(time[11:-1]),
                               mtgdate=str(date))
    ##Make a patient and doctor field *********
    ##make a joinURL field on this AND the mtg detail page
##        strTmp = "Meeting Title: "+str(jsonResp.get("topic"))+" <br>"
##        finalStr+=strTmp
##        strTmp = "Meeting Time: "+str(jsonResp.get("start_time"))+" <br>"
##        finalStr+=strTmp
##        strTmp = "Patient Username: "+str(request.form['patientUser'])+" <br>"
##        finalStr+=strTmp
##        strTmp = "Join URL: "+str(jsonResp.get("join_url"))+" <br>"
##        finalStr+=strTmp
##        strTmp = "Meeting ID: "+str(jsonResp.get("id"))+" <br>"
##        finalStr+=strTmp
##        finalStr = finalStr+"<a href="+"'{{ url_for("+"show_mtg"+"') }}'"+" class='btn btn-primary btn-large btn-block'>Calendar</a><br><a href='"+"{{ url_for('"+"home') }}'"+">Home</a>"
##    
##    return finalStr

@app.route('/data')
def return_data():
    #***********************

    #jsonResp = getMtgsFromUserID('HE1A37EjRIiGjh_wekf90A');
    arrOfMtgs =aws_appt.getAllApptsFromUsername(session['username'])
    #[{ "title": "Meeting",
    #"start": "2014-09-12T10:30:00-05:00",
    #"end": "2014-09-12T12:30:00-05:00",
    #"url":"absolute or relative?"},{...}]
    
    mtgList = []#mtgList = jsonResp.get("meetings")
    finalStr = ""
    for item in arrOfMtgs:
        time = str(item.get("start_time"))
        mtgid = str(item.get("mtgid"))
        time = time[:-1]
        end_time = int(float(time[11:13]))+1
        strend = time[:11]+str(end_time)+time[13:]
        mtgObj = {"title":str(item.get("mtgName")), "start": time, "end":strend, "url":("/showmtgdetail/"+mtgid)}
        mtgList.append(mtgObj)
    #BADDDD (change this)
    with open('appts.json', 'w') as outfile:
        json.dump(mtgList, outfile)
    with open('appts.json', "r") as input_data:
        return input_data.read()    


#
@app.route('/showmtgdetail/<mtgid>', methods=['POST','GET'])
def show_mtgdetail(mtgid):     # TODO ---(make this calendar) Or when the calendar is clicked, have it call the show mtgs and format each mtg to show up correctly
    jsonResp,awsResp = zoomtest_post.getMtgFromMtgID(str(mtgid))
##    finalStr = ""
##    strTmp = "Meeting Title: "+str(jsonResp.get("topic"))+" <br>"
##    finalStr+=strTmp
##    strTmp = "Meeting Time: "+str(jsonResp.get("start_time"))+" <br>"
##    finalStr+=strTmp
##    strTmp = "Join URL: "+str(jsonResp.get("join_url"))+" <br>"
##    finalStr+=strTmp
##    strTmp = "Meeting ID: "+mtgid+" <br>"
##    finalStr+=strTmp
    #finalStr = finalStr+"<a href='/deleterender/"+mtgid+"'>Delete</a><br><a href='"+"{{ url_for('"+"home') }}'"+"class='btn btn-primary btn-large btn-block'>Home</a><br><a href='/editrender/"+mtgid+"'>Edit</a><br><br>"
    time=str(jsonResp.get("start_time"))
    #split and display
    date=time[:10]
    docUser = awsResp.get('Item').get('doctor').get('S')
    patUser = awsResp.get('Item').get('patient').get('S')
    if(session.get('logged_in_p')):
        return render_template('apptDetail.html',
                               mtgnum=mtgid,
                               doctor=docUser,
                               patient = session['username'],
                               mtgname=str(jsonResp.get("topic")),
                               mtgtime=str(time[11:-1]),
                               mtgdate=str(date))
    elif(session.get('logged_in_d')):
        return render_template('apptDetailDrOptions.html',
                       mtgnum=mtgid,
                       doctor =docUser,#session['username'],
                       patient = patUser,#request.form['patientUser'],
                       mtgname=str(jsonResp.get("topic")),
                       mtgtime=str(time[11:-1]),
                       mtgdate=str(date))
    #return finalStr

@app.route("/editrender/", methods=['POST','GET'])
def editPgFromID():
    mtgid = str(request.form['mtgnum'])
    if session['logged_in_p']:
        return accessDenied()
    jsonResp = zoomtest_post.getMtgFromMtgID(str(mtgid))
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

##@app.route("/editrender/<mtgid>", methods=['POST','GET'])
##def editPgFromID(mtgid):
##    if session['logged_in_p']:
##        return accessDenied()
##    jsonResp = getMtgFromMtgID(str(mtgid))
##    #mtgname, pword, mtgtime, mtgdate
##    time=str(jsonResp.get("start_time"))
##    #split and display
##    date=time[:10]
##
##
##    return render_template('edit.html',
##                           mtgnum=mtgid,
##                           mtgname=str(jsonResp.get("topic")),
##                           pword=str(jsonResp.get("password")),
##                           mtgtime=str(time[11:-1]),
##                           mtgdate=str(date))


@app.route("/editmtg", methods=['POST','GET'])
def editSubmit():
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00Z'
    print(str(request.form['mtgnum']),str(request.form['mtgname']), time,str(request.form['password']))
    jsonResp = zoomtest_post.updateMtg(str(request.form['mtgnum']),str(request.form['mtgname']), time,str(request.form['password']))

    finalStr = "UPDATED MTG "+str(request.form['mtgnum'])+"<br>"
    strTmp = "Meeting Title: "+str(jsonResp.get("topic"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting Time: "+str(jsonResp.get("start_time"))+" <br>"
    finalStr+=strTmp
    strTmp = "Join URL: "+str(jsonResp.get("join_url"))+" <br>"
    finalStr+=strTmp
    strTmp = "Meeting ID: "+str(jsonResp.get("id"))+" <br>"
    finalStr+=strTmp
    finalStr = finalStr+"<a href='/'>Home</a><br><a href='/showallmtgs'>Calendar</a>"
    
    return finalStr

@app.route('/acctdetails', methods=['POST','GET'])
def acct_details():     
    return "Account Details"

@app.route('/patients/<username>', methods=['POST','GET'])
def patientAcct(username):
    response = aws_appt.getAcctFromUsername(str(username))
    return render_template('patientAcctDetails.html', 
                           username=username,
                           docstatus=response.get('Item').get('docStatus').get('S'),
                           nm=response.get('Item').get('name').get('S'),
                           email=response.get('Item').get('email').get('S')
                           )

@app.route('/patients', methods=['POST','GET'])
def list_patients():
    #opItem = [{'name':'a'}, {'name':'b'},{'name':'c'},{'name':'d'}]
    listStr = aws_appt.returnAllPatients()
    return render_template('picture.html', options=listStr)
    
    x=""
    for i in listStr:
        x = x+i+"<br>"
    return x

@app.route('/showallmtgs', methods=['POST','GET'])
def show_mtg():     
    return render_template("calendar.html")

#This is what is needed to be able to link to this page
#make a get method a part of the route
@app.route("/deleterender", methods=['POST','GET'])
def deletePg():
    if session['logged_in_p']:
        return accessDenied()
    return render_template('delete.html', mtg="")

@app.route("/deleteRenderNum/", methods=['POST','GET'])
def deletePgNum():
    if session['logged_in_p']:
        return accessDenied()
    mtgid = str(request.form['mtgnum'])
    return render_template('delete.html', mtg=mtgid)


@app.route("/deletemtg", methods=['POST','GET'])
def deleteMtg():
    if session['logged_in_p']:
        return accessDenied()
    jsonResp = zoomtest_post.getMtgFromMtgID(str(request.form['mtgID']))
    try:
        x=jsonResp.get("start_time")
        print(zoomtest_post.deleteMtgFromID(str(request.form['mtgID'])))
        return "Successfully deleted meeting "+str(request.form['mtgID'])+"<br><a href='/showallmtgs'>Calendar</a>"
    except:
        return "That is a bad meeting ID, please go back and try again<br><a href='/deleterender'>Delete</a>"
        

@app.route("/logout", methods=['POST','GET'])
def logout():
    session['logged_in_p'] = False
    session['logged_in_d'] = False
    return home()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
