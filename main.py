import telebot
from telebot import types
from user import User
from admin import Admin
import psycopg2, re
import requests, tempfile
from API_modul import APIModule
import os


# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(
    dbname='cobook_db',
    user='postgres',
    password='',
    host='localhost',
    port='5432'
)

TOKEN = "6952946591:AAHdXTymUStAGFKiiXS-O_WeFEPF2yA5e30"
bot = telebot.TeleBot(TOKEN)
api_key = "cddf22cd9bmshad6e03418d2edcep141e40jsn38428a79a6b5"
# Создание курсора для взаимодействия с базой данных
cursor = conn.cursor()

# Команда создания таблицы для зарегистрированных пользователей
create_users_table = '''
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255),
    password VARCHAR(255),
    chat_id VARCHAR(255)
);
'''

cursor.execute(create_users_table)
conn.commit()

# Команда создания таблицы для кулинарной книги
create_recipes_table = '''
CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    photo_url VARCHAR(255),
    user_id INTEGER REFERENCES users(id)
);
'''

cursor.execute(create_recipes_table)
conn.commit()

create_recipes_table_on_moderation = '''
CREATE TABLE IF NOT EXISTS recipes_on_moderation (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    photo_url VARCHAR(255),
    user_id INTEGER REFERENCES users(id),
    approved BOOLEAN,
    chat_id VARCHAR(255)
);
'''
def request_to_api():
    api_module = APIModule(api_key, conn, cursor)

    # Получение данных из API
    recipes_data = api_module.fetch_recipes(query='food')

    # Конвертация в CSV
    csv_filename = api_module.convert_to_csv(recipes_data)

    # Загрузка в базу данных
    api_module.add_recipes_to_database(csv_filename)
    # Дополнительные действия, если необходимо

cursor.execute(create_recipes_table_on_moderation)
request_to_api()

conn.commit()
#создание  пустых экземпляров объектов Пользователя и Администратора
user = User(None, None, None, None, None)
admin = Admin(None, None, None, None, None)
TOKEN = "6952946591:AAHdXTymUStAGFKiiXS-O_WeFEPF2yA5e30"
bot = telebot.TeleBot(TOKEN)
#стартовый обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = menu_status1(message)
    bot.send_message(message.chat.id, 'Привет, {0.first_name}!'.format(message.from_user), reply_markup = markup)
#Объявление статусов меню
def menu_status1(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Регистрация ✏️")
    item2 = types.KeyboardButton('Войти в аккаунт 👤')
    item3 = types.KeyboardButton("Информация ℹ️")
    markup.add(item1, item2, item3)
    return markup
#Вошли в аккаунт
def menu_status2(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Мои рецепты 🍔")
    item2 = types.KeyboardButton('Поиск рецепта 📋')
    item3 = types.KeyboardButton('Выйти из аккаунта 🚪')
    item4 = types.KeyboardButton("Назад ◀️")
    markup.add(item1, item2, item3, item4)
    return markup
def menu_status3(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Рецепты на модерации 📕")
    item2 = types.KeyboardButton('Выйти из аккаунта 🚪')
    item3 = types.KeyboardButton("Назад ◀️")
    markup.add(item1,item2, item3)
    return markup

#Обработчики текстовых команд пользователя
@bot.message_handler(content_types=['text'])
def bot_message(message):
    if message.chat.type == "private":
        if message.text == "Регистрация ✏️":
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            back = types.KeyboardButton("Назад ◀️")
            markup.add(back)
            bot.send_message(message.chat.id,"Регистрация ✏️", reply_markup = markup)
            bot.send_message(message.chat.id, "Введите логин:")
            bot.register_next_step_handler(message, process_login_step)
        elif message.text == "Войти в аккаунт 👤":
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            back = types.KeyboardButton("Назад ◀️")
            markup.add(back)
            bot.send_message(message.chat.id, "Войти в аккаунт 👤️", reply_markup=markup)
            #Проверка на существование объекта Пользователя
            if user.username:
                bot.send_message(message.chat.id, "Вы уже вошли в аккаунт")
            else:
                bot.send_message(message.chat.id, "Введите логин:")
                bot.register_next_step_handler(message, handler_login_step)
        elif message.text == "Назад ◀️":
            if user.username:
                markup = menu_status2(message)
            elif admin.username:
                markup = menu_status3(message)
            else:
                markup = menu_status1(message)
            bot.send_message(message.chat.id,"Назад ◀️", reply_markup = markup)
        elif message.text == "Мои рецепты 🍔":
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            item1 = types.KeyboardButton("Отправить рецепт на модерацию 📍")
            item2 = types.KeyboardButton('Рецепты на модерации 👤')
            markup.add(item1, item2)
            bot.send_message(message.chat.id,"Мои рецепты 🍔", reply_markup = markup)
        elif message.text == "Рецепты на модерации 👤":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Назад ◀️")
            markup.add(back)
            send_recipes_on_moderation_for_user(message)
        elif message.text == "Отправить рецепт на модерацию 📍":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Назад ◀️")
            markup.add(back)
            bot.send_message(message.chat.id, "Отправить рецепт на модерацию 📍", reply_markup=markup)
            bot.send_message(message.chat.id, "Введите текст рецепта:")
            bot.register_next_step_handler(message, lambda msg: handler_recipe_step(msg, user))
        elif message.text == "Поиск рецепта 📋":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Назад ◀️")
            markup.add(back)
            bot.send_message(message.chat.id, "Введите текст рецепта:")
            bot.register_next_step_handler(message, process_search)
        elif message.text == "Рецепты на модерации 📕":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Назад ◀️")
            markup.add(back)
            bot.send_message(message.chat.id,"Рецепты на модерации 📕", reply_markup = markup)
            send_recipes_on_moderation(message)
        elif message.text == "Выйти из аккаунта 🚪":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Назад ◀️")
            markup.add(back)
            log_out_from_account(message)
            bot.send_message(message.chat.id,"Выйти из аккаунта 🚪", reply_markup = markup)
#Функция выхода из аккаунтов
def log_out_from_account(message):
    global user, admin
    if user.username:
        user = User(None, None, None, None, None)
    elif admin.username:
        admin = Admin(None, None, None, None, None)
    bot.send_message(message.chat.id, "Вы вышли из аккаунта")
#Функция отправки рецептов на модерации пользователю
def send_recipes_on_moderation_for_user(message):
    admin_panel_recipes = user.check_recipes_on_moderation()
    for recipe in admin_panel_recipes:
        id, title, description, photo_url = recipe
        message_text = f"*{title}*\n{description}"

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(requests.get(photo_url).content)
            temp_file.seek(0)  # Перемещаем указатель в начало файла
            bot.send_photo(chat_id=message.chat.id, photo=temp_file, caption=message_text, parse_mode='Markdown')
#Функция отправки рецептов на модерации администратору
def send_recipes_on_moderation(message):
    admin_panel_recipes = admin.check_recipes_on_moderation()
    for recipe in admin_panel_recipes:
        id, title, description, photo_url = recipe
        message_text = f"*{title}*\n{description}"

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(requests.get(photo_url).content)
            temp_file.seek(0)  # Перемещаем указатель в начало файла
            bot.send_photo(chat_id=message.chat.id, photo=temp_file, caption=message_text, parse_mode='Markdown')
    admin_panel(message)
# Функция для получения списка рецептов на модерации
def admin_panel(message):
    recipes_on_moderation = admin.check_recipes_on_moderation()

    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(row_width=2)
    for recipe in recipes_on_moderation:
        recipe_id, title, description, photo_url = recipe
        markup.add(types.KeyboardButton(f"{recipe_id}: {title}"))

    # Добавляем кнопку "Выход"
    markup.add(types.KeyboardButton("Выход"))

    bot.send_message(message.chat.id, "Выберите рецепты для утверждения:", reply_markup=markup)

    bot.register_next_step_handler(message, process_admin_choice)

# Обработчик выбора администратором

def process_admin_choice(message):
    # Проверяем, была ли нажата кнопка "Выход"
    if message.text == "Выход":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Назад ◀️")
        markup.add(back)
        bot.send_message(message.chat.id, "Вы вышли из редактора", reply_markup=markup)
        bot.register_next_step_handler(message, process_admin_exit)
        return

    # Используем регулярное выражение для извлечения чисел из ввода
    choices = re.findall(r'\d+', message.text)
    approved_recipes = [int(choice) for choice in choices]

    # Добавляем утвержденные рецепты в основную таблицу
    for recipe_id in approved_recipes:
        answer, chat_id = admin.insert_approved_recipe(recipe_id)
        bot.send_message(chat_id, answer)
    # Повторяем вызов админской панели
    admin_panel(message)
#Обработчик события кнопки Выход на клавиатуре
def process_admin_exit(message):
    if message.text == "Рецепты на модерации":
        # Выводим список рецептов на модерации
        recipes_on_moderation = admin.check_recipes_on_moderation()
        response = "Рецепты на модерации:\n"
        for recipe in recipes_on_moderation:
            recipe_id, title = recipe
            response += f"{recipe_id}: {title}\n"

        bot.send_message(message.chat.id, response)
    elif message.text == "Выход":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Назад ◀️")
        markup.add(back)
        bot.send_message(message.chat.id, "Вы вышли из редактора", reply_markup=markup)

#Обработчик поиска рецепта по названию
def process_search(message):
    search_query = message.text
    # Ищем рецепты по названию
    search_results = user.serch_recipes(search_query)

    if search_results:
        for recipe in search_results:
            id, title, description, photo_url = recipe
            message_text = f"*{title}*\n{description}"

            # Определение формата ссылки
            is_telegram_link = photo_url.startswith('https://api.telegram.org/file/bot')

            # Загрузка изображения
            try:
                if is_telegram_link:
                    # Ссылка из Telegram
                    file_path = photo_url.split('/')[-1]
                    image_content = requests.get(photo_url).content
                else:
                    # Ссылка из другого источника
                    image_content = requests.get(photo_url).content
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {e}")
                continue  # Пропустить текущий рецепт и перейти к следующему

            # Создание временного каталога для сохранения изображения
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, "recipe_image.jpg")
                with open(temp_file_path, 'wb') as temp_file:
                    temp_file.write(image_content)

                # Отправка изображения пользователю
                with open(temp_file_path, 'rb') as photo_file:
                    try:
                        bot.send_photo(chat_id=message.chat.id, photo=photo_file, caption=None, parse_mode='Markdown')
                        bot.send_message(chat_id=message.chat.id, text=message_text, parse_mode='Markdown')

                    except telebot.apihelper.ApiTelegramException as e:
                        print(f"Telegram API Error: {e}")


#Этапы обработки ввода текста и фото рецепта пользователем
def handler_recipe_step(message, user):
    title = message.text
    # Передаем объект user вместе с title
    bot.send_message(message.chat.id, "Введите описание рецепта:")
    bot.register_next_step_handler(message, lambda msg: handler_recipe_description_step(msg, title, user))

def handler_recipe_description_step(message, title, user):
    description = message.text
    bot.send_message(message.chat.id, "Отправьте фото к рецепту:")
    bot.register_next_step_handler(message, handler_recipe_photo_step, title=title, description=description, user=user)

def handler_recipe_photo_step(message, title, description, user):
    # Обработка фото
    if message.content_type == 'photo':
        # Получаем объект PhotoSize, который содержит информацию о фотографии
        photo = message.photo[-1]

        # Получаем объект File по его ID
        file_info = bot.get_file(photo.file_id)

        # Получаем ссылку на файл
        file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}'
        user.send_recipe_for_moderation(title, description, file_url, message.chat.id)
        bot.send_message(message.chat.id, f"Ваш Рецепт '{title}' проходит модерацию, мы сообщим когда он будет добавлен!")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте фото к рецепту.")
        bot.register_next_step_handler(message, handler_recipe_photo_step, title=title, description=description, user=user)
#Обработка пароля введеного пользователем
def handler_login_step(message):
    login = message.text
    bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(message, handler_password_step, login)
#Создание объекта Пользователя или Администратора
def handler_password_step(message, login):
    global user, admin
    password = message.text

    # Проверка аккаунта в базе данных
    check_account_query = "SELECT * FROM users WHERE username = %s AND password = %s;"
    cursor.execute(check_account_query, (login, password))
    account = cursor.fetchone()

    if login == "admin" and password == "admin":
        user_id = account[0]
        admin = Admin(user_id, login, password, conn, cursor)
        markup = menu_status3(message)
        bot.send_message(message.chat.id, f"Рады приветсвовать admin!", reply_markup=markup)
    elif account:
        # Если аккаунт существует, вход выполнен
        user_id = account[0]
        user = User(user_id, login, password, conn, cursor)
        bot.send_message(message.chat.id, f"Вы вошли в аккаунт!")
        markup = menu_status2(message)
        bot.send_message(message.chat.id, f'Привет, {login}!', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"Не удается войти в аккаунт с логином {login}. Попробуйте снова")

# Пример функции регистрации пользователя
def process_login_step(message):
    login = message.text

    # Сохраняем chat_id пользователя
    chat_id = message.chat.id

    bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(message, process_password_step, login, chat_id)
def process_password_step(message, login, chat_id):
    password = message.text

    # Добавляем пользователя в базу данных
    insert_user_query = "INSERT INTO users (username, password, chat_id) VALUES (%s, %s, %s);"
    cursor.execute(insert_user_query, (login, password, chat_id))
    conn.commit()

    bot.send_message(message.chat.id, f"Пользователь с логином {login} успешно зарегистрирован!")


try:
    bot.polling(none_stop=True)
finally:
    # Закрытие соединения с базой данных в случае любых ошибок
    cursor.close()
    conn.close()