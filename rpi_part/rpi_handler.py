import requests as rqs
import os
import RPi.GPIO as GPIO
import time
import picamera
from bs4 import BeautifulSoup

BUTTON_P = 8
BUTTON_M = 10
BUTTON_STOP = 12
DELAY_SEC = 0.05

prev_p, cur_p = False, False
prev_m, cur_m = False, False

URL = 'http://176.120.8.20/'
LOGIN = 'admin'
PASSWORD = 'admin'
APP_ROOT = '/home/pi/project-mars'

camera = picamera.PiCamera()

def setup():
    camera.resolution = (480, 320)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_P, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BUTTON_M, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BUTTON_STOP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def image_request(mark):
    camera.resolution = (2160, 1440)

    r = rqs.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})
    
    camera.capture(APP_ROOT + '/rpi_image_cache/cached.jpg')
    
    img = open(APP_ROOT + '/rpi_image_cache/cached.jpg', 'rb')

    files = {'photo': img}

    r = rqs.post(URL + 'lk/put_mark', files=files, data={'mark': mark})

    img.close()
    os.remove(APP_ROOT +'/rpi_image_cache/' + 'cached.jpg')
    camera.resolution = (480, 320)

    s = r.text
    soup = BeautifulSoup(s, 'html.parser')

    data = soup.findAll('b')
    if len(data) == 0:
        print('Система не смогла распознать ученика в камере')
    else:
        print(f'Имя ученика: {data[0].text}')



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
