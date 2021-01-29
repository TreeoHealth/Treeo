import mysql.connector
from mysql.connector import errorcode
from classFile import apptObjectClass
from password_strength import PasswordPolicy
from passlib.context import CryptContext
import email_validator
from datetime import date, datetime,timezone, timedelta

# config = {
#   'host':'treeo-server.mysql.database.azure.com',
#   'user':'treeo_master@treeo-server',
#   'password':'Password1',
#   'database':'treeohealthdb'
# }
# cnx = mysql.connector.connect(**config)
cnx = mysql.connector.connect(user='root', password='password',
                              host='127.0.0.1')
cursor = cnx.cursor()
cursor.execute("USE treeo_health_db")

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )

#Purpose: add meeting to archive database and delete if from the current meetings database
def archiveAppt(mtgid, cursor, cnx):
    apptDetails=getApptFromMtgId(mtgid,cursor,cnx)
    formatInsert = ("INSERT INTO archiveApptTable "
                   "(mtgID, patient,provider,mtgName,"
                    "start_time) "
                   "VALUES (%s, %s,%s, %s, %s)") #NOTE: use %s even with numbers
    insertContent = (apptDetails.meetingID, apptDetails.patient, apptDetails.provider, apptDetails.meetingName, apptDetails.startTime)
    cursor.execute(formatInsert, insertContent)
    cnx.commit()
    deleteAppt(mtgid,cursor,cnx)

#Purpose: add meeting to the current meetings database
def createAppt(mtgName, mtgid, provider, patient, start_time, joinURL, cursor, cnx):
    formatInsert = ("INSERT INTO apptTable "
                   "(mtgID, provider,patient,mtgName,"
                    "startTime,joinURL) "
                   "VALUES (%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (mtgid, provider, patient, mtgName, start_time, joinURL)
    cursor.execute(formatInsert, insertContent)
    cnx.commit()
    return "success create"

#Purpose: when a patient deletes their acct, update all archive entries they are a part of to
#   be a [deleted] username (so they don't show up when you query for original username)
def deactivateAllArchivedAppts(username, cursor, cnx):
    update_test = (
                "UPDATE archiveApptTable SET patient=%s "
                "WHERE patient = %s")
    cursor.execute(update_test, (str(username+" [deleted]"),username))
    cnx.commit()
    return "success update"

#Purpose: delete meeting from the current meetings database
def deleteAppt(mtgid, cursor, cnx):
    delete_test = (
        "DELETE FROM apptTable " #table name NOT db name
        "WHERE mtgID = %s")
    cursor.execute(delete_test, (mtgid,))
    cnx.commit()
    # for item in cursor:
    #     return "deleted "+mtgid
 
#Purpose: return an array of appointment class objects where each obj holds an appt
#   that the username is involved in (patient or provider)
def getAllApptsFromUsername(username, tempcursor, cursor, cnx):
    query = ("SELECT mtgID, provider, patient, mtgName, startTime, joinURL FROM apptTable WHERE provider = %s OR patient = %s")         
    cursor.execute(query, (username, username)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    apptArr = []
    for mI, d, p, mN, sT, jU in cursor:  
        
        startDate= sT.split('T')[0]
        if(datetime.now().strftime('%Y-%m-%d')>startDate): #if the date of the appt is past todays date FULLY, archive it
            archiveAppt(mI, tempcursor, cnx)
        else: #else it's today or later so keep it in the calendar
            apptArr.append(apptObjectClass (mI, d, p, mN, sT, jU) )  
    return apptArr

#Purpose: return an appointment class object that holds all details of queried mtg
def getApptFromMtgId(mtgid, cursor, cnx):
    query = ("SELECT mtgID, provider, patient, mtgName, startTime, joinURL FROM apptTable WHERE mtgID = %s")         
    cursor.execute(query, (mtgid,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for mI, d, p, mN, sT, jU in cursor:  
        apptClassObj = apptObjectClass (mI, d, p, mN, sT, jU)   
        return apptClassObj
 
#Purpose: return true if appt is in the table, false if it is not
def isMeetingIDValid(mtgid, cursor, cnx):
    query = ("SELECT mtgID FROM apptTable WHERE mtgID = %s")         
    cursor.execute(query, (mtgid, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True
    return False

#Purpose: if the start time of the mtg is past the current time, this will return true (otherwise, false)
def isMtgStartTimePassed(mtgID, cursor, cnx):
    if(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")>getApptFromMtgId(mtgID, cursor, cnx).startTime):
        return True
    return False  

#Purpose: check if the desired start time is AT LEAST 30 mins in the future (for appt creation/updated time)
#   return true if it is 30+ mins in future, false if it is within 30 mins of now
def isTime30MinInFuture(startTime):
    if((datetime.now()+ timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")<=startTime):
        return True
    return False  

#Purpose: update the meeting details of the meeting in the table
def updateAppt(mtgName, mtgid,start_time, cursor, cnx): 
    update_test = (
                "UPDATE apptTable SET mtgName=%s, startTime=%s "
                "WHERE mtgID = %s")
    cursor.execute(update_test, (mtgName,start_time, mtgid))
    cnx.commit()
    return "success update"


cursor.close()
cnx.close()