from xml.etree.ElementTree import tostring
from requests import patch, request
import telebot
import TOKEN
from telebot import types
import qrcode
import time
import sqlite3

bot = telebot.TeleBot(TOKEN.token)

connect = sqlite3.connect('db.sqlite')
cursor = connect.cursor()
cursor.execute(""" SELECT * FROM users """)


@ bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.InlineKeyboardButton("Да, мне есть 18")
    button2 = types.InlineKeyboardButton("Нет, мне нет 18")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, 'Добро пожаловать. Я преставляю магазин MintShop. У меня ты можешь получить свой qr код с которым поделишься с друзьями, получишь бонусы и сможешь потратить их в нашем магазине по адресу: г. Нижний новгород, б. Заречный 2, ТЦ Корона, 2 этаж. Покупки в нашем магазине можно осуществлять только после совершеннолетия. Тебе есть 18?', reply_markup=markup)


@ bot.message_handler(content_types=['text'])
def func(message):
    if(message.text == "Нет, мне нет 18"):
        bot.send_message(message.chat.id, 'Тогда заходи, когда вырастешь)')
    elif(message.text == "Да, мне есть 18"):
        text = 'Окей. Ты согласен на обработку персональных данных?'
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button1 = types.KeyboardButton("Согласен", request_contact=True)
        button2 = types.KeyboardButton("Не согласен")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(content_types=['contact'])
def contact(message):
    print(message.contact.phone_number)
    text = 'Хорошо, сейчас зарегестрирую тебя'
    bot.send_message(message.chat.id, text)
    # Код регистрации
    text = 'Регистрация прошла успешно) ВОт твой qr код, ИНФА ПРО QR КОД И ЕГО РАБОТУ'
    bot.send_message(message.chat.id, text +
                     '. Твой номер')
    id = '428'
    img = qrcode.make(message.contact.phone_number + id)

    path = 'qrs/' + id + '.png'
    img.save(path)
    photo = open(path, 'rb')
    bot.send_photo(message.chat.id, photo)


bot.polling(none_stop=True)
