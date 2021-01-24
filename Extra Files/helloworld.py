from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
from password_strength import PasswordPolicy
import password_strength
app = Flask(__name__)

@app.route("/")
def index():
    option = []
    option.append("Doctor1")
    option.append("Doctor2")
    option.append("Doctor3")
    option.append("Doctor4")
    return render_template("testForm.html", options=option)

@app.route('/approve', methods=['POST','GET'])
def approve():
    return "help"

@app.route('/approve/<username>', methods=['POST','GET'])
def approveForm(username):
    #mySQL_userDB.verifyDoctor(username, cursor, cnx)
    return render_template("approveTest.html",
                           drname  = username)


# def usernamencheck():
#     #text = request.args.get('jsdata')
#     policy = PasswordPolicy.from_names(
#             length=8,  # min length: 8
#             uppercase=2,  # need min. 2 uppercase letters
#             numbers=2  # need min. 2 digits
#             )
# ##PASSWORD STRENGTH
#     #isEnough = policy.test("abcAAAaa")
#     if len(isEnough):
#         #print(type(isEnough[0]))
#         if len(isEnough)==1:
#             if type(isEnough[0])==password_strength.tests.Length:
#                 return "<8 characters"
#             elif type(isEnough[0])==password_strength.tests.Uppercase:
#                 return "<2 capital letters"
#             elif type(isEnough[0])==password_strength.tests.Numbers: 
#                 return "<2 digits"
#         elif len(isEnough)==2: #any 2 combinationsS
#             if type(isEnough[0])==password_strength.tests.Length:
#                 if type(isEnough[1])==password_strength.tests.Uppercase:
#                     return "<8 characters\n<2 capital letters"
#                 elif type(isEnough[1])==password_strength.tests.Numbers: 
#                     return "<8 characters\n<2 digits"
#             elif type(isEnough[0])==password_strength.tests.Uppercase:
#                 if type(isEnough[1])==password_strength.tests.Numbers: 
#                     return "<2 capital letters\n<2 digits"
#                 elif type(isEnough[1])==password_strength.tests.Length: 
#                     return "<2 capital letters\n<8 characters"
#             elif type(isEnough[0])==password_strength.tests.Numbers: 
#                 if type(isEnough[1])==password_strength.tests.Uppercase:
#                     return "<2 digits\n<2 capital letters"
#                 elif type(isEnough[1])==password_strength.tests.Length: 
#                     return "<2 digits\n<8 characters"
#         else: #all 3
#             return "<8 characters\n<2 capital letters\n<2 digits"
# #CHANGE THE FORMAT of the message
            #[x]/[x]/[x]?
#usernamecheck()
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000)
