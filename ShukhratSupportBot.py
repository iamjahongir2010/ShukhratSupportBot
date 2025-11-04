from flask import Flask, request
import telebot
from telebot import types

# ====== НАСТРОЙКИ ======
BOT_API = "7547480592:AAGI74gexvju7JooRE2PkfsHIOaE_mOfXKE"   # <- вставь сюда токен бота
ADMIN_ID = 306835182           # <- вставь сюда свой Telegram ID

bot = telebot.TeleBot(BOT_API)
app = Flask(__name__)

WEBHOOK_URL = "https://shukhratsupportbot.onrender.com/"

# ====== ПРАЙС-ЛИСТ ======
PRICES = {
    'online_psych': {
        'Таджикистан': '150 смн/час',
        'СНГ': '2500 руб/час',
        'Другое': '35$ США/час'
    },
    'business_online': {
        'Таджикистан': '300 смн/час',
        'СНГ': '3500 руб/час',
        'Другое': '70$ США/час'
    },
    'hypnosis_online': {
        'Таджикистан': '500 смн/1-1.5 часа',
        'СНГ': '5000 руб/час',
        'Другое': '100$ США/час'
    },
    'offline_individual': {'Таджикистан': '150 смн/час'},
    'offline_family': {'Таджикистан': '250 смн/час (2 человека)'},
    'offline_home': {'Таджикистан': '100 смн + 250 смн/час'},
    'offline_hypnosis_1': {'Таджикистан': '600 смн/час'},
    'offline_hypnosis_2': {'Таджикистан': '800 смн/1-2 часа'},
    'offline_hypnosis_3': {'Таджикистан': '1000 смн/2-3 часа'},
    'course_growth': {
        'Таджикистан': '2500 смн/весь курс (10 уроков)',
        'СНГ': '35000 руб/весь курс',
        'Другое': '450$ США/весь курс'
    },
    'business_offline': {'Таджикистан': '300 смн/час (до 3 человек)'},
    'group_training': {'Таджикистан': '50 смн с человека (мин. 1000 смн с группы)/1.5-2 часа'}
}

# ====== ХРАНИЛИЩЕ ДАННЫХ ======
user_data = {}

# ====== ДИНАМИЧЕСКИЕ ОПИСАНИЯ ======
def get_therapy_description(place, is_offline=False):
    if place == "Таджикистан" and is_offline:
        return (
            "<b>Офлайн-услуги (живая встреча):</b>\n\n"
            "• <b>Индивидуальный сеанс</b>\n"
            "• <b>Семейный сеанс (2 чел)</b>\n"
            "• <b>Сеанс на дому</b>\n"
            "• <b>Регрессивный гипноз</b> — 1, 1-2 или 2-3 часа\n"
            "• <b>Бизнес-консультация офлайн</b>\n"
            "• <b>Групповой тренинг</b>\n\n"
            "<i>Цены будут показаны после выбора услуги.</i>"
        )
    else:
        return (
            "<b>Онлайн-услуги:</b>\n\n"
            "• <b>Консультация (психология)</b>\n"
            "• <b>Бизнес-консультация</b>\n"
            "• <b>Регрессивный гипноз</b>\n"
            "• <b>Курс личностного роста</b>\n\n"
        )

# ====== СТАРТ ======
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("Да, готов"))
    markup.add(types.KeyboardButton("Нет, не готов"))

    bot.send_message(
        message.chat.id,
        "Привет! 👋\n\n"
        "Я — бот-помощник для записи на сеансы к психологу.\n"
        "Готовы начать?",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "Нет, не готов")
def not_ready(message):
    bot.send_message(message.chat.id, "Хорошо! Когда будете готовы — нажмите /start",
                     reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: message.text == "Да, готов")
def ask_place(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Таджикистан", "Страны СНГ", "Другое")
    bot.send_message(message.chat.id, "Откуда вы?", reply_markup=markup)

# ====== ВЫБОР РЕГИОНА ======
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

# ====== ВЫБОР ОНЛАЙН/ОФФЛАЙН ======
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

# ====== ВЫБОР ТЕРАПИИ (ОНЛАЙН) ======
def ask_therapy(chat_id, place):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Онлайн консультация (психология)",
               "Бизнес-консультация (онлайн)",
               "Регрессивный гипноз (онлайн)",
               "Курс личностного роста",
               "Я не знаю, что есть что")
    bot.send_message(chat_id, "Какую услугу вы хотите?", reply_markup=markup)

# ====== ВЫБОР ОФФЛАЙН ======
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

# ====== КНОПКА "Я НЕ ЗНАЮ" ======
@bot.message_handler(func=lambda m: "Я не знаю, что есть что" in m.text)
def send_descriptions(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        bot.send_message(message.chat.id, "Начните с /start")
        return

    place = user_data[user_id].get('place', 'Таджикистан')
    is_offline = (place == "Таджикистан" and user_data[user_id].get('mode') == "Офлайн (живая встреча)")
    bot.send_message(message.chat.id, get_therapy_description(place, is_offline), parse_mode='HTML')

    if is_offline:
        show_offline_therapies(message.chat.id)
    else:
        ask_therapy(message.chat.id, place)

# ====== ОБРАБОТКА ВЫБОРА УСЛУГИ ======
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
    text = message.text
    place = user_data[user_id]['place']

    therapy_key = None
    if "Онлайн консультация (психология)" in text: therapy_key = 'online_psych'
    elif "Бизнес-консультация (онлайн)" in text: therapy_key = 'business_online'
    elif "Регрессивный гипноз (онлайн)" in text: therapy_key = 'hypnosis_online'
    elif "Курс личностного роста" in text: therapy_key = 'course_growth'
    elif "индивидуальный" in text: therapy_key = 'offline_individual'
    elif "семейный" in text: therapy_key = 'offline_family'
    elif "сеанс на дому" in text: therapy_key = 'offline_home'
    elif "регрессивный гипноз (1 час)" in text: therapy_key = 'offline_hypnosis_1'
    elif "регрессивный гипноз (1-2 часа)" in text: therapy_key = 'offline_hypnosis_2'
    elif "регрессивный гипноз (2-3 часа)" in text: therapy_key = 'offline_hypnosis_3'
    elif "Бизнес-консультация офлайн" in text: therapy_key = 'business_offline'
    elif "Групповой тренинг" in text: therapy_key = 'group_training'

    price = PRICES.get(therapy_key, {}).get(place, "Цена недоступна")
    bot.send_message(message.chat.id, f"Вы выбрали: <b>{text}</b>\nЦена: <b>{price}</b>", parse_mode='HTML')

# ====== WEBHOOK ======
@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return "Bot is running", 200

# ====== УСТАНОВКА WEBHOOK ======
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ====== ЗАПУСК FLASK ======
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
