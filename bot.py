import telebot
import TOKEN
from telebot import types

bot = telebot.TeleBot(TOKEN.token)


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.InlineKeyboardButton("Да, мне есть 18")
    button2 = types.InlineKeyboardButton("Нет, мне нет 18")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, 'Добро пожаловать. Я преставляю магазин MintShop. У меня ты можешь получить свой qr код с которым поделишься с друзьями, получишь бонусы и сможешь потратить их в нашем магазине по адресу: г. Нижний новгород, б. Заречный 2, ТЦ Корона, 2 этаж. Покупки в нашем магазине можно осуществлять только после совершеннолетия. Тебе есть 18?', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def func(message):
    if(message.text == "Нет, мне нет 18"):
        bot.send_message(message.chat.id, 'Тогда заходи, когда вырастешь)')


bot.polling(none_stop=True)
