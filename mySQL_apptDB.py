
import mysql.connector
from mysql.connector import errorcode

from password_strength import PasswordPolicy
from passlib.context import CryptContext
import email_validator
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
from datetime import date, datetime,timezone

config = {
  'host':'treeo-server.mysql.database.azure.com',
  'user':'treeo_master@treeo-server',
  'password':'Password1',
  'database':'treeohealthdb'
}
cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()
cursor.execute("USE treeoHealthDB")

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )

def insertUser(username, password, email, fname, lname, docStatus, cursor, cnx):
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

    if docStatus!='doctor' and docStatus!='patient':
        return "bad status specifier"

    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )

    formatInsert = ("INSERT INTO userTable "
                   "(username, password,email,fname,"
                    "lname,docStatus,creationDate) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s)") #NOTE: use %s even with numbers
    insertContent = (username, pwd_context.hash(password), email, fname, lname, docStatus, str(date.today().strftime("%B %d, %Y")))
    cursor.execute(formatInsert, insertContent)
    cnx.commit()

    return "success"


def isUsernameTaken(username, cursor, cnx):
    query = ("SELECT username FROM userTable WHERE username = %s")         #BETWEEN %s AND %s")
    cursor.execute(query, (username, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True
    return False


def checkUserLogin(username, pwrd, cursor, cnx):
    query = ("SELECT username, password FROM userTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )
    for usern, password in cursor:
        if( False==(pwd_context.verify(pwrd, password))):
            print("WRONG PASSWORD")
            return False
        else:
            return True
    print("bad username")
    return False
    

def returnAllPatients(cursor, cnx): 
    query = ("SELECT username FROM userTable")         #BETWEEN %s AND %s")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for un in cursor:
        patientArr.append(un[0])
    return patientArr

def searchPatientList(cursor, cnx):
    query = ("SELECT username, fname, lname, docStatus FROM userTable")         #BETWEEN %s AND %s")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for un,fn,ln,dcS in cursor:
        if(dcS == 'patient'):
            tmp = str(un+" - "+ln+", "+fn)
            patientArr.append(tmp)
    return patientArr

def searchDoctorList(cursor, cnx):
    query = ("SELECT username, fname, lname, docStatus FROM userTable")         #BETWEEN %s AND %s")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    docArr = []
    for un,fn,ln,dcS in cursor:
        if(dcS == 'doctor'):
            tmp = str(un+" - "+ln+", "+fn)
            docArr.append(tmp)
    return docArr

def getAcctFromUsername(username, cursor, cnx):
    query = ("SELECT username, fname, lname, docStatus, email, creationDate FROM userTable WHERE username = %s")   
    cursor.execute(query, (username, ))
    for u, f, l, dS, e, cD in cursor:
        return (u, dS, str(f+" "+l), e, cD)
    return

def userAcctInfo(user, cursor, cnx):
    query = ("SELECT email, fname, lname, password FROM userTable WHERE username = %s")   
    cursor.execute(query, (user, ))
    for emailAdd,fn, ln,passw in cursor:
        return (emailAdd,fn, ln,passw)
    return
    

def updateUserAcct(user, emailAdd,fn, ln,passw, cursor, cnx):
    if(passw==""): #if password is not being updated
        try:
            valid = validate_email(emailAdd)
        except:
            return "bad email or domain"
    
        if len(fn)<2 or len(ln)<2:
            return "short name error"
        
        update_test = (
            "UPDATE userTable SET email=%s, fname=%s, lname=%s"
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

        update_test = (
                "UPDATE userTable SET email=%s, fname=%s, lname=%s, password = %s "
                "WHERE username = %s")
        cursor.execute(update_test, (emailAdd, fn, ln, pwd_context.hash(passw), user))
        cnx.commit()
        return "success"


    
    
    

def deleteUserAcct(username, cursor, cnx):
    delete_test = (
        "DELETE FROM userTable " #table name NOT db name
        "WHERE username = %s")
    cursor.execute(delete_test, (username,))
    cnx.commit()
    return "deleted "+username


def getAllApptsFromUsername(username, cursor, cnx):
    query = ("SELECT mtgID, mtgName, startTime FROM apptTable")         #BETWEEN %s AND %s")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for mI, mN, sT in cursor:
        patientArr.append([mI, mN, sT])
    return patientArr

def isMeetingIDValid(mtgid, cursor, cnx):
    query = ("SELECT mtgID FROM apptTable WHERE mtgID = %s")         #BETWEEN %s AND %s")
    cursor.execute(query, (mtgid, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True
    return False

def getApptFromMtgId(mtgid, cursor, cnx):
    query = ("SELECT mtgID, doctor, patient, mtgName, startTime, joinURL FROM apptTable")         #BETWEEN %s AND %s")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for mI, d, p, mN, sT, jU in cursor:
        return (mI, d, p, mN, sT, jU)

def createAppt(mtgName, mtgid, doctor, patient, start_time, joinURL, cursor, cnx):
    formatInsert = ("INSERT INTO apptTable "
                   "(mtgID, doctor,patient,mtgName,"
                    "startTime,joinURL) "
                   "VALUES (%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (mtgid, doctor, patient, mtgName, start_time, joinURL)
    cursor.execute(formatInsert, insertContent)
    cnx.commit()
    return "success create"

def deleteAppt(mtgid, cursor, cnx):
    delete_test = (
        "DELETE FROM apptTable " #table name NOT db name
        "WHERE mtgID = %s")
    cursor.execute(delete_test, (mtgid,))
    cnx.commit()
    # for item in cursor:
    #     return "deleted "+mtgid
    

def updateAppt(mtgName, mtgid,start_time, cursor, cnx): 
    update_test = (
                "UPDATE apptTable SET mtgName=%s, startTime=%s "
                "WHERE mtgID = %s")
    cursor.execute(update_test, (mtgName,start_time, mtgid))
    cnx.commit()
    return "success update"

# query = ("SELECT * FROM apptTable ")         #BETWEEN %s AND %s")
# cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
# for item in cursor:
#    print(item) #each item = a row = a tuple


cursor.close()
cnx.close()