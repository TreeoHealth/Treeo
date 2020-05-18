from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from flask import Flask, jsonify
import boto3
import aws_controller

app = Flask(__name__)

dynamo_client = boto3.client('dynamodb')

@app.route('/get-items')
def get_items():
    return jsonify(aws_controller.get_items())

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return 'Hello Boss!  <a href="/get-items">Get table</a>'

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
