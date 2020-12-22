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
insertContent = (str(datetime.now().strftime('%H%M%S')), "B", "C", "D",
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
