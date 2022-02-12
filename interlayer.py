import cv2
from FaceRec import FaceRec
from spreadsheet import Spreadsheet

def start():
    spreadsheet = Spreadsheet()
    fr = FaceRec('faces')
    fr.startWork()
    return fr, spreadsheet

def main_func(fr, spreadsheet):

    face = fr.recogniteTheFace()

    if face != -1:
        spreadsheet.put_mark(["01.12.2021", face])

    return face