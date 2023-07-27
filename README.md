# [Проект МАРС](http://176.120.8.20)

МАРС - Мобильная Автоматическая Рейтинговая Система - проект, призванный автоматизировать выставление оценок учащимся (например, при их устном ответе на уроке) при помощи Computer Vision.

Для использования нашей разработки вам необходимо пройти на [наш сайт](http://176.120.8.20). Там вы найдёт в числе прочего и инструкцию по эксплуатации.

**Программная** часть проекта состоит из четырёх основных модулей:
  - **face_rec.py** - отвечает за распознавания лиц (библиотеки OpenCV, face_recognition)
    + **static/faces** - папка с фотографиями учеников
  - **Графический интерфейс** проекта для конечного пользователя - сайт, написанный на flask:
  	- **app.py** - основной файл визуализации, в нём прописаны все отслеживаемые страницы и взаимодействие с БД.
  	- **mars.db** - база данных, содержащая таблицы необходимой сатйту информацией:
  	  + _Teacher_ - таблица, содержащая информацию об учителях (ID, имя, логин и хэш пароля)
  	  + _Student_ - содержит информацию об учениках (ID, имя, класс, ID учителя)
  	  + _Mark_ - содержит информацию о "плюсиках" выставленных ученикам. Каждая запись имеет вид:
  	    > _ID плюсика - ID ученика - Дата (в численном формате вида ГГГГММДД)_
    - **system_vars.py** - файл, содержащий инициализацию классов БД и самого сайта.
    - **strings.py** - файл строковых констант
    - **funcs.py** - вспомогательные функции
    - **static** - папка, содержащая .html, .css и .ico файлы сайта. Также в ней хранится важная папка **undefined_image_cache**, в которой сохраняются все нераспознанные ученики с возможностью их потом распознать.
    - **templates** - папка с шаблонами сайта
  - **interlayer.py** - файл с функциями, выполняющими функцию запуска системы распознавания лиц и записи информации об оценке в БД.
  - **RPI - файлы** - (отдельный [репозиторий](http://176.120.8.20)) модуль, код которого находится на _Raspberry Pi_ и которых осуществляет захват (библиотека **cv2**) изображения и отправку его на сайт (библиотека **requests**)

**Аппаратная** состоит из камеры и кнопки, подключенных к микрокомпьютеру _Raspberry Pi_. При нажатии на кнопку делается снимок, который с помощью модуля **rpi_handler.py**  обрабатывается и отправляется на сайт, где и происходит распознавание.
