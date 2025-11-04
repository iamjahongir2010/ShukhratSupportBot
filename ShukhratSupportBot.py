import os
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Загружаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Клавиатура выбора терапии
def therapy_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Терапия 1", "Терапия 2", "Терапия 3")
    return kb

# Клавиатура для отправки контакта
def contact_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("Отправить контакт", request_contact=True))
    return kb

# Обработка стартового сообщения
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Выберите терапию:", reply_markup=therapy_keyboard())

# Обработка выбора терапии
@bot.message_handler(func=lambda m: m.text in ["Терапия 1", "Терапия 2", "Терапия 3"])
def therapy_chosen(message):
    therapy = message.text
    bot.send_message(
        message.chat.id,
        f"Вы выбрали {therapy}. Теперь отправьте ваш контакт.",
        reply_markup=contact_keyboard()
    )

# Обработка отправки контакта
@bot.message_handler(content_types=['contact'])
def contact_received(message):
    contact = message.contact.phone_number
    bot.send_message(
        message.chat.id,
        f"Спасибо! Мы получили ваш контакт: {contact}",
        reply_markup=ReplyKeyboardRemove()
    )

# Вебхук для Render
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

if __name__ == "__main__":
    # Для локального теста (не нужен на Render)
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("WEBHOOK_URL"))  # https://yourapp.onrender.com/
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
