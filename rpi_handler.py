import requests as rqs
import os, cv2
import PIL.Image

URL = 'https://umarnurmatov.pythonanywhere.com/'
LOGIN = 'testlogin44'
PASSWORD = 'testpassword44'

def image_request():
    video_capture = cv2.VideoCapture(0)
    ret, rgb = video_capture.read()
    video_capture.release()
    

    r = rqs.post(URL + 'login', data={'login': LOGIN, 'password': PASSWORD})
    print(r)
    teacher_id = int(r.url.split('user=')[1].split('/')[0])

    img = PIL.Image.fromarray(rgb, 'RGB')

    img.save('rpi_image_cache/' + 'cached.png')
    img = open('rpi_image_cache/' + 'cached.png', 'rb')

    files= {'photo': img}
    r = rqs.post(URL + 'user='+ str(teacher_id) + '/put_mark', files=files)

    img.close()
    os.remove('rpi_image_cache/' + 'cached.png')

    print(r.text)

if __name__ == '__main__':
    image_request()

    