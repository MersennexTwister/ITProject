from FaceRec import FaceRec
from spreadsheet import Spreadsheet
import pytz
import datetime

class Interlayer():

    tz = pytz.timezone('Europe/Moscow')

    def __init__(self):
        self.spreadsheet = Spreadsheet()
        self.fr = FaceRec('faces')
        self.fr.startWork()


    def recount(self):
        self.spreadsheet = Spreadsheet()
        self.fr = FaceRec('faces')
        self.fr.startWork()

    def put_mark_recognize(self, img):
        face_id = self.fr.recogniteTheFace(img)

        if face_id != -1:
            dt = datetime.datetime.now(self.tz)
            self.spreadsheet.put_mark([dt.strftime("%d.%m.%Y"), face_id])

        return face_id

    def put_mark_direct(self, id):
        dt = datetime.datetime.now(self.tz)
        self.spreadsheet.put_mark([dt.strftime("%d.%m.%Y"), id])