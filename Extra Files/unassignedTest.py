from flask import Flask, render_template, request,session, jsonify

app = Flask(__name__)



@app.route('/')
def index():
   o = []
   o.append("hello")
   o.append("there")
   o.append("general")
   o.append("kenobi")
   o.append("lmaop")
   return render_template("unassignedList.html",
                          options=o)

if __name__ == '__main__':
   app.run(debug=True)



