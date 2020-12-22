import mysql.connector
from mysql.connector import errorcode
import sys
# import boto3
import os

from datetime import date, datetime,timezone

config = {
  'host':'treeo-server.mysql.database.azure.com',
  'user':'treeo_master@treeo-server',
  'password':'Password1',
  'database':'treeohealthdb'
}

try:
   conn = mysql.connector.connect(**config)
   print("Connection established")
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with the user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
  cursor = conn.cursor()


# cnx = mysql.connector.connect(user='root', password='password',
#                               host='127.0.0.1')
# #cnx = mysql.connector.connect(user='root',password='password')
# # cursor = cnx.cursor()

#create a new database for treeo

# DB_NAME = 'treeoHealthDB'
# cursor.execute(
#    "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))

#make messageDB table

#~~~~~~~~~~~~~~~~~~~~~~~~~~~ONE TIME CODE FOR DB SETUP ~~~~~~~~~~~~~~~~~~~~~~

DB_NAME = 'treeoHealthDB'
cursor.execute("USE {}".format(DB_NAME))
cursor.execute("DROP TABLE IF EXISTS messageDB;")
print("Finished dropping table (if existed).")
cursor.execute("CREATE TABLE messageDB ("
       "  messageID varchar(30) NOT NULL,"
       "  sender varchar(40) NOT NULL,"
       "  reciever varchar(40) NOT NULL,"
       "  subject varchar(70) NOT NULL,"
       "  msgbody varchar(700) NOT NULL,"
       "  convoID varchar(30) NOT NULL,"
       "  send_time varchar(30) NOT NULL,"
       "  send_date varchar(30) NOT NULL,"
       "  read_status varchar(10) NOT NULL,"
       "  sender_loc varchar(30) NOT NULL,"
       "  reciever_loc varchar(30) NOT NULL,"
       "  perm_del varchar(5) NOT NULL,"
       "  PRIMARY KEY (messageID), UNIQUE KEY messageID (messageID)"
       ") ENGINE=InnoDB"
   )
print("Finished creating table.")
formatInsert = ("INSERT INTO messageDB "
                   "(messageID, sender,reciever,subject,"
                    "msgbody,convoID,send_time,send_date,"
                    "read_status,sender_loc,reciever_loc,perm_del) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
insertContent = ("A", "B", "C", "D",
                             "E", "F",
                             str(datetime.now().strftime('%H:%M:%S')),str(date.today().strftime("%B %d, %Y")),
                             "G", "H","I", "J")
cursor.execute(formatInsert, insertContent)

cursor.execute("SELECT * FROM messageDB;")
rows = cursor.fetchall()
for r in rows:
   print(r)
conn.commit()
cursor.close()
conn.close()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#create a new table
####DB_NAME = 'testDB'
####cursor.execute("USE {}".format(DB_NAME))
####
####cursor.execute("CREATE TABLE `testDB` ("
####    "  `msgID` int(14) NOT NULL,"
####    "  `msgBody` varchar(40) NOT NULL,"
####    "  PRIMARY KEY (`msgID`), UNIQUE KEY `msgID` (`msgID`)"
####    ") ENGINE=InnoDB"
####    )


#insert an item into a table
####messageID = ""
####messageID= messageID+str(datetime.now().strftime('%H%M%S'))
####messageID= messageID+str(datetime.now()).split(".")[1]
####
####DB_NAME = 'testDB'
####cursor.execute("USE {}".format(DB_NAME))
####formatInsert = ("INSERT INTO testDB "
####               "(msgID, msgBody) "
####               "VALUES (%s, %s)") #NOTE: use %s even with numbers
####insertContent = (int(messageID[:10]), 'Hello World')
####    #NOTE: 10 digit limit because of int type (use long for longer numbers)
####
####cursor.execute(formatInsert, insertContent)
####cnx.commit()


#query a table
####DB_NAME = 'testDB'
####cursor.execute("USE {}".format(DB_NAME))
####query = ("SELECT msgID, msgBody FROM testDB "
####         "WHERE msgID = %s")         #BETWEEN %s AND %s")
####cursor.execute(query, (2116405525,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
####
####for (msgID, msgBody) in cursor:
####    print(msgID, msgBody)
####print(cursor)

#scan all items in a table
####DB_NAME = 'testDB'
####cursor.execute("USE {}".format(DB_NAME))
####query = ("SELECT * FROM testDB ")         #BETWEEN %s AND %s")
####cursor.execute(query) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE
####
####for item in cursor:
####    print(item) #each item = a row = a tuple
####print(cursor)

#update an item in the table
####DB_NAME = 'testDB'
####cursor.execute("USE {}".format(DB_NAME))
####update_test = (
####  "UPDATE testDB SET msgBody = %s "
####  "WHERE msgID = %s")
####cursor.execute(update_test, ("Goodbye world.",2116405525))
####cnx.commit()


#delete an item in the table
####DB_NAME = 'testDB'
####cursor.execute("USE {}".format(DB_NAME))
####delete_test = (
####  "DELETE FROM testDB " #table name NOT db name
####  "WHERE msgID = %s")
####cursor.execute(delete_test, (4421883,))
####cnx.commit()
#####4421883


# cursor.close()
# cnx.close()
