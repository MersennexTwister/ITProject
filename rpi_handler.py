import requests as rqs
import os
import RPi.GPIO as GPIO
import time
import picamera
from tkinter import *
from tkinter import ttk
import urllib.request

def check_connect(host='http://google.com'):
    try:
        urllib.request.urlopen(host)
        return True
    except:
        return False

master = Tk()
W, H = 100, 100
master.geometry("100x100")

BUTTON_P = 8
BUTTON_M = 10
BUTTON_STOP = 12
DELAY_SEC = 0.05

prev_p, cur_p = False, False
prev_m, cur_m = False, False

URL = 'http://mars-project.ru/'
LOGIN = 'testlogin44'
PASSWORD = 'testpassword44'
APP_ROOT = '/home/pi/project-mars'

camera = picamera.PiCamera()

def setup():
    camera.resolution = (480, 320)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_P, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BUTTON_M, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BUTTON_STOP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def send_image(mark, path=APP_ROOT + '/rpi_image_cache/cached.jpg'):
    r = rqs.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})
    img = open(path, 'rb')

    files = {'photo': img}

    r = rqs.post(URL + 'lk/put_mark', files=files, data={'mark': mark})

    img.close()
    os.remove(path)

    s = r.text
    print(s)
    ind = s.find('<b>')
    if ind == -1:
        Label(master, text= "Мы не смогли распознать изображение").pack()
    else:
        ind2 = s.find('</b>')
        Label(master, text= s[ind1+2:ind2]).pack()
    master.after(3000,lambda:master.destroy())
    master.mainloop()

def send_unsended():
    not_send = os.listdir(APP_ROOT + '/rpi_image_cache')
    for photo in not_send:
        if photo != 'cached.jpg':
            mark = photo[photo.rfind('.')-1:photo.rfind('.')]
            send_image(mark, APP_ROOT + '/rpi_image_cache/' + photo)

def image_request(mark):
    camera.resolution = (2160, 1440)
    if check_connect():
        camera.capture(APP_ROOT + '/rpi_image_cache/cached.jpg')
        send_image(mark)
        
    else:
        not_send = os.listdir(APP_ROOT + '/rpi_image_cache')
        camera.capture(APP_ROOT + '/rpi_image_cache/cached_not_send_' + str(len(not_send)) + '_' + mark + '.jpg')
    
    camera.resolution = (480, 320)



if __name__ == '__main__':
    setup()

    camera.start_preview()
    
    while True:
        cur_p = GPIO.input(BUTTON_P)
        cur_m = GPIO.input(BUTTON_M)

        if GPIO.input(BUTTON_STOP):
            exit()

        if not prev_p and cur_p:
            time.sleep(DELAY_SEC)
            cur_p = GPIO.input(BUTTON_P)
            if not prev_p and cur_p:
                camera.stop_preview()
                print("Button + pressed")
                image_request('+')
                camera.start_preview()
            
        elif not prev_m and cur_m:
            time.sleep(DELAY_SEC)
            cur_m = GPIO.input(BUTTON_M)
            if not prev_m and cur_m:
                camera.stop_preview()
                print("Button - pressed")
                image_request('-') 
                camera.start_preview()

        prev_p = cur_p
        prev_m = cur_m
