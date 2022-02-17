import os
import shutil

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import sqlite3 as sql

from werkzeug.utils import secure_filename

from interlayer import main_func, start

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
fr, s = start()

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
    teacher_id = db.Column(db.Integer)

    def __repr__(self):
        return '<student %r>' % self.id


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/to-do")
def instruction():
    return render_template("todo.html")


@app.route("/about")
def teacher_inf():
    return render_template("about.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":

        id = len(Teacher.query.order_by(Teacher.id).all())
        name = request.form['name']
        login = request.form['login']
        password = request.form['password']

        t = Teacher(id=id, name=name, login=login, password=password)

        try:
            db.session.add(t)
            db.session.commit()
            return redirect('/')
        except:
            return 'При регистрации произошла ошибка'

    return render_template("register.html")


user_id = None


@app.route('/enter', methods=["POST", "GET"])
def enter():
    global user_id
    if request.method == "POST":
        conn, cur = get_connection('data.db')
        login = request.form['login']
        password = request.form['password']
        ask = 'SELECT id FROM teacher WHERE login = "' + login + '" AND password = "' + password + '"'
        print(ask)
        ok = cur.execute(ask).fetchall()
        try:
            user_id = ok[0][0]
            return redirect('/user=' + str(user_id) + '/lk')
        except:
            return 'При попытке входа произошла ошибка'


    return render_template("enter.html")


@app.route('/user=<int:id>/lk', methods=["POST", "GET"])
def lk(id):
    if id != user_id:
        return "Нет доступа"
    if request.method == "POST":
        face = main_func(fr, s)
        if face == -1:
            return redirect('/user=' + str(id) + '/error_page')
        return redirect('/user=' + str(id) + '/success_page/student_id=' + str(face))

    conn, cur = get_connection('data.db')
    ask = 'SELECT name, id FROM student WHERE teacher_id = ' + str(id)
    res = cur.execute(ask).fetchall()
    st = []
    for i in res:
        st.append([i[0], '/user=' + str(id) + '/delete_student/student_id=' + str(i[1])])
    ask = 'SELECT name FROM teacher WHERE id = ' + str(id)
    name = cur.execute(ask).fetchone()[0]
    print(name)
    return render_template('lk.html', name=name, students=st, link="/user=" + str(id) + "/add_student")


@app.route('/user=<int:id>/add_student', methods=["POST", "GET"])
def add_student(id):
    if id != user_id:
        return "Нет доступа"
    if request.method == "POST":
        name = request.form['name']
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

        t = Student(id=inf, name=name, teacher_id=id)

        try:
            db.session.add(t)
            db.session.commit()
            return redirect('/user=' + str(id) + '/lk')
        except:
            return 'При доабвлении ученика произошла ошибка'

    return render_template('add_student.html')


@app.route('/user=<int:id>/delete_student/student_id=<int:st_id>', methods=["POST", "GET"])
def delete_student(id, st_id):
    if id != user_id:
        return 'Нет доступа'
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
        return 'Нет доступа'
    ask = "SELECT name FROM student WHERE id = " + str(st_id)
    conn, cur = get_connection('data.db')
    name = cur.execute(ask).fetchone()[0]
    return render_template('success_page.html', name=name, link="/user=" + str(id) + "/lk")


@app.route('/user=<int:id>/error_page')
def error_page(id):
    if id != user_id:
        return 'Нет доступа'
    return render_template('error_page.html', link="/user=" + str(id) + "/lk")


if __name__ == "__main__":
    app.run(debug=True)