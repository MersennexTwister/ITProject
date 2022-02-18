import os
import shutil

import cv2
from flask import Flask, render_template, request, redirect, Blueprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, exc
import sqlite3 as sql

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from interlayer import main_func, start

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
fr, s = start()
user_id = None

app.jinja_env.globals.update(teacher_name = None, lk_link = None)

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


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/todo")
def instruction():
    return render_template("todo.html")


@app.route("/about")
def teacher_inf():
    return render_template("about.html")

    
@app.route('/error_no_access')
def error_no_access():
    return render_template('error_no_access.html')


@app.route("/register", methods=["POST", "GET"])
def register():
    global user_id
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
                user_id = id
                return redirect('/user=' + str(id) + '/lk')
            except exc.IntegrityError:
                error = f'Пользватель с логином "{login}" уже зарегестрирован!'
            except:
                return redirect('/error_register')

    return render_template("register.html", error = error)

@app.route('/login', methods=["POST", "GET"])
def login():
    global user_id
    if request.method == "POST":
        conn, cur = get_connection('data.db')

        login = request.form['login']
        password = request.form['password']

        error = None
        teacher = cur.execute('SELECT * FROM teacher WHERE login = ?', (login,)).fetchone()

        if teacher == None:
            error = 'Неверный логин.'
        elif not check_password_hash(teacher[3], password):
            error = 'Неверный пароль.'

        if error == None:
            user_id = teacher[0]
            app.jinja_env.globals.update(teacher_name = teacher[1], lk_link = f'/user={teacher[0]}/lk')
            return redirect('/user=' + str(user_id) + '/lk')
        
        return render_template("login.html", error = error)

    return render_template("login.html", error = None)


@app.route('/user=<int:id>/lk', methods = ["POST", "GET"])
def lk(id):
    if id != user_id:
        return redirect('/error_no_access')
    conn, cur = get_connection('data.db')
    ask = 'SELECT name, cl, id FROM student WHERE teacher_id = ' + str(id) + ' ORDER BY cl ASC'
    res = cur.execute(ask).fetchall()
    st = []
    print(res)
    for i in res:
        st.append([i[0], i[1], '/user=' + str(id) + '/delete_student/student_id=' + str(i[2])])
    ask = 'SELECT name FROM teacher WHERE id = ' + str(id)
    name = cur.execute(ask).fetchone()[0]
    print(name)
    return render_template('lk.html', name=name, students=st, link="/user=" + str(id) + "/add_student")


@app.route('/user=<int:id>/add_student', methods=["POST", "GET"])
def add_student(id):
    if id != user_id:
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
        return redirect('/user=' + str(id) + '/lk')


    return render_template('add_student.html')


@app.route('/user=<int:id>/delete_student/student_id=<int:st_id>', methods=["POST", "GET"])
def delete_student(id, st_id):
    if id != user_id:
        return redirect('/error_no_access')
    if request.method == "POST":
        conn, cur = get_connection('data.db')
        ask = 'DELETE FROM student WHERE id = ' + str(st_id)
        cur.execute(ask)
        conn.commit()
        shutil.rmtree('faces/' + str(st_id))
        return redirect('/user=' + str(id) + '/lk')
    conn, cur = get_connection('data.db')
    ask = "SELECT name FROM student WHERE id = " + str(st_id)
    name = cur.execute(ask).fetchone()[0]
    return render_template('delete_student.html', name=name)


@app.route('/user=<int:id>/success_page/student_id=<int:st_id>')
def success_page(id, st_id):
    if id != user_id:
        return redirect('/error_no_access')
    ask = "SELECT name FROM student WHERE id = " + str(st_id)
    conn, cur = get_connection('data.db')
    name = cur.execute(ask).fetchone()[0]
    return render_template('success_page.html', name=name, link="/user=" + str(id) + "/lk")


@app.route('/user=<int:id>/error_page')
def error_page(id):
    if id != user_id:
        return redirect('/error_no_access')
    return render_template('error_page.html', link="/user=" + str(id) + "/lk")


@app.route('/user=<int:id>/put_mark', methods=['POST', 'GET'])
def put_mark(id):
    if id != user_id:
        return redirect('/error_no_access')
    if request.method == 'POST':
        f = request.files['photo']

        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_FOLD = 'site_image_cache'
        UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        img = cv2.imread("site_image_cache/" + f.filename, cv2.IMREAD_COLOR)
        face = main_func(fr, s, img)
        os.remove('site_image_cache/' + f.filename)
        if face == -1:
            return redirect('/user=' + str(id) + '/error_page')
        return redirect('/user=' + str(id) + '/success_page/student_id=' + str(face))
    return render_template('put_mark.html')

@app.route('/singout')
def singout():
    app.jinja_env.globals.update(teacher_name = None, lk_link = None)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
