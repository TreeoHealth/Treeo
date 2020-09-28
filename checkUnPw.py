from flask import Flask, render_template, request
import requests
from aws_appt import returnAllPatients
#from bs4 import BeautifulSoup


app = Flask(__name__)
takenUn = returnAllPatients()

@app.route('/')
def index():
    return render_template('checkUnPw.html',errorMsg="")


@app.route('/suggestions')
def suggestions():
    text = request.args.get('jsdata')
    print(text)
    
    #suggestions_list=[]
    if(text in takenUn):
        print(text)
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