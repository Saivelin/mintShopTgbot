from xml.etree.ElementTree import tostring
from requests import patch, request
import TOKEN
import telebot
from telebot import types
import qrcode
import sqlite3
import re
import time

usr_commands = ['/start', '/menu', '/showqr', '/showbonus']
adm_commands = ['/addbonus', '/subtractbonus']
db_users_name = 'db.sqlite'
bot = telebot.TeleBot(TOKEN.token)

@ bot.message_handler(commands=['start'])
def start_message(message):
    con = sqlite3.connect(db_users_name)
    curs = con.cursor()
    curs.execute("SELECT id FROM users WHERE id = ?", (message.chat.id,))
    usr_id = curs.fetchone()
    if usr_id is not None:
        bot.send_message(message.chat.id, 'Вы уже зарегестрированы')
        mainMenu(message)
        return

    text = "Добро пожаловать. Я преставляю магазин MintShop. У меня ты можешь получить свой qr код с которым поделишься с друзьями, получишь бонусы и сможешь потратить их в нашем магазине по адресу: г. Нижний новгород, б. Заречный 2, ТЦ Корона, 2 этаж. Покупки в нашем магазине можно осуществлять только после совершеннолетия. Тебе есть 18?'"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.InlineKeyboardButton("Да, мне есть 18")
    button2 = types.InlineKeyboardButton("Нет, мне нет 18")
    markup.add(button1, button2)

    msg = bot.reply_to(message, text, reply_markup=markup)
    bot.register_next_step_handler(msg, check_age)

def check_age(message):

    if(message.text == "Нет, мне нет 18"):
        bot.send_message(message.chat.id, "Тогда заходи, когда вырастешь)")
    elif(message.text == "Да, мне есть 18"):
        text = "Окей. Ты согласен на обработку персональных данных?"

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button1 = types.KeyboardButton("Согласен", request_contact=True)
        button2 = types.KeyboardButton("Не согласен")
        markup.add(button1, button2)

        msg = bot.reply_to(message, text, reply_markup=markup)
        bot.register_next_step_handler(msg, check_text_answer)

def check_text_answer(message):
    if message.text == "Не согласен":
        bot.send_message(message.chat.id, "Нажимай /start если передумаешь)")

@bot.message_handler(content_types=['contact'])
def try_add_contact(message):
    pn = message.contact.phone_number
    id = int(message.chat.id)
    print(pn)
    print(id)
    text = 'Хорошо, сейчас зарегестрирую тебя'
    bot.send_message(message.chat.id, text)

    con = sqlite3.connect(db_users_name)
    curs = con.cursor()
    curs.execute("SELECT phoneNum FROM users WHERE phoneNum = ?", (pn,))
    usr = curs.fetchone()

    if usr is None: # регистрация (такого пользователя нет)
        curs.execute(
            f"INSERT INTO users (id, phoneNum, bonus, role) VALUES ('{id}','{pn}', 0, 'user')")
        text = 'Регистрация прошла успешно)'
        con.commit()
    else:
        text = 'Ты уже зарегистрирован)'

    msg = bot.send_message(message.chat.id, text)
    mainMenu(msg)

@bot.message_handler(commands=['menu'])
def mainMenu(message):
    # генерация кнопок (а лучше просто месседж кинуть, будет ахуенно)
    # заглушка
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for i in range(0, len(usr_commands)):
        button = types.InlineKeyboardButton(usr_commands[i])
        markup.add(button)
    if (check_usr_or_admin(message)):
        for i in range(0, len(adm_commands)):
            button = types.InlineKeyboardButton(adm_commands[i])
            markup.add(button)
    bot.send_message(message.chat.id, "Меню", reply_markup=markup)

@bot.message_handler(commands=['showqr'])
def show_qr(message):
    con = sqlite3.connect(db_users_name)
    curs = con.cursor()
    curs.execute("SELECT phoneNum FROM users WHERE id = ?", (message.chat.id,))
    usr_phone = str(curs.fetchone())

    pn = re.sub("[(|)|,|']", "", usr_phone)
    id = str(message.chat.id)
    img = qrcode.make(id + '_' + pn)

    # система с сохранением может быть хуетой если сохраняется на серваке,
    # сервак рано или поздно забьётся
    path = 'qrs/' + id + '.png'
    img.save(path)
    photo = open(path, 'rb')
    bot.send_photo(message.chat.id, photo)

    text = "Вот твой qr код, ИНФА ПРО QR КОД И ЕГО РАБОТУ. \nТвой номер: "
    bot.send_message(message.chat.id, text + pn)

@bot.message_handler(commands=['showbonus'])
def show_bonus(message):
    con = sqlite3.connect(db_users_name)
    curs = con.cursor()
    curs.execute("SELECT bonus FROM users WHERE id = ?", (message.chat.id,))
    usr_bonus = str(curs.fetchone())
    bot.send_message(message.chat.id, re.sub("[(|)|,]", "", usr_bonus))

def check_usr_or_admin(message):
    con = sqlite3.connect(db_users_name)
    curs = con.cursor()
    curs.execute('SELECT role FROM users WHERE id = ?', (message.chat.id,))
    usr_role = re.sub("[(|)|,]", "", str(curs.fetchone()))
    print(usr_role)
    if usr_role != '\'admin\'':
        bot.send_message(message.chat.id, 'Вы не являетесь администратором')
        return False
    bot.send_message(message.chat.id, 'Вы являетесь администратором')
    return True

@bot.message_handler(commands=['addbonus'])
def add_bonus(message):
    check_usr_or_admin(message)

@bot.message_handler(commands=['subtractbonus'])
def subtract_bonus(message):
    check_usr_or_admin(message)

#def enter_usr_chat_id(message):
    

bot.polling(none_stop=True)
