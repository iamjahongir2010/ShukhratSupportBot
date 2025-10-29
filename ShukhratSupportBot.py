import os
import telebot
from telebot import types
from flask import Flask, request

# 🔐 Токен и админ
BOT_TOKEN = '7547480592:AAGI74gexvju7JooRE2PkfsHIOaE_mOfXKE'
ADMIN_ID = 7518403875

bot = telebot.TeleBot(BOT_TOKEN)

# Flask для webhook
app = Flask(__name__)
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/"

# Удаляем старый webhook и ставим новый
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# --------------------
# ВСЁ, что ниже — обычный код твоего бота
# price, handlers, функции и т.д.
# --------------------
price = {
    'Одиночный сеанс': {'Америка': '$30', 'Европа': '€25', 'Россия': '1800 ₽', 'Таджикистан': '150 смн', 'Другое': '$25'},
    'Семейный сеанс': {'Америка': '$45', 'Европа': '€40', 'Россия': '3000 ₽', 'Таджикистан': '250 смн', 'Другое': '$40'},
    'ПФР': {'Америка': '$55', 'Европа': '€50', 'Россия': '3600 ₽', 'Таджикистан': '300 смн', 'Другое': '$50'},
    'Регрессивный гипноз': {'Америка': '$45', 'Европа': '€40', 'Россия': '3000 ₽', 'Таджикистан': '250 смн', 'Другое': '$40'},
}

therapy = None
place = None

# ... все остальные хендлеры start, place_func, therapy_func, get_contact_question, contact_handler ...

if __name__ == "__main__":
    # Запуск Flask сервера на Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))