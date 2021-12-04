from imutils import paths
import face_recognition
import pickle
import cv2
import os

def clearFile(fileName):
    f = open(fileName, "wb+")
    f.seek(0)
    f.close()

class System:

    def __init__(self, path):
        self.workPath = path
        self.studentsDict = {}

    def startWork(self):
        imagePaths = list(paths.list_images(self.workPath))
        knownEncodings = []
        knownId = []
        for (i, imagePath) in enumerate(imagePaths):
            id = imagePath.split(os.path.sep)[-2]
            image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownId.append(id)
        data = {"encodings": knownEncodings, "names": knownId}
        clearFile("face_enc")
        f = open("face_enc", "wb")
        f.write(pickle.dumps(data))
        f.close()

    def recogniteTheFace(self):
        data = pickle.loads(open('face_enc', "rb").read())
        video_capture = cv2.VideoCapture(0)
        ret, rgb = video_capture.read()
        video_capture.release()
        faces = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb)
        names = []
        flist = {}
        for encoding in encodings:
            matches = face_recognition.compare_faces(data["encodings"], encoding)
            name = "Unknown"
            if True in matches:
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                    name = max(counts, key=counts.get)
                names.append(name)

        for (s_faceLoc, name) in zip(faces, names):
            x1, y1, x2, y2 = s_faceLoc[3], s_faceLoc[0], s_faceLoc[1], s_faceLoc[2]
            flist[name] = [x1, y1, x2, y2]

        id = self.getGoodFace(flist, rgb)
        return id

    def getGoodFace(self, faceList, img):
        height, width = img.shape[:2]
        x0, y0 = height / 2, width / 2
        mn = height ** 2 + width ** 2
        k = -1
        for key in faceList:
            x1, y1, x2, y2 = faceList[key]
            x, y = (x1 + x2) / 2, (y1 + y2) / 2
            dist = (x - x0) ** 2 + (y - y0) ** 2
            if mn > dist:
                mn = dist
                k = key
            return key




sys = System("faces")
sys.startWork()
print(sys.recogniteTheFace())