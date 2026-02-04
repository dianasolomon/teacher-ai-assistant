from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Teacher-Guided AI Assistant Backend Running"

if __name__ == "__main__":
    app.run(debug=True)
