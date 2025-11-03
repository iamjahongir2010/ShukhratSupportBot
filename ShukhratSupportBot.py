import telebot
from telebot import types
from flask import Flask, request
# === НАСТРОЙКА ===
BOT_TOKEN = "7547480592:AAGI74gexvju7JooRE2PkfsHIOaE_mOfXKE"
ADMIN_ID = 306835182
WEBHOOK_URL = "https://shukhratsupportbot.onrender.com"  # 👈 замени на свой URL

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

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
    'course_growth': {'Таджикистан': '2500 смн/курс', 'СНГ': '35000 руб/курс', 'Другое': '450$ США/курс'},
    'business_offline': {'Таджикистан': '300 смн/час (до 3 человек)'},
    'group_training': {'Таджикистан': '50 смн/чел (мин. 1000 смн/группа)'}
}

# === ХРАНЕНИЕ ===
user_data = {}

# === ОПИСАНИЯ ===
def get_therapy_description(place, is_offline=False):
    if place == "Таджикистан" and is_offline:
        return (
            "📍 <b>Офлайн-услуги:</b>\n\n"
            "• Индивидуальный сеанс\n"
            "• Семейный сеанс\n"
            "• Сеанс на дому\n"
            "• Регрессивный гипноз (1–3 часа)\n"
            "• Бизнес-консультация офлайн\n"
            "• Групповой тренинг\n\n"
            "<i>Цены появятся после выбора.</i>"
        )
    else:
        return (
            "🌐 <b>Онлайн-услуги:</b>\n\n"
            "• Онлайн консультация\n"
            "• Бизнес-консультация (онлайн)\n"
            "• Регрессивный гипноз (онлайн)\n"
            "• Курс личностного роста\n\n"
            "<i>Цены появятся после выбора.</i>"
        )

# === /START ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Да, готов", "Нет, не готов")
    bot.send_message(message.chat.id,
                     "Привет! 👋 Я помогу записаться на сеанс к психологу.\n\nГотовы начать?",
                     reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Нет, не готов")
def no_start(msg):
    bot.send_message(msg.chat.id, "Хорошо! Напишите /start, когда будете готовы.")

@bot.message_handler(func=lambda msg: msg.text == "Да, готов")
def ask_country(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Таджикистан", "Страны СНГ", "Другое")
    bot.send_message(msg.chat.id, "Откуда вы?", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["Таджикистан", "Страны СНГ", "Другое"])
def handle_country(msg):
    user_id = msg.from_user.id
    user_data[user_id] = {'place': msg.text}

    if msg.text == "Таджикистан":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Онлайн", "Офлайн (живая встреча)")
        bot.send_message(msg.chat.id, "Онлайн или офлайн?", reply_markup=markup)
    else:
        ask_service(msg.chat.id, msg.text)

@bot.message_handler(func=lambda msg: msg.text in ["Онлайн", "Офлайн (живая встреча)"])
def mode_select(msg):
    uid = msg.from_user.id
    user_data[uid]['mode'] = msg.text
    place = user_data[uid]['place']
    if msg.text == "Онлайн":
        ask_service(msg.chat.id, place)
    else:
        ask_offline_service(msg.chat.id)

def ask_service(chat_id, place):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "Онлайн консультация (психология)",
        "Бизнес-консультация (онлайн)",
        "Регрессивный гипноз (онлайн)",
        "Курс личностного роста",
        "Я не знаю, что есть что"
    )
    bot.send_message(chat_id, "Выберите услугу:", reply_markup=markup)

def ask_offline_service(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    options = [
        "Офлайн: индивидуальный сеанс",
        "Офлайн: семейный сеанс",
        "Офлайн: сеанс на дому",
        "Офлайн: регрессивный гипноз (1 час)",
        "Офлайн: регрессивный гипноз (1-2 часа)",
        "Офлайн: регрессивный гипноз (2-3 часа)",
        "Бизнес-консультация офлайн",
        "Групповой тренинг",
        "Я не знаю, что есть что"
    ]
    for o in options:
        markup.add(o)
    bot.send_message(chat_id, "Выберите офлайн-услугу:", reply_markup=markup)

@bot.message_handler(func=lambda msg: "Я не знаю" in msg.text)
def send_desc(msg):
    uid = msg.from_user.id
    place = user_data[uid].get('place', 'Таджикистан')
    is_offline = place == "Таджикистан" and user_data[uid].get('mode') == "Офлайн (живая встреча)"
    bot.send_message(msg.chat.id, get_therapy_description(place, is_offline), parse_mode='HTML')
    if is_offline:
        ask_offline_service(msg.chat.id)
    else:
        ask_service(msg.chat.id, place)

@bot.message_handler(func=lambda msg: any(x in msg.text for x in [
    "Онлайн консультация", "Бизнес-консультация", "Регрессивный гипноз", "Курс личностного роста",
    "Офлайн:", "Групповой тренинг"
]))
def handle_service(msg):
    uid = msg.from_user.id
    user_data[uid]['therapy'] = msg.text
    place = user_data[uid]['place']

    mapping = {
        "Онлайн консультация": 'online_psych',
        "Бизнес-консультация (онлайн)": 'business_online',
        "Регрессивный гипноз (онлайн)": 'hypnosis_online',
        "Курс личностного роста": 'course_growth',
        "индивидуальный": 'offline_individual',
        "семейный": 'offline_family',
        "на дому": 'offline_home',
        "1 час": 'offline_hypnosis_1',
        "1-2 часа": 'offline_hypnosis_2',
        "2-3 часа": 'offline_hypnosis_3',
        "Бизнес-консультация офлайн": 'business_offline',
        "Групповой тренинг": 'group_training'
    }

    key = next((v for k, v in mapping.items() if k in msg.text), None)
    if not key:
        bot.send_message(msg.chat.id, "Ошибка. Выберите услугу из списка.")
        return

    price = PRICES[key].get(place, PRICES[key].get('Таджикистан', '—'))
    user_data[uid]['price'] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Отправить контакт", request_contact=True))
    bot.send_message(msg.chat.id,
                     f"📋 <b>Ваша заявка:</b>\n\n"
                     f"🌍 Место: <b>{place}</b>\n"
                     f"🧠 Услуга: <b>{msg.text}</b>\n"
                     f"💰 Цена: <b>{price}</b>\n\n"
                     "Отправьте контакт:",
                     parse_mode='HTML', reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(msg):
    uid = msg.from_user.id
    data = user_data.get(uid)
    if not data:
        bot.send_message(msg.chat.id, "Начните с /start")
        return

    name = msg.contact.first_name
    phone = msg.contact.phone_number
    username = f"@{msg.from_user.username}" if msg.from_user.username else "—"

    text = (f"📩 <b>Новая заявка</b>\n\n"
            f"👤 Имя: {name}\n"
            f"📱 Телефон: {phone}\n"
            f"🆔 Username: {username}\n"
            f"🌍 Место: {data['place']}\n"
            f"🧠 Услуга: {data['therapy']}\n"
            f"💰 Цена: {data['price']}")

    bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    bot.send_message(msg.chat.id, "✅ Заявка отправлена! С вами скоро свяжутся.",
                     reply_markup=types.ReplyKeyboardRemove())

# === FLASK ДЛЯ ВЕБХУКА ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Unsupported Media Type', 415

@app.route('/')
def index():
    return 'Бот работает ✅'

# === ЗАПУСК ===
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
