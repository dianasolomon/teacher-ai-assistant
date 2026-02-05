from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/teacher-notes')
def teacher_notes():
    return render_template('teacher_notes.html')

@app.route('/student-doubt')
def student_doubt():
    return render_template('student_doubt.html')

@app.route('/assignment-upload')
def assignment_upload():
    return render_template('assignment_upload.html')

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)
