import mysql.connector
from mysql.connector import errorcode

from datetime import date, datetime,timezone


cnx = mysql.connector.connect(user='root', password='password',
                              host='127.0.0.1')


#cnx = mysql.connector.connect(user='root',password='password')
cursor = cnx.cursor()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~ONE TIME CODE FOR DB SETUP ~~~~~~~~~~~~~~~~~~~~~~
#create a new database for treeo
####
####DB_NAME = 'treeoHealthDB'
####cursor.execute(
####    "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))

#make messageDB table
##                        'messageID':{"N":messageID},
##			'sender':{"S":sender},
##			'reciever': {"S":reciever},
##			'subject': {"S":subject},
##			'msgbody':{"S":body},
##			'convoID': {"N":messageID},
##			'send_time': {"S":str(datetime.now().strftime('%H:%M:%S'))},
##			'send_date':{"S":str(date.today().strftime("%B %d, %Y"))},
##			'read_status':{"S":"unread"},
##			'sender_loc':{"S":"sent_folder"}, #sent_folder, deleted (in trash), [tbd - draft]
##			'reciever_loc':{"S":"inbox"}, #inbox (in inbox), deleted (in trash)
##			'perm_del':{"S":"n"} #n = neither, r = reciever, s = sender, sr = delete from database
######DB_NAME = 'treeoHealthDB'
######cursor.execute("USE {}".format(DB_NAME))
######cursor.execute("CREATE TABLE `messageDB` ("
######        "  `messageID` varchar(30) NOT NULL,"
######        "  `sender` varchar(40) NOT NULL,"
######        "  `reciever` varchar(40) NOT NULL,"
######        "  `subject` varchar(70) NOT NULL,"
######        "  `msgbody` varchar(700) NOT NULL,"
######        "  `convoID` varchar(30) NOT NULL,"
######        "  `send_time` varchar(30) NOT NULL,"
######        "  `send_date` varchar(30) NOT NULL,"
######        "  `read_status` varchar(10) NOT NULL,"
######        "  `sender_loc` varchar(30) NOT NULL,"
######        "  `reciever_loc` varchar(30) NOT NULL,"
######        "  `perm_del` varchar(5) NOT NULL,"
######        "  PRIMARY KEY (`messageID`), UNIQUE KEY `messageID` (`messageID`)"
######        ") ENGINE=InnoDB"
######    )

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

cursor.close()
cnx.close()
