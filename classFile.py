class doctorUserClass:
    def __init__(self, username, password, email, fname, lname, creationDate, doctorType):
        self.username = username
        self.password = password
        self.email = email
        self.fname = fname
        self.lname = lname
        self.creationDate = creationDate
        self.doctorType = doctorType

class patientUserClass:
    def __init__(self, username, password, email, fname, lname, creationDate, dr1User, dr2User, dr3User):
        self.username = username
        self.password = password
        self.email = email
        self.fname = fname
        self.lname = lname
        self.creationDate = creationDate
        self.dietician = dr1User
        self.physician = dr2User
        self.healthcoach = dr3User
        
class adminUserClass:
    def __init__(self, username, password, fname, lname, creationDate):
        self.username = username
        self.password = password
        self.fname = fname
        self.lname = lname
        self.creationDate = creationDate
        
class apptObjectClass:
    def __init__(self, mtgID, doctor, patient, mtgName, startTime, joinURL):
        self.meetingID = mtgID
        self.doctor = doctor
        self.patient = patient
        self.meetingName = mtgName
        self.startTime = startTime
        self.joinURL = joinURL
        
class messageObjectClass:
    def __init__(self, messageID, sender,reciever,subject,
                    msgbody,convoID,send_time,send_date,
                    read_status,sender_loc,reciever_loc,perm_del):
        self.messageID = messageID
        self.sender = sender
        self.reciever = reciever
        self.subject = subject
        self.msgbody = msgbody
        self.convoID = convoID
        self.send_time = send_time
        self.send_date = send_date
        self.read_status = read_status
        self.sender_loc = sender_loc
        self.reciever_loc = reciever_loc
        self.perm_del = perm_del