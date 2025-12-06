from flask import Flask, request
import telebot
import os
from telebot import types

app = Flask(__name__)

BOT_TOKEN = "7547480592:AAGI74gexvju7JooRE2PkfsHIOaE_mOfXKE"
if not BOT_TOKEN:
    print("ОШИБКА: Установите BOT_TOKEN в переменных окружения!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 7518403875

PRICES = {
    'online_psych': {'Таджикистан': '150 смн/час', 'СНГ': '2500 руб/час', 'Другое': '35$ США/час'},
    'business_online': {'Таджикистан': '300 смн/час', 'СНГ': '3500 руб/час', 'Другое': '70$ США/час'},
    'hypnosis_online': {'Таджикистан': '500 смн/1–1.5 часа', 'СНГ': '5000 руб/1–1.5 часа', 'Другое': '100$ США'},
    'offline_individual': {'Таджикистан': '150 смн/час'},
    'offline_family': {'Таджикистан': '250 смн/час (2 человека)'},
    'offline_home': {'Таджикистан': '100 смн (выездной) + 250 смн/час'},
    'hypnosis_offline': {'Таджикистан': '600 смн/1–1.5 часа'},
    'course_growth': {'Таджикистан': '2500 смн/весь курс (10 уроков)', 'СНГ': '35000 руб/весь курс', 'Другое': '450$ США/весь курс'},
    'business_offline': {'Таджикистан': '300 смн/час (до 3 человек)'},
    'group_training': {'Таджикистан': '50 смн с человека (мин. 1000 смн с группы)/1.5–2 часа'}
}

user_data = {}

def ask_use_buttons_and_repeat(message, repeat_func, *args):
    bot.send_message(
        message.chat.id,
        "Пожалуйста, используйте кнопки ниже — это поможет выбрать нужный вариант 🙂",
        parse_mode='HTML'
    )
    repeat_func(message.chat.id, *args)

def get_therapy_description(place, is_offline=False):
    if place == "Таджикистан" and is_offline:
        return (
            "🧘‍♀️ <b>Офлайн-услуги:</b>\n\n"
            "• <b>Индивидуальный сеанс</b> — личная консультация с психологом в живом формате.\n\n"
            "• <b>Семейный сеанс (2 чел.)</b> — совместная работа для улучшения понимания и гармонии в семье.\n\n"
            "• <b>Сеанс на дому</b> — выезд специалиста к вам, если комфортнее консультироваться дома.\n\n"
            "• <b>Регрессивный гипноз (офлайн)</b> — глубокая работа с подсознанием в безопасной атмосфере.\n\n"
            "• <b>Бизнес-консультация офлайн</b> — очная встреча по вопросам управления, команды и роста.\n\n"
            "• <b>Групповой тренинг</b> — развитие уверенности, общения и лидерства в группе.\n\n"
            "Выберите услугу ниже 👇"
        )
    else:
        return (
            "🌐 <b>Онлайн-услуги:</b>\n\n"
            "• <b>Онлайн консультация (психология)</b> — личная работа с психологом для понимания эмоций, уверенности и гармонии.\n\n"
            "• <b>Бизнес-консультация (онлайн)</b> — помощь в развитии бизнеса, карьеры и управлении стрессом.\n\n"
            "• <b>Регрессивный гипноз (онлайн)</b> — мягкое погружение в подсознание, чтобы отпустить старые установки и создать новые.\n\n"
            "• <b>Курс личностного роста</b> — 10 онлайн-уроков с практиками уверенности и внутреннего баланса.\n\n"
            "Выберите подходящую услугу ниже 👇"
        )

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да, готов", "Нет, не готов")

    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\n"
        "Рад вас видеть. Я — бот, который поможет записаться к психологу, подобрать подходящую терапию и узнать стоимость.\n\n"
        "💬 Все консультации проходят конфиденциально, в спокойной и поддерживающей атмосфере.\n\n"
        "<b>Готовы начать?</b>",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "Нет, не готов")
def not_ready(message):
    bot.send_message(message.chat.id, "Хорошо! Нажмите /start, когда будете готовы.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "Да, готов")
def ask_place(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Таджикистан", "Страны СНГ", "Другое")
    bot.send_message(message.chat.id, "🌍 Уточните, пожалуйста, где вы находитесь — это нужно, чтобы рассчитать стоимость консультации.", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_any(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return

    state = user_data[user_id]

    if 'place' not in state:
        if message.text in ["Таджикистан", "Страны СНГ", "Другое"]:
            state['place'] = message.text
            if message.text == "Таджикистан":
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add("Онлайн", "Офлайн (живая встреча)")
                bot.send_message(message.chat.id, "💡 Какой формат вам удобнее — онлайн встреча или живая консультация (офлайн)?", reply_markup=markup)
            else:
                ask_therapy(message.chat.id, message.text)
        else:
            ask_use_buttons_and_repeat(message, ask_place)
        return

    if state['place'] == "Таджикистан" and 'mode' not in state:
        if message.text in ["Онлайн", "Офлайн (живая встреча)"]:
            state['mode'] = message.text
            if message.text == "Онлайн":
                ask_therapy(message.chat.id, state['place'])
            else:
                show_offline_therapies(message.chat.id)
        else:
            ask_use_buttons_and_repeat(message, lambda cid: (
                types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                .add("Онлайн", "Офлайн (живая встреча)"),
                bot.send_message(cid, "💡 Какой формат вам удобнее — онлайн встреча или живая консультация (офлайн)?", reply_markup=_)
            )[1], message.chat.id)
        return

    if 'therapy' not in state:
        if "Я не знаю, что есть что" in message.text:
            send_descriptions(message)
            return

        expected = [
            "Онлайн консультация (психология)", "Бизнес-консультация (онлайн)",
            "Регрессивный гипноз (онлайн)", "Курс личностного роста",
            "Офлайн: индивидуальный сеанс", "Офлайн: семейный сеанс (2 чел)",
            "Офлайн: сеанс на дому", "Регрессивный гипноз (офлайн)",
            "Бизнес-консультация офлайн (до 3 чел)", "Групповой тренинг"
        ]
        if any(opt in message.text for opt in expected):
            handle_therapy(message)
        else:
            if state.get('mode') == "Офлайн (живая встреча)":
                ask_use_buttons_and_repeat(message, show_offline_therapies, message.chat.id)
            else:
                ask_use_buttons_and_repeat(message, ask_therapy, message.chat.id, state['place'])
        return

def ask_therapy(chat_id, place):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Онлайн консультация (психология)")
    markup.add("Бизнес-консультация (онлайн)")
    markup.add("Регрессивный гипноз (онлайн)")
    markup.add("Курс личностного роста")
    markup.add("Я не знаю, что есть что")
    bot.send_message(chat_id, "💬 Какую услугу вы хотите выбрать?\nВыберите вариант из списка ниже, чтобы узнать подробности и стоимость.", reply_markup=markup)

def show_offline_therapies(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Офлайн: индивидуальный сеанс")
    markup.add("Офлайн: семейный сеанс (2 чел)")
    markup.add("Офлайн: сеанс на дому")
    markup.add("Регрессивный гипноз (офлайн)")
    markup.add("Бизнес-консультация офлайн (до 3 чел)")
    markup.add("Групповой тренинг")
    markup.add("Я не знаю, что есть что")
    bot.send_message(chat_id, "Выберите офлайн-услугу:", reply_markup=markup)

@bot.message_handler(func=lambda m: "Я не знаю, что есть что" in m.text)
def send_descriptions(message):
    user_id = message.from_user.id
    if user_id not in user_data or 'place' not in user_data[user_id]:
        bot.send_message(message.chat.id, "Начните с /start")
        return

    place = user_data[user_id]['place']
    is_offline = (place == "Таджикистан" and user_data[user_id].get('mode') == "Офлайн (живая встреча)")

    desc = get_therapy_description(place, is_offline)
    bot.send_message(message.chat.id, desc, parse_mode='HTML')

    if is_offline:
        show_offline_therapies(message.chat.id)
    else:
        ask_therapy(message.chat.id, place)

def handle_therapy(message):
    user_id = message.from_user.id
    therapy_text = message.text
    place = user_data[user_id]['place']

    therapy_key = None
    price = None

    if "Онлайн консультация (психология)" in therapy_text:
        therapy_key = 'online_psych'
        price = PRICES[therapy_key].get(place, PRICES[therapy_key].get('Таджикистан'))
    elif "Бизнес-консультация (онлайн)" in therapy_text:
        therapy_key = 'business_online'
        price = PRICES[therapy_key].get(place, PRICES[therapy_key].get('Таджикистан'))
    elif "Регрессивный гипноз (онлайн)" in therapy_text:
        therapy_key = 'hypnosis_online'
        price = PRICES[therapy_key].get(place, PRICES[therapy_key].get('Таджикистан'))
    elif "Курс личностного роста" in therapy_text:
        therapy_key = 'course_growth'
        price = PRICES[therapy_key].get(place, PRICES[therapy_key].get('Таджикистан'))
    elif "индивидуальный сеанс" in therapy_text:
        therapy_key = 'offline_individual'
        price = PRICES[therapy_key]['Таджикистан']
    elif "семейный сеанс" in therapy_text:
        therapy_key = 'offline_family'
        price = PRICES[therapy_key]['Таджикистан']
    elif "сеанс на дому" in therapy_text:
        therapy_key = 'offline_home'
        price = PRICES[therapy_key]['Таджикистан']
    elif "Регрессивный гипноз (офлайн)" in therapy_text:
        therapy_key = 'hypnosis_offline'
        price = PRICES[therapy_key]['Таджикистан']
    elif "Бизнес-консультация офлайн" in therapy_text:
        therapy_key = 'business_offline'
        price = PRICES[therapy_key]['Таджикистан']
    elif "Групповой тренинг" in therapy_text:
        therapy_key = 'group_training'
        price = PRICES[therapy_key]['Таджикистан']

    if not therapy_key:
        return

    user_data[user_id]['therapy'] = therapy_text
    user_data[user_id]['price'] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("Отправить контакт", request_contact=True))

    bot.send_message(
        message.chat.id,
        f"💬 <b>Ваша заявка:</b>\n\n"
        f"🌍 Регион: <b>{place}</b>\n"
        f"🧠 Услуга: <b>{therapy_text}</b>\n"
        f"💰 Стоимость: <b>{price}</b>\n\n"
        f"📱 Отправьте свой контакт, чтобы специалист мог с вами связаться.",
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
    user_link = f"<a href='tg://user?id={user_id}'>Перейти к пользователю</a>"

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
        f"<b>Ссылка:</b> {user_link}\n"
        f"<b>ID:</b> <code>{user_id}</code>"
    )
    bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML', disable_web_page_preview=True)

    bot.send_message(
        message.chat.id,
        "💫 Спасибо!\n\n"
        "Ваша заявка отправлена. Психолог свяжется с вами в ближайшее время, чтобы уточнить удобное время и формат.\n\n"
        "Вы сделали шаг к переменам — всё начинается с этого шага 🌱",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )

    del user_data[user_id]

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

def setup_webhook():
    hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
    if hostname:
        url = f"https://{hostname}{WEBHOOK_PATH}"
        bot.remove_webhook()
        bot.set_webhook(url=url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    setup_webhook()
    app.run(host='0.0.0.0', port=port)