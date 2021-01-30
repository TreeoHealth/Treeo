
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
from classFile import adminUserClass, apptObjectClass, patientUserClass, providerUserClass
import zoomtest_post

#global variables for paging, connection to database, password checking and some username arrays
app = Flask(__name__)
patientPages = []
currPg=0

# config = {
#   'host':'treeo-server.mysql.database.azure.com',
#   'user':'treeo_master@treeo-server',
#   'password':'Password1',
#   'database':'treeohealthdb'
# }
# cnx = mysql.connector.connect(**config)
cnx = mysql.connector.connect(user='root', password='password',
                              host='127.0.0.1')

#NOTE: NEED 2 cursors for nested queries!!!
cursor = cnx.cursor(buffered=True)
cursor.execute("USE treeo_health_db")
tmpcursor = cnx.cursor(buffered=True) #THIS IS TO FIX "Unread result found error"
tmpcursor.execute("USE treeo_health_db")

takenUsernames = mySQL_userDB.returnAllTakenUsernames(cursor, cnx)
patientList = mySQL_userDB.searchPatientList(cursor, cnx)

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )


#******************log in/out/home pages**********************************************************************************************************

#Purpose: if patient user has somehow reached a page they aren't supposed to, render the access denied page
def accessDenied():
    return render_template('accessDenied.html')

#Endpoint trigger: when they submit the login page form (to check username/password)
#Purpose: check the database to see if the login was valid. If it was, decide which type of user logged 
#   in and set the session value (if not, render error)
@app.route('/login', methods=['POST','GET'])
def check_login():
    if(request.form['username'] in mySQL_adminDB.getAllAdminUsers(cursor,cnx)):
        result = mySQL_adminDB.verifyAdminLogin(request.form['username'], request.form['password'],cursor, cnx)
        if(result==False):
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
        return render_template('login.html', errorMsg="Incorrect username or password.")
    else:
        acct_info = mySQL_userDB.getAcctFromUsername(request.form['username'],cursor, cnx)
        if(type(acct_info)==providerUserClass):
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


#Endpoint trigger: when user logs in or navigates to home
#Purpose: display their home page and info depending on what type of user they are (3 diff home pages)
@app.route('/homepage')
def displayLoggedInHome():
    if(session.get('logged_in_d')):
        docStatus = 'provider'
        return render_template('homePageDr.html',
                               docStat = docStatus,
                               docType= mySQL_userDB.getDrTypeOfAcct(session['username'], cursor, cnx),
                               name=session['name'])
    elif(session.get('logged_in_a')):
        return displayAdminHome()
    else:
        docStatus = 'patient'
        return render_template('homePage.html',docStat = docStatus,name=session['name'])

#Endpoint trigger: when user is typing in email input on register form (every char entered triggers this)
#Purpose: checks if email is valid (domain and syntax). Dynamically shows an error msg if either is violated
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
            return "Incorrectly formatted email adprovideress."
        if(type(e)==EmailUndeliverableError):
            text=""
            return "Invalid domain."
        
        text = ""
        return str(e)

#Endpoint trigger: 1st page of the site
#Purpose: if they are logged in, take them to their home page, else show the login page
@app.route('/')
def home():
    if not (session.get('logged_in_p') or session.get('logged_in_d') or session.get('logged_in_a')):
        return render_template('login.html', errorMsg="")
    else:
        return displayLoggedInHome()

#Endpoint trigger: when user clicks the logout button on the nav bar or home page
#Purpose: log the user out and render the login page
@app.route("/logout", methods=['POST','GET'])
def logout():
    session['logged_in_p'] = False
    session['logged_in_d'] = False
    session['logged_in_a'] = False
    return home()

#Endpoint trigger: when user is typing in first/last name inputs on register form (every char entered triggers this)
#Purpose: checks if first/last name are at least 2 chars. Dynamically shows an error msg if this is violated
@app.route('/nameLengthCheck', methods=['POST','GET'])
def namecheck():
    text = request.args.get('jsdata')
    if(len(text)<2):
        text=""
        return 'First and last name need 2+ characters'
    return ""

#Endpoint trigger: when user submits "register" form
#Purpose: verify username is unique and try to insert the user type into the database (read reaponse to see if it worked).
#   if it was inserted, log the user in (unless provider user). if it was not, render appropriate error msg with filled out register pg.
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
        docType = request.form['providerType']
        reply = mySQL_userDB.insertProvider(request.form['username'], 
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
        if(docStatus=='provider'):
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

#Endpoint trigger: when user is typing in password input on register form (every char entered triggers this)
#Purpose: checks complexity of password. Dynamically shows the correct error msg if any part of the password rule is broken
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
  
#Endpoint trigger: when user chooses "register" option from login pg
#Purpose: render register form page
@app.route('/registerrender', methods=['POST','GET'])
def regPg():
    return render_template('register.html')
  
#Endpoint trigger: when user is typing in username input on register form (every char entered triggers this)
#Purpose: checks if username is taken and checks if it violates the regex rules. Dynamically shows
#   an error msg if either is violated
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


  
#******************admin functions**********************************************************************************************************

#Endpoint trigger: when admin user clicks the "approved providers"
#Purpose: get all approved providers from database and send to page in array for list display
@app.route('/approved', methods=['POST','GET'])
def adminListApproved():
    listPat = mySQL_userDB.getAllApprovedDrs(cursor, cnx)
    if(len(listPat)==0):
        return render_template("emptyApprovedList.html")
    else:
        return render_template("approvedList.html",
                           options = listPat)

#Endpoint trigger: when admin user clicks the "unapproved providers"
#Purpose: get all unapproved providers from database and send to page in array for list display
@app.route('/unapproved', methods=['POST','GET'])
def adminListUnapproved():
    listPat = mySQL_userDB.getAllUnapprovedDrs(cursor, cnx)
    if(len(listPat)==0):
        return render_template("emptyUnapprovedList.html")
    else:
        return render_template("unapprovedList.html",
                           options = listPat)
 
#Endpoint trigger: when admin user clicks the "unassigned patients"
#Purpose: get all unassigned users from database and send to page in array for list display
@app.route('/unassigned', methods=['POST','GET'])
def adminListUnassigned():
    listPat = mySQL_userDB.getAllUnassignedPatients(cursor, cnx)
    if(len(listPat)==0):
        return render_template("emptyUnassignedList.html")
    else:
        return render_template("unassignedList.html",
                           options = listPat)

#Endpoint trigger: when admin user clicks a provider user's name in the unapproved list
#Purpose: approve the provider user in the db and send an automated message then render confirmation pg
@app.route('/approve/<username>', methods=['POST','GET'])
def approveForm(username):
    mySQL_userDB.verifyProvider(username, cursor, cnx)
    providerAcctName = mySQL_userDB.getNameFromUsername(username, cursor, cnx)
    emailBody = "Hello "+providerAcctName+",\r\nWelcome to Treeo!\r\nYou are now approved as a care provider!\r\n\r\nWelcome to the team! Let us know if you have any questions.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(username,"Treeo Approval - Welcome",emailBody) 
    emailBody = "Hello "+session['name']+",\r\nYou have approved "+providerAcctName+ " (" +username+") as a care provider. If this was a mistake, please remedy immediately.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(session['username'],"Provider Approved",emailBody) 
    return render_template("approveConfirmation.html",
                           providername  = str(username + " - " +providerAcctName))

#Endpoint trigger: when admin user clicks a patient user's name in the unassigned list
#Purpose: render the form to assign 3 care providers to patient user
@app.route('/assign/<username>', methods=['POST','GET'])
def assignForm(username):
    userObject = mySQL_userDB.getAcctFromUsername(username, cursor, cnx)
    return render_template("assignCareTeam.html",
                           username  = username,
                           dietitian = userObject.dietitian if userObject.dietitian !="N/A" else "",
                           physician = userObject.physician if userObject.physician !="N/A" else "",
                           coach = userObject.coach if userObject.coach !="N/A" else "",)

#Endpoint trigger: when admin user submits form to assign 3 care providers to patient user
#Purpose: validate if all 3 providers selected are valid 
#   if they are, assign, send auto msgs and render patient acct pg. if they are not, render error pg
@app.route('/assignCareTeam', methods=['POST','GET'])
def assignTeam(): #submit update form
    provider1 = request.form['dietitian'].split(" - ")[0]
    provider2 = request.form['physician'].split(" - ")[0]
    provider3 = request.form['coach'].split(" - ")[0]
    if(mySQL_userDB.isDrDietitian(provider1, cursor, cnx)==False):
        return render_template("assignCareTeam.html",
                            errorMsg = "Invalid dietitian user (does not exist or is unapproved).",
                           username  = request.form['username'],
                           dietitian = provider1,
                           physician = provider2,
                           coach=provider3)
    elif(mySQL_userDB.isDrPhysician(provider2, cursor, cnx)==False):
        return render_template("assignCareTeam.html",
                            errorMsg = "Invalid physician user (does not exist or is unapproved).",
                           username  = request.form['username'],
                           dietitian = provider1,
                           physician = provider2,
                           coach=provider3)
    elif mySQL_userDB.isDrCoach(provider3, cursor, cnx)==False:
        return render_template("assignCareTeam.html",
                            errorMsg = "Invalid health coach user (does not exist or is unapproved).",
                           username  = request.form['username'],
                           dietitian = provider1,
                           physician = provider2,
                           coach=provider3)     
    else:
        mySQL_userDB.assignPatientCareTeam(request.form['username'], provider1, provider2, provider3, cursor, cnx) 
        emailBody = "Hello,\r\nYou have been assigned a care team.\r\n\r\n\tDietitian: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(provider1,cursor, cnx)+" ("+provider1+")\r\n\tPhysician: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(provider2,cursor, cnx)+" ("+provider2+")\r\n\tHealth Coach: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(provider3,cursor, cnx)+" ("+provider3+")\r\n"
        emailBody = emailBody+"\r\nPlease reach out with any questions or concerns.\r\nSincerely,\r\n    Your Treeo Team"
        sendAutomatedAcctMsg(request.form['username'],"Care Team Assignment",emailBody) 
        
        emailBody = "Hello,\r\nYou have been assigned to a patient: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(request.form['username'],cursor, cnx)+" ("+request.form['username'] +")\r\n Here is your team:\r\n\r\n\tDietitian: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(provider1,cursor, cnx)+" ("+provider1+")\r\n\tPhysician: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(provider2,cursor, cnx)+" ("+provider2+")\r\n\tHealth Coach: "
        emailBody=emailBody+mySQL_userDB.getNameFromUsername(provider3,cursor, cnx)+" ("+provider3+")\r\n"
        emailBody =emailBody+"\r\nPlease reach out with any questions or concerns.\r\nSincerely,\r\n    Your Treeo Admins"
        sendAutomatedAcctMsg(provider1,"Care Team Assignment",emailBody) 
        sendAutomatedAcctMsg(provider2,"Care Team Assignment",emailBody) 
        sendAutomatedAcctMsg(provider3,"Care Team Assignment",emailBody) 
        return patientAcct(request.form['username'])

#Endpoint trigger: when admin selects the "create new admin user" from home page
#Purpose: renders the form for creating new admin user
@app.route('/renderNewAdmin', methods=['POST','GET'])
def createAdminPg():
    return render_template('createAdminAcct.html')

#Endpoint trigger: when admin submits form to create new admin user
#Purpose: checks if all information is correct. if it is, registers admin user in db, else render error msg pg
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
 
#Endpoint trigger: when admin is typing in 1st input on assign page (every char entered triggers this)
#Purpose: sends a list of autocomplete values containing username/first name/last name of all dietitians
@app.route("/dietitianList")
def dAutocomplete():
   jsonSuggest = []
   query = request.args.get('query')
   listDr=mySQL_userDB.getAllDrDietitian(cursor, cnx)
   for username in listDr:
       if(query.lower() in username.lower()):
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})

#Purpose: render admin home page with their name
def displayAdminHome():
    return render_template('adminHome.html',
                           name = session['name'])

#Endpoint trigger: when admin is typing in 3rd input on assign page (every char entered triggers this)
#Purpose: sends a list of autocomplete values containing username/first name/last name of all health coaches
@app.route("/coachList")
def hcAutocomplete():
   jsonSuggest = []
   query = request.args.get('query')
   listDr=mySQL_userDB.getAllDrHealth(cursor, cnx)
   for username in listDr:
       if(query.lower() in username.lower()):
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})

#Endpoint trigger: when admin is typing in 2nd input on assign page (every char entered triggers this)
#Purpose: sends a list of autocomplete values containing username/first name/last name of all physicians
@app.route("/physicianList")
def pAutocomplete():
   jsonSuggest = []
   query = request.args.get('query')
   listDr=mySQL_userDB.getAllDrPhysician(cursor, cnx)
   for username in listDr:
       if(query.lower() in username.lower()):
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})

#Endpoint trigger: when admin user clicks a provider user's name in the approved list
#Purpose: remove approval of the provider user in the db and send an automated message then render confirmation pg
@app.route('/removeapproval/<username>', methods=['POST','GET'])
def unapproveForm(username):
    mySQL_userDB.unverifyProvider(username, cursor, cnx)
    providerAcctName = mySQL_userDB.getNameFromUsername(username, cursor, cnx)
    emailBody = "Hello "+providerAcctName+",\r\You have been suspended from being a care provider temporarily.\r\n\r\nLet us know if you have any questions.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(username,"Provider Account Suspended",emailBody) 
    emailBody = "Hello "+session['name']+",\r\nYou have removed provider approval for "+providerAcctName+ " (" +username+"). If this was a mistake, please remedy immediately.\r\nSincerely,\r\n    Your Treeo Team"
    sendAutomatedAcctMsg(session['username'],"Provider Approval Revoked",emailBody) 
    
    providerAccType = mySQL_userDB.getDrTypeOfAcct(username, cursor, cnx)
    assignedPatients = mySQL_userDB.returnPatientsAssignedToDr(username, cursor, cnx)
    for patientUser in assignedPatients:
        emailBody = "Hello "+patientUser+",\r\nYour "+providerAccType+" ("+providerAcctName+" - "+username+") on your care team has been removed from the system.\r\nWe will assign a replacement ASAP.\r\nSincerely,\r\n\tYour Treeo Team"
        sendAutomatedAcctMsg(patientUser, "Care Team Revision", emailBody)
    mySQL_userDB.removeDrFromAllCareTeams(username, cursor, cnx)
    return render_template("unapproveConfirmation.html",
                           providername  = str(username + " - " +providerAcctName))



#******************search functions**********************************************************************************************************

#Endpoint trigger: when provider user changes the size of search result page (dropdown)
#Purpose: gets array stitched into pg ("x,x,x|y,y,y|...") and splits into a different size of pg 
#   (resplit array and parse into new string). Rerender the page with the same contents but diff size (updates page marker).
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

#Purpose: gets array of patient usernames to be displayed and the size of the page then splits
#   that array into a the string to be stitched into the html pg ("x,x,x|y,y,y|...") and decides which
#   page to render (if there is a next pg, do firstPg but if not, do onlyPg, etc.)
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

#Endpoint trigger: when link for provider acct is clicked from patient detail page or from curr care team page
#Purpose: if provider had "emptyDr", render a preset page, else render the acct info for that provider acct
@app.route('/providers/<username>', methods=['POST','GET'])
def providerAcctPage(username):
    if(username == "emptyDr"):
        return render_template("providerDoesNotExist.html")
    providerInfoObj = mySQL_userDB.getAcctFromUsername(str(username),cursor, cnx)
    return render_template("providerAcctDetails.html",
                           username=username,
                           nm=providerInfoObj.fname+" "+providerInfoObj.lname,
                           email=providerInfoObj.email,
                           createDate=providerInfoObj.creationDate)
    

#Endpoint trigger: when provider user clicks "assigned patients" option from home page
#Purpose: queries for all patient usernames that are assigned to the curr provider user
#   and returns the paged search page (10 patients per pg)
@app.route('/patientsAssigned', methods=['POST','GET'])
def list_assigned_patients():
    listStr = mySQL_userDB.returnPatientsAssignedToDr(session['username'], cursor, cnx)
    listStr.sort()
    patientPages = []
    currPg=0
    return displayPagedSearch(listStr, 10)

#Endpoint trigger: when provider user clicks "List all patients" option from home page
#Purpose: queries for all patient usernames and returns the paged search page (10 patients per pg)
@app.route('/patients', methods=['POST','GET'])
def list_patients():
    listStr = mySQL_userDB.returnAllPatients(cursor, cnx)
    listStr.sort()
    patientPages = []
    currPg=0
    return displayPagedSearch(listStr, 10)

#Endpoint trigger: when provider user presses next/prev buttons on the search page
#Purpose: take the page str stitched into the html pg ("x,x,x|y,y,y|...") and decide which direction we went
#    (update currPg value) and decide which page to render and what patient users go on the page
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

#Endpoint trigger: when provider user clicks on patient user link from search list
#Purpose: queries for that patient acct info and renders in readonly form (care team included)
@app.route('/patients/<username>', methods=['POST','GET'])
def patientAcct(username):
    ##provider will not be given the option to edit any details
    ##this is where medical details will eventually be rendered
    patientInfoObj = mySQL_userDB.getAcctFromUsername(str(username),cursor, cnx)
    providerList = mySQL_userDB.getCareTeamOfUser(str(username),cursor, cnx)
    return render_template('patientAcctDetails.html', 
                           username=username,
                           nm=patientInfoObj.fname + " " +patientInfoObj.lname,
                           email=patientInfoObj.email,
                           d1Username= "emptyDr" if patientInfoObj.dietitian=="N/A" else patientInfoObj.dietitian,
                           providerOne=providerList[0],
                           d2Username="emptyDr" if patientInfoObj.physician=="N/A" else patientInfoObj.physician,
                           providerTwo=providerList[1],
                           d3Username="emptyDr" if patientInfoObj.coach=="N/A" else patientInfoObj.coach,
                           providerThree=providerList[2],
                           createDate = patientInfoObj.creationDate
                           )

#Endpoint trigger: when provider is typing in search box input on search page (every char entered triggers this)
#Purpose: sends a list of autocomplete values containing username/first name/last name of all patient users
@app.route("/search/<string:box>")
def process(box):
    jsonSuggest = []
    query = request.args.get('query')
    listPatients=patientList
    for username in listPatients:
        if(query.lower() in username.lower()):
            jsonSuggest.append({'value':username,'data':username})
    return jsonify({"suggestions":jsonSuggest})

#Endpoint trigger: when provider user submits a search in the search form
#Purpose: if search was blank, return all patients in paged search page (10 patients per pg).
#   if provider used the autocomplete to select a specific patient -> take them to the account page directly.
#   if they just did a general search, render list of patient accts that match the query (10 patients per pg)  
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
        
        patientInfoObj = mySQL_userDB.getAcctFromUsername(str(actualUsername),cursor, cnx)
        providerList = mySQL_userDB.getCareTeamOfUser(str(actualUsername),cursor, cnx)
        return render_template('patientAcctDetails.html', 
                           username=actualUsername,
                           nm=patientInfoObj.fname + " " +patientInfoObj.lname,
                           email=patientInfoObj.email,
                           d1Username=patientInfoObj.dietitian,
                           providerOne=providerList[0],
                           d2Username=patientInfoObj.physician,
                           providerTwo=providerList[1],
                           d3Username=patientInfoObj.coach,
                           providerThree=providerList[2],
                           createDate = patientInfoObj.creationDate
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

#Endpoint trigger: when provider user clicks "Search patients" option from home page
#Purpose: renders form for provider to search for patients
@app.route('/searchpgrender', methods=['POST','GET'])
def search_patients():
    return render_template('searchPg.html')



#******************user acct management/edit**********************************************************************************************************

#Endpoint trigger: when user clicks "acct details" option from nav bar
#Purpose: retrieves user info from db and renders in a page (read only) with edit/delete options
@app.route('/acctdetails', methods=['POST','GET'])
def acct_details():     
    acct_info = mySQL_userDB.getAcctFromUsername(str(session['username']),cursor, cnx)
    return render_template('ownAcctPg.html', 
                           username=acct_info.username,
                           docstatus= ("patient" if type(acct_info) == patientUserClass else acct_info.providerType),
                           nm=acct_info.fname+" "+acct_info.lname,
                           email=acct_info.email,
                           createDate = acct_info.creationDate
                           )

#Purpose: changes all msgs to/from deleted username to be to/from "<deactivatedUser>" 
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

#Endpoint trigger: when user clicks "delete acct" option from acct details page (and confirms popup)
#Purpose: deletes all appts user is in, deletes acct, changes all msgs to/from to be to/from "deactivatedUser",
#   deletes all notifications, updates archived appts (username), and logs the user out
@app.route('/acctDelete', methods=['POST','GET'])
def deleteAccount():
    providerUsername = str(request.form['username'])
    userAcctObj = mySQL_userDB.getAcctFromUsername(providerUsername, cursor, cnx)
    
    if(type(userAcctObj)==providerUserClass):
        assignedPatients = mySQL_userDB.returnPatientsAssignedToDr(providerUsername, cursor, cnx)
        for patientUser in assignedPatients:
            emailBody = "Hello "+patientUser+",\r\nYour "+userAcctObj.providerType+" ("+userAcctObj.fname+" "+userAcctObj.lname+" - "+providerUsername+") on your care team has been removed from the system.\r\nWe will assign a replacement ASAP.\r\nSincerely,\r\n\tYour Treeo Team"
            sendAutomatedAcctMsg(patientUser, "Care Team Revision", emailBody)
        
        mySQL_userDB.removeDrFromAllCareTeams(providerUsername, cursor, cnx)
        
    allAppts = mySQL_apptDB.getAllApptsFromUsername(providerUsername, tmpcursor, cursor, cnx)
    for apptInfo in allAppts:
        autoDeleteMtg(apptInfo.meetingID)
        
    mySQL_userDB.deleteUserAcct(providerUsername, cursor, cnx)
    deactivateAllMsgsUsername(providerUsername)
    deleteAllNotifDeactive()
    mySQL_apptDB.deactivateAllArchivedAppts(providerUsername,cursor, cnx )
    
    return logout()
  
#Purpose: deletes all msgs btwn "<deactivatedUser>" and either Treeo notification bot or another deactivated acct (remove bloat from dtb)
def deleteAllNotifDeactive():
    try:
        delete_test = (
            "DELETE FROM messageDB " #table name NOT db name
            "WHERE (sender = %s AND reciever = %s) OR (sender = %s AND reciever = %s) "
            "OR (sender = %s AND reciever = %s) OR (sender = %s AND reciever = %s) "
            "OR (sender = %s AND reciever = %s)")
        cursor.execute(delete_test, ("<deactivatedUser>","TreeoCalendar", 
                                     "TreeoCalendar","<deactivatedUser>", 
                                     "<deactivatedUser>","TreeoNotification", 
                                     "TreeoNotification","<deactivatedUser>",
                                     "<deactivatedUser>","<deactivatedUser>"))
        cnx.commit()
        
    except:
        return "ERROR. Could not clean out messages."

#Endpoint trigger: when user submits "edit acct" form from acct details page
#Purpose: if changing pw, checks if password is diff from old password and if the new ones match (errors if not).
#   Checks name length and email format (render error pg if wrong). if all check out, updates acct info in 
#   dtb and renders acct detail page with updated info.
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
    emailAdprovider=str(request.form['email'])
    try:
        valid = validate_email(emailAdprovider)
    except:
        return render_template('editProfile.html',
                           errorMsg="Invalid email adprovideress format.",
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

#Endpoint trigger: when user clicks "edit acct" option from acct details page
#Purpose: retrieves user info from db and renders in a form that will allow them to update their acct info
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


#Endpoint trigger: when user clicks "Send Message" from patient acct details pg OR  provider acct details pg
#Purpose: opens a new email with that username as the reciever
@app.route('/new_message/<username>', methods=['POST','GET'])
def composeNewMsg(username):
    return render_template("newEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          sender_username = session['username'],
                          errorMsg="",
                          userNotif = "",
                          reciever_username=username,
                          subject = "",
                          email_body = "")

#******************meeting CRUD**********************************************************************************************************

#Purpose: if mtgID is valid, cancels the appt via the mtgID, sends 2 automated notifications to patient and 
#   provider, and deletes appt from zoom API then renders confirmation (if not valid id, render the manual delete form)
def autoDeleteMtg(mtgid):
   
    if (mySQL_apptDB.isMeetingIDValid(str(mtgid), cursor, cnx)==True):
        mtgDetailsObject = mySQL_apptDB.getApptFromMtgId(str(mtgid), cursor, cnx)
        
        emailBody="Hello "+mtgDetailsObject.patient+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetailsObject.provider, cursor, cnx)+" ("+mtgDetailsObject.provider+") has been cancelled. \r\n\r\n\t"
        emailBody= emailBody+"Appointment details: \r\nDate: "+mtgDetailsObject.startTime[:10]+"\r\nTime: "+mtgDetailsObject.startTime[11:]+"\r\n\r\nThis has been removed from your calendar. Let us know if there are any issues or you wish to reschedule.\r\nSincerely,\r\n\tYour Treeo Team"
        sendAutomatedApptMsg(mtgDetailsObject.patient,"Appointment Cancelled",emailBody)
        emailBody="Hello "+mtgDetailsObject.provider+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetailsObject.patient, cursor, cnx)+" ("+mtgDetailsObject.patient+") has been cancelled. \r\n\r\n\t"
        emailBody= emailBody+"Appointment details: \r\nDate: "+mtgDetailsObject.startTime[:10]+"\r\nTime: "+mtgDetailsObject.startTime[11:]+"\r\n\r\nThis has been removed from your calendar. Let us know if there are any issues or you wish to reschedule.\r\nSincerely,\r\n\tYour Treeo Team"
        sendAutomatedApptMsg(mtgDetailsObject.provider,"Appointment Cancelled",emailBody)
        
        zoomtest_post.deleteMtgFromID(str(mtgid), cursor, cnx)
        
        return render_template('deleteConfirm.html', mtgnum=str(mtgid))
    else:
        return deletePg()

#Endpoint trigger: when provider user submits form to create mtg
#Purpose: tries to create mtg through zoompost call (if it throws error, render error msg),
#   if mtg was created, send automated msgs to provider and patient and render appt details page.
@app.route('/createmtg', methods=['POST','GET'])
def create_mtg():
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00'
    
    if False == mySQL_apptDB.isTime30MinInFuture(time):
        return render_template('create_mtg.html',
                           errorMsg = "ERROR: Start time must be 30 or more minutes in the future.",
                           patientUser = "")
    
    #need to ensure that what is entered is either autocorrect, or valid
    try:
        if len(request.form['patientUser'].split(" - "))>1:
            username = request.form['patientUser'].split(" - ")[0]
            jsonResp = zoomtest_post.createMtg(time,str(request.form['password']),session['username'], username, cursor, cnx)
        else:
            jsonResp = zoomtest_post.createMtg(time,str(request.form['password']),session['username'], request.form['patientUser'],cursor, cnx)
        date=time[:10]
        finalStr = ""
    except Exception as e:    
        print(e)
        return render_template('create_mtg.html',
                               errorMsg = "ERROR. Could not create meeting.",
                               patientUser = "")
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
                               provider =session['username'],
                               patient = patientUsername,
                               mtgname=apptClassObj.meetingName,
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
    ##make a joinURL field on this AND the mtg detail page

#Endpoint trigger: when provider user selects "create meeting" option from provider home pg
#Purpose: renders the form for creating an appt
@app.route('/createrender', methods=['POST','GET'])
def createPg():
    if session['logged_in_p']:
        return accessDenied()
    return render_template('create_mtg.html',
                           errorMsg = "",
                           patientUser = "")

#Endpoint trigger: when provider is typing in patient input on create mtg form (every char entered triggers this)
#Purpose: autocompletes entered text with matching dropdown items from the database (username/first name/last name)
@app.route('/create_search', methods=['POST','GET'])
def createUserSearch():
    jsonSuggest = []
    query = request.args.get('query')
    listPatients=mySQL_userDB.searchPatientList(cursor, cnx)
    for username in listPatients:
        if(query.lower() in username.lower()):
            jsonSuggest.append({'value':username,'data':username.split(" - ")[0]})
            
    return jsonify({"suggestions":jsonSuggest})

#Endpoint trigger: when provider user selects "+ meeting" option from listed users in search result
#Purpose: renders the form for creating an appt
@app.route('/createrender/<username>', methods=['POST','GET'])
def createWithUsername(username):
    if session['logged_in_p']:
        return accessDenied()

    return render_template('create_mtg.html',
                           errorMsg = "",
                           patientUser = username)

#Endpoint trigger: when provider manually submits a mtg ID to be cancelled in the delete mtg form
#Purpose: invokes cancellation process for the appt via the mtgID
@app.route("/deletemtg", methods=['POST','GET'])
def deleteMtg():
   return autoDeleteMtg(str(request.form['mtgID']))

#Endpoint trigger: when provider clicks "delete mtg" option from home pg
#Purpose: renders form to allow provider to manually enter a mtg id to be cancelled
@app.route("/deleterender", methods=['POST','GET'])
def deletePg():
    if session['logged_in_p']:
        return accessDenied()
    return render_template('delete.html', mtg="")

#Endpoint trigger: when user clicks "cancel" option from appt detail pg
#Purpose: invokes cancellation process for the appt via the mtgID
@app.route("/deleteRenderNum/", methods=['POST','GET']) 
def deletePgNum():
    return autoDeleteMtg(str(request.form['mtgnum']))

#Endpoint trigger: when provider user clicks "edit appt" option from details page
#Purpose: gets the appt detail from the database and zoom API and renders details in editable (pre-filled) form
@app.route("/editrender/", methods=['POST','GET'])
def editPgFromID():
    mtgid = str(request.form['mtgnum'])
    if session['logged_in_p']:
        return accessDenied()
    jsonResp = zoomtest_post.getMtgFromMtgID(request.form['mtgnum'])

    time = mySQL_apptDB.getApptFromMtgId(request.form['mtgnum'], cursor, cnx).startTime
    #split and display
    date=time[:10]
    if(time[-1]=='Z'):
        time = time[:-1] #takes off the 'z'
    return render_template('edit.html',
                           errorMsg = "",
                           mtgnum=mtgid,
                           mtgname=str(jsonResp.get("topic")),
                           pword=str(jsonResp.get("password")),
                           mtgtime=str(time[11:]),
                           mtgdate=str(date))

#Endpoint trigger: when provider user submits edit appt form
#Purpose: updates meeting time in zoom API and database, send automated notification to provider and patient
#   and renders appt detail (if time is passed, don't let them have the option to edit again)
@app.route("/editmtg", methods=['POST','GET'])
def editSubmit():
    if session['logged_in_p']:
        return accessDenied()
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00'
    
    if False == mySQL_apptDB.isTime30MinInFuture(time):
        jsonResp = zoomtest_post.getMtgFromMtgID(request.form['mtgnum'])
        time = mySQL_apptDB.getApptFromMtgId(request.form['mtgnum'], cursor, cnx).startTime
        #split and display
        date=time[:10]
        if(time[-1]=='Z'):
            time = time[:-1] #takes off the 'z'
        return render_template('edit.html',
                               errorMsg = "ERROR: New time must be 30 mins or more in the future.",
                               mtgnum=request.form['mtgnum'],
                               mtgname=str(jsonResp.get("topic")),
                               pword=str(jsonResp.get("password")),
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
    
    jsonResp = zoomtest_post.updateMtg(str(request.form['mtgnum']),str(request.form['mtgname']), time,cursor, cnx)

    jsonResp= zoomtest_post.getMtgFromMtgID(str(request.form['mtgnum']))

    mtgDetails = mySQL_apptDB.getApptFromMtgId(str(request.form['mtgnum']), cursor, cnx)
    time=mtgDetails.startTime
    
    #split and display
    date=time[:10]
    docUser = mtgDetails.provider
    patUser = mtgDetails.patient
    if(time[-1]=='Z'):
        time = time[:-1] #takes off the 'z'
    emailBody="Hello "+mtgDetails.patient+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetails.patient, cursor, cnx)+" ("+mtgDetails.provider+") has been updated. \r\n\r\n\t"
    emailBody= emailBody+"Updated appointment details: \r\nDate: "+date+"\r\nTime: "+time[11:]+"\r\nJoinURL: "+mtgDetails.joinURL+"\r\n\r\nThis has been changed in your calendar. Let us know if there are any issues or you wish to cancel.\r\nSincerely,\r\n\tYour Treeo Team"
    sendAutomatedApptMsg(mtgDetails.patient,"Appointment Updated",emailBody)
    emailBody="Hello "+mtgDetails.provider+",\r\nYour appointment with "+mySQL_userDB.getNameFromUsername(mtgDetails.patient, cursor, cnx)+" ("+mtgDetails.patient+") has been updated. \r\n\r\n\t"
    emailBody= emailBody+"Updated appointment details: \r\nDate: "+date+"\r\nTime: "+time[11:]+"\r\nJoinURL: "+mtgDetails.joinURL+"\r\n\r\nThis has been changed your calendar. Let us know if there are any issues or you wish to cancel.\r\nSincerely,\r\n\tYour Treeo Team"
    sendAutomatedApptMsg(mtgDetails.provider,"Appointment Updated",emailBody)
    if(mySQL_apptDB.isMtgStartTimePassed(request.form['mtgnum'], cursor, cnx)==True): #if it is passed so it should not be edited
        return render_template('apptDetail.html',
                               mtgnum=str(request.form['mtgnum']),
                               provider=docUser,
                               patient = patUser,
                               mtgname=str(jsonResp.get("topic")),
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
    else:
        return render_template('apptDetailDrOptions.html',
                       mtgnum=str(request.form['mtgnum']),
                       provider =docUser,
                       patient = patUser,
                       mtgname=str(jsonResp.get("topic")),
                       mtgtime=str(time[11:]),
                       mtgdate=str(date))

#Endpoint trigger: called in the background when a user opens their calendar
#Purpose: gets all appts in the db for the current user, formats for error handling and read/writes to calendar
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

#Endpoint trigger: when user clicks "Care team" button on home page
#Purpose: renders the logged in patient's care team
@app.route('/user_careteam', methods=['POST','GET'])
def show_care_team():
    userObj = mySQL_userDB.getAcctFromUsername(session['username'], cursor, cnx)
    providerList = mySQL_userDB.getCareTeamOfUser(session['username'], cursor, cnx)
    
    return render_template("careTeamDetails.html",
                           username = session['username'],
                           nm = session['name'],
                           d1Username= "emptyDr" if userObj.dietitian=="N/A" else userObj.dietitian,
                           providerOne=providerList[0],
                           d2Username="emptyDr" if userObj.physician=="N/A" else userObj.physician,
                           providerTwo=providerList[1],
                           d3Username="emptyDr" if userObj.coach=="N/A" else userObj.coach,
                           providerThree=providerList[2])


#Endpoint trigger: when user navigates to calendar from home page or nav bar
#Purpose: renders calendar page (invokes background processes for formatting/functionality in flaskcalendar)
@app.route('/showallmtgs', methods=['POST','GET'])
def show_mtg():
    return render_template("calendar.html")

#Endpoint trigger: when user clicks an appt from the calendar
#Purpose: gets the appt detail from the database and zoom API and displays details. if user is a provider, 
#   render pg to allow editing. if user is patient or time is past the start, render pg that does not allow editing.
@app.route('/showmtgdetail/<mtgid>', methods=['POST','GET'])
def show_mtgdetail(mtgid):     
    jsonResp = zoomtest_post.getMtgFromMtgID(str(mtgid))
    apptDetail = mySQL_apptDB.getApptFromMtgId(str(mtgid), cursor, cnx)
    time=apptDetail.startTime
    #split and display
    date=time[:10]
    if(time[-1]=='Z'):
        time = time[:-1] #takes off the 'z'
    docUser = apptDetail.provider
    patUser = apptDetail.patient
    if(session.get('logged_in_p')):
        return render_template('apptDetail.html',
                               mtgnum=mtgid,
                               provider=docUser,
                               patient = session['username'],
                               mtgname=str(apptDetail.meetingName),
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
    elif(session.get('logged_in_d')):
        if(mySQL_apptDB.isMtgStartTimePassed(mtgid, cursor, cnx)==True): #if it is passed so it should not be edited
            return render_template('apptDetail.html',
                               mtgnum=mtgid,
                               provider=docUser,
                               patient = patUser,
                               mtgname=str(apptDetail.meetingName),
                               mtgtime=str(time[11:]),
                               mtgdate=str(date))
        else:
            return render_template('apptDetailDrOptions.html',
                       mtgnum=mtgid,
                       provider =docUser,
                       patient = patUser,
                       mtgname=str(apptDetail.meetingName),
                       mtgtime=str(time[11:]),
                       mtgdate=str(date))



#******************all inbox functions**********************************************************************************************************

#Endpoint trigger: when user is typing in msg body input any message page (every char entered triggers this)
#Purpose: Dynamically shows character count and max chars for the msg body input
@app.route('/bodyWordCheck', methods=['POST','GET'])
def bodyCheck():
   text = str(len(request.args.get('jsdata')))
   text = text + "/600"
   print(text)
   return text

#Purpose: return a tally of all unread emails in this user's inbox
def countUnreadInInbox(username):

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

#Purpose: return a tally of all unread emails in this user's trash folder
def countUnreadInTrash(username):

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

#Endpoint trigger: when user clicks any of the icon options (perm trash/prev/next/etc.) on their trash folder
#Purpose: handle the clicks of the picture buttons on the trash folder (try except structure tells what button
#   was pressed). Applies the option selected to all messages selected by the checkboxes on the current page
#   and reopens trash
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

#Endpoint trigger: when user clicks "send" on msg they composed
#Purpose: checks username of who they are sending to (verify is it valid, else render an error). If it
#   is valid, insert the msg as the 1st in the conversation (the "0") and send them back to their inbox.
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

#Endpoint trigger: when user clicks "send" on msg replying to another msg
#Purpose: insert the msg as a reply in the conversation (the "headMsgID") and send them back to their inbox.
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

#Purpose: query table to find all messages that are located in the user's inbox
def getAllMessages(username):

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

#Purpose: render the nth page of the inbox folder by calculating current location, which msgs to show,
#   updating the page indicator and rendering the correct page (next button, next and prev buttons, etc.)
def getAllMessagesPaged(username, pgNum): #page to be rendered
    
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

#Purpose: query table to find all messages that are located in the user's sent folder
def getAllMessagesSent(username):

    query = ("SELECT send_date, send_time, subject, messageID, reciever FROM messageDB "
             "WHERE sender = %s AND sender_loc = %s")  
    cursor.execute(query, (username,"sent_folder")) 
    msgList = []
    for (send_date, send_time, subject, messageID, reciever) in cursor:
        msgList.append([str(send_date + " - " +send_time),messageID,"To:",reciever,send_date,subject])

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
    return msgList

#Purpose: return array of messages in a conversation that share a convoID (how you identify replies)
#   and sort by date (most recent at top) so the conversation is rendered in order
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

#Purpose: query table to find all messages that are located in the user's trash folder
def getAllTrashMessages(username):

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

#Purpose: insert message into the message database (combine parameter data with date and time)
def insertMessage(sender, reciever, subject,body, convoID):

    
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

#Purpose: update a message to be marked as read
def markAsRead(msgID):

    try:
        read_status='read'
        updateFormat = ("UPDATE messageDB SET read_status = %s "
                                "WHERE messageID = %s")
        cursor.execute(updateFormat, (read_status,msgID))
        cnx.commit()

    except:
        
        return "ERROR. Could not mark as read."

#Purpose: update a message to be marked as unread
def markAsUnread(msgID):

    try:
        read_status='unread'
        updateFormat = ("UPDATE messageDB SET read_status = %s "
                                "WHERE messageID = %s")
        cursor.execute(updateFormat, (read_status,msgID))
        cnx.commit()
        
    except:
        return "ERROR. Could not mark as unread."

#Purpose: update a message to be located in the trash
def moveToTrash(msgIDList, del_username):

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

#Endpoint trigger: when user is clicks the "compose" option
#Purpose: render new email form (with a note about not being assigned if they are an unassigned patient)
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

#Endpoint trigger: when user opens inbox from anywhere (nav bar from home page or anywhere in inbox)
#Purpose: render 1st page of the inbox
@app.route('/inbox')
def openInbox():
   return getAllMessagesPaged(session['username'],"0")

#Endpoint trigger: when user is clicks a message in any folder
#Purpose: render the conversation (if the other account is deactivated, do not allow the user to reply)
#   NOTE: the if/else is simply to decide where the active is (if the msg is in the sent folder, the inbox in the nav bar should not be the active one)
@app.route('/msg/<msgid>', methods=['POST','GET'])
def openMsg(msgid):
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

#Purpose: given a list of msgIDs and the user deleting the messages, we dictate which messages are actually
#   fully removed from the database (permanently deleted with 'sr') vs just hidden from this user ('s','r',or 'n')
#   NOTE: 'n' = neither of the users has deleted, 's' = sender has deleted, reciever has not
#   NOTE: 'r' = reciever has deleted, sender has not, 'sr' = both have deleted (so remove from dtb)
#   NOTE: if the other person involved is a deleted user or a notification bot, perma delete that msg
def permenantDel(msgIDList, del_username):
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

#Purpose: render the nth page of the sent folder by calculating current location, which msgs to show,
#   updating the page indicator and rendering the correct page (next button, next and prev buttons, etc.)
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

#Purpose: render the nth page of the trash folder by calculating current location, which msgs to show,
#   updating the page indicator and rendering the correct page (next button, next and prev buttons, etc.)
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

#Endpoint trigger: when user is clicks the reply button when on message info page
#Purpose: render a reply email (set sender/reciever and subject, they only change msg body)
@app.route('/reply', methods=['POST','GET'])
def reply():
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

#Endpoint trigger: when user clicks any of the icon options (trash/prev/next/etc.) on their inbox page
#Purpose: handle the clicks of the picture buttons on the inbox page (try except structure tells what button
#   was pressed). Applies the option selected to all messages selected by the checkboxes on the current page
#   and reopens inbox
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

#Endpoint trigger: when user clicks any of the icon options (trash/prev/next/etc.) on their sent page
#Purpose: handle the clicks of the picture buttons on the inbox page (try except structure tells what button
#   was pressed). Applies the option selected to all messages selected by the checkboxes on the current page
#   and reopens sent folder
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
    return sentFolder()

#Purpose: sends an automatic msg from this bot (has to do with account info)
def sendAutomatedAcctMsg(reciever,subject,msgBody):
    insertMessage("TreeoNotification",
           reciever,
           subject,
           msgBody,
                 "0"
                 )

#Purpose: sends an automatic msg from this bot (has to do with appointment info)
def sendAutomatedApptMsg(reciever,subject,msgBody):
    insertMessage("TreeoCalendar",
           reciever,
           subject,
           msgBody,
                 "0"
                 )

#Endpoint trigger: when user clicks on their sent folder in side nav bar
#Purpose: render 1st page of the sent folder
@app.route('/sentFolder', methods=['POST','GET'])
def sentFolder():
    return renderPagedSent(0)

#Endpoint trigger: when user is typing in subject input any message page (every char entered triggers this)
#Purpose: Dynamically shows character count and max chars for the subject input
@app.route('/subjWordCheck', methods=['POST','GET'])
def subjCheck():
   text = str(len(request.args.get('jsdata')))
   text = text + "/50"
   print(text)
   return text

#Endpoint trigger: when user clicks on their trash folder in side nav bar
#Purpose: render 1st page of the trash folder
@app.route('/trashFolder', methods=['POST','GET'])
def trashFolder():
    return renderPagedTrash(0)

#Purpose: sends message from the trash back to where it came from 
#   if it is from the current user -> sent, if it is to the current user -> inbox.
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

#Endpoint trigger: when user is typing in To: input on email compose page (every char entered triggers this)
#Purpose: sends a list of autocomplete values containing username/first name/last name of all possible users
#   (patient can only message care team and help acct, provider can msg provider/patients, admins can msg all users)
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
        listPatients= mySQL_userDB.getCareTeamOfUserEmailList(session['username'],cursor, cnx)
   for username in listPatients:
       if(query.lower() in username.lower()): #match regardless of case
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})


#starts the app and sets up the session object
if __name__ == "__main__":
    patientPages = []
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
