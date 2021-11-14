import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

spreadsheetId = '14PjpStDXX_HueWUH2gNHlsd3yzADQ-RcQAZOOOfNcVI'
CREDENTIALS_FILE ='striped-century-332109-4fbbc3b60d84.json'  # Имя файла с закрытым ключом, вы должны подставить свое

# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API


# Получаем список листов, их Id и название
spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
sheetList = spreadsheet.get('sheets')
sheetId = sheetList[0]['properties']['sheetId']

# ПРИМЕР #
# Рисуем рамку
results = service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheetId,
    body={
        "requests": [
            {'updateBorders': {'range': {'sheetId': sheetId,
                                         'startRowIndex': 1,
                                         'endRowIndex': 3,
                                         'startColumnIndex': 1,
                                         'endColumnIndex': 4},
                               'bottom': {
                                   # Задаем стиль для верхней границы
                                   'style': 'SOLID',  # Сплошная линия
                                   'width': 1,  # Шириной 1 пиксель
                                   'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},  # Черный цвет
                               'top': {
                                   # Задаем стиль для нижней границы
                                   'style': 'SOLID',
                                   'width': 1,
                                   'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                               'left': {  # Задаем стиль для левой границы
                                   'style': 'SOLID',
                                   'width': 1,
                                   'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                               'right': {
                                   # Задаем стиль для правой границы
                                   'style': 'SOLID',
                                   'width': 1,
                                   'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                               'innerHorizontal': {
                                   # Задаем стиль для внутренних горизонтальных линий
                                   'style': 'SOLID',
                                   'width': 1,
                                   'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                               'innerVertical': {
                                   # Задаем стиль для внутренних вертикальных линий
                                   'style': 'SOLID',
                                   'width': 1,
                                   'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}}

                               }}
        ]
    }).execute()