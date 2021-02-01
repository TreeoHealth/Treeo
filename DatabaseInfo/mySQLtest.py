import mysql.connector
from mysql.connector import errorcode
import sys
# import boto3
import os

from datetime import date, datetime,timezone

# config = {
#   'host':'treeo-server.mysql.database.azure.com',
#   'user':'treeo_master@treeo-server',
#   'password':'Password1',
#   'database':'treeohealthdb'
# }

try:
  conn = mysql.connector.connect(user='root', password='#GGnorem8',
                              host='127.0.0.1')
  #  conn = mysql.connector.connect(**config)
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



#create a new database for treeo

DB_NAME = 'treeo_health_DB'
cursor.execute(
   "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))

#make messageDB table

#~~~~~~~~~~~~~~~~~~~~~~~~~~~ONE TIME CODE FOR DB SETUP ~~~~~~~~~~~~~~~~~~~~~~
DB_NAME = 'treeo_health_DB'
cursor.execute("USE {}".format(DB_NAME))
cursor.execute("DROP TABLE IF EXISTS adminTable;")
cursor.execute("DROP TABLE IF EXISTS apptTable;")
cursor.execute("DROP TABLE IF EXISTS archiveApptTable;")
cursor.execute("DROP TABLE IF EXISTS messageDB;")
cursor.execute("DROP TABLE IF EXISTS patientTable;")
cursor.execute("DROP TABLE IF EXISTS providerTable;")




print("Finished dropping table (if existed).")



cursor.execute("CREATE TABLE adminTable ("
       "  username varchar(30) NOT NULL,"
       "  password varchar(100) NOT NULL,"
       "  fname varchar(30) NOT NULL,"
       "  lname varchar(30) NOT NULL,"
       "  creationDate varchar(50) NOT NULL,"
       "  PRIMARY KEY (username), UNIQUE KEY username (username)"
       ") ENGINE=InnoDB"
   )

cursor.execute("CREATE TABLE apptTable ("
       "  mtgID varchar(30) NOT NULL,"
       "  provider varchar(30) NOT NULL,"
       "  patient varchar(30) NOT NULL,"
       "  mtgName varchar(100) NOT NULL,"
       "  startTime varchar(50) NOT NULL,"
       "  joinURL varchar(100) NOT NULL,"
       "  PRIMARY KEY (mtgID), UNIQUE KEY mtgID (mtgID)"
       ") ENGINE=InnoDB"
   )

cursor.execute("CREATE TABLE archiveApptTable ("
       "  mtgID varchar(30) NOT NULL,"
       "  provider varchar(30) NOT NULL,"
       "  patient varchar(30) NOT NULL,"
       "  mtgName varchar(100) NOT NULL,"
       "  startTime varchar(50) NOT NULL,"
       "  PRIMARY KEY (mtgID), UNIQUE KEY mtgID (mtgID)"
       ") ENGINE=InnoDB"
   )

cursor.execute("CREATE TABLE messageDB ("
       "  messageID varchar(30) NOT NULL,"
       "  sender varchar(75) NOT NULL,"
       "  reciever varchar(75) NOT NULL,"
       "  subject varchar(150) NOT NULL,"
       "  msgbody varchar(600) NOT NULL,"
       "  convoID varchar(30) NOT NULL,"
       "  send_time varchar(30) NOT NULL,"
       "  send_date varchar(50) NOT NULL,"
       "  read_status varchar(30) NOT NULL,"
       "  sender_loc varchar(30) NOT NULL,"
       "  reciever_loc varchar(30) NOT NULL,"
       "  perm_del varchar(10) NOT NULL,"
       "  PRIMARY KEY (messageID), UNIQUE KEY messageID (messageID)"
       ") ENGINE=InnoDB"
   )

cursor.execute("CREATE TABLE patientTable ("
       "  username varchar(30) NOT NULL,"
       "  password varchar(100) NOT NULL,"
       "  email varchar(50) NOT NULL,"
       "  fname varchar(30) NOT NULL,"
       "  lname varchar(30) NOT NULL,"
       "  creationDate varchar(50) NOT NULL,"
       "  providerOne varchar(50) NOT NULL,"
       "  providerTwo varchar(50) NOT NULL,"
       "  providerThree varchar(50) NOT NULL,"
       "  verified varchar(50) NOT NULL,"
       "  PRIMARY KEY (username), UNIQUE KEY username (username)"
       ") ENGINE=InnoDB"
   )

cursor.execute("CREATE TABLE providerTable ("
       "  username varchar(30) NOT NULL,"
       "  password varchar(100) NOT NULL,"
       "  email varchar(50) NOT NULL,"
       "  fname varchar(30) NOT NULL,"
       "  lname varchar(30) NOT NULL,"
       "  providerType varchar(30) NOT NULL,"
       "  creationDate varchar(50) NOT NULL,"
       "  verified varchar(10) NOT NULL,"
       "  PRIMARY KEY (username), UNIQUE KEY username (username)"
       ") ENGINE=InnoDB"
   )

print("Finished creating tables.")

cursor.close()
conn.close()
