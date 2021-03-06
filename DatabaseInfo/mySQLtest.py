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

DB_NAME = 'treeo_health_db'
cursor.execute("USE {}".format(DB_NAME))
# cursor.execute("DROP TABLE IF EXISTS userTable;")
# cursor.execute("DROP TABLE IF EXISTS providerTable;")
# cursor.execute("DROP TABLE IF EXISTS patientTable;")
# cursor.execute("DROP TABLE IF EXISTS archiveApptTable;")

# cursor.execute("DROP TABLE IF EXISTS apptTable;")
cursor.execute("DROP TABLE IF EXISTS patientTable;")
#cursor.execute("DROP TABLE IF EXISTS doctorTable;")
# cursor.execute("DROP TABLE IF EXISTS archiveApptTable;")
print("Finished dropping table (if existed).")

# cursor.execute("CREATE TABLE providerTable ("
#        "  username varchar(30) NOT NULL,"
#        "  password varchar(100) NOT NULL,"
#        "  email varchar(50) NOT NULL,"
#        "  fname varchar(30) NOT NULL,"
#        "  lname varchar(30) NOT NULL,"
#        "  providerType varchar(30) NOT NULL,"
#        "  creationDate varchar(50) NOT NULL,"
#        "  verified varchar(10) NOT NULL,"
#        "  PRIMARY KEY (username), UNIQUE KEY username (username)"
#        ") ENGINE=InnoDB"
#    )

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


# cursor.execute("CREATE TABLE apptTable ("
#        "  mtgID varchar(30) NOT NULL,"
#        "  provider varchar(30) NOT NULL,"
#        "  patient varchar(30) NOT NULL,"
#        "  mtgName varchar(100) NOT NULL,"
#        "  startTime varchar(50) NOT NULL,"
#        "  joinURL varchar(100) NOT NULL,"
#        "  PRIMARY KEY (mtgID), UNIQUE KEY mtgID (mtgID)"
#        ") ENGINE=InnoDB"
#    )

# cursor.execute("CREATE TABLE archiveApptTable ("
#        "  mtgID varchar(30) NOT NULL,"
#        "  provider varchar(30) NOT NULL,"
#        "  patient varchar(30) NOT NULL,"
#        "  mtgName varchar(100) NOT NULL,"
#        "  startTime varchar(50) NOT NULL,"
#        "  PRIMARY KEY (mtgID), UNIQUE KEY mtgID (mtgID)"
#        ") ENGINE=InnoDB"
#    )





# cursor.execute("CREATE TABLE adminTable ("
#        "  username varchar(30) NOT NULL,"
#        "  password varchar(100) NOT NULL,"
#        "  fname varchar(30) NOT NULL,"
#        "  lname varchar(30) NOT NULL,"
#        "  creationDate varchar(50) NOT NULL,"
#        "  PRIMARY KEY (username), UNIQUE KEY username (username)"
#        ") ENGINE=InnoDB"
#    )




# cursor.execute("DROP TABLE IF EXISTS apptTable;")
# print("Finished dropping table (if existed).")
# cursor.execute("CREATE TABLE apptTable ("
#        "  mtgID varchar(30) NOT NULL,"
#        "  provider varchar(50) NOT NULL,"
#        "  patient varchar(50) NOT NULL,"
#        "  mtgName varchar(150) NOT NULL,"
#        "  startTime varchar(40) NOT NULL,"
#        "  joinURL varchar(300) NOT NULL,"
#        "  PRIMARY KEY (mtgID), UNIQUE KEY mtgID (mtgID)"
#        ") ENGINE=InnoDB"
#    )
print("Finished creating table.")
# formatInsert = ("INSERT INTO messageDB "
#                    "(messageID, sender,reciever,subject,"
#                     "msgbody,convoID,send_time,send_date,"
#                     "read_status,sender_loc,reciever_loc,perm_del) "
#                    "VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
# insertContent = (str(datetime.now().strftime('%H%M%S')), "B", "C", "D",
#                              "E", "F",
#                              str(datetime.now().strftime('%H:%M:%S')),str(date.today().strftime("%B %d, %Y")),
#                              "G", "H","I", "J")
# cursor.execute(formatInsert, insertContent)

# cursor.execute("SELECT * FROM messageDB;")
# rows = cursor.fetchall()
# for r in rows:
#    print(r)
# conn.commit()
cursor.close()
conn.close()
