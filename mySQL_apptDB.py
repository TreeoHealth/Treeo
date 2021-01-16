
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


def getAllApptsFromUsername(username, cursor, cnx):
    query = ("SELECT mtgID, mtgName, startTime FROM apptTable WHERE doctor = %s OR patient = %s")         #BETWEEN %s AND %s")
    cursor.execute(query, (username, username)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
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

def archiveAppt(mtgid, cursor, cnx):
    apptDetails=getApptFromMtgId(mtgid,cursor,cnx)
        #(mI, d, p, mN, sT, jU)
    formatInsert = ("INSERT INTO archiveApptTable "
                   "(mtgID, patient,doctor,"
                    "startTime) "
                   "VALUES (%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (apptDetails[0], apptDetails[2], apptDetails[1], apptDetails[4])
    cursor.execute(formatInsert, insertContent)
    cnx.commit()
    deleteAppt(mtgid,cursor,cnx)
    

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