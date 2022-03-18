import requests as rqs
import os
# import RPi.GPIO as GPIO
# import time
# import picamera
#
# BUTTON = 8
# DELAY_SEC = 0.05
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# prev, cur = False, False

URL = 'https://umarnurmatov.pythonanywhere.com/'
LOGIN = 'testlogin44'
PASSWORD = 'testpassword44'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# camera = picamera.PiCamera()
# camera.resolution = (2160, 1440)


def image_request(s):
    r = rqs.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})

    camera.capture(APP_ROOT + '/rpi_image_cache/cached.jpg')

    img = open(APP_ROOT + '/rpi_image_cache/cached.jpg', 'rb')

    files = {'photo': img}
    r = rqs.post(URL + 'lk/put_mark', files=files, data={"mark": s})

    img.close()
    os.remove(APP_ROOT + '/rpi_image_cache/' + 'cached.jpg')

    print(r.text)


if __name__ == '__main__':
    # while True:
    #     cur = GPIO.input(BUTTON)
    #     if not prev and cur:
    #         time.sleep(DELAY_SEC)
    #         cur = GPIO.input(BUTTON)
    #         if not prev and cur:
    #             print("Button pressed")
    #             image_request()
    #   prev = cur

    s = input("Какую оценку хотите выставить(+/-): ")
    image_request(s)
