import mysql.connector
from mysql.connector import errorcode
from classFile import apptObjectClass
from password_strength import PasswordPolicy
from passlib.context import CryptContext
import email_validator
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


def getAllApptsFromUsername(username, tempcursor, cursor, cnx):
    query = ("SELECT mtgID, doctor, patient, mtgName, startTime, joinURL FROM apptTable WHERE doctor = %s OR patient = %s")         
    cursor.execute(query, (username, username)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    apptArr = []
    for mI, d, p, mN, sT, jU in cursor:  
        
        startDate= sT.split('T')[0]
        if(datetime.now().strftime('%Y-%m-%d')>startDate): #if the date of the appt is past todays date FULLY, archive it
            archiveAppt(mI, tempcursor, cnx)
        else: #else it's today or later so keep it in the calendar
            apptArr.append(apptObjectClass (mI, d, p, mN, sT, jU) ) 
#TODO -- change this    
    return apptArr

def isMeetingIDValid(mtgid, cursor, cnx):
    query = ("SELECT mtgID FROM apptTable WHERE mtgID = %s")         
    cursor.execute(query, (mtgid, )) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for item in cursor:
        return True
    return False

def getApptFromMtgId(mtgid, cursor, cnx):
    query = ("SELECT mtgID, doctor, patient, mtgName, startTime, joinURL FROM apptTable WHERE mtgID = %s")         
    cursor.execute(query, (mtgid,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    patientArr = []
    for mI, d, p, mN, sT, jU in cursor:  
        apptClassObj = apptObjectClass (mI, d, p, mN, sT, jU)   
        return apptClassObj
    #TODO -- change this    
        return (mI, d, p, mN, sT, jU)
    
def isMtgStartTimePassed(mtgID, cursor, cnx):
    print("NOW",datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "APPT TIME:", getApptFromMtgId(mtgID, cursor, cnx).startTime)
    if(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")>getApptFromMtgId(mtgID, cursor, cnx).startTime):
        print("NOW is AFTER mtg start time")
        #if the start time of the mtg is past the current time, this will return true
        return True
    print("NOW IS BEFORE mtg start time")
    return False

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
    
def deleteBadMsgs():
    delete_test = (
        "DELETE FROM messageDB " #table name NOT db name
        "WHERE sender = %s OR reciever = %s")
    cursor.execute(delete_test, ("deactivatedUser","deactivatedUser"))
    cnx.commit()

def archiveAppt(mtgid, cursor, cnx):
    apptDetails=getApptFromMtgId(mtgid,cursor,cnx)
    formatInsert = ("INSERT INTO archiveApptTable "
                   "(mtgID, patient,doctor,"
                    "start_time) "
                   "VALUES (%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (apptDetails.meetingID, apptDetails.patient, apptDetails.doctor, apptDetails.startTime)
    cursor.execute(formatInsert, insertContent)
    cnx.commit()
    deleteAppt(mtgid,cursor,cnx)
    
def deactivateAllArchivedAppts(username, cursor, cnx):
    update_test = (
                "UPDATE archiveApptTable SET patient=%s "
                "WHERE patient = %s")
    cursor.execute(update_test, (str(username+" [deleted]"),username))
    cnx.commit()
    return "success update"
    

def updateAppt(mtgName, mtgid,start_time, cursor, cnx): 
    update_test = (
                "UPDATE apptTable SET mtgName=%s, startTime=%s "
                "WHERE mtgID = %s")
    cursor.execute(update_test, (mtgName,start_time, mtgid))
    cnx.commit()
    return "success update"

# query = ("SELECT * FROM apptTable ")         
# cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
# for item in cursor:
#    print(item) #each item = a row = a tuple

cursor.close()
cnx.close()