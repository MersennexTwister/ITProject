import requests as rqs
import os, cv2
import PIL.Image
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time

BUTTON = 8
DELAY_SEC = 0.05
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
prev, cur = False, False

URL = 'https://umarnurmatov.pythonanywhere.com/'
LOGIN = 'testlogin44'
PASSWORD = 'testpassword44'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def image_request():    
    video_capture = cv2.VideoCapture(0)
    ret, rgb = video_capture.read()
    video_capture.release()
    

    r = rqs.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})
    print(r.text)


    img = PIL.Image.fromarray(rgb, 'RGB')

    img.save(APP_ROOT + '/rpi_image_cache/cached.png')
    img = open(APP_ROOT + '/rpi_image_cache/cached.png', 'rb')

    files = {'photo': img}
    r = rqs.post(URL + 'lk/put_mark', files=files)

    img.close()
    os.remove(APP_ROOT +'/rpi_image_cache/' + 'cached.png')

    print(r.text)

if __name__ == '__main__':
    while True: # Run forever
        cur = GPIO.input(BUTTON)
        if not prev and cur:
            time.sleep(DELAY_SEC)
            cur = GPIO.input(BUTTON)
            if not prev and cur:
                print("Button pressed")
                image_request() 
        prev = cur
    

    