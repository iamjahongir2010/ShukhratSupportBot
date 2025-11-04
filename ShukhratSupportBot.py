# main.py — Telegram-бот для Render.com (один файл)
from flask import Flask, request
import telebot
import os
import threading
from telebot import types

# === Flask App ===
app = Flask(__name__)

# === ТОКЕН ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (Render) ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ОШИБКА: Установите BOT_TOKEN в переменных окружения на Render!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# === КОНСТАНТЫ ===
ADMIN_ID = 7518403875

# === ПРАЙС-ЛИСТ ===
PRICES = {
    'online_psych': {'Таджикистан': '150 смн/час', 'СНГ': '2500 руб/час', 'Другое': '35$ США/час'},
    'business_online': {'Таджикистан': '300 смн/час', 'СНГ': '3500 руб/час', 'Другое': '70$ США/час'},
    'hypnosis_online': {'Таджикистан': '500 смн/1-1.5 часа', 'СНГ': '5000 руб/час', 'Другое': '100$ США/час'},
    'offline_individual': {'Таджикистан': '150 смн/час'},
    'offline_family': {'Таджикистан': '250 смн/час (2 человека)'},
    'offline_home': {'Таджикистан': '100 смн + 250 смн/час'},
    'offline_hypnosis_1': {'Таджикистан': '600 смн/час'},
    'offline_hypnosis_2': {'Таджикистан': '800 смн/1-2 часа'},
    'offline_hypnosis_3': {'Таджикистан': '1000 смн/2-3 часа'},
    'course_growth': {'Таджикистан': '2500 смн/весь курс (10 уроков)', 'СНГ': '35000 руб/весь курс', 'Другое': '450$ США/весь курс'},
    'business_offline': {'Таджикистан': '300 смн/час (до 3 человек)'},
    'group_training': {'Таджикистан': '50 смн с человека (мин. 1000 смн с группы)/1.5-2 часа'}
}

# === ХРАНИЛИЩЕ ДАННЫХ ===
user_data = {}

# === ОПИСАНИЯ ===
def get_therapy_description(place, is_offline=False):
    if place == "Таджикистан" and is_offline:
        return (
            "<b>Офлайн-услуги (живая встреча):</b>\n\n"
            "• <b>Индивидуальный сеанс</b> — личная консультация\n"
            "• <b>Семейный сеанс (2 чел)</b> — для пары или семьи\n"
            "• <b>Сеанс на дому</b> — выезд к вам\n"
            "• <b>Регрессивный гипноз</b> — 1, 1-2 или 2-3 часа\n"
            "• <b>Бизнес-консультация офлайн</b> — до 3 человек\n"
            "• <b>Групповой тренинг</b> — от 3 человек, 1.5–2 часа\n\n"
            "<i>Цены будут показаны после выбора услуги.</i>"
        )
    else:
        return (
            "<b>Онлайн-услуги:</b>\n\n"
            "• <b>Консультация (психология)</b> — личная помощь, поддержка\n"
            "• <b>Бизнес-консультация</b> — мотивация, стратегия, решения\n"
            "• <b>Регрессивный гипноз</b> — работа с подсознанием, новые установки\n"
            "• <b>Курс личностного роста</b> — 10 уроков для развития\n\n"
            "<i>Цены будут показаны после выбора услуги.</i>"
        )

# === ХЕНДЛЕРЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да, готов", "Нет, не готов")

    bot.send_message(
        message.chat.id,
        "Привет!\n\n"
        "Я — бот-помощник для записи на сеансы к психологу.\n"
        "Я помогу вам быстро выбрать услугу и оставить заявку.\n\n"
        "Для записи мне понадобится немного информации.\n"
        "<b>Готовы начать?</b>",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "Нет, не готов")
def not_ready(message):
    bot.send_message(message.chat.id, "Хорошо! Когда будете готовы — нажмите /start",
                     reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "Да, готов")
def ask_place(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Таджикистан", "Страны СНГ", "Другое")
    bot.send_message(message.chat.id, "Откуда вы?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Таджикистан", "Страны СНГ", "Другое"])
def handle_place(message):
    user_id = message.from_user.id
    place = message.text
    user_data[user_id]['place'] = place

    if place == "Таджикистан":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Онлайн", "Офлайн (живая встреча)")
        bot.send_message(message.chat.id, "Онлайн или офлайн?", reply_markup=markup)
    else:
        ask_therapy(message.chat.id, place)

@bot.message_handler(func=lambda m: m.text in ["Онлайн", "Офлайн (живая встреча)"])
def handle_mode(message):
    user_id = message.from_user.id
    mode = message.text
    user_data[user_id]['mode'] = mode
    place = user_data[user_id]['place']

    if mode == "Онлайн":
        ask_therapy(message.chat.id, place)
    else:
        show_offline_therapies(message.chat.id)

def ask_therapy(chat_id, place):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Онлайн консультация (психология)")
    markup.add("Бизнес-консультация (онлайн)")
    markup.add("Регрессивный гипноз (онлайн)")
    markup.add("Курс личностного роста")
    markup.add("Я не знаю, что есть что")
    bot.send_message(chat_id, "Какую услугу вы хотите?", reply_markup=markup)

def show_offline_therapies(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    options = [
        "Офлайн: индивидуальный сеанс",
        "Офлайн: семейный сеанс (2 чел)",
        "Офлайн: сеанс на дому",
        "Офлайн: регрессивный гипноз (1 час)",
        "Офлайн: регрессивный гипноз (1-2 часа)",
        "Офлайн: регрессивный гипноз (2-3 часа)",
        "Бизнес-консультация офлайн (до 3 чел)",
        "Групповой тренинг",
        "Я не знаю, что есть что"
    ]
    for opt in options:
        markup.add(opt)
    bot.send_message(chat_id, "Выберите офлайн-услугу:", reply_markup=markup)

@bot.message_handler(func=lambda m: "Я не знаю, что есть что" in m.text)
def send_descriptions(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        bot.send_message(message.chat.id, "Начните с /start")
        return

    place = user_data[user_id].get('place', 'Таджикистан')
    is_offline = (place == "Таджикистан" and user_data[user_id].get('mode') == "Офлайн (живая встреча)")

    desc = get_therapy_description(place, is_offline)
    bot.send_message(message.chat.id, desc, parse_mode='HTML')

    if is_offline:
        show_offline_therapies(message.chat.id)
    else:
        ask_therapy(message.chat.id, place)

@bot.message_handler(func=lambda m: any(
    x in m.text for x in [
        "Онлайн консультация", "Бизнес-консультация (онлайн)", "Регрессивный гипноз (онлайн)",
        "Курс личностного роста", "Офлайн: индивидуальный", "Офлайн: семейный",
        "Офлайн: сеанс на дому", "Офлайн: регрессивный гипноз", "Бизнес-консультация офлайн",
        "Групповой тренинг"
    ]
))
def handle_therapy(message):
    user_id = message.from_user.id
    therapy_text = message.text
    place = user_data[user_id]['place']

    therapy_key = None
    if "Онлайн консультация (психология)" in therapy_text:
        therapy_key = 'online_psych'
    elif "Бизнес-консультация (онлайн)" in therapy_text:
        therapy_key = 'business_online'
    elif "Регрессивный гипноз (онлайн)" in therapy_text:
        therapy_key = 'hypnosis_online'
    elif "Курс личностного роста" in therapy_text:
        therapy_key = 'course_growth'
    elif "индивидуальный сеанс" in therapy_text:
        therapy_key = 'offline_individual'
    elif "семейный сеанс" in therapy_text:
        therapy_key = 'offline_family'
    elif "сеанс на дому" in therapy_text:
        therapy_key = 'offline_home'
    elif "гипноз (1 час)" in therapy_text:
        therapy_key = 'offline_hypnosis_1'
    elif "гипноз (1-2 часа)" in therapy_text:
        therapy_key = 'offline_hypnosis_2'
    elif "гипноз (2-3 часа)" in therapy_text:
        therapy_key = 'offline_hypnosis_3'
    elif "Бизнес-консультация офлайн" in therapy_text:
        therapy_key = 'business_offline'
    elif "Групповой тренинг" in therapy_text:
        therapy_key = 'group_training'

    if not therapy_key or therapy_key not in PRICES:
        bot.send_message(message.chat.id, "Ошибка. Выберите услугу из списка.")
        return

    price = PRICES[therapy_key].get(place, PRICES[therapy_key].get('Таджикистан', '—'))
    user_data[user_id]['therapy'] = therapy_text
    user_data[user_id]['price'] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("Отправить контакт", request_contact=True))

    bot.send_message(
        message.chat.id,
        f"<b>Ваша заявка:</b>\n\n"
        f"Вы из: <b>{place}</b>\n"
        f"Услуга: <b>{therapy_text}</b>\n"
        f"Цена: <b>{price}</b>\n\n"
        f"Если всё верно — отправьте контакт:",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if user_id not in user_data or 'therapy' not in user_data[user_id]:
        bot.send_message(message.chat.id, "Ошибка. Начните с /start")
        return

    contact = message.contact
    name = contact.first_name + (f" {contact.last_name}" if contact.last_name else "")
    username = f"@{message.from_user.username}" if message.from_user.username else "—"
    phone = contact.phone_number

    data = user_data[user_id]
    place = data['place']
    therapy = data['therapy']
    price = data['price']

    admin_msg = (
        f"НОВАЯ ЗАЯВКА\n\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Телефон:</b> {phone}\n"
        f"<b>Username:</b> {username}\n"
        f"<b>Место:</b> {place}\n"
        f"Услуга: <b>{therapy}</b>\n"
        f"<b>Цена:</b> {price}\n"
        f"<b>ID:</b> <code>{user_id}</code>"
    )
    bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')

    bot.send_message(
        message.chat.id,
        "Всё готово!\n\n"
        "Скоро с вами свяжутся для уточнения времени и деталей.",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )

    if user_id in user_data:
        del user_data[user_id]

# === WEBHOOK ===
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN.split(':')[0]}"

@app.route('/')
def index():
    return f"<h1>Бот работает!</h1><p>Webhook: <code>{WEBHOOK_PATH}</code></p>"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    url = f"https://{request.host}{WEBHOOK_PATH}"
    bot.remove_webhook()
    success = bot.set_webhook(url=url)
    return f"Webhook {'установлен' if success else 'ошибка'}: {url}"

# === АВТО-УСТАНОВКА WEBHOOK ПРИ СТАРТЕ ===
def setup_webhook():
    import time
    time.sleep(2)  # даем время на запуск
    hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
    if not hostname:
        return
    url = f"https://{hostname}{WEBHOOK_PATH}"
    bot.remove_webhook()
    bot.set_webhook(url=url)

# === ЗАПУСК ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=setup_webhook, daemon=True).start()
    app.run(host='0.0.0.0', port=port)