fill_all_fields = 'Заполните все поля!'
incorrect_symbols = 'Имя содержит недопустимые символы (& и/или -)!'
incorrect_login = 'Неверный логин!'
incorrect_password = 'Неверный пароль!'
student_already_exists = 'Ученик уже есть у вас в классе!'
incorrect_data = 'Вы ввели несуществующую дату!'
bad_data = 'Неправильно введена дата!'


def login_already_used(login):
    return f'Пользватель с логином "{login}" уже зарегестрирован!'