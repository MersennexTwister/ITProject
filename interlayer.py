import cv2
from FaceRec import FaceRec
from spreadsheet import Spreadsheet

def start():
    spreadsheet = Spreadsheet()
    fr = FaceRec('faces')
    fr.startWork()
    return fr, spreadsheet

def main_func(fr, spreadsheet, img):

    face = fr.recogniteTheFace(img)

    if face != -1:
        spreadsheet.put_mark(["01.12.2021", face])

    return face