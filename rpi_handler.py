import requests as rqs
import os
import RPi.GPIO as GPIO
import time
import picamera
from tkinter import Tk, Label    
from PIL import ImageTk, Image


BUTTON_P = 8
BUTTON_M = 10
DELAY_SEC = 0.05

prev_p, cur_p = False, False
prev_m, cur_m = False, False

URL = 'https://umarnurmatov.pythonanywhere.com/'
LOGIN = 'testlogin44'
PASSWORD = 'testpassword44'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

camera = picamera.PiCamera()

window = Tk()
window.title("project-mars")
window.geometry("480x320")

def setup():
    camera.resolution = (480, 320)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_P, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BUTTON_M, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def image_request(mark):
    global camera
    camera.resolution = (2160, 1440)

    r = rqs.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})
    
    camera.capture(APP_ROOT + '/rpi_image_cache/cached.jpg')
    
    img = open(APP_ROOT + '/rpi_image_cache/cached.jpg', 'rb')

    files = {'photo': img}

    r = rqs.post(URL + 'lk/put_mark', files=files, data={'mark': mark})

    img.close()
    os.remove(APP_ROOT +'/rpi_image_cache/' + 'cached.jpg')
    camera.resolution = (480, 320)

    print(r.text)

def dispaly_frame():
    global camera
    camera.capture(APP_ROOT + '/rpi_image_cache/display_cache.jpg')
    img = ImageTk.PhotoImage(APP_ROOT + "/rpi_image_cache/display_cache.jpg")
    label = Label(window, image = img)
    label.pack()


if __name__ == '__main__':
    setup()
    
    while True:
        dispaly_frame()
        window.mainloop()

        cur_p = GPIO.input(BUTTON_P)
        cur_m = GPIO.input(BUTTON_M)

        if not prev_p and cur_p:
            time.sleep(DELAY_SEC)
            cur_p = GPIO.input(BUTTON_P)
            if not prev_p and cur_p:
                print("Button + pressed")
                image_request('+') 
        elif not prev_m and cur_m:
            time.sleep(DELAY_SEC)
            cur_m = GPIO.input(BUTTON_M)
            if not prev_m and cur_m:
                print("Button - pressed")
                image_request('-') 

        prev_p = cur_p
        prev_m = cur_m
