from xml.etree.ElementTree import tostring
from requests import patch, request
import TOKEN
import telebot
from telebot import types
import qrcode
import sqlite3
import re
from pathlib import Path
import time
import cv2
import PIL
import os

usr_commands = ['/info', '/showqr', '/showbonus']
adm_commands = ['/info', '/regpay']
db_users_name = 'db.sqlite'
bot = telebot.TeleBot(TOKEN.token)


@ bot.message_handler(commands=['start'])
def start_message(message):
    if auth_check(message):
        bot.send_message(message.chat.id, 'Вы уже зарегестрированы')
        mainMenu(message)
        return

    text = "Добро пожаловать. " \
           "Я преставляю магазин MintShop. " \
           "У меня ты можешь получить свой qr код с которым поделишься с друзьями, " \
           "получишь бонусы и сможешь потратить их в нашем магазине по адресу: " \
           "г. Нижний новгород, б. Заречный 2, ТЦ Корона, 2 этаж. " \
           "Покупки в нашем магазине можно осуществлять только после совершеннолетия. "

    print(message.chat.id)
    bot.send_message(message.chat.id, text)
    ask_age(message)


def ask_age(message):
    text = "Тебе есть 18 ?"

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = types.InlineKeyboardButton("Да, мне есть 18")
    button2 = types.InlineKeyboardButton("Нет, мне нет 18")
    markup.add(button1, button2)

    msg = bot.send_message(message.chat.id, text, reply_markup=markup)
    bot.register_next_step_handler(msg, check_age)


def check_age(message):
    if(message.text == "Нет, мне нет 18"):
        bot.send_message(message.chat.id, "Тогда заходи, когда вырастешь) \nНажми /start если уже повзрослел")
    elif(message.text == "Да, мне есть 18"):
        ask_consent(message)


def ask_consent(message):
    text = "Окей. Ты согласен на обработку персональных данных?"

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = types.KeyboardButton("Согласен", request_contact=True)
    markup.add(button1)

    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(content_types=['contact'])
def try_add_contact(message):
    clear_buttons(message)
    pn = message.contact.phone_number
    id = int(message.chat.id)

    text = 'Хорошо, сейчас зарегестрирую тебя'
    bot.send_message(message.chat.id, text)

    con = bd_connect()
    curs = con.cursor()

    if auth_check(message): # пользователь уже есть
        text = 'Ты уже зарегистрирован)'
    else: # регистрация (такого пользователя нет)
        curs.execute(
            f"INSERT INTO users (id, phoneNum, bonus, role) VALUES ({id}, {pn}, 0, 'user')")
        con.commit()
        text = 'Остался всего 1 шаг'

    bot.send_message(message.chat.id, text)
    ask_ref_s1(message)


@ bot.message_handler(commands=['addref'])
def ask_ref_s1(message):
    if (ref_check(message.chat.id)):
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        but1 = types.KeyboardButton("Да, есть")
        but2 = types.KeyboardButton("Нет, такого")
        markup.add(but1, but2)
        msg = bot.send_message(message.chat.id, "У тебя есть друг, который тебя пригласил ?", reply_markup=markup)
        bot.register_next_step_handler(msg, ask_ref_s2)
    else:
        mainMenu(message)


def ask_ref_s2(message):
    clear_buttons(message)
    if message.text == "Да, есть":
        msg = bot.send_message(message.chat.id, 'Отправь сюда фото QR кода своего друга')
        bot.register_next_step_handler(msg, try_add_ref)
    elif message.text == "Нет, такого":
        mainMenu(message)
    else:
        mainMenu(message)


def try_add_ref(message): # сюда уже должен прийти месседж с фото с QR
    ref_id = handle_docs_photo(message)
    print("ref id = ", ref_id)

    if ref_id != 0 and ref_id != None:
        print("registr ref")
        bd_update("users", "urRefId", ref_id, "id", message.chat.id)
        mainMenu(message)
    else:
        print("try again")
        bot.send_message(message.chat.id, "нажми /addref и попробуй сфткать ещё раз, либо перейди в /menu")


@bot.message_handler(commands=['menu'])
def mainMenu(message):
    # генерация кнопок (а лучше просто месседж кинуть, будет ахуенно)
    # заглушка
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if (check_usr_or_admin(message)):
        text = "Меню администратора Mint shop" \
               "\n/info - для информации что нужно делать" \
               "\n/regpay - отправить и считать QR код для снятия и начисления бонусов"
        for i in range(0, len(adm_commands)):
            button = types.InlineKeyboardButton(adm_commands[i])
            markup.add(button)
    else:
        text = "Меню Mint shop" \
               "\n/info - для информации по QR коду" \
               "\n/showqr - показать твой QR код" \
               "\n/showbonus - показать счётчик бонусов"
        for i in range(0, len(usr_commands)):
            button = types.InlineKeyboardButton(usr_commands[i])
            markup.add(button)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=['showqr'])
def show_qr(message):
    usr_phone = bd_select_one_str("phoneNum", "users", "id", message.chat.id)

    pn = re.sub("[(|)|,|']", "", usr_phone)
    id = str(message.chat.id)
    #img = qrcode.make(id + '_' + pn)
    img = qrcode.make(id)

    # система с сохранением может быть хуетой если сохраняется на серваке,
    # сервак рано или поздно забьётся
    path = 'qrs/' + id + '.png'
    img.save(path)
    photo = open(path, 'rb')
    bot.send_photo(message.chat.id, photo)

    text = "Вот твой qr код, нажми /info чтобы узнать как он работает"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['showbonus'])
def show_bonus(message):
    usr_bonus = bd_select_one_str("bonus", "users", "id", message.chat.id)
    bot.send_message(message.chat.id, re.sub("[(|)|,]", "", usr_bonus))


@bot.message_handler(commands=['info'])
def info(message):
    if (check_usr_or_admin(message)):
        bot.send_message(message.chat.id, 'Ты админ, '
                                          'чтобы начислить или '
                                          'списать бонусы '
                                          'тебе нужно сделать фотку'
                                          ' в QR посетителя, затем '
                                          'загрузить его мне.'
                                          'Я обработаю фото и скажу '
                                          'кто перед тобой, введи сумму '
                                          'его заказа '
                                          'я начислю бынусы.')
    else:
        bot.send_message(message.chat.id, 'ну у тебя есть меню, потыкай, '
                                          'приглашай друзей и получай '
                                          'за них бонусы)')


@bot.message_handler(commands=['regpay'])
def reg_pay(message):
    text = "Сфотографируй QR код покупателя и отправь мне"
    msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(msg, check_qr)


def check_qr(message):
    if message.content_type == 'photo':
        usr_chat_id = handle_docs_photo(message)
        if usr_chat_id != 0 and usr_chat_id != None:
            enter_sum(message, usr_chat_id)
        else:
            bot.send_message(message.chat.id, "Упс. что-то пошло не так")
            mainMenu(message)
    else:
        mainMenu(message)


def enter_sum(message, usr_chat_id):
    text = "На какую сумму приобрёл товара ?"
    msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(msg, subtract_bonus, usr_chat_id=usr_chat_id)


def subtract_bonus(message, usr_chat_id):
    # Подключение к базе + апдейт бонусов
    try:
        good_price = int(message.text)
        usr_bonus = bd_select_one_str("bonus", "users", "id", usr_chat_id)
        usr_bonus = re.sub("[(|)|,]",  "", usr_bonus)

        text = "У пользователя на счету: " + usr_bonus + "\nСколько хотите списать?"
        bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(message, get_new_sum, usr_chat_id=usr_chat_id, good_price=good_price, usr_bonus=int(usr_bonus))
    except Exception:
        print(type(message.text))
        bot.send_message(message.chat.id, "Не могу прочитать число")
        mainMenu(message)


def get_new_sum(message, usr_chat_id, good_price, usr_bonus):
    try:
        if usr_bonus == 0:
            text = "Было потрачено: 0 бонусов.\nСтоимость покупки: " + str(good_price) + "руб."
            bot.send_message(message.chat.id, text)
            add_bonus(message, usr_chat_id, good_price, usr_bonus)
            return

        lost_bonus = int(message.text)
        if usr_bonus < lost_bonus:
            lost_bonus = usr_bonus
        if good_price < lost_bonus:
            lost_bonus = good_price

        good_price -= lost_bonus
        usr_bonus -= lost_bonus

        text = "Было потрачено: " + str(lost_bonus) + " бонусов.\nСтоимость покупки: " + str(good_price) + "руб."
        bot.send_message(message.chat.id, text)
        add_bonus(message, usr_chat_id, good_price, usr_bonus)
    except Exception:
        print(type(message.text))
        bot.send_message(message.chat.id, "Не могу прочитать число")
        mainMenu(message)


def add_bonus(message, usr_chat_id, good_price, usr_bonus):
    bonus = good_price // 10
    bonus += usr_bonus

    bd_update("users", "bonus", bonus, "id", usr_chat_id)
    text = "Спасибо за покупку, вам начислено: " \
           + str(good_price//10) + " бонусов.\nТеперь у вас: " + str(bonus) + " бонусов."
    bot.send_message(message.chat.id, text)
    bot.send_message(usr_chat_id, text)

    if ref_check(usr_chat_id):
        ref_id = bd_select_one_str("urRefId", "users", "id", usr_chat_id)
        ref_id = re.sub("[(|)|,]",  "", ref_id)
        ref_bonus = good_price//20
        bot.send_message(ref_id, "Вам начислено: " + str(ref_bonus) + " бонусов.")
        ref_bonus += int(re.sub("[(|)|,]",  "", bd_select_one_str("bonus", "users", "id", ref_id)))
        bd_update("users", "bonus", ref_bonus, "id", int(ref_id))

    mainMenu(message)




def handle_docs_photo(message):
    Path(f'files/{message.chat.id}/').mkdir(parents=True, exist_ok=True)
    if message.content_type == 'photo':
        file_info = bot.get_file(
            message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = f'files/{message.chat.id}/' + \
              file_info.file_path.replace('photos/', '')
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        # read the QRCODE image
        image = cv2.imread(src)
        # initialize the cv2 QRCode detector
        detector = cv2.QRCodeDetector()
        # detect and decode
        data, vertices_array, binary_qrcode = detector.detectAndDecode(
            image)
        # if there is a QR code
        # print the data
        if vertices_array is not None:
            bot.send_message(message.chat.id, "qr code")
            bot.send_message(message.chat.id, data)
            return data
        else:
            bot.send_message(message.chat.id, 'Упс. Я не вижу здесь QR код')
            print("There was some error")
            return 0


def clear_buttons(message):
    markuo = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "очистка", reply_markup=markuo)


def check_usr_or_admin(message):
    usr_role = bd_select_one_str("role", "users", "id", message.chat.id)
    usr_role = re.sub("[(|)|,]", "", usr_role)
    print(usr_role)

    # текст не обязателен, потом лучше убрать
    if usr_role != '\'admin\'':
        #bot.send_message(message.chat.id, 'Вы не являетесь администратором')
        return False
    else:
        #bot.send_message(message.chat.id, 'Вы являетесь администратором')
        return True

def bd_connect():
    con = sqlite3.connect(db_users_name)
    return con

def bd_select_one_str(s_what, s_list, s_where, s_what_where):
    curs = bd_connect().cursor()
    curs.execute("SELECT " + s_what + " FROM " + s_list + " WHERE " + s_where + " = ?", (s_what_where,))
    selected = str(curs.fetchone()) # возможно вернуть стринг
    return selected

def bd_update(u_list, u_what, u_set, what_where, u_what_where):
    con = bd_connect()
    curs = con.cursor()
    curs.execute(f"UPDATE {u_list} SET {u_what} = {u_set} WHERE {what_where} = {u_what_where}")
    con.commit()


def auth_check(message):
    usr_id = bd_select_one_str("id", "users", "id", message.chat.id)
    if usr_id != 'None':
        #bot.send_message(message.chat.id, 'Вы уже зарегестрированы')
        return True
    else:
        return False


def ref_check(chat_id):
    ref_id = bd_select_one_str("urRefId", "users", "id", chat_id)
    if ref_id != None and ref_id != 0:
        return True
    else:
        return False

bot.polling(none_stop=True)
