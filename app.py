from flask import Flask, render_template, request 

app = Flask(__name__)

app.config["SECRET_KEY"] = "oauh"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/speech", methods=["POST"])
def speech():
    return

if __name__ == '__main__':
    app.run(debug=True)