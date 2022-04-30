import os
import shutil

import cv2
from flask import Flask, render_template, request, redirect, session, g
from flask_sqlalchemy import SQLAlchemy
from imutils import paths
from sqlalchemy import Column, exc

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from FaceRec import FaceRec
import pytz
import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = '28bee993c5553ec59b3c051d535760198f6f018ed1cca1ddadcdb570352ef05b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def get_connection_read():
    return sqlite3.connect(APP_ROOT + 'data.db').cursor()

def get_connection_read_write():
    conn = sqlite3.connect(APP_ROOT + 'data.db')
    cur = conn.cursor()
    return conn, cur


APP_ROOT = '/var/www/mars-project.ru/'

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<teacher %r>' % self.id

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cl = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer)

    def __repr__(self):
        return '<student %r>' % self.id


class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<mark %r>' % self.id

class Minus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<minus %r>' % self.id


class Interlayer():
    tz = pytz.timezone('Europe/Moscow')

    def __init__(self):
        self.faceRec = FaceRec(APP_ROOT)

    def put_mark(self, mark_data):
        cur = get_connection_read()
        new_id = cur.execute('SELECT COUNT(id) FROM mark').fetchone()[0] + cur.execute('SELECT COUNT(id) FROM minus').fetchone()[0]
        if mark_data[2]:
            m = Mark(id=new_id, student_id=mark_data[1], data=mark_data[0])
        else:
            m = Minus(id=new_id, student_id=mark_data[1], data=mark_data[0])
        db.session.add(m)
        db.session.commit()

    def recount(self):
        self.faceRec = FaceRec(APP_ROOT)
        self.faceRec.countFaces()

    def put_mark_recognize(self, img, type):
        face_id = self.faceRec.recogniteTheFace(img)

        if face_id != -1:
            dt = datetime.datetime.now(self.tz)
            self.put_mark([dt.strftime("%d.%m.%Y"), face_id, type])

        return face_id

    def put_mark_direct(self, id, type):
        dt = datetime.datetime.now(self.tz)
        self.put_mark([dt.strftime("%d.%m.%Y"), id, type])

interlayer = Interlayer()

def update():
    interlayer.recount()

@app.before_request
def load_logged_in_user():
    id = session.get('user_id')

    if id is None:
        g.teacher_name = None
    else:
        cur = get_connection_read()
        teacher = cur.execute('SELECT * FROM teacher WHERE id = ?', (id,)).fetchone()
        g.teacher_name = teacher[1]


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/instruction")
def instruction():
    return render_template("instruction.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/error_no_access')
def error_no_access():
    return render_template('error_no_access.html')


@app.route("/register", methods=["POST", "GET"])
def register():
    error = None
    if request.method == "POST":

        id = len(Teacher.query.order_by(Teacher.id).all())
        name = request.form['name']
        login = request.form['login']
        password = request.form['password']

        if login == '' or name == '' or password == '':
            error = 'Заполните все поля!'

        t = Teacher(id = id, name = name, login = login, password = generate_password_hash(password))
        if error == None:
            try:
                db.session.add(t)
                db.session.commit()
                session['user_id'] = id
                return redirect('/user=' + str(id) + '/lk')
            except exc.IntegrityError:
                error = f'Пользватель с логином "{login}" уже зарегестрирован!'
            except:
                return redirect('/error_register')

    return render_template("register.html", error = error)

@app.route('/login', methods=["POST", "GET"])
def login():
    error = None
    if request.method == "POST":
        cur = get_connection_read()

        login = request.form['login']
        password = request.form['password']

        teacher = cur.execute('SELECT * FROM teacher WHERE login = ?', (login,)).fetchone()

        if teacher == None:
            error = 'Неверный логин.'
        elif not check_password_hash(teacher[3], password):
            error = 'Неверный пароль.'

        if error == None:
            session['user_id'] = teacher[0]
            session['add_student_photo_num'] = 3
            return redirect('/lk')

    return render_template("login.html", error = error)


@app.route('/lk', methods = ["POST", "GET"])
def lk():
    id = session.get('user_id')
    if id is None:
        return redirect('/error_no_access')
    if request.method == 'POST':
        update()
        return redirect('/lk')
    cur = get_connection_read()
    ask = 'SELECT cl, name, id FROM student WHERE teacher_id = ' + str(id)
    res = sorted(cur.execute(ask).fetchall())
    st = []
    for i in res:
        st.append([i[1], i[0], 'lk/delete_student/student_id=' + str(i[2]), 'lk/edit_student/student_id=' + str(i[2])])
    return render_template('lk.html', students=st)


@app.route('/lk/add_student', methods=["POST", "GET"])
def add_student():
    id = session.get('user_id')
    if id is None:
        return redirect('/error_no_access')
    photo_list = []
    def form_photo_list():
        photo_list.clear()
        for i in range(session['add_student_photo_num']):
            photo_list.append('photo' + str(i))
    form_photo_list()
    if request.method == "POST":
        if 'add_student' in request.form:
            name = request.form['surname'] + ' ' + request.form['name'] + ' ' + request.form['patronymic']
            cl = request.form['class']
            cur = get_connection_read()
            ask = "SELECT COUNT(id) FROM student WHERE name = '" + name + "' AND teacher_id = " + str(id)
            inf = cur.execute(ask).fetchone()[0]
            if inf > 0:
                return 'Ученик уже есть у вас в классе!'
            ask = "SELECT MAX(id) FROM student"
            inf = cur.execute(ask).fetchone()[0] + 1

            UPLOAD_FOLD = 'faces/' + str(inf)
            os.mkdir(APP_ROOT + 'faces/' + str(inf))

            for photo in request.files:
                request.files[photo].save(
                    os.path.join(APP_ROOT + 'faces/' + str(inf), secure_filename(request.files[photo].filename)))

            t = Student(id=inf, name=name, cl=cl, teacher_id=id)

            db.session.add(t)
            db.session.commit()
            return redirect('/lk')

        elif 'increase_photo_num' in request.form:
            session['add_student_photo_num'] = session['add_student_photo_num'] + 1
            form_photo_list()
        elif 'decrease_photo_num' in request.form:
            session['add_student_photo_num'] = max(1, session['add_student_photo_num'] - 1)
            form_photo_list()


    return render_template('add_student.html', photo_list=photo_list)


@app.route('/lk/delete_student/student_id=<int:st_id>', methods=["POST", "GET"])
def delete_student(st_id):
    id = session.get('user_id')
    if id is None:
        return redirect('/error_no_access')

    if request.method == "POST":
        conn, cur = get_connection_read_write()
        ask = 'DELETE FROM student WHERE id = ' + str(st_id)
        cur.execute(ask)
        conn.commit()
        shutil.rmtree(APP_ROOT + 'faces/' + str(st_id))
        return redirect('/lk')
    cur = get_connection_read()
    ask = "SELECT name FROM student WHERE id = " + str(st_id)
    name = cur.execute(ask).fetchone()[0]
    return render_template('delete_student.html', name=name)


@app.route('/lk/success_page/student_id=<int:st_id>')
def success_page(st_id):
    ask = "SELECT name FROM student WHERE id = " + str(st_id)
    cur = get_connection_read()
    name = cur.execute(ask).fetchone()[0]
    return render_template('success_page.html', name=name)


@app.route('/lk/error_recognise')
def error_recognise():
    return render_template('error_recognise.html')


@app.route('/lk/put_mark', methods=['POST', 'GET'])
def put_mark():
    if request.method == 'POST':
        f = request.files['photo']
        s = request.form['mark']

        UPLOAD_FOLD = 'site_image_cache'
        UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        f.save(APP_ROOT + 'site_image_cache/1.png')
        img = cv2.imread(APP_ROOT + "site_image_cache/1.png", cv2.IMREAD_COLOR)
        face = interlayer.put_mark_recognize(img, s == "+")

        if face == -1:
            pathList = list(paths.list_images(APP_ROOT + 'static'))
            cnt = len(pathList) + 1
            os.replace(APP_ROOT + 'site_image_cache/1.png', APP_ROOT + 'static/undefined_image_cache/' + str(cnt) + '.png')
            return redirect('/lk/error_recognise')
        else:
            os.remove(APP_ROOT + 'site_image_cache/1.png')
        return redirect('/lk/success_page/student_id=' + str(face))
    return render_template('put_mark.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/lk/undefined_students', methods=['POST', 'GET'])
def undefined_students():
    id = session.get('user_id')
    if id is None:
        return redirect('/error_no_access')

    pathList = list(paths.list_images(APP_ROOT + 'static/undefined_image_cache'))
    nameList = []
    for p in pathList:
        fname = p.split(os.path.sep)[-1]
        nameList.append((APP_ROOT + 'undefined_image_cache/' + fname, fname[:fname.find('.')], fname[:fname.find('.')] + 'mark'))
    error = False
    if request.method == 'POST':
        for (p, id, idmark) in nameList:
            markNotSelected = False
            q = request.form[id]
            try:
                s = request.form[idmark]
            except KeyError:
                print("KeyError!!!")
                markNotSelected = True
            print('s', s, 'q', q)
            APP_ROOT = os.path.dirname(os.path.abspath(__file__))
            if q != 'Ошибка':
                if markNotSelected:
                    error = True
                else:
                    cur = get_connection_read()
                    ask = 'SELECT id FROM student WHERE name = "' + q + '"'
                    t_id = cur.execute(ask).fetchone()[0]
                    pathList = list(paths.list_images('faces/' + str(t_id)))
                    interlayer.put_mark_direct(t_id, s == "+")
                    os.replace(APP_ROOT + '/static/undefined_image_cache/' + id + '.png', APP_ROOT + '/faces/' + str(t_id) + '/' + str(len(pathList) + 1) + '.png')
            else:
                os.remove(APP_ROOT + '/static/undefined_image_cache/' + id + '.png')
        return redirect('/lk')

    ask = "SELECT name FROM student WHERE teacher_id = " + str(id)
    cur = get_connection_read()
    nl = cur.execute(ask).fetchall()
    stList = []
    for name in nl:
        stList.append(name[0])

    return render_template('undefined_students.html', fList=nameList, nameList=stList, error=error)


@app.route('/lk/data_results/type=<string:type>', methods=['POST', 'GET'])
def data_results(type):
    id = session.get('user_id')
    if id == None:
        return redirect('/error_no_access')
    if request.method == 'POST':
        date = request.form['date-choose']
        name = request.form['name-choose']
        cl = request.form['class-choose']
        session['name-choose'] = name
        session['date-choose'] = date
        session['class-choose'] = cl
        return redirect('/lk/data_results/type=show')
    cur = get_connection_read()
    res = cur.execute(f'SELECT data FROM mark INNER JOIN student ON student.id = mark.student_id WHERE teacher_id = {id}').fetchall() + cur.execute(f'SELECT data FROM minus INNER JOIN student ON student.id = minus.student_id WHERE teacher_id = {id}').fetchall()
    dataSet = set()
    for i in res:
        e = list(map(int, i[0].split('.')))
        dataSet.add((e[2], e[1], e[0], i[0]))
    dataSet = sorted(list(dataSet))
    res = cur.execute(f"""SELECT student_id FROM mark
                      INNER JOIN student ON student.id = mark.student_id
                      WHERE teacher_id = {id}""").fetchall() + \
          cur.execute(f"""SELECT student_id FROM minus
                      INNER JOIN student ON student.id = minus.student_id
                      WHERE teacher_id = {id}""").fetchall()

    studentData = set()
    for i in res:
        st_id = i[0]
        name = cur.execute(f'SELECT name FROM student WHERE id = {st_id}').fetchone()[0]
        studentData.add(name)
    studentData = sorted(list(studentData))
    if type != 'unknown':
        cur = get_connection_read()
        ask = f"""SELECT student_id, data FROM mark
         INNER JOIN student ON student.id = mark.student_id
         WHERE teacher_id = {id} AND """
        ask2 = f'SELECT cl, name FROM student WHERE teacher_id = {id} AND '
        if session['name-choose'] != 'Выберите ученика':
            name = session['name-choose']
            s_id = cur.execute(f'SELECT id FROM student WHERE name = "{name}" AND teacher_id = {id}').fetchone()[0]
            ask += f'student_id = {s_id} AND '
            ask2 += f'id = {s_id} AND '
        if session['date-choose'] != 'Выберите дату':
            date = session['date-choose']
            ask += f'data = "{date}" AND '
        if session['class-choose'] != 'Выберите класс':
            cl = session['class-choose']
            stList = cur.execute(f'SELECT id FROM student WHERE cl = {cl} AND teacher_id = {id}').fetchall()
            if len(stList) != 0:
                ask += '('
                ask2 += '('
                for i in stList:
                    s_id = i[0]
                    ask += f'student_id = {s_id} OR '
                    ask2 += f'id = {s_id} OR '
                ask = ask[:-4]
                ask2 = ask2[:-4]
                ask += ')'
                ask2 += ')'
            else:
                ask += 'student_id = 4 AND student_id = 5'
                ask2 += 'id = 4 AND id = 5'
        if ask[-5:] == ' AND ':
            ask = ask[:-5]
        if ask2[-5:] == ' AND ':
            ask2 = ask2[:-5]
        res = cur.execute(ask).fetchall()
        d = {}
        dates = set()
        for i in res:
            e = list(map(int, i[1].split('.')))
            dates.add((e[2], e[1], e[0], i[1]))
            d[i[1]] = {}
        names = cur.execute(ask2).fetchall()
        for i in res:
            name = cur.execute(f'SELECT name FROM student WHERE id = {i[0]}').fetchone()[0]
            if name not in d[i[1]]:
                d[i[1]][name] = 0
            d[i[1]][name] += 1
        ask = f"""SELECT student_id, data FROM minus
                 INNER JOIN student ON student.id = minus.student_id
                 WHERE teacher_id = {id} AND """
        ask2 = f'SELECT cl, name FROM student WHERE teacher_id = {id} AND '
        if session['name-choose'] != 'Выберите ученика':
            name = session['name-choose']
            s_id = cur.execute(f'SELECT id FROM student WHERE name = "{name}" AND teacher_id = {id}').fetchone()[0]
            ask += f'student_id = {s_id} AND '
            ask2 += f'id = {s_id} AND '
        if session['date-choose'] != 'Выберите дату':
            date = session['date-choose']
            ask += f'data = "{date}" AND '
        if session['class-choose'] != 'Выберите класс':
            cl = session['class-choose']
            stList = cur.execute(f'SELECT id FROM student WHERE cl = {cl} AND teacher_id = {id}').fetchall()
            if len(stList) != 0:
                ask += '('
                ask2 += '('
                for i in stList:
                    s_id = i[0]
                    ask += f'student_id = {s_id} OR '
                    ask2 += f'id = {s_id} OR '
                ask = ask[:-4]
                ask2 = ask2[:-4]
                ask += ')'
                ask2 += ')'
            else:
                ask += 'student_id = 4 AND student_id = 5'
                ask2 += 'id = 4 AND id = 5'
        if ask[-5:] == ' AND ':
            ask = ask[:-5]
        if ask2[-5:] == ' AND ':
            ask2 = ask2[:-5]
        res = cur.execute(ask).fetchall()
        d2 = {}
        for i in res:
            e = list(map(int, i[1].split('.')))
            dates.add((e[2], e[1], e[0], i[1]))
            d2[i[1]] = {}
        names += cur.execute(ask2).fetchall()
        for i in res:
            name = cur.execute(f'SELECT name FROM student WHERE id = {i[0]}').fetchone()[0]
            if name not in d2[i[1]]:
                d2[i[1]][name] = 0
            d2[i[1]][name] += 1
        names = sorted(list(set(names)))
        dates = sorted(list(dates))
        return render_template('results.html', type=type, dataSet=dataSet, studentData=studentData, resplus=d, resminus=d2, names=names, dates=dates)
    return render_template('results.html', type=type, dataSet=dataSet, studentData=studentData)


@app.route('/lk/delete_all', methods=['POST', 'GET'])
def delete_all():
    id = session.get('user_id')
    if id == None:
        return redirect('/error_no_access')
    if request.method == 'POST':
        conn, cur = get_connection_read_write()
        cur.execute(f'DELETE FROM mark WHERE student_id IN(SELECT student_id FROM mark INNER JOIN student ON student.id = mark.student_id WHERE teacher_id = {id})')
        cur.execute(f'DELETE FROM minus WHERE student_id IN(SELECT student_id FROM minus INNER JOIN student ON student.id = minus.student_id WHERE teacher_id = {id})')
        conn.commit()
        return redirect('/lk/data_results/type=unknown')
    return render_template('delete_all.html')

@app.route('/lk/edit_student/student_id=<int:st_id>', methods=['POST', 'GET'])
def edit_student(st_id):
    id = session.get('user_id')
    if id == None:
        return redirect('/error_no_access')
    conn, cur = get_connection_read_write()
    if request.method == 'POST':
        cur.execute(f'UPDATE student SET name = "{request.form["surname"] + " " + request.form["name"] + " " + request.form["patronymic"]}" WHERE teacher_id = {id} AND id = {st_id}')
        cur.execute(f'UPDATE student SET cl = {int(request.form["cl"].split()[0])} WHERE teacher_id = {id} AND id = {st_id}')
        conn.commit()
        return redirect('/lk')
    name = cur.execute(f'SELECT name FROM student WHERE teacher_id = {id} AND id = {st_id}').fetchone()[0]
    cl = cur.execute(f'SELECT cl FROM student WHERE teacher_id = {id} AND id = {st_id}').fetchone()[0]
    nameList = name.split()
    return render_template('enter_student.html', st_name=name, st_class=f"{cl} класс", nameList=nameList)

if __name__ == "__main__":
    app.run(host='0.0.0.0')