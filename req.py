import requests as rqs
import os, cv2
import PIL.Image
import numpy as np

video_capture = cv2.VideoCapture(0)
ret, rgb = video_capture.read()
site_adress = 'https://umarnurmatov.pythonanywhere.com/'

r = rqs.post(site_adress + 'enter', data={'login': 'testlogin44', 'password': 'testpassword44'})
teacher_id = int(r.url.split('user=')[1].split('/')[0])

img = PIL.Image.fromarray(rgb, 'RGB')

img.save('hierundda/' + 'qwerty.png')

img = open('hierundda/' + 'qwerty.png', 'rb')

files= {'photo': img}
r = rqs.post(site_adress+'user='+str(teacher_id)+'/put_mark',files=files)

img.close()

os.remove('hierundda/' + 'qwerty.png')

print(r.text)