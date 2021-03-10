from flask import Flask, render_template, request
import requests
from aws_appt import returnAllPatients
#from bs4 import BeautifulSoup


app = Flask(__name__)
takenUn = returnAllPatients()

@app.route('/')
def index():
    return render_template('checkUnPw.html',errorMsg="")


@app.route('/suggestions', methods=['POST','GET'])
def suggestions():
    #print(request.form)
    #print(request.args)
    text = request.form.get('jsdata')
    #print(text)
    htmlTest='<select'
   
    suggestions_list=["alpha","beta","chi"]
    htmlTest+=str(len(suggestions_list))
    htmlTest+=">"
    for item in suggestions_list:
        htmlTest+="<option>"
        htmlTest+=item
        htmlTest+="</option>"
    htmlTest+="</select>"
    return htmlTest
    if(text in suggestions_list):
        #print(text)
        text=""
        print("USERNAME TAKEN")
        return '<div class="error">USERNAME TAKEN</div>'
            #render_template('checkUnPw.html',errorMsg="USERNAME TAKEN")
        #suggestions_list = ["USERNAME TAKEN"]
    return ""
    #return render_template('checkUnPw.html',errorMsg="")
    #return render_template('suggestions.html', suggestions=suggestions_list)


if __name__ == '__main__':
    app.run(debug=True)
