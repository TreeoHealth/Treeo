
import mysql.connector
from mysql.connector import errorcode
from classFile import patientUserClass, adminUserClass, doctorUserClass
from password_strength import PasswordPolicy
from passlib.context import CryptContext
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
from datetime import date, datetime,timezone

#global declarations to connect to the database
config = {
  'host':'treeo-server.mysql.database.azure.com',
  'user':'treeo_master@treeo-server',
  'password':'Password1',
  'database':'treeohealthdb'
}
cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()
cursor.execute("USE treeoHealthDB")

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for doctor and patient users 
def allSearchUsers(cursor, cnx):
    query=("SELECT username, fname, lname FROM patientTable")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    nameArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        nameArr.append(tmp)
    query=("SELECT username, fname, lname FROM doctorTable")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        nameArr.append(tmp)
    return nameArr

#Purpose: updates a patient user's acct to be assigned the 3 dr users
def assignPatientCareTeam(patientUser, dr1User, dr2User, dr3User, cursor, cnx):
    update_test = (
                "UPDATE patientTable SET drOne=%s, drTwo=%s, drThree=%s"
                "WHERE username = %s")
    cursor.execute(update_test, (dr1User, dr2User, dr3User, patientUser))
    cnx.commit()
    return "success"

#Purpose: given a username and password, it checks the hash of the password and returns true if the 
#   user can log in, false otherwise
def checkUserLogin(username, pwrd, cursor, cnx):
    
    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000 #num of times it will hash before writing
    )
    
    query = ("SELECT username, password FROM doctorTable WHERE username = %s")
    cursor.execute(query, (username, ))
    for un, pw in cursor: #this loop will not be entered if it does not exist in the doctorDB
        if( True==(pwd_context.verify(pwrd, pw))):
            return True
        else: #because there can only be 1 match, this query can only be run 1 time max 
            return False
              
    query = ("SELECT username, password FROM patientTable WHERE username = %s")
    cursor.execute(query, (username, ))
    for un, pw in cursor: #this loop will not be entered if it does not exist in the patientDB
        if( True==(pwd_context.verify(pwrd, pw))):
            return True
        else:
            return False
    return False

#Purpose: remove username from the database (any user table)
def deleteUserAcct(username, cursor, cnx):
    result = getAcctFromUsername(username, cursor, cnx)
    if(type(result)==doctorUserClass):
        delete_test = (
            "DELETE FROM doctorTable " #table name NOT db name
            "WHERE username = %s")
        cursor.execute(delete_test, (username,))
        cnx.commit()
    elif type(result)==adminUserClass:
        delete_test = (
            "DELETE FROM adminTable " #table name NOT db name
            "WHERE username = %s")
        cursor.execute(delete_test, (username,))
        cnx.commit()
    else:
        delete_test = (
            "DELETE FROM patientTable " #table name NOT db name
            "WHERE username = %s")
        cursor.execute(delete_test, (username,))
        cnx.commit()
    return "deleted "+username

#Purpose: returns a class object with all database items packaged in it for any user table
def getAcctFromUsername(username, cursor, cnx):
    query = ("SELECT username, password, fname, lname, email, creationDate, drType FROM doctorTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    for u,p, f, l, e, cD, dT in cursor:
        drClassObj = doctorUserClass( u, p, e, f, l, cD, dT)
        return drClassObj
    
    query = ("SELECT username, password, fname, lname, email, creationDate, drOne, drTwo, drThree FROM patientTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    for u, p,f, l, e, cD, d1, d2, d3 in cursor:
        patientClassObj = patientUserClass(u,p,e, f, l, cD, 
                                            d1, d2, d3)
        return patientClassObj
    
    query = ("SELECT username, password, fname, lname, creationDate FROM adminTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    for u, p, f, l, cD in cursor:
        adminClassObj = adminUserClass(u, p, f, l, cD)
        return adminClassObj
    return

#Purpose: returns an array of all usernames for doctors that have been verified by an admin
def getAllApprovedDrs(cursor, cnx):
    query = ("SELECT username, fname FROM doctorTable WHERE verified=%s")         
    cursor.execute(query, ("1",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn in cursor:
        docArr.append(un)
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for doctor users that ARE dieticians
def getAllDrDietician(cursor, cnx):
    query = ("SELECT username, fname, lname FROM doctorTable WHERE drType=%s")         
    cursor.execute(query, ("dietician",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for doctor users that ARE healthcoaches
def getAllDrHealth(cursor, cnx):
    query = ("SELECT username, fname, lname FROM doctorTable WHERE drType=%s")         
    cursor.execute(query, ("healthcoach",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for doctor users that ARE physicians
def getAllDrPhysician(cursor, cnx):
    query = ("SELECT username, fname, lname FROM doctorTable WHERE drType=%s")         
    cursor.execute(query, ("physician",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    return docArr

#Purpose: returns an array of all usernames for doctors that have not been verified by an admin yet
def getAllUnapprovedDrs(cursor, cnx):
    query = ("SELECT username, fname FROM doctorTable WHERE verified=%s")         
    cursor.execute(query, ("0",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn in cursor:
        docArr.append(un)
    return docArr

#Purpose: returns an array of all usernames for patients that have at least 1
#   dr on their care team not yet assigned
def getAllUnassignedPatients(cursor, cnx):
    
    query = ("SELECT username, creationDate FROM patientTable WHERE drOne = %s OR drTwo=%s OR drThree=%s" )
    cursor.execute(query, ("N/A","N/A","N/A"))
    unassigned = []
    for un, cd in cursor:
        unassigned.append(un)
    return unassigned

#Purpose: returns an array of the 3 drs that are assigned to a patient user
#   for email recipient dropdown (so add the help account as well)
def getCareTeamOfUser(username, cursor, cnx):
    query = ("SELECT drOne, drTwo, drThree FROM patientTable WHERE username = %s") 
    cursor.execute(query, (username, ))
    docArr = []

    for d1, d2, d3 in cursor:
        print(d1, d2, d3)
        if(d1=="N/A" or d2=="N/A" or d3=="N/A"):
            docArr.append("TreeoHelp - help, treeo") #let them message a help account
        else: #dr team is assigned so they can be in the dropdown
            u1 = d1
            r1 = userAcctInfo(u1, cursor, cnx)
            if(r1!=None):
                docArr.append(str(u1+" - "+r1[2]+", "+r1[1]))
            
            u2 = d2
            r2 = userAcctInfo(u2, cursor, cnx)
            if(r2!=None):
                docArr.append(str(u2+" - "+r2[2]+", "+r2[1]))
            
            u3 = d3
            #(e,f,l,p)
            r3 = userAcctInfo(u3, cursor, cnx)
            if(r3!=None):
                docArr.append(str(u3+" - "+r3[2]+", "+r3[1]))
            
            docArr.append("TreeoHelp - help, treeo")
    return docArr

#Purpose: returns the dietician assigned to a particular patient user (N/A if patient username invalid)
def getDieticianOfPatient(username, cursor, cnx):
    query = ("SELECT drOne, creationDate FROM patientTable WHERE username = %s" )
    cursor.execute(query, (username,))
    for dr1, cd in cursor:
        return dr1
    return "N/A"

#Purpose: returns the drType of the dr username (dietician/physician/healthcoach)
def getDrTypeOfAcct(username, cursor, cnx):
    query = ("SELECT drType FROM doctorTable WHERE username=%s")
    cursor.execute(query, (username, ))
    for dr in cursor:
        return dr[0]
    return

#Purpose: returns the healthcoach assigned to a particular patient user (N/A if patient username invalid)
def getHealthcoachOfPatient(username, cursor, cnx):
    query = ("SELECT drThree, creationDate FROM patientTable WHERE username = %s" )
    cursor.execute(query, (username,))
    for dr3, cd in cursor:
        return dr3
    return "N/A"

#Purpose: given a username, query any user table for and assemble  first + last name into a string and return
#   if the username is invalid, return N/A N/A
def getNameFromUsername(username, cursor, cnx): 
    #the 2 queries need to have the same # of attributes in the select for a union
    query = ("SELECT fname, lname FROM doctorTable WHERE username = %s " ) #always check drTable 1st (smaller)
    cursor.execute(query, (username, ))
    for f, l in cursor:
        return str(f+" "+l)
    
    query = ("SELECT fname, lname FROM adminTable WHERE username = %s " ) #always check patTable 2nd (much larger)
    cursor.execute(query, (username,))
    for f, l in cursor:
        return str(f+" "+l)
    
    query = ("SELECT fname, lname FROM patientTable WHERE username = %s " ) #always check patTable 2nd (much larger)
    cursor.execute(query, (username,))
    for f, l in cursor:
        return str(f+" "+l)
    return "N/A N/A"

#Purpose: returns the physician assigned to a particular patient user (N/A if patient username invalid)
def getPhysicianOfPatient(username, cursor, cnx):
    query = ("SELECT drTwo, creationDate FROM patientTable WHERE username = %s" )
    cursor.execute(query, (username,))
    for dr2, cd in cursor:
        return dr2
    return "N/A"

#Purpose: verifies all information given and either returns a string with an error 
#   or inserts the item into the doctor database
def insertDoctor(username, password, email, fname, lname, drType, cursor, cnx):
    if(isUsernameTaken(username,cursor, cnx)):
        return "taken error"

    policy = PasswordPolicy.from_names(
            length=8,  # min length: 8
            uppercase=1,  # need min. 2 uppercase letters
            numbers=1  # need min. 2 digits
            )
    

    isEnough = policy.test(password)
    if len(isEnough)!=0:
        return "weak password"
    
    try:
        valid = validate_email(email)
    except:
        return "bad email or domain"

    if len(fname)<2 or len(lname)<2:
        return "short name error"

    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )

    formatInsert = ("INSERT INTO doctorTable "
                   "(username, password,email,fname,"
                    "lname,drType,creationDate, verified) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (username, pwd_context.hash(password), email, fname, lname, drType, str(date.today().strftime("%B %d, %Y")), "0")
    cursor.execute(formatInsert, insertContent)
    cnx.commit()

    return "success"

#Purpose: verifies all information given and either returns a string with an error 
#   or inserts the item into the patient database
def insertPatient(username, password, email, fname, lname, cursor, cnx):
    if(isUsernameTaken(username,cursor, cnx)):
        return "taken error"

    policy = PasswordPolicy.from_names(
            length=8,  # min length: 8
            uppercase=1,  # need min. 2 uppercase letters
            numbers=1  # need min. 2 digits
            )
    

    isEnough = policy.test(password)
    if len(isEnough)!=0:
        return "weak password"
    
    try:
        valid = validate_email(email)
    except:
        return "bad email or domain"

    if len(fname)<2 or len(lname)<2:
        return "short name error"


    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )

    formatInsert = ("INSERT INTO patientTable "
                   "(username, password,email,fname,"
                    "lname,drOne, drTwo, drThree,creationDate) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s)") #NOTE: use %s even with numbers
    
        #their care team is not assigned at creation, so N/A
    insertContent = (username, pwd_context.hash(password), email, fname, lname, "N/A", "N/A", "N/A", str(date.today().strftime("%B %d, %Y")))
    cursor.execute(formatInsert, insertContent)
    cnx.commit()

    return "success"

#Purpose: checks if drType is dietician (returns true if it is, false otherwise)
def isDrDietician(username, cursor, cnx):
    query = ("SELECT username FROM doctorTable WHERE username=%s AND drType = %s")
    cursor.execute(query, (username, "dietician"))
    for dr in cursor:
        return True
    return False

#Purpose: checks if drType is healthcoach (returns true if it is, false otherwise)
def isDrHealthCoach(username, cursor, cnx):
    query = ("SELECT username FROM doctorTable WHERE username=%s AND drType = %s")
    cursor.execute(query, (username, "healthcoach"))
    for dr in cursor:
        return True
    return False

#Purpose: checks if drType is physician (returns true if it is, false otherwise)
def isDrPhysician(username, cursor, cnx):
    query = ("SELECT username FROM doctorTable WHERE username=%s AND drType = %s")
    cursor.execute(query, (username, "physician"))
    for dr in cursor:
        return True
    return False

#Purpose: checks if username is taken by checking all 3 user databases (returns true if it is)
def isUsernameTaken(username, cursor, cnx): #fix SQL DONE
        #the 2 queries need to have the same # of attributes in the select
    query = ("SELECT username FROM doctorTable WHERE username = %s" ) 
        #because the doctor table will always be smaller, always query it first
    cursor.execute(query, (username,))
    for item in cursor:
        return True #if this is a dr, if will not query the patientTable
    
    query = ("SELECT username FROM patientTable WHERE username = %s") 
    cursor.execute(query, (username, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True 
    
    query = ("SELECT username FROM adminTable WHERE username = %s") 
    cursor.execute(query, (username, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True 
    
    return False #it was queried in both tables and neither matched

#Purpose: returns an array of all usernames in the patient table
def returnAllPatients(cursor, cnx): 
    query = ("SELECT username FROM patientTable")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for un in cursor: #NOTE: un is (username, ) - a 1 item tuple - so i index into it
        patientArr.append(un[0])
    return patientArr

#Purpose: returns an array of all usernames in all user tables
def returnAllTakenUsernames(cursor, cnx): 
    query = ("SELECT username FROM patientTable")         
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    userArr = []
    for un in cursor:
        userArr.append(un[0])
        
    query = ("SELECT username FROM doctorTable")         
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un in cursor:
        userArr.append(un[0])
    
    query = ("SELECT username FROM adminTable")         
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un in cursor:
        userArr.append(un[0])
        
    return userArr

#Purpose: returns an array of all usernames in the patient table that have been assigned this 
#   doctor user as part of their care team
def returnPatientsAssignedToDr(username, cursor, cnx): 
    query = ("SELECT username FROM patientTable WHERE drOne = %s OR drTwo = %s OR drThree = %s")         
    cursor.execute(query, (username,username,username)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for un in cursor:
        patientArr.append(un[0])
    return patientArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for doctor users
def searchDoctorList(cursor, cnx):
    query = ("SELECT username, fname, lname FROM doctorTable")         
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    docArr.append("TreeoHelp - help, treeo")
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for patient users
def searchPatientList(cursor, cnx):
    query = ("SELECT username, fname, lname FROM patientTable")         
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for un,fn,ln in cursor:
        patientArr.append(str(un+" - "+ln+", "+fn))
    return patientArr

#Purpose: update doctor user to no longer be verified (done by admin)
def unverifyDoctor(username, cursor, cnx):
    update_test = (
                "UPDATE doctorTable SET verified = %s "
                "WHERE username = %s")
    cursor.execute(update_test, ("0",username ))
    cnx.commit()
    return "success"

#Purpose: update patient/dr user acct details only after verifying they are all valid 
#   #(otherwise return a str with the error)
def updateUserAcct(user, emailAdd,fn, ln,passw, cursor, cnx):
    if(passw==""): #if password is not being updated
        try:
            valid = validate_email(emailAdd)
        except:
            return "bad email or domain"
    
        if len(fn)<2 or len(ln)<2:
            return "short name error"
        
        result = getAcctFromUsername(user, cursor, cnx)
        if(type(result)==doctorUserClass):
            update_test = (
                "UPDATE doctorTable SET email=%s, fname=%s, lname=%s"
                "WHERE username = %s")
            cursor.execute(update_test, (emailAdd, fn, ln, user))
            cnx.commit()
            return "success"
        else:
            update_test = (
                "UPDATE patientTable SET email=%s, fname=%s, lname=%s"
                "WHERE username = %s")
            cursor.execute(update_test, (emailAdd, fn, ln, user))
            cnx.commit()
            return "success"
    else:
        
        policy = PasswordPolicy.from_names(
            length=8,  # min length: 8
            uppercase=1,  # need min. 2 uppercase letters
            numbers=1  # need min. 2 digits
            )
        isEnough = policy.test(passw)
        if len(isEnough)!=0:
            return "weak password"
        try:
            valid = validate_email(emailAdd)
        except:
            return "bad email or domain"

        if len(fn)<2 or len(ln)<2:
            return "short name error"

        pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000)
        
        result = getAcctFromUsername(user, cursor, cnx)
        if(type(result)==doctorUserClass):
            update_test = (
                "UPDATE doctorTable SET email=%s, fname=%s, lname=%s, password = %s "
                "WHERE username = %s")
            cursor.execute(update_test, (emailAdd, fn, ln, pwd_context.hash(passw), user))
            cnx.commit()
            return "success"
        else:
            update_test = (
                "UPDATE patientTable SET email=%s, fname=%s, lname=%s, password = %s "
                "WHERE username = %s")
            cursor.execute(update_test, (emailAdd, fn, ln, pwd_context.hash(passw), user))
            cnx.commit()
            return "success"

#Purpose: returns a class object with all database items packaged in it for any patient or dr user
def userAcctInfo(user, cursor, cnx):
    query = ("SELECT username, password, fname, lname, email, creationDate, drType FROM doctorTable WHERE username = %s")   
    cursor.execute(query, (user, ))
    for u,p, f, l, e, cD, dT in cursor:
        drClassObj = doctorUserClass( u, p, e, f, l, cD, dT)
        return drClassObj
    
    query = ("SELECT username, password, fname, lname, email, creationDate, drOne, drTwo, drThree FROM patientTable WHERE username = %s")   
    cursor.execute(query, (user, ))
    for u, p,f, l, e, cD, d1, d2, d3 in cursor:
        patientClassObj = patientUserClass(u,p,e, f, l, cD, 
                                            d1, d2, d3)
        return patientClassObj

    return
    
#Purpose: update doctor user to be verified (done by admin)
def verifyDoctor(username, cursor, cnx):
    update_test = (
                "UPDATE doctorTable SET verified = %s "
                "WHERE username = %s")
    cursor.execute(update_test, ("1",username ))
    cnx.commit()
    return "success"


cursor.close()
cnx.close()