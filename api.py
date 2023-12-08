from system import *
import cv2, interlayer, os
from imutils import paths
from flask import render_template, request, redirect, session, g, url_for

@app.route('/ident', methods=["POST", "GET"])
def ident():

    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']
        res, tid = auth(login, password)
        name = ""
        if res == 2:
            name = db.session.get(Teacher, tid).name

        return { "is": res, "name": name }
    
    return render_template('login.html', error=None)

@app.route('/put_mark', methods=['POST', 'GET'])
def put_mark():

    if request.method == 'POST':
        photo = request.files['photo']
        mark = request.form['mark']
        login = request.form['login']
        password = request.form['password']

        res, teacher_id = auth(login, password)

        if res < 2:
            return { "is": 0, "name": "" }

        UPLOAD_FOLD = 'site_image_cache'
        UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        photo.save(APP_ROOT + 'site_image_cache/1.png')
        img = cv2.imread(APP_ROOT + "site_image_cache/1.png", cv2.IMREAD_COLOR)
        face = interlayer.put_mark_recognize(teacher_id, img, mark == "+")

        if face == -1:
            UPLOAD_FOLD = f'static/undefined_image_cache/{teacher_id}/'
            cnt = len(list(paths.list_images(APP_ROOT + UPLOAD_FOLD))) + 1
            os.replace(APP_ROOT + 'site_image_cache/1.png', APP_ROOT + UPLOAD_FOLD + str(cnt) + '.png')
            return { "is": 1, "name": "" }
        else:
            os.remove(APP_ROOT + 'site_image_cache/1.png')

        name = db.session.get(Student, face).name
        return { "is": 2, "name": name }

    return render_template('put_mark.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')