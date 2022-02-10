import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3

DATABASE = 'data.db'                                            # Имя файла с таблицей
spreadsheetId = '14PjpStDXX_HueWUH2gNHlsd3yzADQ-RcQAZOOOfNcVI'  # ID гугл-таблицы
CREDENTIALS_FILE = 'striped-century-332109-4fbbc3b60d84.json'   # Имя файла с закрытым ключом
CLASS_LIST = [5, 6, 7, 8, 9, 10, 11]                            # Список номеров классов
SPREADSHEET_TITLE = "Google API test"                           # Название таблицы
MAX_COLUMN_COUNT = 500                                          # Максимальное кол-во столбцов (т.е. макс. кол-во дней - 2)
MAX_ROW_COUNT = 50                                              # Максимальное кол-во строк (т.е. макс. кол-во учеников - 2)

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
            - ячейки заполняются либо "", либо цифрами 2, 2, 3 (кол-во +, полученных учеником на уроке)
    '''

    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __to_sheet_range__(self, num):
        '''
        Преобразование Y-координаты из численной формы в буквенную,
        например: 2 -> А, 13 -> M, 500 -> SF
        '''
        if num // len(self.alphabet) > 0:
            return self.alphabet[num // len(self.alphabet) - 1] + self.alphabet[num % len(self.alphabet) - 1]
        else:
            return self.alphabet[num - 1]

    def __create_sheet_title__(self, class_id):
        '''
        Генерирует название листа
        '''
        return str(class_id) + " класс"

    def __init__(self):
        '''
        Инициализация для подготовки таблицы к работе:
            - создание нужных листов
            - обновление параметров существующих листов
            - удаление лишних листов
        '''

        # Настравиваем общение с базой данных
        self.conn = sqlite3.connect(DATABASE)
        self.cursor = self.conn.cursor()

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
        self.service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

        # Получаем список листов, их Id и название
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
        sheet_list = spreadsheet.get('sheets')

        # Запросы на:
        initialize_requests = []  # Создание недостающих листов
        delete_requests = []  # Удаление лишних (не подходящих по sheetId)
        update_request = []  # Обновление существующих (изменение макс. размера листа)

        class_list_copy = CLASS_LIST

        for sheet in sheet_list:
            delete_flag = True
            # Если sheetId соответсвует номеру класса из CLASS_LIST, опускаем флаг
            for class_id in class_list_copy:
                if sheet["properties"]["sheetId"] == class_id:
                    delete_flag = False

            update_flag = True
            # Если макс. кол-во строк и столбцов листа соотв. заданному, опускаем флаг
            if (sheet["properties"]["gridProperties"]["rowCount"] == MAX_ROW_COUNT
                    and sheet["properties"]["gridProperties"]["columnCount"] == MAX_COLUMN_COUNT):
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
                class_list_copy.remove(sheet["properties"]["sheetId"])  #
                update_request.append({
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet["properties"]["sheetId"],
                            "title": sheet["properties"]["title"],
                            "gridProperties": {
                                "rowCount": MAX_ROW_COUNT,
                                "columnCount": MAX_COLUMN_COUNT
                            }
                        },
                        "fields": "*"
                    }
                })
            else:
                class_list_copy.remove(sheet["properties"]["sheetId"])

        # Обновляем параметры таблицы
        initialize_requests.append({
            "updateSpreadsheetProperties": {
                "properties": {
                    "title": SPREADSHEET_TITLE,
                    "locale": "ru_RU"
                },
                "fields": "*"
            }
        })

        # Создаем новые (недостающие) листы
        # sheetId (UID листа) = номер класса
        # Название листа (title) - см. __create_sheet_title__()
        for class_id in class_list_copy:
            initialize_requests.append({
                "addSheet": {
                    "properties": {
                        "sheetId": class_id,
                        "title": self.__create_sheet_title__(class_id),
                        "gridProperties": {
                            "columnCount": MAX_COLUMN_COUNT,
                            "rowCount": MAX_ROW_COUNT
                        }
                    }
                }
            })

            # Если request не пустой, отправляем его
        if len(initialize_requests) > 0:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId,
                body={"requests": initialize_requests}
            ).execute()
        if len(delete_requests) > 0:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId,
                body={"requests": delete_requests}
            ).execute()
        if len(update_request) > 0:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId,
                body={"requests": update_request}
            ).execute()

        self.max_column_count_conv = self.__to_sheet_range__(MAX_COLUMN_COUNT)

    # Массив с новыми данными
    data_request = []
    # Параметры обновления листов
    sheet_list_updated = []

    def put_mark(self, mark_data):
        print(mark_data)
        '''
        Выставление оценки (+)

        Parameters
        ----------
        mark_data : list
            Формат: [<ДД.ММ.ГГ>,<id ученика>].
        '''

        # Получаем список листов в таблице
        sheet_list = self.service.spreadsheets().get(spreadsheetId=spreadsheetId).execute().get('sheets')

        # Координаты оценки (coordY ∈ {"A", "B", ..., "AA", ... }, coordX ∈ {2, 2, 3 ...})
        coordY, coordX = "0", "0"

        def find_id(_ID):
            '''
            Поиск данных ученика по ID

            Return
            ------
                - ФИО (string)
                - Класс (int)
            '''
            _id_ = self.cursor.execute("SELECT name FROM student where id = " + str(_ID)).fetchone()
            _class_ = self.cursor.execute("SELECT class FROM student where id = " + str(_ID)).fetchone()
            return _id_[0], int(_class_[0])

        student_surname, student_class = find_id(mark_data[1])

        # Ищем нужный лист (соответсвенно с классом ученика) для дальнейшей работы с ним
        sheet = None
        for _sheet in sheet_list:
            if _sheet["properties"]["sheetId"] == student_class:
                sheet = _sheet

        # Дата #
        new_date_flag = True

        try:
            dates = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheetId,
                range=sheet["properties"]["title"] + "!" + "B1:" + self.max_column_count_conv + "1"
            ).execute()["values"][0]
        except KeyError:
            coordY = 2
        else:
            if dates[-1] == mark_data[0]:
                coordY = len(dates) + 1
                new_date_flag = False
            else:
                coordY = len(dates) + 2

        if new_date_flag:
            self.data_request.append({
                "range": sheet["properties"]["title"] + "!" + self.__to_sheet_range__(coordY) + "1",
                "majorDimension": "COLUMNS",
                "values": [
                    [mark_data[0]]
                ]
            })

        # Фамилия #
        new_surname_flag = True
        try:
            surnames = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheetId,
                range=sheet["properties"]["title"] + "!" + "A2:A"
            ).execute()["values"]
        except KeyError:
            coordX = 2
        else:
            for i in range(len(surnames)):
                if student_surname == surnames[i][0]:
                    coordX = i + 2
                    new_surname_flag = False
                    break
            if (new_surname_flag):
                coordX = len(surnames) + 2

        if (new_surname_flag):
            self.data_request.append({
                "range": sheet["properties"]["title"] + "!" + "A" + str(coordX),
                "majorDimension": "ROWS",
                "values": [
                    [student_surname]
                ]
            })

        # Оценка #
        new_mark = 1
        try:
            previous_mark = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheetId,
                range=sheet["properties"]["title"] + "!" + self.__to_sheet_range__(coordY) + str(coordX)
            ).execute()["values"][0][0]
        except KeyError:
            pass
        else:
            new_mark = int(previous_mark) + 1

        self.data_request.append({
            "range": sheet["properties"]["title"] + "!" + self.__to_sheet_range__(coordY) + str(coordX),
            "majorDimension": "ROWS",
            "values": [
                [str(new_mark)]
            ]
        })

        # Отправка новых данных
        if len(self.data_request) > 0:
            self.service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheetId, body={
                "valueInputOption": "RAW",
                "data": self.data_request
            }).execute()

            # Сортировка по фамилии (А -> Я, в лексикографическом порядке)
            self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=
            {
                "requests": [{
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
                        ]}
                }]
            }).execute()

if __name__ == "__main__":
    sp = Spreadsheet()
    sp.put_mark(['12.01.2012', 1])