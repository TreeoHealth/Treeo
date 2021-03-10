
import mysql.connector
from mysql.connector import errorcode
from classFile import patientUserClass, adminUserClass, providerUserClass
from password_strength import PasswordPolicy
from passlib.context import CryptContext
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
from datetime import date, datetime,timezone

#global declarations to connect to the database
# config = {
#   'host':'treeo-server.mysql.database.azure.com',
#   'user':'treeo_master@treeo-server',
#   'password':'Password1',
#   'database':'treeohealthdb'
# }
# cnx = mysql.connector.connect(**config)
cnx = mysql.connector.connect(user='root', password='#GGnorem8',
                              host='127.0.0.1')
cursor = cnx.cursor()
cursor.execute("USE treeo_health_db")

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for provider and patient users 
def allSearchUsers(cursor, cnx):
    query=("SELECT username, fname, lname FROM patientTable")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    nameArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        nameArr.append(tmp)
    query=("SELECT username, fname, lname FROM providerTable")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        nameArr.append(tmp)
    return nameArr

#Purpose: updates a patient user's acct to be assigned the 3 provider users
def assignPatientCareTeam(patientUser, provider1User, provider2User, provider3User, cursor, cnx):
    update_test = (
                "UPDATE patientTable SET providerOne=%s, providerTwo=%s, providerThree=%s"
                "WHERE username = %s")
    cursor.execute(update_test, (provider1User, provider2User, provider3User, patientUser))
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
    
    query = ("SELECT username, password FROM providerTable WHERE username = %s")
    cursor.execute(query, (username, ))
    for un, pw in cursor: #this loop will not be entered if it does not exist in the providerDB
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
    if(type(result)==providerUserClass):
        delete_test = (
            "DELETE FROM providerTable " #table name NOT db name
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
    query = ("SELECT username, password, fname, lname, email, creationDate, providerType FROM providerTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    for u,p, f, l, e, cD, dT in cursor:
        providerClassObj = providerUserClass( u, p, e, f, l, cD, dT)
        return providerClassObj
    
    query = ("SELECT username, password, fname, lname, email, creationDate, providerOne, providerTwo, providerThree, verified FROM patientTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    for u, p,f, l, e, cD, d1, d2, d3, v in cursor:
        patientClassObj = patientUserClass(u,p,e, f, l, cD, 
                                            d1, d2, d3, v)
        return patientClassObj
    
    query = ("SELECT username, password, fname, lname, creationDate FROM adminTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    for u, p, f, l, cD in cursor:
        adminClassObj = adminUserClass(u, p, f, l, cD)
        return adminClassObj
    return

#Purpose: returns an array of all usernames for providers that have been verified by an admin
def getAllApprovedDrs(cursor, cnx):
    query = ("SELECT username, fname FROM providerTable WHERE verified=%s")         
    cursor.execute(query, ("1",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn in cursor:
        docArr.append(un)
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for provider users that ARE dietitians
def getAllDrDietitian(cursor, cnx):
    query = ("SELECT username, fname, lname FROM providerTable WHERE providerType=%s AND verified=%s")         
    cursor.execute(query, ("dietitian","1")) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for provider users that ARE coaches
def getAllDrHealth(cursor, cnx):
    query = ("SELECT username, fname, lname FROM providerTable WHERE providerType=%s AND verified=%s")         
    cursor.execute(query, ("coach","1")) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for provider users that ARE physicians
def getAllDrPhysician(cursor, cnx):
    query = ("SELECT username, fname, lname FROM providerTable WHERE providerType=%s AND verified=%s")         
    cursor.execute(query, ("physician","1")) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    return docArr

#Purpose: returns an array of all usernames for providers that have not been verified by an admin yet
def getAllUnapprovedDrs(cursor, cnx):
    query = ("SELECT username, fname FROM providerTable WHERE verified=%s")         
    cursor.execute(query, ("0",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn in cursor:
        docArr.append(un)
    return docArr

#Purpose: returns an array of all usernames for VERIFIED patients that have at least 1
#   provider on their care team not yet assigned
def getAllUnassignedPatients(cursor, cnx):
    
    query = ("SELECT username, creationDate FROM patientTable WHERE verified = %s AND (providerOne = %s OR providerTwo=%s OR providerThree=%s)" )
    cursor.execute(query, ("1","N/A","N/A","N/A"))
    unassigned = []
    for un, cd in cursor:
        unassigned.append(un)
    return unassigned

#Purpose: returns an array of all usernames for patients that have not verified their
#   external email address
def getAllUnverifiedPatients(cursor, cnx):
    
    query = ("SELECT username, creationDate FROM patientTable WHERE verified = %s" )
    cursor.execute(query, ("0",))
    unverified = []
    for un, cd in cursor:
        unverified.append(un)
    return unverified


#Purpose: returns an array of the 3 providers that are assigned to a patient user
#   for care team detail purposes
def getCareTeamOfUser(username, cursor, cnx):
    query = ("SELECT providerOne, providerTwo, providerThree FROM patientTable WHERE username = %s") 
    cursor.execute(query, (username, ))
    docArr = []

    for d1, d2, d3 in cursor:
        u1 = d1
        r1 = userAcctInfo(u1, cursor, cnx)
        if(r1!=None):
            docArr.append(str(u1+" - "+r1.lname+", "+r1.fname))
        else:
           docArr.append("Not assigned")
            
        u2 = d2
        r2 = userAcctInfo(u2, cursor, cnx)
        if(r2!=None):
            docArr.append(str(u2+" - "+r2.lname+", "+r2.fname))
        else:
            docArr.append("Not assigned")
        
        u3 = d3
        r3 = userAcctInfo(u3, cursor, cnx)
        if(r3!=None):
            docArr.append(str(u3+" - "+r3.lname+", "+r3.fname))
        else:
            docArr.append("Not assigned")
    
    return docArr

#Purpose: returns an array of the 3 providers that are assigned to a patient user
#   for email recipient dropdown (so add the help account as well)
def getCareTeamOfUserEmailList(username, cursor, cnx):
    query = ("SELECT providerOne, providerTwo, providerThree FROM patientTable WHERE username = %s") 
    cursor.execute(query, (username, ))
    docArr = []

    for d1, d2, d3 in cursor:
        print(d1, d2, d3)
        if(d1=="N/A" or d2=="N/A" or d3=="N/A"):
            docArr.append("TreeoHelp - help, treeo") #let them message a help account
        else: #provider team is assigned so they can be in the dropdown
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

#Purpose: returns the dietitian assigned to a particular patient user (N/A if patient username invalid)
def getDietitianOfPatient(username, cursor, cnx):
    query = ("SELECT providerOne, creationDate FROM patientTable WHERE username = %s" )
    cursor.execute(query, (username,))
    for provider1, cd in cursor:
        return provider1
    return "N/A"

#Purpose: returns the providerType of the provider username (dietitian/physician/coach)
def getDrTypeOfAcct(username, cursor, cnx):
    query = ("SELECT providerType FROM providerTable WHERE username=%s")
    cursor.execute(query, (username, ))
    for provider in cursor:
        return provider[0]
    return

#Purpose: returns the coach assigned to a particular patient user (N/A if patient username invalid)
def getCoachOfPatient(username, cursor, cnx):
    query = ("SELECT providerThree, creationDate FROM patientTable WHERE username = %s" )
    cursor.execute(query, (username,))
    for provider3, cd in cursor:
        return provider3
    return "N/A"

#Purpose: given a username, query any user table for and assemble  first + last name into a string and return
#   if the username is invalid, return N/A N/A
def getNameFromUsername(username, cursor, cnx): 
    #the 2 queries need to have the same # of attributes in the select for a union
    query = ("SELECT fname, lname FROM providerTable WHERE username = %s " ) #always check providerTable 1st (smaller)
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
    query = ("SELECT providerTwo, creationDate FROM patientTable WHERE username = %s" )
    cursor.execute(query, (username,))
    for provider2, cd in cursor:
        return provider2
    return "N/A"

#Purpose: verifies all information given and either returns a string with an error 
#   or inserts the item into the provider database
def insertProvider(username, password, email, fname, lname, providerType, cursor, cnx):
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

    formatInsert = ("INSERT INTO providerTable "
                   "(username, password,email,fname,"
                    "lname,providerType,creationDate, verified) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (username, pwd_context.hash(password), email, fname, lname, providerType, str(date.today().strftime("%B %d, %Y")), "0")
    cursor.execute(formatInsert, insertContent)
    cnx.commit()

    return "success"

#Purpose: checks all information given and either returns a string with an error 
#   or inserts the item into the patient database (unverified)
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
                    "lname,providerOne, providerTwo, providerThree,"
                    "creationDate, verified) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
    
        #their care team is not assigned at creation, so N/A
    insertContent = (username, pwd_context.hash(password), email, fname, 
                     lname, "N/A", "N/A", "N/A", 
                     str(date.today().strftime("%B %d, %Y")), "0")
    cursor.execute(formatInsert, insertContent)
    cnx.commit()

    return "success"

#Purpose: checks if providerType is dietitian (returns true if it is, false otherwise)
def isDrDietitian(username, cursor, cnx):
    query = ("SELECT username FROM providerTable WHERE username=%s AND providerType = %s AND verified=%s")
    cursor.execute(query, (username, "dietitian", "1"))
    for provider in cursor:
        return True
    return False

#Purpose: checks if providerType is coach (returns true if it is, false otherwise)
def isDrCoach(username, cursor, cnx):
    query = ("SELECT username FROM providerTable WHERE username=%s AND providerType = %s AND verified=%s")
    cursor.execute(query, (username, "coach", "1"))
    for provider in cursor:
        return True
    return False

#Purpose: checks if providerType is physician (returns true if it is, false otherwise)
def isDrPhysician(username, cursor, cnx):
    query = ("SELECT username FROM providerTable WHERE username=%s AND providerType = %s AND verified=%s")
    cursor.execute(query, (username, "physician", "1"))
    for provider in cursor:
        return True
    return False

#Purpose: checks if patient acct is verified (returns true if it is, false otherwise)
def isPatientVerified(username, cursor, cnx):
    query = ("SELECT username, verified FROM patientTable WHERE username=%s ")         
    cursor.execute(query, (username,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un, v in cursor:
        if v=="1": #is verified
            return True
        else: #is not verified
            return False
    return False #username DNE in table

#Purpose: checks if username is taken by checking all 3 user databases (returns true if it is)
def isUsernameTaken(username, cursor, cnx): 
        #the 2 queries need to have the same # of attributes in the select
    query = ("SELECT username FROM providerTable WHERE username = %s" ) 
        #because the provider table will always be smaller, always query it first
    cursor.execute(query, (username,))
    for item in cursor:
        return True #if this is a provider, if will not query the patientTable
    
    query = ("SELECT username FROM patientTable WHERE username = %s") 
    cursor.execute(query, (username, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True 
    
    query = ("SELECT username FROM adminTable WHERE username = %s") 
    cursor.execute(query, (username, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True 
    
    return False #it was queried in both tables and neither matched

#Purpose: iterates over all users that this provider user has been assigned and updates the care team assignment
def removeDrFromAllCareTeams(username, cursor, cnx):
    assignedPatients = returnPatientsAssignedToDr(username, cursor, cnx)
    for patient in assignedPatients:
        update_test = (
                "UPDATE patientTable SET providerOne=%s "
                "WHERE username = %s AND providerOne = %s")
        cursor.execute(update_test, ("N/A", patient, username))
        cnx.commit()
        update_test = (
                "UPDATE patientTable SET providerTwo=%s "
                "WHERE username = %s AND providerTwo = %s")
        cursor.execute(update_test, ("N/A", patient, username))
        cnx.commit()
        update_test = (
                "UPDATE patientTable SET providerThree=%s "
                "WHERE username = %s AND providerThree = %s")
        cursor.execute(update_test, ("N/A", patient, username))
        cnx.commit()

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
        
    query = ("SELECT username FROM providerTable")         
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un in cursor:
        userArr.append(un[0])
    
    query = ("SELECT username FROM adminTable")         
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un in cursor:
        userArr.append(un[0])
        
    return userArr

#Purpose: returns an array of all VERIFIED usernames in the patient table that have been assigned this 
#   provider user as part of their care team
def returnPatientsAssignedToDr(username, cursor, cnx): 
    query = ("SELECT username FROM patientTable WHERE verified = %s AND (providerOne = %s OR providerTwo = %s OR providerThree = %s)")         
    cursor.execute(query, ("1",username,username,username)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for un in cursor:
        patientArr.append(un[0])
    return patientArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for VERIFIED provider users
def searchProviderList(cursor, cnx):
    query = ("SELECT username, fname, lname FROM providerTable WHERE verified = %s")         
    cursor.execute(query, ("1",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        docArr.append(tmp)
    docArr.append("TreeoHelp - help, treeo")
    return docArr

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for VERIFIED patient users
def searchPatientList(cursor, cnx):
    query = ("SELECT username, fname, lname FROM patientTable WHERE verified = %s")         
    cursor.execute(query, ("1",)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for un,fn,ln in cursor:
        patientArr.append(str(un+" - "+ln+", "+fn))
    return patientArr

#Purpose: update provider user to no longer be verified (done by admin)
def unverifyProvider(username, cursor, cnx):
    update_test = (
                "UPDATE providerTable SET verified = %s "
                "WHERE username = %s")
    cursor.execute(update_test, ("0",username ))
    cnx.commit()
    return "success"

#Purpose: update patient/provider user acct details only after verifying they are all valid 
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
        if(type(result)==providerUserClass):
            update_test = (
                "UPDATE providerTable SET email=%s, fname=%s, lname=%s"
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
        if(type(result)==providerUserClass):
            update_test = (
                "UPDATE providerTable SET email=%s, fname=%s, lname=%s, password = %s "
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

#Purpose: returns a class object with all database items packaged in it for any patient or provider user
def userAcctInfo(user, cursor, cnx):
    query = ("SELECT username, password, fname, lname, email, creationDate, providerType FROM providerTable WHERE username = %s")   
    cursor.execute(query, (user, ))
    for u,p, f, l, e, cD, dT in cursor:
        providerClassObj = providerUserClass( u, p, e, f, l, cD, dT)
        return providerClassObj
    
    query = ("SELECT username, password, fname, lname, email, creationDate, providerOne, providerTwo, providerThree, verified FROM patientTable WHERE username = %s")   
    cursor.execute(query, (user, ))
    for u, p,f, l, e, cD, d1, d2, d3, v in cursor:
        patientClassObj = patientUserClass(u,p,e, f, l, cD, 
                                            d1, d2, d3,v)
        return patientClassObj

    return

#Purpose: update patient account to be verified (after they verify through email)
def verifyPatient(username, cursor, cnx):
    update_test = (
                "UPDATE patientTable SET verified = %s "
                "WHERE username = %s")
    cursor.execute(update_test, ("1",username ))
    cnx.commit()
    return "success"

    
#Purpose: update provider user to be verified (done by admin)
def verifyProvider(username, cursor, cnx):
    update_test = (
                "UPDATE providerTable SET verified = %s "
                "WHERE username = %s")
    cursor.execute(update_test, ("1",username ))
    cnx.commit()
    return "success"


cursor.close()
cnx.close()