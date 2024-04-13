from imutils import paths
import face_recognition
import pickle, cv2, os, time
from settings import APP_ROOT

def clear_file(fileName):
    f = open(fileName, "wb+")
    f.seek(0)
    f.close()

def count_faces(teacher_id, id_list):
    image_paths = []
    for new_id in id_list:
        print(new_id)
        image_paths += list(paths.list_images(APP_ROOT + f'static/faces/{new_id}'))
    known_encodings = []
    known_id = []
    for (i, imagePath) in enumerate(image_paths):
        iid = imagePath.split(os.path.sep)[-2]
        image = cv2.imread(imagePath)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        for encoding in encodings:
            known_encodings.append(encoding)
            known_id.append(iid)
    data = {"encodings": known_encodings, "names": known_id}
    clear_file(APP_ROOT + f'encs/face_enc_{teacher_id}')
    f = open(APP_ROOT + f'encs/face_enc_{teacher_id}', "wb")
    f.write(pickle.dumps(data))
    f.close()

def recognite_the_face(teacher_id, img):
    data = pickle.loads(open(APP_ROOT + f'encs/face_enc_{teacher_id}', "rb").read())
    rgb = img
    faces = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb)
    face_list = {}
    for (encoding, s_faceLoc) in zip(encodings, faces):
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"
        if True in matches:
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1
                name = max(counts, key=counts.get)
            x1, y1, x2, y2 = s_faceLoc[3], s_faceLoc[0], s_faceLoc[1], s_faceLoc[2]
            face_list[name] = [x1, y1, x2, y2]

    return get_good_face(face_list, rgb)

def get_good_face(face_list, img):

    width, height = img.shape[:2]
    x_center, y_center = height / 2, width / 2
    min_dist = height ** 2 + width ** 2 + 100
    result_id = -1

    for t_id in face_list:
        x1, y1, x2, y2 = face_list[t_id]
        face_x, face_y = (x1 + x2) / 2, (y1 + y2) / 2
        dist = (face_x - x_center) ** 2 + (face_y - y_center) ** 2
        if min_dist > dist:
            min_dist = dist
            result_id = t_id

    return result_id
