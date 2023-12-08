from flask import Flask
from reader import APP_ROOT
from flask_sqlalchemy import SQLAlchemy
import pytz, datetime
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = '28bee993c5553ec59b3c051d535760198f6f018ed1cca1ddadcdb570352ef05b'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{APP_ROOT}instance/mars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 20000000
db = SQLAlchemy(app)


def auth(login, password):
    teacher = db.session.query(Teacher).filter_by(login=login).all()

    if len(teacher) == 0:
        return 0, -1
    elif not check_password_hash(teacher[0].psw, password):
        return 1, -1
    else:
        return 2, teacher[0].id


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
