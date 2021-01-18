from flask import Flask, request, render_template, jsonify
from aws_appt import returnAllPatients
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("autocTest.html")

@app.route("/search/<string:box>")
def process(box):
    query = request.args.get('query')
    if box == 'names':
        # do some stuff to open your names text file
        # do some other stuff to filter
        # put suggestions in this format...
        print(query)
        jsonSuggest = []
        listPatients = returnAllPatients()
        listPatients.append("blue")
        listPatients.append("grey")
        listPatients.append("complex1239")
        listPatients.append("grandma")
        for username in listPatients:
            if(query in username):
                jsonSuggest.append({'value':username,'data':username})
        #suggestions = [{'value': 'joe','data': 'joe'}, {'value': 'jim','data': 'jim'}]
    return jsonify({"suggestions":jsonSuggest})
        #jsonify({"suggestions":suggestions})

if __name__ == "__main__":
    app.run(debug=True)
