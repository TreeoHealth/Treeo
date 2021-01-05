from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from flask import Flask, jsonify
import json
import re
import zoomtest_post
import password_strength
import datetime
from datetime import date, datetime,timezone
import email_validator
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
from password_strength import PasswordPolicy
from passlib.context import CryptContext

import mysql.connector
from mysql.connector import errorcode
import mySQL_apptDB


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

takenUsernames = mySQL_apptDB.returnAllPatients(cursor, cnx)
patientList = mySQL_apptDB.searchPatientList(cursor, cnx)

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )


@app.route('/')
def home():
    if not (session.get('logged_in_p') or session.get('logged_in_d')):
        return render_template('login.html', errorMsg="")
    else:
        return displayLoggedInHome()

@app.route('/homepage')
def displayLoggedInHome():
    if(session.get('logged_in_d')):
        docStatus = 'doctor'
        return render_template('homePageDr.html',
                               docStat = docStatus,
                               docType= mySQL_apptDB.getDrTypeOfAcct(session['username'], cursor, cnx),
                               name=session['name'])
    else:
        docStatus = 'patient'
        return render_template('homePage.html',docStat = docStatus,name=session['name'])

        #name of logged in person printed
        #doctor/patient

@app.route('/login', methods=['POST','GET'])
def check_login():
    result = mySQL_apptDB.checkUserLogin(request.form['username'], request.form['password'],cursor, cnx)
    
    if(result==False):
        print("WRONG PASSWORD")
        return render_template('login.html', errorMsg="Incorrect username or password.")
    else:
        #(u, dS, str(f+" "+l), e, cD)
        info = mySQL_apptDB.getAcctFromUsername(request.form['username'],cursor, cnx)
        if(info[1]=='doctor'):
            session['logged_in_d']=True
            session['logged_in_p']=False
        else:
            session['logged_in_p'] = True
            session['logged_in_d']=False
        session['username'] = request.form['username']
        session['name'] = info[2]
        return displayLoggedInHome()

@app.route('/registerrender', methods=['POST','GET'])
def regPg():
    return render_template('register.html')

@app.route('/register', methods=['POST','GET'])
def new_register():
    if(mySQL_apptDB.isUsernameTaken(request.form['username'],cursor, cnx)):
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
        reply = mySQL_apptDB.insertDoctor(request.form['username'], 
                            request.form['password'], 
                            request.form['email'], 
                            request.form['fname'], 
                            request.form['lname'], 
                            docType,
                            cursor, cnx)
    else:
        reply = mySQL_apptDB.insertPatient(request.form['username'], 
                            request.form['password'], 
                            request.form['email'], 
                            request.form['fname'], 
                            request.form['lname'], 
                            cursor, cnx)
    
    
    
    
    print(reply)
    if reply=="success":
        if(docStatus=='doctor'):
            session['logged_in_d']=True
            session['logged_in_p']=False
        else:
            session['logged_in_p'] = True
            session['logged_in_d']=False
        session['username'] = request.form['username']
        session['name'] = request.form['fname']+" "+request.form['lname']
        print(reply,  session['logged_in_p'],  session['logged_in_d'], session['username'])
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
    #print("in UC", request)
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
    #print("in UC", request)
    text = request.args.get('jsdata')
    if(len(text)<2):
        text=""
        return 'First and last name need 2+ characters'
    return ""

@app.route('/pwStrengthCheck', methods=['POST','GET'])
def pwStrCheck():
    #print(request.form['jsdata'])
    #print(request.args)
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
        #print(type(isEnough[0]))
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
    listStr = mySQL_apptDB.returnAllPatients(cursor, cnx)
    listStr.sort()
    return render_template('create_mtg.html',
                           errorMsg = "",
                           options=listStr)

@app.route('/createrender/<username>', methods=['POST','GET'])
def createWithUsername(username):
    if session['logged_in_p']:
        return accessDenied()
    listStr = []
    listStr.append(username)
    return render_template('create_mtg.html',
                           errorMsg = "",
                           options=listStr)

@app.route('/create_search', methods=['POST','GET'])
def createUserSearch():
    jsonSuggest = []
    query = request.args.get('query')
    listPatients=mySQL_apptDB.searchPatientList(cursor, cnx)
    for username in listPatients:
        if(query in username):
            jsonSuggest.append({'value':username,'data':username.split(" - ")[0]})#'<div style="background-color:#cccccc; text-align:left; vertical-align: middle; padding:20px 47px;">'+username+'<div>'})
        #suggestions = [{'value': 'joe','data': 'joe'}, {'value': 'jim','data': 'jim'}]
    return jsonify({"suggestions":jsonSuggest})

@app.route('/createmtg', methods=['POST','GET'])
def create_mtg():
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00Z'
    #need to ensure that what is entered is either autocorrect, or valid
    try:
        if len(request.form['patientUser'].split(" - "))>1:
            username = request.form['patientUser'].split(" - ")[0]
            jsonResp = zoomtest_post.createMtg(str(request.form['mtgname']), time,str(request.form['password']),session['username'], username, cursor, cnx)
#session['username'] == doctor
        else:
            jsonResp = zoomtest_post.createMtg(str(request.form['mtgname']), time,str(request.form['password']),session['username'], request.form['patientUser'],cursor, cnx)
        date=time[:10]
        finalStr = ""
    except:    
        listStr = mySQL_apptDB.returnAllPatients(cursor, cnx)
        listStr.sort()
        return render_template('create_mtg.html',
                               errorMsg = "ERROR. Could not create meeting.",
                               options=listStr)
#ADD PATIENT FIELD
    
    else:
        return render_template('apptDetail.html',
                               mtgnum=str(jsonResp.get("id")),
                               doctor =session['username'],
                               patient = request.form['patientUser'],
                               mtgname=str(jsonResp.get("topic")),
                               mtgtime=str(time[11:-1]),
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
    arrOfMtgs =mySQL_apptDB.getAllApptsFromUsername(session['username'], cursor, cnx)
    #[{ "title": "Meeting",
    #"start": "2014-09-12T10:30:00-05:00",
    #"end": "2014-09-12T12:30:00-05:00",
    #"url":"absolute or relative?"},{...}]
    
    mtgList = []
    finalStr = ""
    for item in arrOfMtgs:
        #[mI, mN, sT]
        time = str(item[2])
        mtgid = str(item[0])
        if(time[-1]=='Z'):
            time = time[:-1] #takes off the 'z'
        if(len(time[11:].split(":"))>=4): #catches any times with extra :00s
            time = time[:19]
        end_time = int(float(time[11:13]))+1
        strend = time[:11]+str(end_time)+time[13:]
        if(end_time<=9): #catches any times <9 that would be single digit
            strend = time[:11]+"0"+str(end_time)+time[13:]
        
        mtgObj = {"title":str(item[1]), "start": time, "end":strend, "url":("/showmtgdetail/"+mtgid)}
        mtgList.append(mtgObj)
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
        #(mI, d, p, mN, sT, jU)
    time=str(jsonResp.get("start_time"))
    #split and display
    date=time[:10]
    docUser = apptDetail[1]
    patUser = apptDetail[2]
    if(session.get('logged_in_p')):
        return render_template('apptDetail.html',
                               mtgnum=mtgid,
                               doctor=docUser,
                               patient = session['username'],
                               mtgname=str(apptDetail[3]),
                               mtgtime=str(time[11:-1]),
                               mtgdate=str(date))
    elif(session.get('logged_in_d')):
        return render_template('apptDetailDrOptions.html',
                       mtgnum=mtgid,
                       doctor =docUser,
                       patient = patUser,
                       mtgname=str(apptDetail[3]),
                       mtgtime=str(time[11:-1]),
                       mtgdate=str(date))

@app.route("/editrender/", methods=['POST','GET'])
def editPgFromID():
    mtgid = str(request.form['mtgnum'])
    if session['logged_in_p']:
        return accessDenied()
    jsonResp = zoomtest_post.getMtgFromMtgID(request.form['mtgnum'])

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
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00Z'
    jsonResp = zoomtest_post.updateMtg(str(request.form['mtgnum']),str(request.form['mtgname']), time,cursor, cnx)

    jsonResp= zoomtest_post.getMtgFromMtgID(str(request.form['mtgnum']))
    time=str(jsonResp.get("start_time"))

    apptDetail = mySQL_apptDB.getApptFromMtgId(str(request.form['mtgnum']), cursor, cnx)
        #(mI, d, p, mN, sT, jU)
    #split and display
    date=time[:10]
    docUser = apptDetail[1]
    patUser = apptDetail[2]
    return render_template('apptDetailDrOptions.html',
                       mtgnum=str(request.form['mtgnum']),
                       doctor =docUser,
                       patient = patUser,
                       mtgname=str(jsonResp.get("topic")),
                       mtgtime=str(time[11:-1]),
                       mtgdate=str(date))

@app.route('/acctdetails', methods=['POST','GET'])
def acct_details():     
    #(u, dS, str(f+" "+l), e, cD)
    info = mySQL_apptDB.getAcctFromUsername(str(session['username']),cursor, cnx)
    return render_template('ownAcctPg.html', 
                           username=info[0],
                           docstatus= (info[1] if info[1] == 'patient' else str(info[1]+" - "+mySQL_apptDB.getDrTypeOfAcct(session['username'], cursor, cnx))),
                           nm=info[2],
                           email=info[3],
                           createDate = info[4]
                           )

@app.route('/acctEditrender/', methods=['POST','GET'])
def editAcctRender():
    #(emailAdd,fn, ln,passw)
    info = mySQL_apptDB.userAcctInfo(str(request.form['username']),cursor, cnx)
    return render_template('editProfile.html',
                           errorMsg="",
                           username=session['username'],
                           pword1="",
                           pwordNew1="",
                           pwordNew2="",
                           email=info[0],
                           fname=info[1],
                           lname=info[2]
                           )

@app.route('/editacct', methods=['POST','GET'])
def editAcctDetails():
    oldPw = str(request.form['pword1'])
    newPw1 = str(request.form['pwordNew1'])
    newPw2 = str(request.form['pwordNew2'])
    #(emailAdd,fn, ln,passw)
    info = mySQL_apptDB.userAcctInfo(str(request.form['username']),cursor, cnx)
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
        oldPassw = info[3]
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
                           email=info[0],
                           fname=info[1],
                           lname=info[2]
                           )
    #if the password is fine, check names and email formatting
    if len(request.form['fname'])<2 or len(request.form['lname'])<2:
        return render_template('editProfile.html',
                           errorMsg="First and last name must have at least 2 characters.",
                           username=session['username'],
                           pword1="",
                           pwordNew1="",
                           pwordNew2="",
                           email=info[0],
                           fname=info[1],
                           lname=info[2]
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
                           email=info[0],
                           fname=info[1],
                           lname=info[2]
                           )
    print("UPDATE CALL")
    #if it's gotten past here, we know password is fine (or not being updated), email is fine, f and l name are fine
    if(pwUpdate==False):
        response = mySQL_apptDB.updateUserAcct(session['username'], str(request.form['email']),request.form['fname'], request.form['lname'], "",cursor, cnx)
        print("1", response)
    else:
        response = mySQL_apptDB.updateUserAcct(session['username'], str(request.form['email']),request.form['fname'], request.form['lname'], newPw1,cursor, cnx)
        print("2", response)
    session['name']=str(request.form['fname'])+" "+str(request.form['lname'])
    return acct_details()



@app.route('/patients/<username>', methods=['POST','GET'])
def patientAcct(username):
    ##dr will not be given the option to edit any details
    ##this is where medical details will eventually be rendered
    print("PATIENT USER")
    #(u, dS, str(f+" "+l), e, cD)
    info = mySQL_apptDB.getAcctFromUsername(str(username),cursor, cnx)
    return render_template('patientAcctDetails.html', 
                           username=username,
                           docstatus=info[1],
                           nm=info[2],
                           email=info[3],
                           createDate = info[4]
                           )

@app.route('/patients', methods=['POST','GET'])
def list_patients():
    listStr = mySQL_apptDB.returnAllPatients(cursor, cnx)
    listStr.sort()
    patientPages = []
    currPg=0
    return displayPagedSearch(listStr, 10)
    #return render_template('picture.html', options=listStr) #THIS

@app.route('/searchpgrender', methods=['POST','GET'])
def search_patients():
    return render_template('searchPg.html')

@app.route('/searchResult', methods=['POST','GET'])
def search_page():
    query = request.form['names']
    if(query==""): #if the form is empty, return all of the usernames
        listStr = mySQL_apptDB.returnAllPatients(cursor, cnx)
##        listStr = ["alpha","beta","chi","delta",
##              "eta","epsilon","gamma","iota",
##              "kappa", "lambda","mu","nu",
##              "omicron","omega","pi","phi",
##              "psi","rho","sigma","tau",
##              "theta", "upsilon", 'xi',"zeta"]
        listStr.sort()
        patientPages = []
        currPg=0
        return displayPagedSearch(listStr,10)
        #return render_template('picture.html', options=listStr) #THIS
    
    actualUsername = (query.split(" - "))[0] #username - last name, first name
    info = mySQL_apptDB.getAcctFromUsername(actualUsername,cursor, cnx)
    
    if(len(query.split(" - "))==2 and mySQL_apptDB.isUsernameTaken(actualUsername,cursor, cnx)):
            #if the username exists and the user used the autocomplete -> take them to the account page directly
        return render_template('patientAcctDetails.html', 
                            username=info[0],
                           nm=info[2],
                           email=info[3],
                           createDate = info[4]
                           )
    
    jsonSuggest=[]
    listStr=[]
    listPatients=patientList
    for username in listPatients:
        if(query in username):
            jsonSuggest.append({'value':username,'data':username})
            actualUsername = (username.split(" - "))[0]
            listStr.append(actualUsername)
##    listStr = ["alpha","beta","chi","delta",
##              "eta","epsilon","gamma","iota",
##              "kappa", "lambda","mu","nu",
##              "omicron","omega","pi","phi",
##              "psi","rho","sigma","tau",
##              "theta", "upsilon", 'xi',"zeta"]
    listStr.sort()
    patientPages = []
    currPg=0
    return displayPagedSearch(listStr,10)
    #return render_template('picture.html', options=listStr) #THIS

@app.route('/changePgSize', methods=['POST','GET'])
def changePgSize():
    pageSize = int(request.form['listStatus'])
    
    pageStr = request.form['fullPagesArr']
    #print("CHANGE SIZE TO ",pageSize,pageStr)
    allPatients = []
    pages = pageStr.split("|")
    for page in pages:
        for patient in page.split(","):
            allPatients.append(patient)
    #print("CHANGE ALL PAT ",allPatients)
    return displayPagedSearch(allPatients, pageSize)

def displayPagedSearch(patientList, listSize):
    #the PROBLEM is that the patientPages needs to be cleared every time this is called
    #but for some reason if it is cleared before appending, it is blank when nextPg() is triggered and tries to access the array
    #to be solved
   patientPages = []
   numPatientsOnPg = listSize
    #print("1-->",patientPages)
   currPg=0
   numOfPages = 0
   if(len(patientList)>listSize):
       #patientPages = []
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
       #print("2-->",patientPages)
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
        #patientPages = []
        result = ""
        for patient in patientList:
            result = result + str(patient)+","
        result = result[:-1] #take off the last ,
        #print("3-->",patientPages)
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
    #print("4-->",patientPages)
    
    #rint(pageNum)
    try:
        #print(request.form['prev'])
        currPg = int(request.form['prev'])
    except:
        #print(request.form['next'])
        currPg = int(request.form['next'])
    #print("CurrPg",currPg)

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

    
#UNUSED
##@app.route("/search")
##def processSearch():
##    jsonSuggest = []
##    query = request.args.get('jsdata')
##    #query = request.args.get('query')
##    listPatients=patientList
##    num = 0
##    for username in listPatients:
##        if(query in username):
##            num+=1#'<div style="background-color:#cccccc; text-align:left; vertical-align: middle; padding:20px 47px;">'+username+'<div>'})
##        #suggestions = [{'value': 'joe','data': 'joe'}, {'value': 'jim','data': 'jim'}]
##    print("HERRRRRRRRRE")
##    return '<div class="error">BLACH</div>'#'<textarea style="height:'+str(num*25)+'px;"></textarea>'

@app.route("/search/<string:box>")
def process(box):
    jsonSuggest = []
    query = request.args.get('query')
    listPatients=patientList
    for username in listPatients:
        if(query in username):
            jsonSuggest.append({'value':username,'data':username})
    return jsonify({"suggestions":jsonSuggest})

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
   
    if (mySQL_apptDB.isMeetingIDValid(str(request.form['mtgID']), cursor, cnx)==True):
        zoomtest_post.deleteMtgFromID(str(request.form['mtgID']), cursor, cnx)
        return render_template('deleteConfirm.html', mtgnum=str(request.form['mtgID']))
    else:
        return deletePg()

    
@app.route('/submitEmail', methods=['POST','GET'])
def formatEmail():

    query = request.form['reciever_username']
    # insertMessage(request.form['sender_username'],
    #         request.form['reciever_username'],
    #         request.form['subject'],
    #         request.form['email_body'],
    #               "0"
    #               )
    actualUsername = (query.split(" - "))[0] #username - last name, first name
    response = mySQL_apptDB.getAcctFromUsername(actualUsername, cursor, cnx)
        #(u, dS, str(f+" "+l), e, cD)
    if(len(query.split(" - "))==2): #if they chose from dropdown
       insertMessage(request.form['sender_username'],
           actualUsername,
           request.form['subject'],
           request.form['email_body'],
                 "0"
                 )
    elif(mySQL_apptDB.isUsernameTaken(query, cursor, cnx)): #if it is a raw usern (not from dropdown)
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
        #return (False, msgList[0:pageSize-1], True)
        #print("HERE", msgList[0:pageSize])
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
        #return (False, msgList[0:], False)
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
        #return (True, msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)], True)
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

    if(len(msgList)==0): #if the query is empty
        #return (False, [], False) #no prev, no next
        return render_template("emptyTrash.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = ""
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        #return (True, msgList[pageNumber*pageSize:], False)
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
        #return (False, msgList[0:pageSize-1], True)
        #print("HERE", msgList[0:pageSize])
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
        #return (False, msgList[0:], False)
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
        #return (True, msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)], True)
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

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))


    pageNumber = int(pgNum)
    if(pageNumber<0):
        pageNumber=0 #first page
    elif pageNumber>(len(msgList)/pageSize):
        pageNumber=(len(msgList)/pageSize) #final possible page number

    if(len(msgList)==0): #if the query is empty
        #return (False, [], False) #no prev, no next
        return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        #return (True, msgList[pageNumber*pageSize:], False)
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
        #return (False, msgList[0:pageSize-1], True)
        #print("HERE", msgList[0:pageSize])
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
        #return (False, msgList[0:], False)
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
        #return (True, msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)], True)
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
                for check in request.form:
                    print(check)
                    if(str(check)!='trash.x' and str(check)!='trash.y'and str(check)!='selectAll'):
                        moveToTrash(str(check), session['username'])
                return sentFolder()
            except:
                return sentFolder()


@app.route("/emailsearch/<string:box>")
def usernameSearch(box):
   jsonSuggest = []
   query = request.args.get('query')
   listPatients=[]
   if(session['logged_in_d']==True):
        listPatients= mySQL_apptDB.allSearchUsers(cursor, cnx)
   else:
        listPatients= mySQL_apptDB.getCareTeamOfUser(session['username'],cursor, cnx)
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
                for check in request.form:
                    if(str(check)!='permdel.x' and str(check)!='permdel.y' and str(check)!='selectAll'):
                        permenantDel(str(check), session['username'])
            except:
                x = str(request.form['undotrash.x'])
                for check in request.form:
                    if(str(check)!='undotrash.x' and str(check)!='undotrash.y' and str(check)!='selectAll'):
                        undoTrash(str(check), session['username'])

    return trashFolder()

   


def undoTrash(msgID, username):
    #if it is in the trash and the sender == current username -> move it to sent folder
    #else move it to inbox
#<MYSQL FUNCTIONAL>
    sender_loc='sent_folder'
    reciever_loc='inbox'

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



def insertMessage(sender, reciever, subject,body, convoID):
#<MYSQL FUNCTIONAL>
    
    msgID= ""
    msgID= msgID+str(datetime.now().strftime('%H%M%S'))
    msgID= msgID+str(datetime.now()).split(".")[1]

    #TODO -- account for convoID 0 or not
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
        unassigned = mySQL_apptDB.getAllUnassignedPatients(cursor, cnx)
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
    

def permenantDel(msgID, del_username):
#<MYSQL FUNCITIONAL>
    query = ("SELECT sender, reciever, perm_del FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (msgID,))
    perm_del = "n"
    for (sender, reciever, perm_del) in cursor:
        if sender == del_username and perm_del=='n':
            perm_del = 's'
        elif sender == del_username and perm_del=='r':
            perm_del = 'sr'
        elif reciever == del_username and perm_del=='n':
            perm_del = 'r'
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

    
def moveToTrash(msgID, del_username):
#<MYSQL FUNCTIONAL>
    sender_loc='trash'
    reciever_loc='trash'

    query = ("SELECT sender, reciever FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (msgID,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE

    for (sender, reciever) in cursor:
        if sender == del_username:
            updateFormat = ("UPDATE messageDB SET sender_loc = %s "
                                "WHERE messageID = %s")
            cursor.execute(updateFormat, (sender_loc,msgID))
            cnx.commit()
        else:
            updateFormat = ("UPDATE messageDB SET reciever_loc = %s "
                                "WHERE messageID = %s")
            cursor.execute(updateFormat, (reciever_loc,msgID))
            cnx.commit()


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
        send = str(sender+ " - " + mySQL_apptDB.getNameFromUsername(sender,tmpcursor, cnx))
        recieve = str(reciever+ " - " + mySQL_apptDB.getNameFromUsername(reciever,tmpcursor, cnx))
        #print(send, recieve)
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
    return home()

if __name__ == "__main__":
    patientPages = []
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
