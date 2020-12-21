from flask import Flask, render_template, request,session, jsonify
import os
import json
import datetime
from datetime import date, datetime,timezone
import time
import aws_appt

import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)
cnx = mysql.connector.connect(user='root', password='password',
                              host='127.0.0.1')
cursor = cnx.cursor()
cursor.execute("USE treeoHealthDB")

@app.route('/submitEmail', methods=['POST','GET'])
def formatEmail():

    query = request.form['reciever_username']
    insertMessage(request.form['sender_username'],
            request.form['reciever_username'],
            request.form['subject'],
            request.form['email_body'],
                  "0"
                  )
#    actualUsername = (query.split(" - "))[0] #username - last name, first name
#    response = aws_appt.getAcctFromUsername(actualUsername)
#    if(len(query.split(" - "))==2 and len(response)==2):
#        insertMessage(request.form['sender_username'],
#            actualUsername,
#            request.form['subject'],
#            request.form['email_body'],
#                  "0"
#                  )
#    elif(len(aws_appt.getAcctFromUsername(query))==2):
#        insertMessage(request.form['sender_username'],
#            request.form['reciever_username'],
#            request.form['subject'],
#            request.form['email_body'],
#                  "0"
#                  )
#    else:
#        return render_template("newEmail.html",
#                           inboxUnread =countUnreadInInbox(session['username']),
#                           trashUnread = countUnreadInTrash(session['username']),
#                           sender_username = session['username'],
#                           errorMsg="Please enter a valid user ID",
#                           reciever_username="",
#                           subject = request.form['subject'],
#                           email_body = request.form['email_body'])
    msgListObj = getAllMessages(session['username'])
    if(len(msgListObj)==0):
       return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
    else:
       return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          msgList = msgListObj)

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
       return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          msgList = msgListObj)

@app.route('/sentFolder', methods=['POST','GET'])
def sentFolder():
   msgListObj = getAllMessagesSent(session['username'])
   if(len(msgListObj)==0):
       return render_template("emptySent.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username'])
                          );
   else:
       return render_template("sentBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          msgList=msgListObj);

@app.route('/trashFolder', methods=['POST','GET'])
def trashFolder():
   msgListObj = getAllTrashMessages(session['username'])
   if(len(msgListObj)==0):
       return render_template("emptyTrash.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = ""
                          );
   else:
       return render_template("trashBox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          msgList=msgListObj);


@app.route('/selectOption', methods=['POST','GET'])
def selectOption():
    x = ""
    try:
       x = str(request.form['prevPg'])
       pageNum = request.form['currPageNum']
       print("Prev")
       return getAllMessagesPaged(session['username'], int(pageNum)-1, 7)
       
    except:
        try:
            x = str(request.form['nextPg'])
            pageNum = request.form['currPageNum']
            print("Next")
            return getAllMessagesPaged(session['username'], int(pageNum)+1, 7)
            
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



def getAllMessagesPaged(username, pageNumber, pageSize): #page to be rendered
#<MYSQL FUNCTIONAL>
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

    if(len(msgList)==0): #if the query is empty
        #return (False, [], False) #no prev, no next
        return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
    if((pageNumber*pageSize+(pageSize)>=len(msgList))):  #this is the final page
        #return (True, msgList[pageNumber*pageSize:], False)
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = True,
                          currPageNum = pageNumber,
                          msgList=msgList[pageNumber*pageSize:])
    elif(pageNumber==0 and pageSize<len(msgList)): #this is the first page and there is a next page
        #return (False, msgList[0:pageSize-1], True)
        print("HERE", msgList[0:pageSize])
        msgList = msgList[0:pageSize]
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = False,
                          currPageNum =pageNumber,
                          msgList=msgList)
    elif(pageNumber==0): #this is the first and only page
        #return (False, msgList[0:], False)
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = True,
                          noNext = True,
                          currPageNum =pageNumber,
                          msgList=msgList[0:])
    else: #there is a prev and next page
        #return (True, msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)], True)
        return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          noPrev = False,
                          noNext = False,
                          currPageNum =pageNumber,
                          msgList=msgList[pageNumber*pageSize:pageNumber*pageSize+(pageSize-1)])

    return msgList

@app.route('/selectSent', methods=['POST','GET'])
def selectSent():
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
   listPatients= aws_appt.searchPatientList()
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


def getAllMsgsInConvo(convoID):
#<MYSQL FUNCTIONAL>
    query = ("SELECT send_date, send_time,sender, subject, messageID, msgbody, reciever FROM messageDB "
             "WHERE convoID = %s")  
    cursor.execute(query, (convoID,)) 

    convoList = []
    for (send_date, send_time,sender, subject, messageID, msgbody, reciever) in cursor:
        dateWhole = str(send_date + "   " +send_time)
        convoList.append([dateWhole,messageID,sender, reciever, subject, msgbody])
       
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
   return getAllMessagesPaged(session['username'], 0, 7)



   msgListObj = getAllMessages(session['username'])
   if(len(msgListObj)==0):
       return render_template("emptyInbox.html",
                          inboxUnread ="",
                          trashUnread = countUnreadInTrash(session['username'])
                          )
   else:
       return render_template("messageInbox.html",
                          inboxUnread =countUnreadInInbox(session['username']),
                          trashUnread = countUnreadInTrash(session['username']),
                          msgList=msgListObj)


@app.route('/u1')
def user1():
   session['username'] = "first_user"
   return openInbox()

@app.route('/u2')
def user2():
   session['username'] = "second_user"
   return openInbox()

@app.route('/u3')
def user3():
   session['username'] = "third_user"
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
#getAllMsgsInConvo("232028501183")

##cursor.close()
##cnx.close()

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

#WRITE QUERY FOR SELECTIVE RETURNS
    #when they are a patient user, the dropdown should only have doctors
    #when they are a doctor user, the dropdown should only be doctors/patients

#*--read up on if AWS can support paged queries (only query for items on that page?)

#MAKE NEXT/PREV inherently disabled on empty
#catch if page num given is out of bounds (go the furthest it allows and send back that new number)
#eventually
#*--make pages for inbox

