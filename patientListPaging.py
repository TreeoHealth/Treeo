from flask import Flask, render_template, request
import requests
from aws_appt import returnAllPatients
#from bs4 import BeautifulSoup


app = Flask(__name__)
takenUn = returnAllPatients()

patientList = []
listStr = ["alpha","beta","chi","delta",
              "eta","epsilon","gamma","iota",
              "kappa", "lambda","mu","nu",
              "omicron","omega","pi","phi",
              "psi","rho","sigma","tau",
              "theta", "upsilon", 'xi',"zeta"]
patientPages = []
currPg=0

testList = ["blank" ]
#secondList = ["test","a","b","c"]
firstList = ["alpha","beta","chi","delta",
              "eta","epsilon","gamma","iota",
            "kappa", "lambda","mu","nu"]
secondList= ["omicron","omega","pi","phi",
              "psi","rho","sigma","tau",
              "theta", "upsilon", 'xi',"zeta"]
currPg = 0
@app.route('/')
def index():
    return render_template('testPg.html')
    #if len(testList)>=20:

#plan
    #split the full array into the partial paged ones
    #change the design of the html to have a prev variable and a next variable
            #The value for the buttons will be the page number
            #that can be sent from this
    #make an array of pairs -> the array, the page number
    #FIGURE OUT - how to send the render template with array, prev/next pg nums
        #FROM THIS PAGE
    
    return render_template('patPgn.html',
                           options=testMaster[currPg],
                           #ppgnum=currPg-1, #do more error catching relative to size
                           npgnum=currPg+1)



@app.route('/listb', methods=['POST','GET'])
def listb():
    patientPages = []
    currPg=0
    return displayPagedSearch(secondList)

    #return render_template('patientPaging.html',options=testList)


@app.route('/lista', methods=['POST','GET'])
def lista():#search_page():
    #query = request.form['names']
    #if(query==""): #if the form is empty, return all of the usernames
    patientPages = []
    currPg=0
    return displayPagedSearch(firstList)
        #return render_template('picture.html', options=listStr) #THIS
    
    #actualUsername = (query.split(" - "))[0] #username - last name, first name
    #response = aws_appt.getAcctFromUsername(actualUsername)
##    if(len(query.split(" - "))==2 and len(response)==2):
##            #if the username exists and the user used the autocomplete -> take them to the account page directly
##        name = str(response.get('Item').get('fname').get('S'))+" "+str(response.get('Item').get('lname').get('S'))
##        return render_template('patientAcctDetails.html', 
##                           username=actualUsername,
##                           docstatus=response.get('Item').get('docStatus').get('S'),
##                           nm=name,
##                           email=response.get('Item').get('email').get('S')
##                           )
    


def displayPagedSearch(patientList):
    #the PROBLEM is that the patientPages needs to be cleared every time this is called
    #but for some reason if it is cleared before appending, it is blank when nextPg() is triggered and tries to access the array
    #to be solved
    patientPages = []
    #print("1-->",patientPages)
    currPg=0
    if(len(patientList)>5):
       #patientPages = []
       numOfPages = (len(patientList)/5)+1
       position = 0
       tempList = []
       for item in patientList:
           tempList.append(item)
           position = position+1
           if(position==5):
               patientPages.append(tempList)
               position=0
               tempList=[]
       patientPages.append(tempList) #tacks on the last partial page
       #print("2-->",patientPages)
       result = ""
       for page in patientPages:
           for patient in page:
               result = result + str(patient)+","
           result = result[:-1] #take off the last ,
           result = result + "|"
       result = result[:-1] #take off the last |
               
       
       return render_template('patPgn.html',
                           options=patientPages[currPg],
                              fullPagesArr=result,
                           npgnum=currPg+1)
    else:
        #patientPages = []
        result = ""
        for patient in patientPages:
            result = result + str(patient)+","
        result = result[:-1] #take off the last ,
        #print("3-->",patientPages)
        patientPages.append(patientList)
        return render_template('patientPaging.html',
                           options=patientList,
                            fullPagesArr=result)

       
@app.route('/page', methods=['POST','GET'])
def nextPg():
    
    pageStr = request.form['fullPagesArr']
    patientPages = []
    pages = pageStr.split("|")
    temp = []
    for page in pages:
        for patient in page.split(","):
            temp.append(patient)
        patientPages.append(temp)
        temp = []
    pageNum = len(patientPages)
    print("4-->",patientPages)
    #rint(pageNum)
    try:
        #print(request.form['prev'])
        currPg = int(request.form['prev'])
    except:
        #print(request.form['next'])
        currPg = int(request.form['next'])
    print("CurrPg",currPg)
    
    if(len(patientPages)==1):
        return render_template('patientPaging.html',
                           options=patientPages[currPg],
                               fullPagesArr=pageStr)
    elif(currPg==0):
        return render_template('patPgn.html',
                           options=patientPages[currPg],
                               fullPagesArr=pageStr,
                           npgnum=currPg+1)
    elif(currPg==(pageNum-1)):
        return render_template('patPgp.html',
                           options=patientPages[currPg],
                               fullPagesArr=pageStr,
                           ppgnum=currPg-1)
    else:
        return render_template('patPgnp.html',
                           options=patientPages[currPg],
                               fullPagesArr=pageStr,
                           ppgnum=currPg-1,
                            npgnum=currPg+1)




if __name__ == '__main__':
    app.run(debug=True)
