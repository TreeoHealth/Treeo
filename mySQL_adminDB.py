import mysql.connector
from password_strength import PasswordPolicy
from passlib.context import CryptContext
import email_validator
from datetime import date, datetime,timezone
import mySQL_userDB

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

#Purpose: returns an array of the search dropdown items (username + first name + last name)
#   for admin, doctor and patient users 
def adminAllSearchUsers(cursor, cnx): 
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
    query=("SELECT username, fname, lname FROM adminTable")
    cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
    for un,fn,ln in cursor:
        tmp = str(un+" - "+ln+", "+fn)
        nameArr.append(tmp)
    return nameArr

#Purpose: check info sent then (if verified) insert into database. Otherwise, return string error msg.
def createAdminUser(username, pw, fn, ln, cursor, cnx):
    if(mySQL_userDB.isUsernameTaken(username,cursor, cnx)):
        return "taken error"
    policy = PasswordPolicy.from_names(
            length=8,  # min length: 8
            uppercase=1,  # need min. 2 uppercase letters
            numbers=1  # need min. 2 digits
            )
    isEnough = policy.test(pw)
    if len(isEnough)!=0:
        return "weak password"
    
    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
    )
  
    formatInsert = ("INSERT INTO adminTable "
                   "(username, password,fname,"
                    "lname,creationDate) "
                   "VALUES (%s, %s,%s, %s,%s)") #NOTE: use %s even with numbers
    
        #their care team is not assigned at creation, so N/A
    insertContent = (username, pwd_context.hash(pw), fn, ln, str(date.today().strftime("%B %d, %Y")))
    cursor.execute(formatInsert, insertContent)
    cnx.commit()

    return "success"
    
#Purpose: return array of all admin usernames
def getAllAdminUsers(cursor, cnx):
    query = ("SELECT username, password FROM adminTable")
    cursor.execute(query)
    admins=[]
    for un, pw in cursor: 
        admins.append(un)
    return admins

#Purpose: check username/password for logging into an admin acct
def verifyAdminLogin(un, pwrd, cursor, cnx):
    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000 #num of times it will hash before writing
    )
    
    query = ("SELECT username, password FROM adminTable WHERE username = %s")
    cursor.execute(query, (un, ))
    for un, pw in cursor: #this loop will not be entered if it does not exist in the doctorDB
        if( True==(pwd_context.verify(pwrd, pw))):
            return True
        else: #because there can only be 1 match, this query can only be run 1 time max (not O(n^2))
            print("WRONG PASSWORD")
            return False
    return False


cursor.close()
cnx.close()