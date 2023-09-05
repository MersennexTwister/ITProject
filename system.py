from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pytz, datetime
import funcs

app = Flask(__name__)
app.secret_key = '28bee993c5553ec59b3c051d535760198f6f018ed1cca1ddadcdb570352ef05b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 20000000
db = SQLAlchemy(app)


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    login = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), unique=True)

    def __repr__(self):
        return f"<teacher {self.id}>"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    grade = db.Column(db.Integer)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"))

    def __repr__(self):
        return f"<student {self.id}>"


class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))
    date = db.Column(db.Integer)
    type = db.Column(db.Integer)

    def __repr__(self):
        return f"<mark {self.id}>"
