import pytz, os
import source.face_rec as face_rec
from source.system import *
from source.reader import APP_ROOT
import source.funcs as funcs

tz = pytz.timezone('Europe/Moscow')

def create_teacher(teacher_id):
    open(f"{APP_ROOT}encs/face_enc_{teacher_id}", 'a').close()
    os.system(f"mkdir {APP_ROOT}static/undefined_image_cache/{teacher_id}/")

def put_mark(mark_data):
    new_id = Mark.query.count()
    new_data = Mark(id=new_id, student_id=mark_data[1], date=mark_data[0], type=(1 if (mark_data[2]) else -1))
    db.session.add(new_data)
    db.session.commit()

def recount(teacher_id):
    id_list = []
    our_students = db.session.query(Student).filter_by(teacher_id=teacher_id).all()
    for student in our_students:
        id_list.append(student.id)
    face_rec.count_faces(teacher_id, id_list)

def put_mark_recognize(teacher_id, img, type):
    face_id = face_rec.recognite_the_face(teacher_id, img)

    if face_id != -1:
        dt = datetime.datetime.now(tz)
        put_mark([funcs.form_date(int(dt.day), int(dt.month), int(dt.year)), face_id, type])

    return face_id

def put_mark_direct(id, type):
    dt = datetime.datetime.now(tz)
    put_mark([funcs.form_date(int(dt.day), int(dt.month), int(dt.year)), id, type])