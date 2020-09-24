from flask import Flask, render_template, request
import requests
from aws_appt import returnAllPatients
#from bs4 import BeautifulSoup


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('checkUnPw.html')


@app.route('/suggestions')
def suggestions():
    text = request.args.get('jsdata')
    print(text)
    takenUn = returnAllPatients()
    suggestions_list=[]
    if(text in takenUn):
        text=""
        suggestions_list = ["USERNAME TAKEN"]
    return render_template('suggestions.html', suggestions=suggestions_list)


if __name__ == '__main__':
    app.run(debug=True)
