import os
import shutil

import cv2
from flask import Flask, render_template, request, redirect, session, g
from flask_sqlalchemy import SQLAlchemy
from imutils import paths
from sqlalchemy import Column, exc
import sqlite3 as sql

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from interlayer import main_func, start, recount, put_mark_directly

app = Flask(__name__)
app.secret_key = '28bee993c5553ec59b3c051d535760198f6f018ed1cca1ddadcdb570352ef05b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
fr, spreadsheet = start()

def update():
    global fr
    if session['is_changed']:
        fr = recount()
        session['is_changed'] = False

def get_connection(db_name):
    conn = sql.connect(db_name)
    cur = conn.cursor()
    return conn, cur

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
    ask = 'SELECT name, cl, id FROM student WHERE teacher_id = ' + str(id) + ' ORDER BY cl ASC'
    res = cur.execute(ask).fetchall()
    st = []
    print(res)
    for i in res:
        st.append([i[0], i[1], 'lk/delete_student/student_id=' + str(i[2])])
    ask = 'SELECT name FROM teacher WHERE id = ' + str(id)
    name = cur.execute(ask).fetchone()[0]
    print(name)
    return render_template('lk.html', name=name, students=st)


@app.route('/lk/add_student', methods=["POST", "GET"])
def add_student():
    id = session['user_id']
    if id is None:
        return redirect('/error_no_access')

    if request.method == "POST":
        name = request.form['name']
        cl = request.form['class']
        conn, cur = get_connection('data.db')
        ask = "SELECT COUNT(id) FROM student WHERE name = '" + name + "' AND teacher_id = " + str(id)
        inf = cur.execute(ask).fetchone()[0]
        if inf > 0:
            return 'Ученик уже есть у вас в классе!'
        photo1, photo2, photo3 = request.files['photo1'], request.files['photo2'], request.files['photo3']
        ask = "SELECT COUNT(id) FROM student"
        inf = cur.execute(ask).fetchone()[0] + 1
        set_path(inf)
        photo1.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo1.filename)))
        photo2.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo2.filename)))
        photo3.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo3.filename)))

        t = Student(id=inf, name=name, cl = cl, teacher_id=id)


        db.session.add(t)
        db.session.commit()
        session['is_changed'] = True
        return redirect('/lk')


    return render_template('add_student.html')


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

        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_FOLD = 'site_image_cache'
        UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        img = cv2.imread("site_image_cache/" + f.filename, cv2.IMREAD_COLOR)
        face = main_func(fr, spreadsheet, img)

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
        nameList.append(('undefined_image_cache/' + fname, fname[:fname.find('.')]))

    if request.method == 'POST':
        for (p, id) in nameList:
            q = request.form[id]
            APP_ROOT = os.path.dirname(os.path.abspath(__file__))
            if q != 'Ошибка':
                conn, cur = get_connection('data.db')
                ask = 'SELECT id FROM student WHERE name = "' + q + '"'
                t_id = cur.execute(ask).fetchone()[0]
                pathList = list(paths.list_images('faces/' + str(t_id)))
                put_mark_directly(t_id, spreadsheet)
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


if __name__ == "__main__":
    app.run(debug=True)
