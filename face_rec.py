from imutils import paths
import face_recognition
import pickle
import cv2
import os

def clear_file(fileName):
    f = open(fileName, "wb+")
    f.seek(0)
    f.close()

class FaceRec:

    def __init__(self, app_root):
        self.APP_ROOT = app_root

    def count_faces(self, id_list):
        image_paths = []
        for new_id in id_list:
            list(paths.list_images(self.APP_ROOT + f'static/faces/{id_list}'))
        known_encodings = []
        known_id = []
        for (i, imagePath) in enumerate(image_paths):
            id = imagePath.split(os.path.sep)[-2]
            image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)
            for encoding in encodings:
                known_encodings.append(encoding)
                known_id.append(id)
        data = {"encodings": known_encodings, "names": known_id}
        clear_file(self.APP_ROOT + 'face_enc')
        f = open(self.APP_ROOT + 'face_enc', "wb")
        f.write(pickle.dumps(data))
        f.close()

    def recognite_the_face(self, img):
        data = pickle.loads(open(self.APP_ROOT + 'face_enc', "rb").read())
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

        return self.get_good_face(face_list, rgb)

    def get_good_face(self, face_list, img):
        height, width = img.shape[:2]
        x0, y0 = height / 2, width / 2
        mn = height ** 2 + width ** 2
        result_id = -1
        for t_id in face_list:
            x1, y1, x2, y2 = face_list[t_id]
            x, y = (x1 + x2) / 2, (y1 + y2) / 2
            dist = (x - x0) ** 2 + (y - y0) ** 2
            if mn > dist:
                mn = dist
                result_id = t_id
        return result_id