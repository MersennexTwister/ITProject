import cv2, requests, os
from bs4 import BeautifulSoup

URL = 'http://176.120.8.20:8080/'
LOGIN = 'admin'
PASSWORD = 'admin'
APP_ROOT = '/home/semen/Development/project-mars'
cam = cv2.VideoCapture(0)

rq = requests.Session()

ret, frame = cam.read()
rq.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})

cv2.imwrite("rpi_image_cache/cached.png", frame)
img = open(APP_ROOT + '/rpi_image_cache/cached.png', 'rb')

files = {'photo': img}

r = rq.post(URL + 'lk/put_mark', files=files, data={'mark': "+"})
print(r.text)
img.close()

soup = BeautifulSoup(r.text, "html.parser")

data = soup.findAll("b")
if len(data) == 0:
    print("Не удалось распознать")
else:
    print(data[0].text)