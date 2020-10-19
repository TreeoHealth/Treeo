from flask import Flask, render_template, request
import requests
from aws_appt import returnAllPatients
#from bs4 import BeautifulSoup


app = Flask(__name__)
takenUn = returnAllPatients()

testList = ["blank" ]
secondList = ["test","a","b","c"]
testMaster = [["alpha","beta","chi","delta"],
              ["eta","epsilon","gamma","iota"],
              ["kappa", "lambda","mu","nu"],
              ["omicron","omega","pi","phi"],
              ["psi","rho","sigma","tau"],
              ["theta", "upsilon", 'xi',"zeta"]]
currPg = 0
@app.route('/')
def index():
    
    #if len(testList)>=20:

#plan
    #split the full array into the partial paged ones
    #change the design of the html to have a prev variable and a next variable
            #The value for the buttons will be the page number
            #that can be sent from this
    #make an array of pairs -> the array, the page number
    #FIGURE OUT - how to send the render template with array, prev/next pg nums
        #FROM THIS PAGE
    
    return render_template('patientPaging.html',
                           options=testMaster[currPg],
                           ppgnum=currPg-1, #do more error catching relative to size
                           npgnum=currPg+1)


@app.route('/page', methods=['POST','GET'])
def nextPg():
    try:
        print(request.form['prev'])
        currPg = int(request.form['prev'])
    except:
        print(request.form['next'])
        currPg = int(request.form['next'])
    return render_template('patientPaging.html',
                           options=testMaster[currPg],
                           ppgnum=currPg-1,
                           npgnum=currPg+1)
    #return render_template('patientPaging.html',options=testList)



if __name__ == '__main__':
    app.run(debug=True)
