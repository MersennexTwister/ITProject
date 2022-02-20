from FaceRec import FaceRec
from spreadsheet import Spreadsheet
import pytz
import datetime

tz = pytz.timezone('Europe/Moscow')

def start():
    spreadsheet = Spreadsheet()
    fr = FaceRec('faces')
    fr.startWork()
    return fr, spreadsheet

def recount():
    fr = FaceRec('faces')
    fr.startWork()
    return fr

def main_func(fr, spreadsheet, img):

    face_id = fr.recogniteTheFace(img)

    if face_id != -1:
        dt = datetime.datetime.now(tz)
        spreadsheet.put_mark([dt.strftime("%d.%m.%Y"), face_id])

    return face_id

def put_mark_directly(id, spreadsheet):
    dt = datetime.datetime.now(tz)
    spreadsheet.put_mark([dt.strftime("%d.%m.%Y"), id])