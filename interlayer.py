import cv2
from FaceRec import FaceRec
from spreadsheet import Spreadsheet

if __name__ == "__main__":
    spreadsheet = Spreadsheet()
    fr = FaceRec('../faces')
    fr.startWork()
    while True:
        print("Ready!")
        input("Press Enter to continue...")
        try:
            spreadsheet.put_mark(["01.12.2021", fr.recogniteTheFace()])
        except:
            print("Лицо не распознано!")