
from flask import Flask, flash, redirect, render_template, request, session, abort,jsonify
import os
import json
import re
from datetime import date, datetime,timezone
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
import password_strength
from password_strength import PasswordPolicy
from passlib.context import CryptContext
import mysql.connector

import mySQL_apptDB
import mySQL_userDB
import mySQL_adminDB
from classFile import adminUserClass, apptObjectClass, patientUserClass, doctorUserClass
import zoomtest_post


app = Flask(__name__)
patientPages = []
currPg=0

config = {
  'host':'treeo-server.mysql.database.azure.com',
  'user':'treeo_master@treeo-server',
  'password':'Password1',
  'database':'treeohealthdb'
}
cnx = mysql.connector.connect(**config)

#NOTE: NEED 2 cursors for nested queries!!!
cursor = cnx.cursor(buffered=True)
cursor.execute("USE treeoHealthDB")
tmpcursor = cnx.cursor(buffered=True) #THIS IS TO FIX "Unread result found error"
tmpcursor.execute("USE treeoHealthDB")

takenUsernames = mySQL_userDB.returnAllTakenUsernames(cursor, cnx)
patientList = mySQL_userDB.searchPatientList(cursor, cnx)

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )


@app.route('/')
def home():
    if not (session.get('logged_in_p') or session.get('logged_in_d') or session.get('logged_in_a')):
        return render_template('login.html', errorMsg="")
    else:
        return displayLoggedInHome()

@app.route('/homepage')
def displayLoggedInHome():
    if(session.get('logged_in_d')):
        docStatus = 'doctor'
        return render_template('homePageDr.html',
                               docStat = docStatus,
                               docType= mySQL_userDB.getDrTypeOfAcct(session['username'], cursor, cnx),
                               name=session['name'])
    elif(session.get('logged_in_a')):
        return displayAdminHome()
    else:
        docStatus = 'patient'
        return render_template('homePage.html',docStat = docStatus,name=session['name'])

        #name of logged in person printed
        #doctor/patient

@app.route('/login', methods=['POST','GET'])
def check_login():
    if(request.form['username'] in mySQL_adminDB.getAllAdminUsers(cursor,cnx)):
        result = mySQL_adminDB.verifyAdminLogin(request.form['username'], request.form['password'],cursor, cnx)
        if(result==False):
            print("WRONG PASSWORD ADMIN")
            return render_template('login.html', errorMsg="Incorrect username or password.")
        else:
            acct_info = mySQL_userDB.getAcctFromUsername(request.form['username'],cursor, cnx)
            session['logged_in_a']=True
            session['logged_in_p']=False
            session['logged_in_d']=False
            session['username'] = request.form['username']
            session['name'] = acct_info.fname+" "+acct_info.lname
            return displayAdminHome()
    result = mySQL_userDB.checkUserLogin(request.form['username'], request.form['password'],cursor, cnx)
    
    if(result==False):
        print("WRONG PASSWORD")
        return render_template('login.html', errorMsg="Incorrect username or password.")
    else:
        acct_info = mySQL_userDB.getAcctFromUsername(request.form['username'],cursor, cnx)
        if(type(acct_info)==doctorUserClass):
            if(request.form['username'] in mySQL_userDB.getAllUnapprovedDrs(cursor, cnx)):
                return render_template('login.html', errorMsg="You have not been verified. Check your email for updates.")
            session['logged_in_d']=True
            session['logged_in_p']=False
            session['logged_in_a']=False
        else:
            session['logged_in_p'] = True
            session['logged_in_d']=False
            session['logged_in_a']=False
        session['username'] = request.form['username']
        session['name'] = acct_info.fname+" "+acct_info.lname
        return displayLoggedInHome()

def displayAdminHome():
    return render_template('adminHome.html',
                           name = session['name'])
    
@app.route('/unassigned', methods=['POST','GET'])
def adminListUnassigned():
    listPat = mySQL_userDB.getAllUnassignedPatients(cursor, cnx)
    if(len(listPat)==0):
        return render_template("emptyUnassignedList.html")
    else:
        return render_template("unassignedList.html",
                           options = listPat)
        
@app.route('/unapproved', methods=['POST','GET'])
def adminListUnapproved():
    listPat = mySQL_userDB.getAllUnapprovedDrs(cursor, cnx)
    if(len(listPat)==0):
        return render_template("emptyUnapprovedList.html")
    else:
        return render_template("unapprovedList.html",
                           options = listPat)
        
@app.route('/approved', methods=['POST','GET'])
def adminListApproved():
    listPat = mySQL_userDB.getAllApprovedDrs(cursor, cnx)
    if(len(listPat)==0):
        return render_template("emptyApprovedList.html")
    else:
        return render_template("approvedList.html",
                           options = listPat)

#/assign/{{item}}
@app.route('/assign/<username>', methods=['POST','GET'])
def assignForm(username):
    return render_template("assignCareTeam.html",
                           username  = username)
    


@app.route('/approve/<username>', methods=['POST','GET'])
def approveForm(username):
    mySQL_userDB.verifyDoctor(username, cursor, cnx)
    drAcctName = mySQL_userDB.getNameFromUsername(username, cursor, cnx)
    emailBody = "Hello "+drAcctName+",\r\nWelcome to Treeo!\r\nYou are now approved as a care provider!\r\n\r\nWelcome to the team! Let us know if you have any questions.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(username,"Treeo Approval - Welcome",emailBody) 
    emailBody = "Hello "+session['name']+",\r\nYou have approved "+drAcctName+ " (" +username+") as a care provider. If this was a mistake, please remedy immediately.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(session['username'],"Provider Approved",emailBody) 
    return render_template("approveConfirmation.html",
                           drname  = str(username + " - " +drAcctName))

@app.route('/removeapproval/<username>', methods=['POST','GET'])
def unapproveForm(username):
    mySQL_userDB.unverifyDoctor(username, cursor, cnx)
    drAcctName = mySQL_userDB.getNameFromUsername(username, cursor, cnx)
    emailBody = "Hello "+drAcctName+",\r\You have been suspended from being a care provider temporarily.\r\n\r\nLet us know if you have any questions.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(username,"Provider Account Suspended",emailBody) 
    emailBody = "Hello "+session['name']+",\r\nYou have removed provider approval for "+drAcctName+ " (" +username+"). If this was a mistake, please remedy immediately.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(session['username'],"Provider Approval Revoked",emailBody) 
    return render_template("unapproveConfirmation.html",
                           drname  = str(username + " - " +drAcctName))



@app.route('/assignCareTeam', methods=['POST','GET'])
def assignTeam(): #submit update form
    dr1 = request.form['dietician'].split(" - ")[0]
    dr2 = request.form['physician'].split(" - ")[0]
    dr3 = request.form['healthcoach'].split(" - ")[0]
    if(mySQL_userDB.isDrDietician(dr1, cursor, cnx)==False):
        return render_template("assignCareTeam.html",
                            errorMsg = "Invalid dietician user.",
                           username  = request.form['username'],
                           dietician = dr1,
                           physician = dr2,
                           healthcoach=dr3)
    elif(mySQL_userDB.isDrPhysician(dr2, cursor, cnx)==False):
        return render_template("assignCareTeam.html",
                            errorMsg = "Invalid physician user.",
                           username  = request.form['username'],
                           dietician = dr1,
                           physician = dr2,
                           healthcoach=dr3)
    elif mySQL_userDB.isDrHealthCoach(dr3, cursor, cnx)==False:
        return render_template("assignCareTeam.html",
                            errorMsg = "Invalid health coach user.",
                           username  = request.form['username'],
                           dietician = dr1,
                           physician = dr2,
                           healthcoach=dr3)     
    else:
        mySQL_userDB.assignPatientCareTeam(request.form['username'], dr1, dr2, dr3, cursor, cnx) 
        emailBody = "Hello,\r\nYou have been assigned a care team.\r\n\r\n\tDietician: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(dr1,cursor, cnx)+" ("+dr1+")\r\n\tPhysician: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(dr2,cursor, cnx)+" ("+dr2+")\r\n\tHealth Coach: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(dr3,cursor, cnx)+" ("+dr3+")\r\n"
        emailBody = emailBody+"\r\nPlease reach out with any questions or concerns.\r\nSincerely,\r\n    Your Treeo Team"
        sendAutomatedAcctMsg(request.form['username'],"Care Team Assignment",emailBody) 
        
        emailBody = "Hello,\r\nYou have been assigned to a patient: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(request.form['username'],cursor, cnx)+" ("+request.form['username'] +")\r\n Here is your team:\r\n\r\n\tDietician: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(dr1,cursor, cnx)+" ("+dr1+")\r\n\tPhysician: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(dr2,cursor, cnx)+" ("+dr2+")\r\n\tHealth Coach: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(dr3,cursor, cnx)+" ("+dr3+")\r\n"
        emailBody =emailBody+"\r\nPlease reach out with any questions or concerns.\r\nSincerely,\r\n    Your Treeo Admins"
        sendAutomatedAcctMsg(dr1,"Care Team Assignment",emailBody) 
        sendAutomatedAcctMsg(dr2,"Care Team Assignment",emailBody) 
        sendAutomatedAcctMsg(dr3,"Care Team Assignment",emailBody) 
        return patientAcct(request.form['username'])


@app.route("/dieticianList")
def dAutocomplete():
   jsonSuggest = []
   query = request.args.get('query')
   listDr=mySQL_userDB.getAllDrDietician(cursor, cnx)
   for username in listDr:
       if(query.lower() in username.lower()):
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})

@app.route("/physicianList")
def pAutocomplete():
   jsonSuggest = []
   query = request.args.get('query')
   listDr=mySQL_userDB.getAllDrPhysician(cursor, cnx)
   for username in listDr:
       if(query.lower() in username.lower()):
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})

@app.route("/healthcoachList")
def hcAutocomplete():
   jsonSuggest = []
   query = request.args.get('query')
   listDr=mySQL_userDB.getAllDrHealth(cursor, cnx)
   for username in listDr:
       if(query.lower() in username.lower()):
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})

@app.route('/renderNewAdmin', methods=['POST','GET'])
def createAdminPg():
    return render_template('createAdminAcct.html')

@app.route('/registerNewAdmin', methods=['POST','GET'])
def createNewAdmin():
    reply = mySQL_adminDB.createAdminUser(request.form['username'], 
                            request.form['password'], 
                            request.form['fname'], 
                            request.form['lname'], 
                            cursor, cnx)
    if(reply=="success"):
        return render_template('adminHome.html',
                               name = session['name'],
                               confirmMsg="CREATED new admin account successfully")
    else:
        if reply=="weak password":
            return render_template('createAdminAcct.html',
                                   errorMsg="Password must be min length 8, 1 upper case, and 1 number.",
                                    username = request.form['username'],
                                   password = request.form['password'],
                                   fname = request.form['fname'],
                                   lname = request.form['lname']
                                   )
        else:
            return render_template('createAdminAcct.html',
                                   errorMsg="Username taken. TRY AGAIN.",
                                   username = request.form['username'],
                                   password = request.form['password'],
                                   fname = request.form['fname'],
                                   lname = request.form['lname']
                                   )
        
    return
    


@app.route('/registerrender', methods=['POST','GET'])
def regPg():
    return render_template('register.html')

@app.route('/register', methods=['POST','GET'])
def new_register():
    if(mySQL_userDB.isUsernameTaken(request.form['username'],cursor, cnx)):
        return render_template('register.html',
                               errorMsg="Username is already taken. Please use a different one.",
                               username = request.form['username'],
                               password = request.form['password'],
                               email = request.form['email'],
                               fname = request.form['fname'],
                               lname = request.form['lname']
                               )
        
        
    docStatus = ""
    try:
        docStatus=request.form['docStatus']
    except:
        docStatus='patient'
    docType=""
    reply = ""
    if(docStatus!='patient'):
        docType = request.form['drType']
        reply = mySQL_userDB.insertDoctor(request.form['username'], 
                            request.form['password'], 
                            request.form['email'], 
                            request.form['fname'], 
                            request.form['lname'], 
                            docType,
                            cursor, cnx)
    else:
        reply = mySQL_userDB.insertPatient(request.form['username'], 
                            request.form['password'], 
                            request.form['email'], 
                            request.form['fname'], 
                            request.form['lname'], 
                            cursor, cnx)
    
    
    
    
    print(reply)
    if reply=="success":
        session['username'] = request.form['username']
        session['name'] = request.form['fname']+" "+request.form['lname']
        emailBody=""
        if(docStatus=='doctor'):
            emailBody = "Hello "+session['name']+",\r\nWelcome to Treeo!\r\nYou are not approved as a care provider yet, but we'll get right on verification. Let us know if you have any questions.\r\nSincerely,\r\n    Your Treeo Team"
            sendAutomatedAcctMsg(request.form['username'],"Welcome to Treeo!",emailBody) 
            return render_template('login.html', errorMsg="You have not been verified. Check your email for updates.")
            
        else:
            session['logged_in_p'] = True
            session['logged_in_d']=False
            session['logged_in_a']=False
            emailBody = "Hello "+session['name']+",\r\nWelcome to Treeo!\r\nYou do not have a care team assigned yet, but we'll get one to you ASAP. Let us know if you have any questions.\r\nSincerely,\r\n    Your Treeo Team"
            
        
        sendAutomatedAcctMsg(request.form['username'],"Welcome to Treeo!",emailBody) 
        takenUsernames.append(request.form['username'])
        
        return displayLoggedInHome()
    elif reply=="bad email or domain":
        return render_template('register.html',
                                   errorMsg="Invalid email format or domain.",
                                    username = request.form['username'],
                                   password = request.form['password'],
                                   email = request.form['email'],
                                   fname = request.form['fname'],
                                   lname = request.form['lname']
                                   ) 
    elif reply=="weak password":
        return render_template('register.html',
                                   errorMsg="Password must be min length 8, 1 upper case, and 1 number.",
                                    username = request.form['username'],
                                   password = request.form['password'],
                                   email = request.form['email'],
                                   fname = request.form['fname'],
                                   lname = request.form['lname']
                                   )
    elif reply=="short name error":
        return render_template('register.html',
                                   errorMsg="First and last name must have at least 2 characters.",
                                    username = request.form['username'],
                                   password = request.form['password'],
                                   email = request.form['email'],
                                   fname = request.form['fname'],
                                   lname = request.form['lname']
                                   )
    elif reply=="bad status specifier":
        return render_template('register.html',
                                   errorMsg="Choose Dr or Patient option.",
                                    username = request.form['username'],
                                   password = request.form['password'],
                                   email = request.form['email'],
                                   fname = request.form['fname'],
                                   lname = request.form['lname']
                                   ) 
    

@app.route('/usernamecheck', methods=['POST','GET'])
def usernamecheck():
    text = request.args.get('jsdata')
    if(text in takenUsernames):
        text=""
        return 'USERNAME TAKEN'
##    no _ or . at the end
##    allowed characters = [a-zA-Z0-9._] (NOT /*$#@+=?><,;':%^&())
##    no __ or _. or ._ or .. inside
##    no _ or . at the beginning
##    username is 5-20 characters long
#
    if not(re.match("^(?=.{5,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$", text)):
        text=""
        return "5-20 characters. No spaces. Cannot start/end with punctuation. Cannot contain /*$#@+=?><,;':%^&()"   
    return ""

@app.route('/emailCheck', methods=['POST','GET'])
def emailcheck():
    text = request.args.get('jsdata')
    try:
        valid = validate_email(text)
        text = ""
        return ""
    except EmailNotValidError as e:
        if(type(e)==EmailSyntaxError):
            text=""
            return "Incorrectly formatted email address."
        if(type(e)==EmailUndeliverableError):
            text=""
            return "Invalid domain."
        
        text = ""
        return str(e)

@app.route('/nameLengthCheck', methods=['POST','GET'])
def namecheck():
    text = request.args.get('jsdata')
    if(len(text)<2):
        text=""
        return 'First and last name need 2+ characters'
    return ""

@app.route('/pwStrengthCheck', methods=['POST','GET'])
def pwStrCheck():
    text = request.form.get('jsdata')
    policy = PasswordPolicy.from_names(
            length=8,  # min length: 8
            uppercase=2,  # need min. 2 uppercase letters
            numbers=2  # need min. 2 digits
            )
##PASSWORD STRENGTH
    isEnough = policy.test(str(text))
    text=""
    if len(isEnough):
        if len(isEnough)==1:
            if type(isEnough[0])==password_strength.tests.Length:
                return "<8 characters"
            elif type(isEnough[0])==password_strength.tests.Uppercase:
                return "<2 capital letters"
            elif type(isEnough[0])==password_strength.tests.Numbers: 
                return "<2 digits"
        elif len(isEnough)==2: #any 2 combinationsS
            if type(isEnough[0])==password_strength.tests.Length:
                if type(isEnough[1])==password_strength.tests.Uppercase:
                    return "<8 characters\n<2 capital letters"
                elif type(isEnough[1])==password_strength.tests.Numbers: 
                    return "<8 characters\n<2 digits"
            elif type(isEnough[0])==password_strength.tests.Uppercase:
                if type(isEnough[1])==password_strength.tests.Numbers: 
                    return "<2 capital letters\n<2 digits"
                elif type(isEnough[1])==password_strength.tests.Length: 
                    return "<2 capital letters\n<8 characters"
            elif type(isEnough[0])==password_strength.tests.Numbers: 
                if type(isEnough[1])==password_strength.tests.Uppercase:
                    return "<2 digits\n<2 capital letters"
                elif type(isEnough[1])==password_strength.tests.Length: 
                    return "<2 digits\n<8 characters"
        else: #all 3
            return "<8 characters\n<2 capital letters\n<2 digits"
    else:
        return ""

def accessDenied():
    return render_template('accessDenied.html')

@app.route('/createrender', methods=['POST','GET'])
def createPg():
    if session['logged_in_p']:
        return accessDenied()
    return render_template('create_mtg.html',
                           errorMsg = "")

@app.route('/createrender/<username>', methods=['POST','GET'])
def createWithUsername(username):
    if session['logged_in_p']:
        return accessDenied()

    return render_template('create_mtg.html',
                           errorMsg = "")

@app.route('/create_search', methods=['POST','GET'])
def createUserSearch():
    jsonSuggest = []
    query = request.args.get('query')
    listPatients=mySQL_userDB.searchPatientList(cursor, cnx)
    for username in listPatients:
        if(query.lower() in username.lower()):
            jsonSuggest.append({'value':username,'data':username.split(" - ")[0]})
            
    return jsonify({"suggestions":jsonSuggest})

@app.route('/createmtg', methods=['POST','GET'])
def create_mtg():
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00'
    #need to ensure that what is entered is either autocorrect, or valid
    
    
    try:
        if len(request.form['patientUser'].split(" - "))>1:
            username = request.form['patientUser'].split(" - ")[0]
            jsonResp = zoomtest_post.createMtg(time,str(request.form['password']),session['username'], username, cursor, cnx)
            print(jsonResp)
    #session['username'] == doctor
        else:
            jsonResp = zoomtest_post.createMtg(time,str(request.form['password']),session['username'], request.form['patientUser'],cursor, cnx)
            print(jsonResp)
        date=time[:10]
        finalStr = ""
    except:    
        return render_template('create_mtg.html',
                               errorMsg = "ERROR. Could not create meeting.")
#ADD PATIENT FIELD
    else:
        apptClassObj = mySQL_apptDB.getApptFromMtgId(jsonResp.get("id"), cursor, cnx)
        patientUsername = request.form['patientUser'].split(" - ")[0]
        emailBody="Hello "+patientUsername+",\r\n\r\nAn appointment has been created for you by "+mySQL_userDB.getNameFromUsername(session['username'], cursor, cnx)+" ("+session['username']+"). \r\n\r\n\t"
        emailBody= emailBody+"Appointment details: \r\nDate: "+date+"\r\nTime: "+time[11:]+"\r\nJoin URL: "+apptClassObj.joinURL+"\r\n\r\nLet us know if there are any issures or you wish to cancel.\r\nSincerely,\r\n\tYour Treeo Team"
        sendAutomatedApptMsg(patientUsername,"New Appointment Scheduled",emailBody)
        emailBody="Hello "+session['username']+",\r\nYou have created an appointment for "+mySQL_userDB.getNameFromUsername(patientUsername, cursor, cnx)+" ("+patientUsername+"). \r\n\r\n\t"
        emailBody= emailBody+"Appointment details: \r\nDate: "+date+"\r\n\r\nTime: "+time[11:]+"\r\nJoin URL: "+apptClassObj.joinURL+"\r\n\r\nLet us know if there are any issures or you wish to cancel.\r\nSincerely,\r\n\tYour Treeo Team"
        sendAutomatedApptMsg(session['username'],"New Appointment Scheduled",emailBody)
        return render_template('apptDetail.html',
                               mtgnum=apptClassObj.meetingID,
                               doctor =session['username'],
                               patient = patientUsername,
                               mtgname=apptClassObj.meetingName,
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
    ##make a joinURL field on this AND the mtg detail page


##CALENDAR FAILS TO DISPLAY FOR THE FOLLOWING CONDITIONS:
    #{"title": "HELP", "start": "2020-09-27T00:53:00", "end": "2020-09-27T1:53:00", "url": "/showmtgdetail/75274348158"}
    #^^^^ END OR START TIME NOT HAVING 2 PLACES (NOT LEADING WITH A 0 WHEN 1 DIGIT TIME)
    #{"title": "asl", "start": "2020-09-21T14:46:00:00", "end": "2020-09-21T15:46:00:00", "url": "/showmtgdetail/75141590110"}
    #^^^^ HAVING AN EXTRA SET OF 00 AFTER THE TIME
#DO ERROR CATCHING ********************************************
    #edited meetings have the extra :00? -> just chop it off every time? or update it in the aws dtb?
    #just tack on the 0 when it's missing

@app.route('/data')
def return_data():
    arrOfMtgs =mySQL_apptDB.getAllApptsFromUsername(session['username'], tmpcursor, cursor, cnx)
    #[{ "title": "Meeting",
    #"start": "2014-09-12T10:30:00-05:00",
    #"end": "2014-09-12T12:30:00-05:00",
    #"url":"absolute or relative?"},{...}]
    
    mtgList = []
    finalStr = ""
    for apptClassItem in arrOfMtgs:
        if(apptClassItem.meetingID=="None" or len(apptClassItem.meetingID)!=11): #skip invalid items that will crash the calendar
            continue
        else:
            #[mI, mN, sT]
            time = str(apptClassItem.startTime)
            print(type(time),time)
            mtgid = str(apptClassItem.meetingID)
            if(time[-1]=='Z'):
                time = time[:-1] #takes off the 'z'
            if(len(time[11:].split(":"))>=4): #catches any times with extra :00s
                time = time[:19]
            end_time = (int(float(time[11:13]))%24)+1
                          
            strend = time[:11]+str(end_time)+time[13:]
            if(end_time<=9): #catches any times <9 that would be single digit
                strend = time[:11]+"0"+str(end_time)+time[13:]
            
        jsonMtgObj = {"title":apptClassItem.meetingName, "start": time, "end":strend, "url":("/showmtgdetail/"+mtgid)}
        mtgList.append(jsonMtgObj)
    #BADDDD (change this)
    with open('appts.json', 'w') as outfile:
        json.dump(mtgList, outfile)
    with open('appts.json', "r") as input_data:
        #print(input_data.read())
        return input_data.read()    

@app.route('/showmtgdetail/<mtgid>', methods=['POST','GET'])
def show_mtgdetail(mtgid):     # TODO ---(make this calendar) Or when the calendar is clicked, have it call the show mtgs and format each mtg to show up correctly
    jsonResp = zoomtest_post.getMtgFromMtgID(str(mtgid))
    apptDetail = mySQL_apptDB.getApptFromMtgId(str(mtgid), cursor, cnx)
    time=apptDetail.startTime
    #split and display
    date=time[:10]
    if(time[-1]=='Z'):
        time = time[:-1] #takes off the 'z'
    docUser = apptDetail.doctor
    patUser = apptDetail.patient
    if(session.get('logged_in_p')):
        return render_template('apptDetail.html',
                               mtgnum=mtgid,
                               doctor=docUser,
                               patient = session['username'],
                               mtgname=str(apptDetail.meetingName),
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
    elif(session.get('logged_in_d')):
        if(mySQL_apptDB.isMtgStartTimePassed(mtgid, cursor, cnx)==True): #if it is passed so it should not be edited
            return render_template('apptDetail.html',
                               mtgnum=mtgid,
                               doctor=docUser,
                               patient = patUser,
                               mtgname=str(apptDetail.meetingName),
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
        else:
            return render_template('apptDetailDrOptions.html',
                       mtgnum=mtgid,
                       doctor =docUser,
                       patient = patUser,
                       mtgname=str(apptDetail.meetingName),
                       mtgtime=str(time[11:]),
                       mtgdate=str(date))

@app.route("/editrender/", methods=['POST','GET'])
def editPgFromID():
    mtgid = str(request.form['mtgnum'])
    if session['logged_in_p']:
        return accessDenied()
    jsonResp = zoomtest_post.getMtgFromMtgID(request.form['mtgnum'])

    #mtgname, pword, mtgtime, mtgdate
    # time=str(jsonResp.get("start_time"))
    time = mySQL_apptDB.getApptFromMtgId(request.form['mtgnum'], cursor, cnx).startTime
    #split and display
    date=time[:10]
    if(time[-1]=='Z'):
        time = time[:-1] #takes off the 'z'
    return render_template('edit.html',
                           mtgnum=mtgid,
                           mtgname=str(jsonResp.get("topic")),
                           pword=str(jsonResp.get("password")),
                           mtgtime=str(time[11:]),
                           mtgdate=str(date))


@app.route("/editmtg", methods=['POST','GET'])
def editSubmit():
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00'
    jsonResp = zoomtest_post.updateMtg(str(request.form['mtgnum']),str(request.form['mtgname']), time,cursor, cnx)

    jsonResp= zoomtest_post.getMtgFromMtgID(str(request.form['mtgnum']))
    #str(jsonResp.get("start_time"))

    mtgDetails = mySQL_apptDB.getApptFromMtgId(str(request.form['mtgnum']), cursor, cnx)
    time=mtgDetails.startTime
    
    #split and display
    date=time[:10]
    docUser = mtgDetails.doctor
    patUser = mtgDetails.patient
    if(time[-1]=='Z'):
        time = time[:-1] #takes off the 'z'
    emailBody="Hello "+mtgDetails.patient+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetails.patient, cursor, cnx)+" ("+mtgDetails.doctor+") has been updated. \r\n\r\n\t"
    emailBody= emailBody+"Updated appointment details: \r\nDate: "+date+"\r\nTime: "+time[11:]+"\r\nJoinURL: "+mtgDetails.joinURL+"\r\n\r\nThis has been changed in your calendar. Let us know if there are any issues or you wish to cancel.\r\nSincerely,\r\n\tYour Treeo Team"
    sendAutomatedApptMsg(mtgDetails.patient,"Appointment Updated",emailBody)
    emailBody="Hello "+mtgDetails.doctor+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetails.patient, cursor, cnx)+" ("+mtgDetails.patient+") has been updated. \r\n\r\n\t"
    emailBody= emailBody+"Updated appointment details: \r\nDate: "+date+"\r\nTime: "+time[11:]+"\r\nJoinURL: "+mtgDetails[5]+"\r\n\r\nThis has been changed your calendar. Let us know if there are any issues or you wish to cancel.\r\nSincerely,\r\n\tYour Treeo Team"
    sendAutomatedApptMsg(mtgDetails.doctor,"Appointment Updated",emailBody)
    if(mySQL_apptDB.isMtgStartTimePassed(request.form['mtgnum'], cursor, cnx)==True): #if it is passed so it should not be edited
        return render_template('apptDetail.html',
                               mtgnum=str(request.form['mtgnum']),
                               doctor=docUser,
                               patient = patUser,
                               mtgname=str(jsonResp.get("topic")),
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
    else:
        return render_template('apptDetailDrOptions.html',
                       mtgnum=str(request.form['mtgnum']),
                       doctor =docUser,
                       patient = patUser,
                       mtgname=str(jsonResp.get("topic")),
                       mtgtime=str(time[11:]),
                       mtgdate=str(date))

@app.route('/acctdetails', methods=['POST','GET'])
def acct_details():     
    acct_info = mySQL_userDB.getAcctFromUsername(str(session['username']),cursor, cnx)
    return render_template('ownAcctPg.html', 
                           username=acct_info.username,
                           docstatus= ("patient" if type(acct_info) == patientUserClass else acct_info.doctorType),
                           nm=acct_info.fname+" "+acct_info.lname,
                           email=acct_info.email,
                           createDate = acct_info.creationDate
                           )

@app.route('/acctEditrender/', methods=['POST','GET'])
def editAcctRender():
    acct_info = mySQL_userDB.userAcctInfo(str(request.form['username']),cursor, cnx)
    return render_template('editProfile.html',
                           errorMsg="",
                           username=session['username'],
                           pword1="",
                           pwordNew1="",
                           pwordNew2="",
                           email=acct_info.email,
                           fname=acct_info.fname,
                           lname=acct_info.lname
                           )

@app.route('/editacct', methods=['POST','GET'])
def editAcctDetails():
    oldPw = str(request.form['pword1'])
    newPw1 = str(request.form['pwordNew1'])
    newPw2 = str(request.form['pwordNew2'])
    
    acct_info = mySQL_userDB.userAcctInfo(str(request.form['username']),cursor, cnx)
    pwUpdate = False
    errMsg=""
    errFlag=False
    if(oldPw=="" and newPw1=="" and newPw2==""):
        #no password change is happening
        pwUpdate=False
        print("NO PASSWORD UPDATE")
    else:
        print("PASSWORD UPDATE")
        policy = PasswordPolicy.from_names(
            length=8,  # min length: 8
            uppercase=1,  # need min. 2 uppercase letters
            numbers=1  # need min. 2 digits
            )
        isEnough = policy.test(newPw1)
        pwUpdate=True
        errMsg=""
        errFlag=False
#FIRST NEED TO VALIDATE THAT THE OLD PASSWORD IS RIGHT!!!
        oldPassw = acct_info.password
        if False==(pwd_context.verify(oldPw, oldPassw)):
            errFlag=True
            errMsg="Password entered does not match the acct's password."
        elif oldPw==newPw1 and newPw1==newPw2:
            errFlag=True
            errMsg="New password has to be different from old password."
        elif newPw1!=newPw2:
            errFlag=True
            errMsg="New passwords did not match"
        #if it gets here, we know the new pw != old pw and new pws match
        elif len(isEnough):
            errFlag=True
            errMsg="New password must be min length 8, 1 upper case, and 1 number."
    print(errMsg)
    if(errMsg!=""):
        return render_template('editProfile.html',
                           errorMsg="ERROR: "+errMsg,
                           username=session['username'],
                           pword1="",
                           pwordNew1="",
                           pwordNew2="",
                           email=acct_info.email,
                           fname=acct_info.fname,
                           lname=acct_info.lname
                           )
    #if the password is fine, check names and email formatting
    if len(request.form['fname'])<2 or len(request.form['lname'])<2:
        return render_template('editProfile.html',
                           errorMsg="First and last name must have at least 2 characters.",
                           username=session['username'],
                           pword1="",
                           pwordNew1="",
                           pwordNew2="",
                           email=acct_info.email,
                           fname=acct_info.fname,
                           lname=acct_info.lname
                           )
    emailAddr=str(request.form['email'])
    try:
        valid = validate_email(emailAddr)
    except:
        return render_template('editProfile.html',
                           errorMsg="Invalid email address format.",
                           username=session['username'],
                           pword1="",
                           pwordNew1="",
                           pwordNew2="",
                           email=acct_info.email,
                           fname=acct_info.fname,
                           lname=acct_info.lname
                           )
    print("UPDATE CALL")
    #if it's gotten past here, we know password is fine (or not being updated), email is fine, f and l name are fine
    if(pwUpdate==False):
        response = mySQL_userDB.updateUserAcct(session['username'], str(request.form['email']),request.form['fname'], request.form['lname'], "",cursor, cnx)
    else:
        response = mySQL_userDB.updateUserAcct(session['username'], str(request.form['email']),request.form['fname'], request.form['lname'], newPw1,cursor, cnx)
    emailBody = "Hello "+session['username']+",\r\nYour account details have been changed.\r\nIf this was not you, please let us know immediately.\r\nSincerely,\r\n\tYour Treeo Team"
    sendAutomatedAcctMsg(session['username'], "Account Updated", emailBody)
    session['name']=str(request.form['fname'])+" "+str(request.form['lname'])
    return acct_details()


@app.route('/acctDelete', methods=['POST','GET'])
def deleteAccount():
    allAppts = mySQL_apptDB.getAllApptsFromUsername(str(request.form['username']), tmpcursor, cursor, cnx)
    for apptInfo in allAppts:
        autoDeleteMtg(apptInfo.meetingID)
    mySQL_userDB.deleteUserAcct(str(request.form['username']), cursor, cnx)
    deactivateAllMsgsUsername(str(request.form['username']))
    deleteAllNotifDeactive()
    mySQL_apptDB.deactivateAllArchivedAppts(str(request.form['username']),cursor, cnx )
    return logout()
    
    
def deactivateAllMsgsUsername(oldUsername):
    try:
        updateFormat = ("UPDATE messageDB SET sender = %s "
                                "WHERE sender = %s")
        cursor.execute(updateFormat, ("<deactivatedUser>",oldUsername))
        cnx.commit()
        updateFormat = ("UPDATE messageDB SET reciever = %s "
                                "WHERE reciever = %s")
        cursor.execute(updateFormat, ("<deactivatedUser>",oldUsername))
        cnx.commit()
        
    except:
        return "ERROR. Could not mark as deactivated."

def deleteAllNotifDeactive():
    try:
        delete_test = (
            "DELETE FROM messageDB " #table name NOT db name
            "WHERE (sender = %s AND reciever = %s) OR (sender = %s AND reciever = %s) "
            "OR (sender = %s AND reciever = %s) OR (sender = %s AND reciever = %s) ")
        cursor.execute(delete_test, ("<deactivatedUser>","TreeoCalendar", "TreeoCalendar","<deactivatedUser>", "<deactivatedUser>","TreeoNotification", "TreeoNotification","<deactivatedUser>"))
        cnx.commit()
        
    except:
        return "ERROR. Could not clean out messages."

@app.route('/patients/<username>', methods=['POST','GET'])
def patientAcct(username):
    ##dr will not be given the option to edit any details
    ##this is where medical details will eventually be rendered
    patientInfoObj = mySQL_userDB.getAcctFromUsername(str(username),cursor, cnx)
    
    
    return render_template('patientAcctDetails.html', 
                           username=username,
                           nm=patientInfoObj.fname + patientInfoObj.lname,
                           email=patientInfoObj.email,
                           drOne=("Not assigned" if patientInfoObj.dietician=="N/A" else patientInfoObj.dietician),
                           drTwo=("Not assigned" if patientInfoObj.physician=="N/A" else patientInfoObj.physician),
                           drThree=("Not assigned" if patientInfoObj.healthcoach=="N/A" else patientInfoObj.healthcoach),
                           createDate = patientInfoObj.creationDate
                           )

@app.route('/patients', methods=['POST','GET'])
def list_patients():
    listStr = mySQL_userDB.returnAllPatients(cursor, cnx)
    listStr.sort()
    patientPages = []
    currPg=0
    return displayPagedSearch(listStr, 10)

@app.route('/patientsAssigned', methods=['POST','GET'])
def list_assigned_patients():
    listStr = mySQL_userDB.returnPatientsAssignedToDr(session['username'], cursor, cnx)
    listStr.sort()
    patientPages = []
    currPg=0
    return displayPagedSearch(listStr, 10)

@app.route('/searchpgrender', methods=['POST','GET'])
def search_patients():
    return render_template('searchPg.html')

@app.route('/searchResult', methods=['POST','GET'])
def search_page():
    query = request.form['names']
    if(query==""): #if the form is empty, return all of the usernames
        listStr = mySQL_userDB.returnAllPatients(cursor, cnx)
        listStr.sort()
        patientPages = []
        currPg=0
        return displayPagedSearch(listStr,10)
    
    actualUsername = (query.split(" - "))[0] #username - last name, first name
    acct_search_item = mySQL_userDB.getAcctFromUsername(actualUsername,cursor, cnx)
    
    if(len(query.split(" - "))==2 and mySQL_userDB.isUsernameTaken(actualUsername,cursor, cnx)):
            #if the username exists and the user used the autocomplete -> take them to the account page directly
        return render_template('patientAcctDetails.html', 
                           username=acct_search_item.username,
                           nm=acct_search_item.fname + acct_search_item.lname,
                           email=acct_search_item.email,
                           drOne=("Not assigned" if acct_search_item.dietician=="N/A" else acct_search_item.dietician),
                           drTwo=("Not assigned" if acct_search_item.physician=="N/A" else acct_search_item.physician),
                           drThree=("Not assigned" if acct_search_item.healthcoach=="N/A" else acct_search_item.healthcoach),
                           createDate = acct_search_item.creationDate
                           )
    
    jsonSuggest=[]
    listStr=[]
    listPatients=patientList
    for username in listPatients:
        if(query.lower() in username.lower()):
            jsonSuggest.append({'value':username,'data':username})
            actualUsername = (username.split(" - "))[0]
            listStr.append(actualUsername)
            
    listStr.sort()
    patientPages = []
    currPg=0
    return displayPagedSearch(listStr,10)

@app.route('/changePgSize', methods=['POST','GET'])
def changePgSize():
    pageSize = int(request.form['listStatus'])
    
    pageStr = request.form['fullPagesArr']
    allPatients = []
    pages = pageStr.split("|")
    for page in pages:
        for patient in page.split(","):
            allPatients.append(patient)
    return displayPagedSearch(allPatients, pageSize)

def displayPagedSearch(patientList, listSize):
   patientPages = []
   numPatientsOnPg = listSize
   currPg=0
   numOfPages = 0
   if(len(patientList)>listSize):
       numOfPages = (len(patientList)/listSize)+1
       position = 0
       tempList = []
       for item in patientList:
           tempList.append(item)
           position = position+1
           if(position==listSize):
               patientPages.append(tempList)
               position=0
               tempList=[]
       patientPages.append(tempList) #tacks on the last partial page
       result = ""
       for page in patientPages:
           for patient in page:
               result = result + str(patient)+","
           result = result[:-1] #take off the last ,
           result = result + "|"
       result = result[:-1] #take off the last |

       selectSize = str(listSize)
       sizesList = ['5','10','20','30','50']
       #<p>Results {{startResultNum}} - {{endResultNum}} / {{totalResultNum}} (Page {{currPgNum}})</p>
       return render_template('firstPgSize.html',
                              sizeList=sizesList,
                               default = selectSize,
                              startResultNum=1,
                              endResultNum=numPatientsOnPg,
                              totalResultNum=len(patientList),
                              currPgNum=currPg+1,
                           options=patientPages[currPg],
                              fullPagesArr=result,
                              pgSize = selectSize,
                           npgnum=currPg+1)
   else:
        result = ""
        for patient in patientList:
            result = result + str(patient)+","
        result = result[:-1] #take off the last ,
        patientPages.append(patientList)
        selectSize = str(listSize)
        sizesList = ['5','10','20','30','50']
        return render_template('onlyPgSize.html',
                               sizeList=sizesList,
                               default = selectSize,
                            startResultNum=1,
                              endResultNum=len(patientList),
                              totalResultNum=len(patientList),
                              currPgNum=currPg+1,
                           options=patientList,
                            fullPagesArr=result,
                               pgSize = selectSize)

       
@app.route('/page', methods=['POST','GET'])
def nextPg():
    numPatientsOnPg = int(request.form['pgSize'])
    pageStr = request.form['fullPagesArr']
    patientPages = []
    pages = pageStr.split("|")
    temp = []
    counter = 0
    for page in pages:
        for patient in page.split(","):
            temp.append(patient)
            counter = counter+1
        patientPages.append(temp)
        temp = []
    pageNum = len(patientPages)
    totalNumPatients = counter
    
    try:
        currPg = int(request.form['prev'])
    except:
        currPg = int(request.form['next'])

    selectSize = str(request.form['pgSize'])
    sizesList = ['5','10','20','30','50']
    if(len(patientPages)==1):
        return render_template('onlyPgSize.html',
                               sizeList=sizesList,
                               default = selectSize,
                                startResultNum=1,
                              endResultNum=numPatientsOnPg,
                              totalResultNum=totalNumPatients,
                              currPgNum=currPg+1,
                           options=patientPages[currPg],
                               fullPagesArr=pageStr,
                               pgSize = request.form['pgSize'])
    elif(currPg==0):
        return render_template('firstPgSize.html',
                                startResultNum=1,
                               sizeList=sizesList,
                               default = selectSize,
                              endResultNum=numPatientsOnPg,
                              totalResultNum=totalNumPatients, 
                              currPgNum=currPg+1,
                           options=patientPages[currPg],
                               fullPagesArr=pageStr,
                               pgSize = request.form['pgSize'],
                           npgnum=currPg+1)
    elif(currPg==(pageNum-1)):
        return render_template('lastPgSize.html',
                               sizeList=sizesList,
                               default = selectSize,
                                startResultNum=((currPg)*numPatientsOnPg)+1,##
                              endResultNum=totalNumPatients,## not +5
                              totalResultNum=totalNumPatients,
                              currPgNum=currPg+1,
                           options=patientPages[currPg],
                               fullPagesArr=pageStr,
                                pgSize = request.form['pgSize'],
                           ppgnum=currPg-1)
    else:
        return render_template('middlePgSize.html',
                               sizeList=sizesList,
                               default = selectSize,
                                startResultNum=((currPg)*numPatientsOnPg)+1, ##
                              endResultNum=((currPg)*numPatientsOnPg)+1+numPatientsOnPg, ##+5
                              totalResultNum=totalNumPatients,
                              currPgNum=currPg+1,
                           options=patientPages[currPg],
                               fullPagesArr=pageStr,
                               pgSize = request.form['pgSize'],
                           ppgnum=currPg-1,
                            npgnum=currPg+1)


@app.route("/search/<string:box>")
def process(box):
    jsonSuggest = []
    query = request.args.get('query')
    listPatients=patientList
    for username in listPatients:
        if(query.lower() in username.lower()):
            jsonSuggest.append({'value':username,'data':username})
    return jsonify({"suggestions":jsonSuggest})

@app.route('/showallmtgs', methods=['POST','GET'])
def show_mtg():
    return render_template("calendar.html")


@app.route("/deleterender", methods=['POST','GET'])
def deletePg():
    if session['logged_in_p']:
        return accessDenied()
    return render_template('delete.html', mtg="")

@app.route("/deleteRenderNum/", methods=['POST','GET']) 
def deletePgNum():
    return autoDeleteMtg(str(request.form['mtgnum']))


def autoDeleteMtg(mtgid):
   
    if (mySQL_apptDB.isMeetingIDValid(str(mtgid), cursor, cnx)==True):
        mtgDetailsObject = mySQL_apptDB.getApptFromMtgId(str(mtgid), cursor, cnx)
        
        emailBody="Hello "+mtgDetailsObject.patient+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetailsObject.doctor, cursor, cnx)+" ("+mtgDetailsObject.doctor+") has been cancelled. \r\n\r\n\t"
        emailBody= emailBody+"Appointment details: \r\nDate: "+mtgDetailsObject.startTime[:10]+"\r\nTime: "+mtgDetailsObject.startTime[11:]+"\r\n\r\nThis has been removed from your calendar. Let us know if there are any issues or you wish to reschedule.\r\nSincerely,\r\n\tYour Treeo Team"
        sendAutomatedApptMsg(mtgDetailsObject.patient,"Appointment Cancelled",emailBody)
        emailBody="Hello "+mtgDetailsObject.doctor+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetailsObject.patient, cursor, cnx)+" ("+mtgDetailsObject.patient+") has been cancelled. \r\n\r\n\t"
        emailBody= emailBody+"Appointment details: \r\nDate: "+mtgDetailsObject.startTime[:10]+"\r\nTime: "+mtgDetailsObject.startTime[11:]+"\r\n\r\nThis has been removed from your calendar. Let us know if there are any issues or you wish to reschedule.\r\nSincerely,\r\n\tYour Treeo Team"
        sendAutomatedApptMsg(mtgDetailsObject.doctor,"Appointment Cancelled",emailBody)
        
        zoomtest_post.deleteMtgFromID(str(mtgid), cursor, cnx)
        
        return render_template('deleteConfirm.html', mtgnum=str(mtgid))
    else:
        return deletePg()

@app.route("/deletemtg", methods=['POST','GET'])
def deleteMtg():
   return autoDeleteMtg(str(request.form['mtgID']))

    
@app.route('/submitEmail', methods=['POST','GET'])
def formatEmail():

    query = request.form['reciever_username']
    actualUsername = (query.split(" - "))[0] #username - last name, first name
    
    if(len(query.split(" - "))==2): #if they chose from dropdown
       insertMessage(request.form['sender_username'],
           actualUsername,
           request.form['subject'],
           request.form['email_body'],
                 "0"
                 )
    elif(mySQL_userDB.isUsernameTaken(query, cursor, cnx)): #if it is a raw usern (not from dropdown)
       insertMessage(request.form['sender_username'],
           request.form['reciever_username'],
           request.form['subject'],
           request.form['email_body'],
                 "0"
                 )
    else: #invalid username
       return render_template("newEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          sender_username = session['username'],
                          errorMsg="Please enter a valid user ID",
                          userNotif = "",
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
       return openInbox()

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
       return openInbox()

@app.route('/sentFolder', methods=['POST','GET'])
def sentFolder():
    return renderPagedSent(0)


def renderPagedSent(pgNum):
    
    pageSize = 10
    msgList = getAllMessagesSent(session['username'])
    pageNumber = int(pgNum)
    if(pageNumber<0):
        pageNumber=0 #first page
    elif pageNumber>(len(msgList)/pageSize):
        pageNumber=(len(msgList)/pageSize) #final possible page number

    if(len(msgList)==0): #if the query is empty
        #return (False, [], False) #no prev, no next
        return render_template("emptySent.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = ""
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        #return (True, msgList[pageNumber*pageSize:], False)
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = True,
                          currPageNum = pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:])
    elif(pageNumber==0 and pageSize<len(msgList)): #this is the first page and there is a next page
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = pageSize,
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:pageSize])
    elif(pageNumber==0): #this is the first and only page
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = True,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:])
    else: #there is a prev and next page
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = pageNumber*pageSize+(pageSize),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize)])


@app.route('/trashFolder', methods=['POST','GET'])
def trashFolder():
    return renderPagedTrash(0)

def renderPagedTrash(pgNum):
    
    pageSize = 10
    msgList = getAllTrashMessages(session['username'])
    pageNumber = int(pgNum)
    if(pageNumber<0):
        pageNumber=0 #first page
    elif pageNumber>(len(msgList)/pageSize):
        pageNumber=(len(msgList)/pageSize) #final possible page number

    if(len(msgList)==0): #if the query is empty #no prev, no next
        return render_template("emptyTrash.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = ""
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = True,
                          currPageNum = pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:])
    elif(pageNumber==0 and pageSize<len(msgList)): #this is the first page and there is a next page
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = pageSize,
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:pageSize])
    elif(pageNumber==0): #this is the first and only page
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = True,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:])
    else: #there is a prev and next page
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = pageNumber*pageSize+(pageSize),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize)])


@app.route('/selectOption', methods=['POST','GET'])
def selectOption():
    #handling for the clicks of the picture buttons on the inbox page
    x = ""
    try:
       x = str(request.form['prevPg.x'])
       pageNum = request.form['currPageNum']
       return getAllMessagesPaged(session['username'], str(int(pageNum)-1))
       
    except:
        try:
            x = str(request.form['nextPg.x'])
            pageNum = request.form['currPageNum']
            return getAllMessagesPaged(session['username'], str(int(pageNum)+1))
            
        except:
            try:
                x = str(request.form['trash.x'])
                msgs = []
                for check in request.form:
                    if(str(check)!='trash.x' and str(check)!='trash.y'and str(check)!='selectAll' and str(check)!="currPageNum"):
                        #trash.x, trash.y and selectAll are values in the list of msgIDs that get returned so ifnore them
                        msgs.append(str(check))
                moveToTrash(msgs, session['username'])
            except:
                try:
                    x = str(request.form['mar.x'])
                    for check in request.form:
                        if(str(check)!='mar.x' and str(check)!='mar.y' and str(check)!='selectAll'):
                             markAsRead(str(check))
                except:
                    try:
                        x = str(request.form['mau.x'])
                        for check in request.form:
                            if(str(check)!='mau.x' and str(check)!='mau.y' and str(check)!='selectAll'):
                                markAsUnread(str(check))
                    except:
                        openInbox()
    return openInbox()

def sendAutomatedAcctMsg(reciever,subject,msgBody):
    insertMessage("TreeoNotification",
           reciever,
           subject,
           msgBody,
                 "0"
                 )
    
def sendAutomatedApptMsg(reciever,subject,msgBody):
    insertMessage("TreeoCalendar",
           reciever,
           subject,
           msgBody,
                 "0"
                 )

def getAllMessagesPaged(username, pgNum): #page to be rendered
#<MYSQL FUNCTIONAL>
    pageSize = 10

    query = ("SELECT send_date, send_time, subject, read_status, messageID, sender FROM messageDB "
             "WHERE reciever = %s AND reciever_loc = %s")  
    cursor.execute(query, (username,"inbox")) 
    msgList = []
    for (send_date, send_time, subject, read_status, messageID, sender) in cursor:
            if read_status=='unread':
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,True])
            else:
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,False])
                
#most recent messages first
    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))


    pageNumber = int(pgNum)
    if(pageNumber<0):
        pageNumber=0 #first page
    elif pageNumber>(len(msgList)/pageSize):
        pageNumber=(len(msgList)/pageSize) #final possible page number

    if(len(msgList)==0): #if the query is empty
        return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = True,
                          currPageNum = pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:])
    elif(pageNumber==0 and pageSize<len(msgList)): #this is the first page and there is a next page
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = pageSize,
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:pageSize])
    elif(pageNumber==0): #this is the first and only page
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = True,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:])
    else: #there is a prev and next page
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = pageNumber*pageSize+(pageSize),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize)])


@app.route('/selectSent', methods=['POST','GET'])
def selectSent():
    #handling for picture icon buttons on the sent page
    try:
       x = str(request.form['prevPg.x'])
       pageNum = request.form['currPageNum']
       return renderPagedSent(str(int(pageNum)-1))
       
    except:
        try:
            x = str(request.form['nextPg.x'])
            pageNum = request.form['currPageNum']
            return renderPagedSent(str(int(pageNum)+1))
            
        except:
            try:
                x = str(request.form['trash.x'])
                msgs = []
                for check in request.form:
                    if(str(check)!='trash.x' and str(check)!='trash.y'and str(check)!='selectAll' and str(check)!="currPageNum"):
                        msgs.append(str(check))
                moveToTrash(msgs, session['username'])
                return sentFolder()
            except:
                return sentFolder()




@app.route("/emailsearch/<string:box>")
def usernameSearch(box):
   jsonSuggest = []
   query = request.args.get('query')
   listPatients=[]
   if(session['logged_in_d']==True):
        listPatients= mySQL_userDB.allSearchUsers(cursor, cnx)
   elif (session['logged_in_a']==True):
       listPatients = mySQL_adminDB.adminAllSearchUsers(cursor, cnx)
   else:
        listPatients= mySQL_userDB.getCareTeamOfUser(session['username'],cursor, cnx)
   for username in listPatients:
       if(query.lower() in username.lower()): #match regardless of case
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
       x = str(request.form['prevPg.x'])
       pageNum = request.form['currPageNum']
       return renderPagedTrash(str(int(pageNum)-1))
       
    except:
        try:
            x = str(request.form['nextPg.x'])
            pageNum = request.form['currPageNum']
            return renderPagedTrash(str(int(pageNum)+1))
            
        except:
            try:
                x = str(request.form['permdel.x'])
                msgs = []
                for check in request.form:
                    if(str(check)!='permdel.x' and str(check)!='permdel.y' and str(check)!='selectAll' and str(check)!='currPageNum'):
                        msgs.append(str(check))
                permenantDel(msgs, session['username'])        
            except:
                try:
                    x = str(request.form['undotrash.x'])
                    msgs=[]
                    for check in request.form:
                        if(str(check)!='undotrash.x' and str(check)!='undotrash.y' and str(check)!='selectAll' and str(check)!='currPageNum'):
                            msgs.append(str(check))
                    undoTrash(msgs, session['username'])
                except:
                    return trashFolder()
    
    return trashFolder()

   


def undoTrash(msgIDList, username):
    #if it is in the trash and the sender == current username -> move it to sent folder
    #else move it to inbox
    sender_loc='sent_folder'
    reciever_loc='inbox'
    for msgID in msgIDList:
        try:
            query = ("SELECT sender, reciever FROM messageDB "
                     "WHERE messageID = %s")  
            cursor.execute(query, (msgID,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
            
            for (sender, reciever) in cursor:
                if sender == username:
                    updateFormat = ("UPDATE messageDB SET sender_loc = %s "
                                        "WHERE messageID = %s")
                    cursor.execute(updateFormat, (sender_loc,msgID))
                    cnx.commit()
                else:
                    updateFormat = ("UPDATE messageDB SET reciever_loc = %s "
                                        "WHERE messageID = %s")
                    cursor.execute(updateFormat, (reciever_loc,msgID))
                    cnx.commit()
                break #NEED THIS OR IT CRASHES AFTER THE FIRST ONE
        except Exception as e:
            print("error in undo trash --> ", e)



def insertMessage(sender, reciever, subject,body, convoID):
#<MYSQL FUNCTIONAL>
    
    msgID= ""
    msgID= msgID+str(datetime.now().strftime('%H%M%S'))
    msgID= msgID+str(datetime.now()).split(".")[1]
    
    formatInsert = ("INSERT INTO messageDB "
                   "(messageID, sender,reciever,subject,"
                    "msgbody,convoID,send_time,send_date,"
                    "read_status,sender_loc,reciever_loc,perm_del) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (msgID, sender, reciever, subject,
                             body, (msgID if convoID == "0" else convoID),
                             str(datetime.now().strftime('%H:%M:%S')),str(date.today().strftime("%B %d, %Y")),
                             "unread", "sent_folder", "inbox", "n")

    cursor.execute(formatInsert, insertContent)
    cnx.commit()
        

@app.route('/newEmail', methods=['POST','GET'])
def newEmail():
    if(session['logged_in_p']==True):
        unassigned = mySQL_userDB.getAllUnassignedPatients(cursor, cnx)
        if(session['username'] in unassigned):
            return render_template("newEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          sender_username = session['username'],
                          errorMsg="",
                          userNotif = "NOTE: your care team has not been assigned, so you can only message the help account",
                          reciever_username="",
                          subject = "",
                          email_body = "")
    return render_template("newEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          sender_username = session['username'],
                          errorMsg="",
                          userNotif = "",
                          reciever_username="",
                          subject = "",
                          email_body = "")

def countUnreadInInbox(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT messageID FROM messageDB "
             "WHERE reciever = %s AND read_status=%s AND reciever_loc=%s")  
    cursor.execute(query, (username,'unread','inbox'))
    unreadNum = 0
    for (messageID,) in cursor:
        unreadNum = unreadNum+1
        
    if(unreadNum == 0):
        return ""
    else:
        return "("+str(unreadNum)+")"

    
  
def countUnreadInTrash(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT messageID FROM messageDB "
             "WHERE reciever = %s AND read_status=%s AND reciever_loc=%s")  
    cursor.execute(query, (username,'unread','trash'))
    unreadNum = 0
    for (messageID,) in cursor:
        unreadNum = unreadNum+1
        
    if(unreadNum == 0):
        return ""
    else:
        return "("+str(unreadNum)+")"


def markAsRead(msgID):
#<MYSQL FUNCTIONAL>
    try:
        read_status='read'
        updateFormat = ("UPDATE messageDB SET read_status = %s "
                                "WHERE messageID = %s")
        cursor.execute(updateFormat, (read_status,msgID))
        cnx.commit()

    except:
        
        return "ERROR. Could not mark as read."


    

def markAsUnread(msgID):
#<MYSQL FUNCTIONAL>
    try:
        read_status='unread'
        updateFormat = ("UPDATE messageDB SET read_status = %s "
                                "WHERE messageID = %s")
        cursor.execute(updateFormat, (read_status,msgID))
        cnx.commit()
        
    except:
        return "ERROR. Could not mark as unread."
    

def permenantDel(msgIDList, del_username):
#<MYSQL FUNCITIONAL>
    for msgID in msgIDList:
        try:
            query = ("SELECT sender, reciever, perm_del FROM messageDB "
                     "WHERE messageID = %s")  
            cursor.execute(query, (msgID,))
            perm_del = "n"
            for (sender, reciever, perm_del) in cursor:
                if sender == del_username and perm_del=='n':
                    perm_del = 's'
                    if(reciever=="<deactivatedUser>"):
                        perm_del = 'sr'
                elif sender == del_username and perm_del=='r':
                    perm_del = 'sr'
                elif reciever == del_username and perm_del=='n':
                    perm_del = 'r'
                    if(sender=="TreeoNotification" or sender=="TreeoCalendar" or sender=="<deactivatedUser>"):
                        perm_del = 'sr'
                elif reciever == del_username and perm_del=='s':
                    perm_del = 'sr'
                else:
                    perm_del = 'n'

                if perm_del == 'sr':    
                    delete_test = (
                        "DELETE FROM messageDB " #table name NOT db name
                        "WHERE messageID = %s")
                    cursor.execute(delete_test, (msgID,))
                    cnx.commit()
                else:
                    updateFormat = ("UPDATE messageDB SET perm_del = %s "
                                        "WHERE messageID = %s")
                    cursor.execute(updateFormat, (perm_del,msgID))
                    cnx.commit()
                break #nned this or it crashes after the first one
        except Exception as e:
            print("error in perma delete --> ", e)

    
def moveToTrash(msgIDList, del_username):
#<MYSQL FUNCTIONAL>
    sender_loc='trash'
    reciever_loc='trash'
    try:
        for msgID in msgIDList:
            query = ("SELECT sender FROM messageDB "
                     "WHERE messageID = %s")  
            cursor.execute(query, (msgID,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
            
            try:
                for (sender) in cursor:
                    if sender[0] == del_username:
                        updateFormat = ("UPDATE messageDB SET sender_loc = %s "
                                            "WHERE messageID = %s")
                        cursor.execute(updateFormat, (sender_loc,msgID))
                        cnx.commit()
                    else:
                        updateFormat = ("UPDATE messageDB SET reciever_loc = %s "
                                            "WHERE messageID = %s")
                        cursor.execute(updateFormat, (reciever_loc,msgID))
                        cnx.commit()
                    break #need this or is crashes after first loop
            except Exception as e:
                print("error in move to trash --> ",e)
    except Exception as e:
        print(e)
        

def getAllTrashMessages(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time,read_status, reciever_loc,subject, perm_del, messageID, sender, sender_loc, reciever FROM messageDB "
             "WHERE reciever = %s OR sender = %s")  
    cursor.execute(query, (username,username)) 

    trashList = []
    for (send_date, send_time,read_status, reciever_loc, subject, perm_del, messageID, sender, sender_loc, reciever) in cursor:
        dateWhole = str(send_date+ " - " +send_time)
        if (reciever==username and reciever_loc=='trash' and perm_del!='r' ) or (sender==username and sender_loc=='trash' and perm_del!='s'):
           if(reciever==username and read_status=='unread'):
               trashList.append([dateWhole,messageID,"",sender,send_date,subject,True])
           elif(sender==username):
               trashList.append([dateWhole, messageID,"To:",reciever,send_date,subject,False])
           else:
               trashList.append([dateWhole,messageID,"",sender,send_date,subject,False])
    trashList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
    return trashList


def getAllMessages(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time, subject, read_status, messageID, sender FROM messageDB "
             "WHERE reciever = %s AND reciever_loc = %s")  
    cursor.execute(query, (username,"inbox")) 
    msgList = []
    #NOTE: bc messageInbox.html is implemented with spans, spaces can't be printed, so we left the username displayed
    for (send_date, send_time, subject, read_status, messageID, sender) in cursor:
            if read_status=='unread':
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,True])
            else:
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,False])

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
    return msgList


def getAllMessagesSent(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time, subject, messageID, reciever FROM messageDB "
             "WHERE sender = %s AND sender_loc = %s")  
    cursor.execute(query, (username,"sent_folder")) 
    msgList = []
    for (send_date, send_time, subject, messageID, reciever) in cursor:
        msgList.append([str(send_date + " - " +send_time),messageID,"To:",reciever,send_date,subject])

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
    return msgList


def getAllMsgsInConvo(convoID):
    query = ("SELECT send_date, send_time,sender, subject, messageID, msgbody, reciever FROM messageDB "
             "WHERE convoID = %s")  
    cursor.execute(query, (convoID,)) 

    convoList = []
    for (send_date, send_time,sender, subject, messageID, msgbody, reciever) in cursor:
        dateWhole = str(send_date + "   " +send_time)
        send = str(sender+ " - " + mySQL_userDB.getNameFromUsername(sender,tmpcursor, cnx))
        recieve = str(reciever+ " - " + mySQL_userDB.getNameFromUsername(reciever,tmpcursor, cnx))
        convoList.append([dateWhole,messageID,send, recieve, subject, msgbody])
       
    convoList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y   %H:%M:%S"))
    return convoList




@app.route('/msg/<msgid>', methods=['POST','GET'])
def openMsg(msgid):
#<TEST MYSQL>
    query = ("SELECT sender, reciever, sender_loc, reciever_loc, convoID FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (msgid,))
    for (sender, reciever, sender_loc, reciever_loc, convoID) in cursor:
        if(reciever==session['username']):
            markAsRead(msgid)
        convoList=getAllMsgsInConvo(convoID)
        
        if(reciever=="<deactivatedUser>" or sender == "<deactivatedUser>"):
            if(reciever == session['username'] and reciever_loc=='inbox'):
                return render_template("msgInfoNoReply.html",
                                      inbox = True,sent = False,trashbox=False,
                              inboxUnread =countUnreadInInbox(session['username']),
                              trashUnread = countUnreadInTrash(session['username']),
                                  headMsgID = convoID,
                                  msgList=convoList,
                                      targetmId = str(msgid)
                                  )
            elif(sender_loc == 'trash' or reciever_loc=='trash'):
                return render_template("msgInfoNoReply.html",
                                      inbox = False,sent = False,trashbox=True,
                              inboxUnread =countUnreadInInbox(session['username']),
                              trashUnread = countUnreadInTrash(session['username']),
                                  headMsgID = convoID,
                                  msgList=convoList,
                                      targetmId = str(msgid)
                                  )
            else:
                return render_template("msgInfoNoReply.html",
                                      inbox = False,sent = True,trashbox=False,
                              inboxUnread =countUnreadInInbox(session['username']),
                              trashUnread = countUnreadInTrash(session['username']),
                                  headMsgID = convoID,
                                  msgList=convoList,
                                      targetmId = str(msgid)
                                  )
        else:
            if(reciever == session['username'] and reciever_loc=='inbox'):
                return render_template("msgInfo.html",
                                      inbox = True,sent = False,trashbox=False,
                              inboxUnread =countUnreadInInbox(session['username']),
                              trashUnread = countUnreadInTrash(session['username']),
                                  headMsgID = convoID,
                                  msgList=convoList,
                                      targetmId = str(msgid)
                                  )
            elif(sender_loc == 'trash' or reciever_loc=='trash'):
                return render_template("msgInfo.html",
                                      inbox = False,sent = False,trashbox=True,
                              inboxUnread =countUnreadInInbox(session['username']),
                              trashUnread = countUnreadInTrash(session['username']),
                                  headMsgID = convoID,
                                  msgList=convoList,
                                      targetmId = str(msgid)
                                  )
            else:
                return render_template("msgInfo.html",
                                      inbox = False,sent = True,trashbox=False,
                              inboxUnread =countUnreadInInbox(session['username']),
                              trashUnread = countUnreadInTrash(session['username']),
                                  headMsgID = convoID,
                                  msgList=convoList,
                                      targetmId = str(msgid)
                                  )
            
        
        

@app.route('/reply', methods=['POST','GET'])
def reply():
#<TEST MYSQL>
    convoID =request.form['headMsgID']
    query = ("SELECT sender, reciever, subject FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (convoID,))
    subj = ""
    for (sender, reciever, subject) in cursor:
        if("re: " in subject):
            subj = subject
        else:
            subj = "re: "+subject
    print(subj)
    originalReciever = reciever
    originalSender = sender

    return render_template("replyEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          headMsgID=convoID,
                          sender_username = session['username'],
                          reciever_username=(originalReciever if originalSender == session['username'] else originalSender),
                          subject = subj,
                          email_body = "")
@app.route('/inbox')
def openInbox():
   return getAllMessagesPaged(session['username'],"0")

@app.route("/logout", methods=['POST','GET'])
def logout():
    session['logged_in_p'] = False
    session['logged_in_d'] = False
    session['logged_in_a'] = False
    return home()

if __name__ == "__main__":
    patientPages = []
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
