import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import urllib.request
import datetime

# Настройки #
spreadsheetId = '14PjpStDXX_HueWUH2gNHlsd3yzADQ-RcQAZOOOfNcVI' # ID гугл-таблицы
CREDENTIALS_FILE ='striped-century-332109-4fbbc3b60d84.json'  # Имя файла с закрытым ключом, вы должны подставить свое
class_list = [5, 6, 7, 8, 9, 10, 11] # список номеров классов
spreadsheetTitle = "Google API test" # название таблицы
maxColumnCount = 500 # максимальное кол-во столбцов (т.е. макс. кол-во дней - 1)
maxRowCount = 50 # максимальное кол-во строк (т.е. макс. кол-во учеников - 1)

# Словарь, хранящий данные об учениках
# Формат - { <id ученика>: [<ФИО>,<класс>], ... }
id_list = {
    12: ["Нурматов Умархон Акмалович", 9],
    13: ["Кухаренко Семен Эннович", 9],
    14: ["Абрамнко Василий Константинович", 10]
}


def is_connected_to_internet(host='http://google.com'):
    '''
    Проверка Интернет-соединения

    host : Сайт, на который пытаемся зайти, string. Дефолт 'http://google.com'.
        - true - если Интернет-соединение есть
        - false - нет
    '''
    try:
        urllib.request.urlopen(host) 
        return True
    except:
        return False

class Spreadsheet():
    '''
    Класс-оболочка для ведения электронного журнала оценок в Google Sheets (Google Sheets API) 
    
    Формат таблицы:
        (Лист "9 класс", ID=9)
        
        +--------------+-------+-------+
        |              | <дата>| <дата>| 
        +--------------+-------+-------+
        | <ФИО>        |   2   |       |
        +--------------+-------+-------+
        | <ФИО>        |   2   |   3   |
        +--------------+-------+-------+
        
        Примечания
            - ячейки заполняются либо "", либо цифрами 1, 2, 3 (кол-во +, полученных учеником на уроке)
    '''
    
    def create_sheet_title(self, class_id):
        '''
        Генерирует название (не sheetId!) листа
        '''
        return str(class_id) + " класс"
    
    def create_date(self):
        return (str(datetime.date.today().day) + 
                "." + str(datetime.date.today().month) + 
                "." + str(datetime.date.today().year))


    def __init__(self):
        ''' 
        Инициализация для подготовки таблицы к работе:
            - создание нужных листов
            - обновление параметров существующих листов
            - удаление лишних листов
        '''
        
        # Читаем ключи из файла
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE,
            ['https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive']
        )
        # Авторизуемся в системе
        httpAuth = credentials.authorize(httplib2.Http())
        
        # Выбираем работу с таблицами и 4 версию API и
        # создаем service-объект, с помощью которого осуществляется работа с таблицей
        self.service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) 
        
        # Получаем список листов, их Id и название
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
        sheet_list = spreadsheet.get('sheets')
        
        initialize_requests = [] # Создание недостающих листов
        delete_requests = [] # Удаление лишних (не подходящих по sheetId)
        update_request = [] # Обновление существующих (изменение макс. размера листа)
        
        class_list_copy = class_list
            
        for sheet in sheet_list:
            delete_flag = True
            # Если sheetId соответсвует номеру класса из class_list, опускаем флаг
            for class_id in class_list_copy: 
                if sheet["properties"]["sheetId"] == class_id:
                    delete_flag = False
           
            update_flag = True
            # Если макс. кол-во строк и столбцов листа соотв. заданному, опускаем флаг
            if (sheet["properties"]["gridProperties"]["rowCount"] == maxRowCount 
                  and sheet["properties"]["gridProperties"]["columnCount"] == maxColumnCount):
                update_flag = False
            
            # Если поднят флаг delete, добавляем лист в delte_request
            if delete_flag:
                delete_requests.append({
                    "deleteSheet": {
                        "sheetId": sheet["properties"]["sheetId"]
                    }
                })
            
            # Если поднят флаг update, добавляем новые параметры в update_request
            elif update_flag:
                class_list_copy.remove(sheet["properties"]["sheetId"]) #
                update_request.append({
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet["properties"]["sheetId"],
                            "title": sheet["properties"]["title"],
                            "gridProperties": {
                                "rowCount": maxRowCount,
                                "columnCount": maxColumnCount
                            }
                        },
                        "fields": "*"
                    }
                })
            else:
                class_list_copy.remove(sheet["properties"]["sheetId"])
                
        
        # Обновляем (на всякий случай) параметры таблицы
        initialize_requests.append({
            "updateSpreadsheetProperties": {
                "properties": {
                    "title": spreadsheetTitle,
                    "locale": "ru_RU"
                },
                "fields": "*"
            }                                                   
        })
        
        # Создаем новые (недостающие) листы 
        # sheetId (UID листа) = номер класса
        # Название листа (title) - см. create_sheet_title()
        for class_id in class_list_copy:
            initialize_requests.append({
                    "addSheet": {
                        "properties": {
                           "sheetId": class_id,
                           "title": self.create_sheet_title(class_id),
                           "gridProperties": {
                               "columnCount": maxColumnCount,
                               "rowCount": maxRowCount
                           }
                     }
                }
            })  
        
        # Если request не пустой, отправляем его
        if len(initialize_requests) > 0:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId,
                body = { "requests": initialize_requests }
            ).execute()
        if len(delete_requests) > 0:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId,
                body = { "requests": delete_requests }
            ).execute()
        if len(update_request) > 0:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId,
                body = { "requests": update_request}
            ).execute()
    
    
    def put_mark(self, mark_data):
        '''
        Выставление оценки (+)

        Parameters
        ----------
        mark_data : list
            Формат: [<день>,<месяц>,<год>,<id ученика>].
        '''
        
        # Массив с новыми данными
        data_request = []
        
        # Получаем список листов в таблице
        sheet_list = self.service.spreadsheets().get(spreadsheetId=spreadsheetId).execute().get('sheets')
        
        # Координаты оценки (coordY ∈ {"A", "B", ..., "AA", ... }, coordX ∈ {1, 2, 3 ...})
        coordY, coordX = "0", "0"
        
        # Ищем нужный лист (соответсвенно с классом ученика) для дальнейшей работы с ним
        sheet = None
        for _sheet in sheet_list:
            if _sheet["properties"]["sheetId"] == id_list[mark_data[3]][1]:
                sheet = _sheet
                
                
        def to_sheet_range(num):
            '''
            Преобразование Y-координаты из численной формы в буквенную,
            например: 1 -> А, 13 -> M, 500 -> SF
            '''
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            if num // len(alphabet) > 0:
                return alphabet[num // len(alphabet) - 1] + alphabet[num % len(alphabet) - 1]
            else:
                return alphabet[num - 1]
                
        _maxColumnCount = to_sheet_range(maxColumnCount)
        
        # Дата #
        new_date_flag = True
        
        try:
            dates = self.service.spreadsheets().values().get(
                        spreadsheetId = spreadsheetId, 
                        range = sheet["properties"]["title"] + "!" + "B1:" + _maxColumnCount + "1"
                        ).execute()["values"][0]
        except KeyError:
            coordY = 2   
        else:
            if dates[-1] == (str(mark_data[0]) + "." + str(mark_data[1]) + "." + str(mark_data[2])):
                coordY = len(dates) + 1
                new_date_flag = False
            else:
                coordY = len(dates) + 2
        
        if new_date_flag:
            data_request.append({
                    "range": sheet["properties"]["title"] + "!" + to_sheet_range(coordY) + "1",
                    "majorDimension": "COLUMNS",
                    "values": [
                        [str(mark_data[0]) + "." + str(mark_data[1]) + "." + str(mark_data[2])]
                    ]
                })
        
        # Фамилия #
        new_surname_flag = True
        try:
            surnames = self.service.spreadsheets().values().get(
                spreadsheetId = spreadsheetId, 
                range = sheet["properties"]["title"] + "!" +"A2:A"
            ).execute()["values"]
        except KeyError:
            coordX = 2
        else:
            for i in range (len(surnames)):
                if id_list[mark_data[3]][0] == surnames[i][0]: 
                    coordX = i + 2
                    new_surname_flag = False
                    break
            if(new_surname_flag):
                coordX = len(surnames) + 2
        
        if(new_surname_flag):
            data_request.append({
                    "range": sheet["properties"]["title"] + "!" + "A" + str(coordX),
                    "majorDimension": "ROWS",
                    "values": [
                        [id_list[mark_data[3]][0]]
                    ]
            })
        
        # Оценка #
        new_mark = 1
        try:
            previous_mark = self.service.spreadsheets().values().get(
                spreadsheetId = spreadsheetId, 
                range = sheet["properties"]["title"] + "!" + to_sheet_range(coordY) + str(coordX)
                ).execute()["values"][0][0]
        except KeyError:
            pass
        else:
            new_mark = int(previous_mark) + 1
            
        data_request.append({
                "range": sheet["properties"]["title"] + "!" + to_sheet_range(coordY) + str(coordX),
                "majorDimension": "ROWS",
                "values": [
                    [str(new_mark)]
                ]
        })
        
        # Отправление новых данных
        if len(data_request) > 0:
            self.service.spreadsheets().values().batchUpdate(spreadsheetId = spreadsheetId, body = {
                "valueInputOption": "RAW",
                "data": data_request
            }).execute() 
                
            # Сортировка по фамилии (А -> Я, в лексикографическом порядке)
            self.service.spreadsheets().batchUpdate(spreadsheetId = spreadsheetId, body =
            {
              "requests": [
                {
                  "sortRange": {
                    "range": {
                      "sheetId": sheet["properties"]["sheetId"],
                      "startRowIndex": 1,
                      "startColumnIndex": 0,
                    },
                    "sortSpecs": [
                      {
                        "dimensionIndex": 0,
                        "sortOrder": "ASCENDING"
                      }
                    ]
                  }
                }
              ]
            }).execute()
     
if __name__ == "__main__":
    spreadsheet = Spreadsheet()
    mark_data = [13, 9, 2021, 14]
    spreadsheet.put_mark(mark_data)