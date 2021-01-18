from flask import Flask, render_template, request,session, jsonify
import os
import json
import datetime
from datetime import date, datetime,timezone
import time
import mySQL_apptDB
import mySQL_userDB

import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)
#cnx = mysql.connector.connect(user='root', password='password',
#                              host='127.0.0.1')
config = {
  'host':'treeo-server.mysql.database.azure.com',
  'user':'treeo_master@treeo-server',
  'password':'Password1',
  'database':'treeohealthdb'
}
cnx = mysql.connector.connect(**config)
tmpcursor = cnx.cursor(buffered=True) #THIS IS TO FIX "Unread result found error"
tmpcursor.execute("USE treeoHealthDB")
cursor = cnx.cursor(buffered=True) #THIS IS TO FIX "Unread result found error"
cursor.execute("USE treeoHealthDB")

@app.route('/submitEmail', methods=['POST','GET'])
def formatEmail():

    query = request.form['reciever_username']
    # insertMessage(request.form['sender_username'],
    #         request.form['reciever_username'],
    #         request.form['subject'],
    #         request.form['email_body'],
    #               "0"
    #               )
    actualUsername = (query.split(" - "))[0] #username - last name, first name
    response = mySQL_userDB.getAcctFromUsername(actualUsername, cursor, cnx)
        #(u, dS, str(f+" "+l), e, cD)
    if(len(query.split(" - "))==2): #if they chose from dropdown
       insertMessage(request.form['sender_username'],
           actualUsername,
           request.form['subject'],
           request.form['email_body'],
                 "0"
                 )
    elif(mySQL_userDB.isUsernameTaken(query, cursor, cnx)): #if it is a raw usern (not from dropdown)
       insertMessage(request.form['sender_username'],
           request.form['reciever_username'],
           request.form['subject'],
           request.form['email_body'],
                 "0"
                 )
    else: #invalid username
       return render_template("newEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          sender_username = session['username'],
                          errorMsg="Please enter a valid user ID",
                          reciever_username="",
                          subject = request.form['subject'],
                          email_body = request.form['email_body'])
    msgListObj = getAllMessages(session['username'])
    if(len(msgListObj)==0):
       return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
    else:
       return openInbox()

@app.route('/submitReplyEmail', methods=['POST','GET'])
def formatReplyEmail():
   insertMessage(request.form['sender_username'],
       request.form['reciever_username'],
       request.form['subject'],
       request.form['email_body'],
       request.form['headMsgID']
                 )
   msgListObj = getAllMessages(session['username'])
   if(len(msgListObj)==0):
       return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
   else:
       return openInbox()

@app.route('/sentFolder', methods=['POST','GET'])
def sentFolder():
    return renderPagedSent(0)


def renderPagedSent(pgNum):
    
    pageSize = 10
    msgList = getAllMessagesSent(session['username'])
    pageNumber = int(pgNum)
    if(pageNumber<0):
        pageNumber=0 #first page
    elif pageNumber>(len(msgList)/pageSize):
        pageNumber=(len(msgList)/pageSize) #final possible page number

    if(len(msgList)==0): #if the query is empty
        #return (False, [], False) #no prev, no next
        return render_template("emptySent.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = ""
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        #return (True, msgList[pageNumber*pageSize:], False)
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = True,
                          currPageNum = pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:])
    elif(pageNumber==0 and pageSize<len(msgList)): #this is the first page and there is a next page
        #return (False, msgList[0:pageSize-1], True)
        #print("HERE", msgList[0:pageSize])
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = pageSize,
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:pageSize])
    elif(pageNumber==0): #this is the first and only page
        #return (False, msgList[0:], False)
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = True,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:])
    else: #there is a prev and next page
        #return (True, msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)], True)
        return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = pageNumber*pageSize+(pageSize),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize)])


@app.route('/trashFolder', methods=['POST','GET'])
def trashFolder():
    return renderPagedTrash(0)

def renderPagedTrash(pgNum):
    
    pageSize = 10
    msgList = getAllTrashMessages(session['username'])
    pageNumber = int(pgNum)
    if(pageNumber<0):
        pageNumber=0 #first page
    elif pageNumber>(len(msgList)/pageSize):
        pageNumber=(len(msgList)/pageSize) #final possible page number

    if(len(msgList)==0): #if the query is empty
        #return (False, [], False) #no prev, no next
        return render_template("emptyTrash.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = ""
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        #return (True, msgList[pageNumber*pageSize:], False)
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = True,
                          currPageNum = pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:])
    elif(pageNumber==0 and pageSize<len(msgList)): #this is the first page and there is a next page
        #return (False, msgList[0:pageSize-1], True)
        #print("HERE", msgList[0:pageSize])
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = pageSize,
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:pageSize])
    elif(pageNumber==0): #this is the first and only page
        #return (False, msgList[0:], False)
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = True,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:])
    else: #there is a prev and next page
        #return (True, msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)], True)
        return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = pageNumber*pageSize+(pageSize),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize)])


@app.route('/selectOption', methods=['POST','GET'])
def selectOption():
    x = ""
    try:
       x = str(request.form['prevPg.x'])
       pageNum = request.form['currPageNum']
       return getAllMessagesPaged(session['username'], str(int(pageNum)-1))
       
    except:
        try:
            x = str(request.form['nextPg.x'])
            pageNum = request.form['currPageNum']
            return getAllMessagesPaged(session['username'], str(int(pageNum)+1))
            
        except:
            try:
                x = str(request.form['trash.x'])
                for check in request.form:
                    if(str(check)!='trash.x' and str(check)!='trash.y' and str(check)!='selectAll'):
                        moveToTrash(str(check), session['username'])
            except:
                try:
                    x = str(request.form['mar.x'])
                    for check in request.form:
                        if(str(check)!='mar.x' and str(check)!='mar.y' and str(check)!='selectAll'):
                             markAsRead(str(check))
                except:
                    x = str(request.form['mau.x'])
                    for check in request.form:
                        if(str(check)!='mau.x' and str(check)!='mau.y' and str(check)!='selectAll'):
                            markAsUnread(str(check))

    return openInbox()



def getAllMessagesPaged(username, pgNum): #page to be rendered
#<MYSQL FUNCTIONAL>
    pageSize = 10

    query = ("SELECT send_date, send_time, subject, read_status, messageID, sender FROM messageDB "
             "WHERE reciever = %s AND reciever_loc = %s")  
    cursor.execute(query, (username,"inbox")) 
    msgList = []
    for (send_date, send_time, subject, read_status, messageID, sender) in cursor:
            if read_status=='unread':
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,True])
            else:
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,False])

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))


    pageNumber = int(pgNum)
    if(pageNumber<0):
        pageNumber=0 #first page
    elif pageNumber>(len(msgList)/pageSize):
        pageNumber=(len(msgList)/pageSize) #final possible page number

    if(len(msgList)==0): #if the query is empty
        #return (False, [], False) #no prev, no next
        return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList)) and pageNumber!=0):  #this is the final page (not not first)
        #return (True, msgList[pageNumber*pageSize:], False)
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = True,
                          currPageNum = pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:])
    elif(pageNumber==0 and pageSize<len(msgList)): #this is the first page and there is a next page
        #return (False, msgList[0:pageSize-1], True)
        #print("HERE", msgList[0:pageSize])
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = pageSize,
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:pageSize])
    elif(pageNumber==0): #this is the first and only page
        #return (False, msgList[0:], False)
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = True,
                          currPageNum =pgNum,
                          startEmailNum = 1,
                          endEmailNum = len(msgList),
                          totalEmailNum = len(msgList),
                          msgList=msgList[0:])
    else: #there is a prev and next page
        #return (True, msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)], True)
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = False,
                          currPageNum =pgNum,
                          startEmailNum = (pageNumber*pageSize)+1,
                          endEmailNum = pageNumber*pageSize+(pageSize),
                          totalEmailNum = len(msgList),
                          msgList=msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize)])


@app.route('/selectSent', methods=['POST','GET'])
def selectSent():
    try:
       x = str(request.form['prevPg.x'])
       pageNum = request.form['currPageNum']
       return renderPagedSent(str(int(pageNum)-1))
       
    except:
        try:
            x = str(request.form['nextPg.x'])
            pageNum = request.form['currPageNum']
            return renderPagedSent(str(int(pageNum)+1))
            
        except:
            try:
                x = str(request.form['trash.x'])
                for check in request.form:
                    print(check)
                    if(str(check)!='trash.x' and str(check)!='trash.y'and str(check)!='selectAll'):
                        moveToTrash(str(check), session['username'])
                return sentFolder()
            except:
                return sentFolder()


@app.route("/search/<string:box>")
def process(box):
   jsonSuggest = []
   query = request.args.get('query')
   if(session['docStatus']=='doctor'):
        listPatients= mySQL_userDB.allSearchUsers(cursor, cnx)
   else:
        listPatients= mySQL_userDB.searchDoctorList(cursor, cnx)
   for username in listPatients:
       if(query in username):
           jsonSuggest.append({'value':username,'data':username})
   return jsonify({"suggestions":jsonSuggest})

@app.route('/subjWordCheck', methods=['POST','GET'])
def subjCheck():
   text = str(len(request.args.get('jsdata')))
   text = text + "/50"
   print(text)
   return text

@app.route('/bodyWordCheck', methods=['POST','GET'])
def bodyCheck():
   text = str(len(request.args.get('jsdata')))
   text = text + "/600"
   print(text)
   return text


@app.route('/permTrash', methods=['POST','GET'])
def emptyTrash():
    x=""
    try:
       x = str(request.form['prevPg.x'])
       pageNum = request.form['currPageNum']
       return renderPagedTrash(str(int(pageNum)-1))
       
    except:
        try:
            x = str(request.form['nextPg.x'])
            pageNum = request.form['currPageNum']
            return renderPagedTrash(str(int(pageNum)+1))
            
        except:
            try:
                x = str(request.form['permdel.x'])
                for check in request.form:
                    if(str(check)!='permdel.x' and str(check)!='permdel.y' and str(check)!='selectAll'):
                        permenantDel(str(check), session['username'])
            except:
                x = str(request.form['undotrash.x'])
                for check in request.form:
                    if(str(check)!='undotrash.x' and str(check)!='undotrash.y' and str(check)!='selectAll'):
                        undoTrash(str(check), session['username'])

    return trashFolder()

   


def undoTrash(msgID, username):
    #if it is in the trash and the sender == current username -> move it to sent folder
    #else move it to inbox
#<MYSQL FUNCTIONAL>
    sender_loc='sent_folder'
    reciever_loc='inbox'

    query = ("SELECT sender, reciever FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (msgID,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE

    for (sender, reciever) in cursor:
        if sender == username:
            updateFormat = ("UPDATE messageDB SET sender_loc = %s "
                                "WHERE messageID = %s")
            cursor.execute(updateFormat, (sender_loc,msgID))
            cnx.commit()
        else:
            updateFormat = ("UPDATE messageDB SET reciever_loc = %s "
                                "WHERE messageID = %s")
            cursor.execute(updateFormat, (reciever_loc,msgID))
            cnx.commit()



def insertMessage(sender, reciever, subject,body, convoID):
#<MYSQL FUNCTIONAL>
    
    msgID= ""
    msgID= msgID+str(datetime.now().strftime('%H%M%S'))
    msgID= msgID+str(datetime.now()).split(".")[1]

    #TODO -- account for convoID 0 or not
    formatInsert = ("INSERT INTO messageDB "
                   "(messageID, sender,reciever,subject,"
                    "msgbody,convoID,send_time,send_date,"
                    "read_status,sender_loc,reciever_loc,perm_del) "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)") #NOTE: use %s even with numbers
    insertContent = (msgID, sender, reciever, subject,
                             body, (msgID if convoID == "0" else convoID),
                             str(datetime.now().strftime('%H:%M:%S')),str(date.today().strftime("%B %d, %Y")),
                             "unread", "sent_folder", "inbox", "n")

    cursor.execute(formatInsert, insertContent)
    cnx.commit()
        

@app.route('/newEmail', methods=['POST','GET'])
def newEmail():
   return render_template("newEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          sender_username = session['username'],
                          errorMsg="",
                          reciever_username="",
                          subject = "",
                          email_body = "")

def countUnreadInInbox(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT messageID FROM messageDB "
             "WHERE reciever = %s AND read_status=%s AND reciever_loc=%s")  
    cursor.execute(query, (username,'unread','inbox'))
    unreadNum = 0
    for (messageID,) in cursor:
        unreadNum = unreadNum+1
        
    if(unreadNum == 0):
        return ""
    else:
        return "("+str(unreadNum)+")"

    
  
def countUnreadInTrash(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT messageID FROM messageDB "
             "WHERE reciever = %s AND read_status=%s AND reciever_loc=%s")  
    cursor.execute(query, (username,'unread','trash'))
    unreadNum = 0
    for (messageID,) in cursor:
        unreadNum = unreadNum+1
        
    if(unreadNum == 0):
        return ""
    else:
        return "("+str(unreadNum)+")"


def markAsRead(msgID):
#<MYSQL FUNCTIONAL>
    try:
        read_status='read'
        updateFormat = ("UPDATE messageDB SET read_status = %s "
                                "WHERE messageID = %s")
        cursor.execute(updateFormat, (read_status,msgID))
        cnx.commit()

    except:
        
        return "ERROR. Could not mark as read."


    

def markAsUnread(msgID):
#<MYSQL FUNCTIONAL>
    try:
        read_status='unread'
        updateFormat = ("UPDATE messageDB SET read_status = %s "
                                "WHERE messageID = %s")
        cursor.execute(updateFormat, (read_status,msgID))
        cnx.commit()
        
    except:
        return "ERROR. Could not mark as unread."
    

def permenantDel(msgID, del_username):
#<MYSQL FUNCITIONAL>
    query = ("SELECT sender, reciever, perm_del FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (msgID,))
    perm_del = "n"
    for (sender, reciever, perm_del) in cursor:
        if sender == del_username and perm_del=='n':
            perm_del = 's'
        elif sender == del_username and perm_del=='r':
            perm_del = 'sr'
        elif reciever == del_username and perm_del=='n':
            perm_del = 'r'
        elif reciever == del_username and perm_del=='s':
            perm_del = 'sr'
        else:
            perm_del = 'n'

        if perm_del == 'sr':    
            delete_test = (
                "DELETE FROM messageDB " #table name NOT db name
                "WHERE messageID = %s")
            cursor.execute(delete_test, (msgID,))
            cnx.commit()
        else:
            updateFormat = ("UPDATE messageDB SET perm_del = %s "
                                "WHERE messageID = %s")
            cursor.execute(updateFormat, (perm_del,msgID))
            cnx.commit()

    
def moveToTrash(msgID, del_username):
#<MYSQL FUNCTIONAL>
    sender_loc='trash'
    reciever_loc='trash'

    query = ("SELECT sender, reciever FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (msgID,)) #NOTE: even if there is only 1 condition, you have to make the item passed to the query into a TUPLE

    for (sender, reciever) in cursor:
        if sender == del_username:
            updateFormat = ("UPDATE messageDB SET sender_loc = %s "
                                "WHERE messageID = %s")
            cursor.execute(updateFormat, (sender_loc,msgID))
            cnx.commit()
        else:
            updateFormat = ("UPDATE messageDB SET reciever_loc = %s "
                                "WHERE messageID = %s")
            cursor.execute(updateFormat, (reciever_loc,msgID))
            cnx.commit()


def getAllTrashMessages(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time,read_status, reciever_loc,subject, perm_del, messageID, sender, sender_loc, reciever FROM messageDB "
             "WHERE reciever = %s OR sender = %s")  
    cursor.execute(query, (username,username)) 

    trashList = []
    for (send_date, send_time,read_status, reciever_loc, subject, perm_del, messageID, sender, sender_loc, reciever) in cursor:
        dateWhole = str(send_date+ " - " +send_time)
        if (reciever==username and reciever_loc=='trash' and perm_del!='r' ) or (sender==username and sender_loc=='trash' and perm_del!='s'):
           if(reciever==username and read_status=='unread'):
               trashList.append([dateWhole,messageID,"",sender,send_date,subject,True])
           elif(sender==username):
               trashList.append([dateWhole, messageID,"To:",reciever,send_date,subject,False])
           else:
               trashList.append([dateWhole,messageID,"",sender,send_date,subject,False])
    trashList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
    return trashList


def getAllMessages(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time, subject, read_status, messageID, sender FROM messageDB "
             "WHERE reciever = %s AND reciever_loc = %s")  
    cursor.execute(query, (username,"inbox")) 
    msgList = []
    #NOTE: bc messageInbox.html is implemented with spans, spaces can't be printed, so we left the username displayed
    for (send_date, send_time, subject, read_status, messageID, sender) in cursor:
            if read_status=='unread':
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,True])
            else:
                msgList.append([str(send_date + " - " +send_time),messageID,sender,send_date,subject,False])

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
    return msgList


def getAllMessagesSent(username):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time, subject, messageID, reciever FROM messageDB "
             "WHERE sender = %s AND sender_loc = %s")  
    cursor.execute(query, (username,"sent_folder")) 
    msgList = []
    for (send_date, send_time, subject, messageID, reciever) in cursor:
        msgList.append([str(send_date + " - " +send_time),messageID,"To:",reciever,send_date,subject])

    msgList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y - %H:%M:%S"))
    return msgList

def testQuery():
    query = ("SELECT * FROM messageDB M INNER JOIN userTable UT ON M.sender=UT.username")  
    cursor.execute(query) 
    for i in cursor:
        print(i)

def getAllMsgsInConvo(convoID):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time,sender, subject, messageID, msgbody, reciever FROM messageDB "
             "WHERE convoID = %s")  
    cursor.execute(query, (convoID,)) 

    convoList = []
    for (send_date, send_time,sender, subject, messageID, msgbody, reciever) in cursor:
        dateWhole = str(send_date + "   " +send_time)
        send = str(sender+ " - " + mySQL_userDB.getNameFromUsername(sender,tmpcursor, cnx))
        recieve = str(reciever+ " - " + mySQL_userDB.getNameFromUsername(reciever,tmpcursor, cnx))
        #print(send, recieve)
        convoList.append([dateWhole,messageID,send, recieve, subject, msgbody])
       
    convoList.sort(reverse=True,key=lambda date: datetime.strptime(date[0], "%B %d, %Y   %H:%M:%S"))
    return convoList




@app.route('/msg/<msgid>', methods=['POST','GET'])
def openMsg(msgid):
#<TEST MYSQL>
    query = ("SELECT sender, reciever, sender_loc, reciever_loc, convoID FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (msgid,))
    for (sender, reciever, sender_loc, reciever_loc, convoID) in cursor:
        if(reciever==session['username']):
            markAsRead(msgid)
        convoList=getAllMsgsInConvo(convoID)
        if(reciever == session['username'] and reciever_loc=='inbox'):
            return render_template("msgInfo.html",
                                  inbox = True,sent = False,trashbox=False,
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                              headMsgID = convoID,
                              msgList=convoList,
                                  targetmId = str(msgid)
                              )
        elif(sender_loc == 'trash' or reciever_loc=='trash'):
            return render_template("msgInfo.html",
                                  inbox = False,sent = False,trashbox=True,
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                              headMsgID = convoID,
                              msgList=convoList,
                                  targetmId = str(msgid)
                              )
        else:
            return render_template("msgInfo.html",
                                  inbox = False,sent = True,trashbox=False,
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                              headMsgID = convoID,
                              msgList=convoList,
                                  targetmId = str(msgid)
                              )

@app.route('/reply', methods=['POST','GET'])
def reply():
#<TEST MYSQL>
    convoID =request.form['headMsgID']
    query = ("SELECT sender, reciever, subject FROM messageDB "
             "WHERE messageID = %s")  
    cursor.execute(query, (convoID,))
    subj = ""
    for (sender, reciever, subject) in cursor:
        if("re: " in subject):
            subj = subject
        else:
            subj = "re: "+subject
    print(subj)
    originalReciever = reciever
    originalSender = sender

    return render_template("replyEmail.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          headMsgID=convoID,
                          sender_username = session['username'],
                          reciever_username=(originalReciever if originalSender == session['username'] else originalSender),
                          subject = subj,
                          email_body = "")

   
   #get the sender from this to be the reciever of the reply
   #get current username to be sender
   #replying subject tack on a re:  (if one is not already on there)

@app.route('/inbox')
def openInbox():
   return getAllMessagesPaged(session['username'],"0")



@app.route('/u1')
def user1():
   session['username'] = "first_user"
   session['docStatus'] = 'patient'
   return openInbox()

@app.route('/u2')
def user2():
   session['username'] = "second_user"
   session['docStatus'] = 'doctor'
   return openInbox()

@app.route('/u3')
def user3():
   session['username'] = "third_user"
   session['docStatus'] = 'patient'
   return openInbox()


@app.route('/')
def index():
   session['username']=""
   return render_template("messageHome.html")

#insertMessage("test_send", "test_recieve", "Hello There","Goodbye", "0")
#insertMessage("test_send", "test_recieve", "Hello World","234rdtfgads", "231558876186")
#moveToTrash("232028501183", "test_send")
#undoTrash("231558876186", "test_send")
#print(countUnreadInInbox("test_recieve"))
#print(countUnreadInTrash("test_recieve"))
#markAsRead("231558876186")
#markAsUnread("231558876186")

#permenantDel("232028501183", "test_send")
#getAllTrashMessages("test_send")
#getAllMessagesSent("test_send")
#testQuery()
#print(getAllMsgsInConvo("134850073356"))

# cursor.close()
# cnx.close()

if __name__ == '__main__':
   app.secret_key = os.urandom(12)
   app.run(debug=True)


# - DONE :) - make a front page with 2 buttons - 1 = log in as user1, 2 = log in as user2
    #(interact with each one's inbox/sent/trash/etc. separately)
#- DONE :) - trash (from inbox or sent) 1
#- DONE :) -make a "trash empty" change the username of whoever moved it to the trash so it does not show up in their scans any more
#- DONE :) -if both sender and reciever have permenantly deleted it, remove it from the database
#- DONE :) -make a top row with blank values with a check that checks all messages in that folder
#- DONE :) -make a limit to the size of the message and make that the max/fixed size of the textarea
#- DONE :) -put character limit on subject line
#- DONE :) -make a dynamically updating character count for subject line and body
#- DONE :) - mark read/unread 2
#- DONE :) - make an "empty trash" button
#- DONE :) - make messages clickable (extend for body and mark as read if unread)
#- DONE :) -make the whole msg bar the <a> click (not just subject)
#- DONE :) -make an inicator of the # of unread msgs in inbox or trash in nav label
#*- DONE :) -allow users to reply
#- DONE :) -make all checkbox implemented in js (no reloading the page)
#- DONE :) -make the select all checkboxes centered/correct (like inbox)

#*- DONE :) -convert scan+filter -> query (MUCH FASTER)
    #Note: the getAllTrashMessages(username) function has 2 inefficient parts that I left in bc they are too hard to replace
    #1 -> there is a 3 way if that turening into a ternary operator for the comprehensive list would be too hard
    #2 -> there is a scan+filter bc it uses not and or as parts of its query logic and python's aws does not support those??

#- DONE :) -figure out how to display a conversation aesthetcially (allow longer messages?)
#- DONE :) -move to inbox or sent from (from trash) 3
#   - DONE :) -Add the time and day
#FORMATTING TO FIX
#   - DONE :) -Fix positioning of the character counter (full screen)
#- DONE :) -change the styling of the new email page to match the msg info page
#- DONE :) -change styling of reply email page
#- DONE :) -order all folders by the time they were recieved/sent
#- DONE :) -message for if user has nothing in a folder
#- DONE :) -FIX PERMENANT DELETE (SMTG WITH BTN STATES??)
#- DONE :) -add unread # updates to unread trash/inbox on reply and new email pages
#- DONE :) -add time to the message in inbox line
#- DONE :) -conditional formatting for read/unread emails in inbox
    #- DONE :) -send the unread value in the message array for each item
    #- DONE :) -do the css for the conditional classes (and change styling for message class)
    #- DONE :) -replicate all in trash folder
#- DONE :) -when you open a message from the trash/sent, the active should shift to trash/sent instead of inbox
#*- DONE :) -when you click a message, have the first thing you see is that message (snap to that message in the convo)
#- DONE :) -fix whitespace in span (after To:)
#- DONE :) -change button/action words to icons
    #- DONE :) -do the deescription on hover
#*- DONE :) -make autocomplete for usernames (user cannot enter an invalid username)
#- DONE :) -in the sent folder, change the sender to who the recipient is
    #-DONE :)- make a "To:" label like trash
#- DONE :) -make reply button into a picture
#- DONE :) -PUT PICTURE ICONS ON ALL EMPTY PAGES
#*- DONE :) -read up on if AWS can support paged queries (only query for items on that page?)
#- DONE :) -MAKE NEXT/PREV inherently disabled on empty
#- DONE :) -catch if page num given is out of bounds (go the furthest it allows and send back that new number)
#- DONE :) -make counter (x-y of z) < >
#- DONE :) -make pictures for 2 icons
#- DONE :) -incorporate paging into trash
#- DONE :) -incorporate into sent
#- DONE :) -#do dropdown styling of messaging 
#- DONE :) -change where messaging's dropdown are coming from
#- DONE :) -connect dropdown check to user dtb
#- DONE :) -incorporate messaging into it
#- DONE :) -REMOTE AZURE CONNECTION IN ALL BELOW IMPLEMENTATION
#- DONE :) -change all aws to mysql queries
#- DONE :) -change all aws dependency in zoom post and apptest

#- DONE :) -Change schema to have a care team assignment
    #- DONE :) -doctor - fn ln un email pw drtype (dietician/dr/lifes)
    #- DONE :) -patient - fn ln un email pw dr1 dr2 dr3
    #- DONE :) -change queries in mySQL_apptDB to check both for login/validity/etc
    #- DONE :) -change info (dr vs patient) -- name
    #- DONE :) -change search users list functions
    #- DONE :) -add user (split into dr/patient)
    #- DONE :) -other etc. utility functions
##- DONE :) -WRITE QUERY FOR SELECTIVE RETURNS
    #- DONE :) -when they are a doctor user, the dropdown should be all doctors/patients
#- DONE :) -fix own acct detail pg styling
#- DONE :) -include inbox link in nav bar pages
#- DONE :) -FIX QUERY (rn doctor1 has admin's appt on his calendar)
#TODO - DONE :) - make a sendAutomatedMsg(username, msgBody)
    #- DONE :) -when we send an automated msg, always send it from TreeoNotification
#- DONE :) -TODO test -when they are a patient user, the dropdown should only have THEIR doctors
#- DONE :) -TEST ALL ABOVE FUNCTIONALITY (via apptest.py) + DEBUG

#-DONE :) --make an ADMIN dashboard 
#-- DONE :) -- view all unassigned patients + update admin data + delete + inbox
#-- DONE :) -make another type of acct (not p/d but admin)
    #-- DONE :) -DO ALL UTILITY FUNCTIONS (create/update/delete)
    #- DONE :) -make ANOTHER table for just admin users?
        #-- DONE :) -part of admin dashboard = make new admin acct
        #-- DONE :) -make ADMIN "TreeoHelp" account that they can msg even if they don't have a care team yet
        #- DONE :) -MAKE SURE TO HANDLE THE "No assigned care team" message so it is not treated as a username -> crash
#- DONE :) -if the user type is admin, go to admin dashboard
#-- DONE :) -show error message when <3 drs assigned (or incorrect username used)
#-- DONE :) -hook up 3 dropdown autocompletes for the 3 types of drs 
    #  - DONE :) -(only allow the dr to be assigned if it is in that dropdown/is that type of dr)
#-- DONE :) -assign 1 dr of each type to unassigned patient
#-- DONE :) -send automated msg to inbox of patient telling them they have been assigned to a care team

#TODO -DONE :)- fix spacing of TreeoNotification messages
#- DONE :) -FIX MYSQL TIMEOUT ERRORS -- what acct is the server on??
# DONE :) FIX ZOOM Api call tokens (jwt)
#TODO -DONE :)- send automsg to drsx3 and patient when assigned
#TODO -DONE :)- send other automated messages (acct creation/acct update/appt create/appt change/appt delete)
    #-DONE :)-acct stuff -> TreeoNotification
        #DONE :)care team assignment x4
        #DONE :)account create x1
        #DONE :)account update x1
    #-DONE :)-appt Stuff -> TreeoCalendar
        #DONE :)appt create x2
        #DONE :)appt cancelled x2
        #DONE :)appt updated x2
        
    #DONE :)make an option fo patients to cancel an appt through mtg detail page
#DONE :)CHANGE how delte is done (no form, just run delete when they hit the cancel btn)
#DONE :) when appt is created/updated/deleted -> notify patient with automated msg
# TODO -DONE :)- unapproved drs in admin dashboard
    #-DONE :)- send email to registered email when they are approved
    #-DONE :)- do not let them log in until they are approved
#-DONE :)- make a way for the dr to be unapproved by an admin
#-DONE :)- give patient the ability to cancel appt (<24h = fee warning) -> notify dr + update calendar
#-DONE :)- make utility function to allow drs to view all patients they are assigned to/are on the care team for
    #-DONE :)- make a page in the dr portal for it
#-DONE :)-when deleting, check if it is from a notification account 
   #-DONE :)-(if it is, permadelete immediately so dtb is not inflated with delted notification msgs)

#- DONE :) -messaging patch
    #- DONE :) -fix trash - inbox
    #- DONE :) -fix trash - sent
    #- DONE :) -fix undo trash
    #- DONE :) -fix perma trash
    #- DONE :) -check all other functionality
#NOTE: CALENDAR -- appts are set in time + 5h in zoom API
    #DONE :) store Zoom time -5h (EST) in apptTable
    #DONE :) add +5 to the time BEFORE sending to zoom API (NO - Zoom adds 5 to go to UTC automatically)
    #DONE :) show apptTable time when showing appt details
    #DONE :) show apptTable time in calendar positioning
#-DONE :)-Calendar -> when querying, remove all appts that happened before the current day 
    #-DONE :)-when editing an appt, if curr time>end time do not let them edit (same day)
#-DONE :)-AUTO SET title of meeting (do not let dr set)
#-DONE :)-make autocomplete noncase sensitive
#-DONE :)-check/fix username check on register
    
    






#--[DELETE] allow deletion of account on acctdetails pg -> UPDATE ALL MESSAGES FROM/TO THEM 
    #--treat msgs from that dummy "deletedAcct" like notif (permadelete if the other person deletes)
    #-tbd how to handle a dr being deleted when they are on patient care team
    #on patient acct deletion, GO INTO ARCHIVE AND DELETE ALL APPTS? -- only if both accts are deleted
        #on patient acct delteion, change name of patient to username+"[deleted]" so if that username is signed up for again, those appts won't show as that user's

#CLEAN UP ALL COMMENTS
#Split apptest.py into smaller files
    
#ADMIN - list/search ALL users (search + see user accts including drs)
#On user acct page/in search result have a "send message" button that takes you to a pre-filled out inbox page

#make appt requested option + do automated message x1 (patient req so only notify dr)
    #what mechnaism for requests?? - form for requesting a range on a certian day? just req a certain day? 
    #make an availability window potion of the appts db for drs, allow patients to request an appt at any point that is not booked
    #(unbooked appts still block out that time until accepted or rejected so the requests don't overlap)

#Maintenence/QOL
    #--fix all calendar styling (wrapper-c id children)
        #fix tiny formatting issues with search page/all info forms
    #in the function where patients and drs are mixed, figure out how to distinguish them
        #conditional formatting of the dropdown (CSS)
    #when there is an error in register, do not dewfault to dietician/patient
    #start putting "are you sure?" warnings on bigger actions
        #cancel appt
        #approve dr
        #permadelete msgs
    #TODO -- remove the links of admin inbox to calendar/etc (make seperate admin pages)
        #-all malibox? (or just remove nav on all mailbox except inbox + only have sep inbox?)
        #-patient acct detail pg







#Archive
    #-DONE :)-(have an archive table for past appts/appt history ) -- not deleted appts, only appts that passed and we removed ourselves
    #-DONE :)-only store patient/dr/date/time
    #allow patients/drs to view summary/access dr notes
    #EVENTUALLY -- allow drs to upload docs/make notes on appt (***HIPAA***)
#EVENTUALLY - can store user's time zone in the db for easier adjustment  


#*--add search bar (mid top of inbox)
#*--put inbox unread tally icon in nav bar
#--make login limit (5 tries before locking acct)
#--empty trash folder every 2 wks
#fix stupid implementation of "paging" in search results
    #make sure when there are 0 results the page counter doesn't start with 1
#--STYLING 
#--redo msgDB schema with FK to user tables


#--eventually - give admin way to delete/ban patient users
    #--when patients are inappropriate on messaging, give notif to admin



