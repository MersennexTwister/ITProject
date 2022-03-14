import requests as rqs
import os
import RPi.GPIO as GPIO
import time
from picamera import PiCamera

BUTTON = 8
DELAY_SEC = 0.05
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
prev, cur = False, False

URL = 'https://umarnurmatov.pythonanywhere.com/'
LOGIN = 'testlogin44'
PASSWORD = 'testpassword44'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

camera = PiCamera()

def image_request():
    r = rqs.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})
    
    camera.capture(APP_ROOT + '/rpi_image_cache/cached.png')
    img = open(APP_ROOT + '/rpi_image_cache/cached.png', 'rb')

    files = {'photo': img}
    r = rqs.post(URL + 'lk/put_mark', files=files)

    img.close()
    os.remove(APP_ROOT +'/rpi_image_cache/' + 'cached.png')

    print(r.text)

if __name__ == '__main__':
    while True:
        cur = GPIO.input(BUTTON)
        if not prev and cur:
            time.sleep(DELAY_SEC)
            cur = GPIO.input(BUTTON)
            if not prev and cur:
                print("Button pressed")
                image_request() 
        prev = cur
    

    
