from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from flask import Flask, jsonify
import boto3
from boto3.dynamodb.conditions import Key, Attr
import aws_controller
from botocore.exceptions import ClientError
from zoomtest_post import createMtg

app = Flask(__name__)

dynamo_client = boto3.client('dynamodb')

@app.route('/get-items')
def get_items():
    return jsonify(aws_controller.get_items())

@app.route('/')
def home():
    if not (session.get('logged_in') or session.get('logged_in_a')):
        return render_template('login.html')
    elif session.get('logged_in'):
        return 'Hello Boss! <a href="/logout">Logout</a>'
    else:
        return 'Hello Boss!  <a href="/get-items">Get table</a> <a href="/logout">Logout</a>'

@app.route('/loginadmin', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in_a'] = True
    else:
        print('wrong password admin!')
    return home()

@app.route('/login', methods=['POST'])
def check_login():
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:4000")

    table = dynamodb.Table('YourTestTable')
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in_a'] = True
        session['logged_in'] = False
        return home()
    else:
        print('wrong password admin!')
    
    try:
        print('before')
        response = dynamo_client.get_item(TableName= 'YourTestTable',
            Key={
                'username': {"S":request.form['username']},
                'password': {"S":request.form['password']}
            }
        )
        print('after')
        session['logged_in'] = True
        session['logged_in_a'] = False
    except ClientError as e:
        print(e.response['Error']['Message'])
    return home()

@app.route('/registerrender', methods=['POST'])
def regPg():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def new_register():
    
#register new user
    response = dynamo_client.put_item(TableName= 'YourTestTable',
       Item={
            'username': {"S":request.form['username']},
            'password': {"S":request.form['password']}
        }
       )
    return home()

@app.route('/createrender', methods=['POST'])
def createPg():
    return render_template('create_mtg.html')

@app.route('/createmtg', methods=['POST'])
def create_mtg():
    time = str(request.form['day'])+'T'+ str(request.form['time'])+':00'
    jsonResp = createMtg(str(request.form['mtgname']), time, str(request.form['password']))
    return jsonResp


@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['logged_in_a'] = False
    return home()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
