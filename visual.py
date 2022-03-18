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


def get_connection(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    return conn, cur

app = Flask(__name__)
app.secret_key = '28bee993c5553ec59b3c051d535760198f6f018ed1cca1ddadcdb570352ef05b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def set_path(id):
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLD = 'faces/' + str(id)

    if not os.path.isdir(UPLOAD_FOLD):
        os.chdir('faces')
        os.mkdir(str(id))
        os.chdir('..')

    UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
        self.fr = FaceRec('faces')
        self.fr.startWork()

    def put_mark(self, mark_data):
        conn, cur = get_connection('data.db')
        new_id = cur.execute('SELECT COUNT(id) FROM mark').fetchone()[0] + cur.execute('SELECT COUNT(id) FROM minus').fetchone()[0]
        if mark_data[2]:
            m = Mark(id=new_id, student_id=mark_data[1], data=mark_data[0])
        else:
            m = Minus(id=new_id, student_id=mark_data[1], data=mark_data[0])
        db.session.add(m)
        db.session.commit()

    def recount(self):
        self.fr = FaceRec('faces')
        self.fr.startWork()

    def put_mark_recognize(self, img, type):
        face_id = self.fr.recogniteTheFace(img)

        if face_id != -1:
            dt = datetime.datetime.now(self.tz)
            self.put_mark([dt.strftime("%d.%m.%Y"), face_id, type])

        return face_id

    def put_mark_direct(self, id, type):
        dt = datetime.datetime.now(self.tz)
        self.put_mark([dt.strftime("%d.%m.%Y"), id, type])

interlayer = Interlayer()

def update():
    global fr
    if session['is_changed']:
        interlayer.recount()
        session['is_changed'] = False

@app.before_request
def load_logged_in_user():
    id = session.get('user_id')

    if id is None:
        g.teacher_name = None
    else:
        conn, cur = get_connection('data.db')
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
                session['is_changed'] = None
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
        conn, cur = get_connection('data.db')

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
            session['is_changed'] = None
            return redirect('/lk')

    return render_template("login.html", error = error)


@app.route('/lk', methods = ["POST", "GET"])
def lk():
    id = session['user_id']
    if id is None:
        return redirect('/error_no_access')
    if request.method == 'POST':
        update()
        return redirect('/lk')
    conn, cur = get_connection('data.db')
    ask = 'SELECT cl, name, id FROM student WHERE teacher_id = ' + str(id)
    res = sorted(cur.execute(ask).fetchall())
    st = []
    print(res)
    for i in res:
        st.append([i[1], i[0], 'lk/delete_student/student_id=' + str(i[2])])
    return render_template('lk.html', students=st)


@app.route('/lk/add_student', methods=["POST", "GET"])
def add_student():
    id = session['user_id']
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
            conn, cur = get_connection('data.db')
            ask = "SELECT COUNT(id) FROM student WHERE name = '" + name + "' AND teacher_id = " + str(id)
            inf = cur.execute(ask).fetchone()[0]
            if inf > 0:
                return 'Ученик уже есть у вас в классе!'
            ask = "SELECT COUNT(id) FROM student"
            inf = cur.execute(ask).fetchone()[0] + 1
            set_path(inf)

            for photo in request.files:
                request.files[photo].save(
                    os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(request.files[photo].filename)))

            t = Student(id=inf, name=name, cl=cl, teacher_id=id)

            db.session.add(t)
            db.session.commit()
            session['is_changed'] = True
            return redirect('/lk')

        elif 'increase_photo_num' in request.form:
            session['add_student_photo_num'] = session['add_student_photo_num'] + 1
            form_photo_list()
        elif 'decrease_photo_num' in request.form:
            session['add_student_photo_num'] = session['add_student_photo_num'] - 1
            form_photo_list()


    return render_template('add_student.html', photo_list=photo_list)


@app.route('/lk/delete_student/student_id=<int:st_id>', methods=["POST", "GET"])
def delete_student(st_id):
    id = session['user_id']
    if id is None:
        return redirect('/error_no_access')

    if request.method == "POST":
        conn, cur = get_connection('data.db')
        ask = 'DELETE FROM student WHERE id = ' + str(st_id)
        cur.execute(ask)
        conn.commit()
        shutil.rmtree('faces/' + str(st_id))
        session['is_changed'] = True
        return redirect('/lk')
    conn, cur = get_connection('data.db')
    ask = "SELECT name FROM student WHERE id = " + str(st_id)
    name = cur.execute(ask).fetchone()[0]
    return render_template('delete_student.html', name=name)


@app.route('/lk/success_page/student_id=<int:st_id>')
def success_page(st_id):
    ask = "SELECT name FROM student WHERE id = " + str(st_id)
    conn, cur = get_connection('data.db')
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

        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_FOLD = 'site_image_cache'
        UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        img = cv2.imread("site_image_cache/" + f.filename, cv2.IMREAD_COLOR)
        face = interlayer.put_mark_recognize(img, s == "+")

        if face == -1:
            pathList = list(paths.list_images('static'))
            cnt = len(pathList) + 1
            os.replace(APP_ROOT + '/site_image_cache/' + f.filename, APP_ROOT + '/static/undefined_image_cache/' + str(cnt) + '.png')
            return redirect('/lk/error_recognise')
        else:
            os.remove('site_image_cache/' + f.filename)
        return redirect('/lk/success_page/student_id=' + str(face))
    return render_template('put_mark.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/lk/undefined_students', methods=['POST', 'GET'])
def undefined_students():
    id = session['user_id']
    if id is None:
        return redirect('/error_no_access')

    pathList = list(paths.list_images('static/undefined_image_cache'))
    nameList = []
    for p in pathList:
        fname = p.split(os.path.sep)[-1]
        nameList.append(('undefined_image_cache/' + fname, fname[:fname.find('.')], fname[:fname.find('.')] + 'mark'))

    if request.method == 'POST':
        for (p, id, idmark) in nameList:
            q = request.form[id]
            s = request.form[idmark]
            APP_ROOT = os.path.dirname(os.path.abspath(__file__))
            if q != 'Ошибка':
                conn, cur = get_connection('data.db')
                ask = 'SELECT id FROM student WHERE name = "' + q + '"'
                t_id = cur.execute(ask).fetchone()[0]
                pathList = list(paths.list_images('faces/' + str(t_id)))
                interlayer.put_mark_direct(t_id, s == "+")
                os.replace(APP_ROOT + '/static/undefined_image_cache/' + id + '.png', APP_ROOT + '/faces/' + str(t_id) + '/' + str(len(pathList) + 1) + '.png')
            else:
                os.remove(APP_ROOT + '/static/undefined_image_cache/' + id + '.png')
        return redirect('/lk')

    ask = "SELECT name FROM student WHERE teacher_id = " + str(id)
    conn, cur = get_connection('data.db')
    nl = cur.execute(ask).fetchall()
    stList = []
    for name in nl:
        stList.append(name[0])

    return render_template('undefined_students.html', fList=nameList, nameList=stList)


@app.route('/lk/data_results/type=<string:type>', methods=['POST', 'GET'])
def data_results(type):
    t_id = session['user_id']
    if t_id == None:
        return redirect('/error_no_access')
    if request.method == 'POST':
        date = request.form['date-choose']
        name = request.form['name-choose']
        cl = request.form['class-choose']
        session['name-choose'] = name
        session['date-choose'] = date
        session['class-choose'] = cl
        return redirect('/lk/data_results/type=show')
    conn, cur = get_connection('data.db')
    res = cur.execute('SELECT data FROM mark').fetchall() + cur.execute('SELECT data FROM minus').fetchall()
    dataSet = set()
    for i in res:
        e = list(map(int, i[0].split('.')))
        dataSet.add((e[2], e[1], e[0], i[0]))
    dataSet = sorted(list(dataSet))
    res = cur.execute(f"""SELECT student_id FROM mark
                      INNER JOIN student ON student.id = mark.student_id
                      WHERE teacher_id = {t_id}""").fetchall() + \
          cur.execute(f"""SELECT student_id FROM minus
                      INNER JOIN student ON student.id = minus.student_id
                      WHERE teacher_id = {t_id}""").fetchall()

    studentData = set()
    for i in res:
        st_id = i[0]
        name = cur.execute(f'SELECT name FROM student WHERE id = {st_id}').fetchone()[0]
        studentData.add(name)
    studentData = sorted(list(studentData))
    if type != 'unknown':
        conn, cur = get_connection('data.db')
        ask = f"""SELECT student_id, data FROM mark
         INNER JOIN student ON student.id = mark.student_id
         WHERE teacher_id = {t_id} AND """
        ask2 = f'SELECT cl, name FROM student WHERE teacher_id = {t_id} AND '
        if session['name-choose'] != 'Выберите ученика':
            name = session['name-choose']
            id = cur.execute(f'SELECT id FROM student WHERE name = "{name}" AND teacher_id = {t_id}').fetchone()[0]
            ask += f'student_id = {id} AND '
            ask2 += f'id = {id} AND '
        if session['date-choose'] != 'Выберите дату':
            date = session['date-choose']
            ask += f'data = "{date}" AND '
        if session['class-choose'] != 'Выберите класс':
            cl = session['class-choose']
            stList = cur.execute(f'SELECT id FROM student WHERE cl = {cl} AND teacher_id = {t_id}').fetchall()
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
                 WHERE teacher_id = {t_id} AND """
        ask2 = f'SELECT cl, name FROM student WHERE teacher_id = {t_id} AND '
        if session['name-choose'] != 'Выберите ученика':
            name = session['name-choose']
            id = cur.execute(f'SELECT id FROM student WHERE name = "{name}" AND teacher_id = {t_id}').fetchone()[0]
            ask += f'student_id = {id} AND '
            ask2 += f'id = {id} AND '
        if session['date-choose'] != 'Выберите дату':
            date = session['date-choose']
            ask += f'data = "{date}" AND '
        if session['class-choose'] != 'Выберите класс':
            cl = session['class-choose']
            stList = cur.execute(f'SELECT id FROM student WHERE cl = {cl} AND teacher_id = {t_id}').fetchall()
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


@app.route('/lk/delete_all')
def delete_all():
    t_id = session['user_id']
    if t_id == None:
        return redirect('/error_no_access')
    if request.method == 'POST':
        conn, cur = get_connection('data.db')
        cur.execute('DELETE FROM mark')
        conn.commit()
        return redirect('/lk/data_results/type=unknown')
    return render_template('delete_all.html')


if __name__ == "__main__":
    app.run(debug=True)
