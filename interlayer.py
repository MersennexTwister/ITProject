import pandas as pd
import cv2
from modules.FaceRec import FaceRec
from spreadsheet import Spreadsheet
import urllib.request

# Название файла с локальной таблицей
LOCAL_MARK_DATA = "local_mdata.xlsx"

class Interlayer:   
    '''
    Промежуточный модуль между CV и GoogleSheets   
    
    Основная задача - проверить наличие Интернета, и при его отсутствии сохранить
    данные локально. Если Интернет есть, выгружает все локальные данные в сеть.
    '''
    
    def __is_connected_to_internet__(self, host='http://google.com'):
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
        
    spreadsheet_init_flag = False
    def __connect_to_google_sheets__(self):
        '''
        Попытка подключения к GoogleSheets и создания service-объекта

        При наличии Интернета создает объект класса Spreadsheet и инициализирует его; 
        опускает флаг
        
        При отсутствии Интернета оставляет флаг поднятым; при следующей попытке
        выставить оценку будет осуществлена еще одна попытка
        '''
        if self.__is_connected_to_internet__() and not self.spreadsheet_init_flag:
            self.spreadsheet = Spreadsheet()
            self.spreadsheet_init_flag = True
            
    def __init__(self):
        self.__connect_to_google_sheets__()
        
        # Таблица с локальными данными об оценках
        # +--------------+----+
        # | date         | ID | 
        # +--------------+----+
        # |  <ДД.ММ.ГГ>  | 0  |
        # +--------------+----+
        # |  <ДД.ММ.ГГ>  | 2  |
        # +--------------+----+
        self.local_mdata = pd.read_excel(LOCAL_MARK_DATA)
    

    def put_mark(self, date, ID):
        print(ID)
        # Соединение с GoogleSheets для работы с интернет-таблицей
        self.__connect_to_google_sheets__()
        
        if self.__is_connected_to_internet__():
            # Считываем локальные данные об оценках
            for i in range(len(self.local_mdata['date'])):
                mdata = [self.local_mdata['date'][i], self.local_mdata['ID'][i]]
                self.spreadsheet.put_mark(mdata)
            # Очищаем локальные данные
            self.local_mdata = pd.DataFrame({'date':[], 'ID':[]})
            
            # Выставляем новую оценку
            mdata = [date, ID]
            self.spreadsheet.put_mark(mdata)
        else:
            # Если Интернета нет, сохраняем оценку локально
            self.local_mdata = self.local_mdata.append({'date':date, 'ID':ID}, ignore_index=True)
        
        # Обновляем локальную таблицу
        self.local_mdata.to_excel(LOCAL_MARK_DATA, index=False)
            
        
    
if __name__ == "__main__":
    interlayer = Interlayer()
    fr = FaceRec('../modules/faces')
    fr.startWork()
    while True:
        print("Ready!")
        input("Press Enter to continue...")
        try:
            interlayer.put_mark("01.12.2021", fr.recogniteTheFace())
        except:
            print("Лицо не распознано!")