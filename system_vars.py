from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pytz, datetime
from face_rec import FaceRec


app = Flask(__name__)
app.secret_key = '28bee993c5553ec59b3c051d535760198f6f018ed1cca1ddadcdb570352ef05b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# APP_ROOT = '/var/www/mars-project.ru/'
APP_ROOT = 'C:/Users/user/Documents/IT/project-mars-main/'


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    login = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), unique=True)

    def __repr__(self):
        return f"<teacher {self.id}>"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
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


class Interlayer:
    tz = pytz.timezone('Europe/Moscow')

    def __init__(self, teacher_id):
        self.faceRec = FaceRec(app_root=APP_ROOT)
        self.teacher_id = teacher_id

    def put_mark(self, mark_data):
        new_id = Mark.query.count()
        new_data = Mark(id=new_id, student_id=mark_data[1], date=mark_data[0], type=(1 if (mark_data[3]) else -1))
        db.session.add(new_data)
        db.session.commit()

    def recount(self):
        self.faceRec = FaceRec(APP_ROOT)
        id_list = []
        our_students = db.session.query(Student).filter_by(teacher_id=self.teacher_id).all()
        for student in our_students:
            id_list.append(student.id)
        self.faceRec.count_faces(id_list)

    def put_mark_recognize(self, img, type):
        face_id = self.faceRec.recognite_the_face(img)

        if face_id != -1:
            dt = datetime.datetime.now(self.tz)
            self.put_mark([form_date(int(dt.day), int(dt.month), int(dt.year)), face_id, type])

        return face_id

    def put_mark_direct(self, id, type):
        dt = datetime.datetime.now(self.tz)
        self.put_mark([dt.strftime("%d.%m.%Y"), id, type])