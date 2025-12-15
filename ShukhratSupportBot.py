#"7547480592:AAGI74gexvju7JooRE2PkfsHIOaE_mOfXKE"
#306835182 - папа
#7518403875 - я
# main.py — с обновлёнными текстами (эмодзи + живой стиль)
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

ADMIN_ID = 306835182

# === ПРАЙС ===
PRICES = {
    'online_psych': {
        'Таджикистан': '150 сомони/час',
        'СНГ': '2500 руб/час',
        'Другое': '35$/час'
    },
    'business_online': {
        'Таджикистан': '350 сомони (1–3 человека)',
        'СНГ': '3500 руб (1–3 человека)',
        'Другое': '70$ (1–3 человека)'
    },
    'hypnosis_online': {
        'Таджикистан': '500 сомони/час',
        'СНГ': '5000 руб/час',
        'Другое': '100$/час'
    },
    'course_growth': {
        'Таджикистан': '2500 сомони/весь курс (10 уроков-презентаций)',
        'СНГ': '35000 руб/весь курс (10 уроков-презентаций)',
        'Другое': '450$/весь курс (10 уроков-презентаций)'
    },
    'offline_individual': {'Таджикистан': '150 сомони/час'},
    'offline_family': {'Таджикистан': '250 сомони/час (2+ человека)'},
    'offline_home': {'Таджикистан': '100 сомони + 250 сомони/час'},
    'hypnosis_offline': {'Таджикистан': '600 сомони/час | 800 сомони/1-2 ч | 1000 сомони/2-3 ч'},
    'business_offline': {'Таджикистан': '350 сомони/час (до 3 человек)'},
    'group_training': {'Таджикистан': '50 сомони с человека (мин. 1000 сомони с группы)/1.5-2 часа'}
}

user_data = {}


def ask_use_buttons_and_repeat(message, repeat_func, *args):
    bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки ниже, чтобы я не ошибся 😊")
    repeat_func(message.chat.id, *args)


def get_therapy_description(place, is_offline=False):
    # Возвращает подробное, "по полочкам" описание услуг (HTML)
    if place == "Таджикистан" and is_offline:
        return (
            "<b>🏠 Офлайн-услуги — что и для кого:</b>\n\n"
            "• <b>Индивидуальный сеанс</b> — работа с тревогой, стрессом, депрессией, "
            "потерей мотивации, прокрастинацией; помогает вернуть ясность, выработать план действий и "
            "постепенно двигаться к личным целям.\n\n"
            "• <b>Семейный сеанс (2 чел)</b> — конфликты между супругами, проблемы в общении, "
            "разногласия по воспитанию детей; фокус на восстановлении диалога, распределении ролей и "
            "поиске компромиссов.\n\n"
            "• <b>Сеанс на дому</b> — удобный формат для тех, кому сложно добираться; те же задачи, "
            "но в комфортной для вас обстановке (подходит при высокой тревоге или ограниченной мобильности).\n\n"
            "• <b>Регрессивный гипноз (офлайн)</b> — углублённая работа с прошлыми травмами и бессознательными стереотипами; "
            "подойдёт при длительных эмоциональных затруднениях или когда традиционные беседы не дают результата. "
            "Сессии могут быть 1, 1–2 или 2–3 часа в зависимости от запроса.\n\n"
            "• <b>Бизнес-консультация офлайн (до 3 чел)</b> — разбор командных коммуникаций, стресса у руководителя, "
            "организационных дублирований; даём практические шаги по улучшению процессов и взаимодействий.\n\n"
            "• <b>Групповой тренинг</b> — развиваем навыки (коммуникация, управление стрессом, командная работа); "
            "эффект от группы сильнее за счёт обмена опытом и практики в реальном времени.\n\n"
            "<i>После выбора покажу точные цены и длительность.</i>"
        )
    else:
        return (
            "<b>💻 Онлайн-услуги — что и для кого:</b>\n\n"
            "• <b>Онлайн консультация (психология)</b> — краткие и глубинные сессии для работы с тревогой, "
            "стрессом, самооценкой, жизненными кризисами и принятием решений; удобно, если нет возможности прийти лично.\n\n"
            "• <b>Бизнес-консультация (онлайн)</b> — помощи руководителям и предпринимателям: управление выгоранием, "
            "навыки делегирования, решение конфликтов в команде и выстраивание структуры работы.\n\n"
            "• <b>Регрессивный гипноз (онлайн)</b> — мягкая работа с подсознанием (1 час); подходит для проработки "
            "вредных паттернов, блоков и внутренних установок. Эффект зависит от запроса и индивидуальной чувствительности.\n\n"
            "• <b>Курс личностного роста (10 уроков)</b> — структурированный курс: постановка целей, управление эмоциями, "
            "продуктивные привычки и навыки общения. Подойдёт тем, кто хочет последовательно прокачивать себя.\n\n"
            "<i>После выбора покажу точные цены, формат и расписание.</i>"
        )


# === СТАРТ ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да, готов", "Нет, не готов")

    bot.send_message(
        message.chat.id,
        "👋 Привет! \n\n"
        "🙂 Я — помощник, который поможет быстро и удобно записаться на сеанс к психологу.\n\n"
        "<b>📝 Готовы начать?</b> ",
        parse_mode='HTML',
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: m.text == "Нет, не готов")
def not_ready(message):
    bot.send_message(
        message.chat.id,
        "👌 Без проблем! Когда будете готовы — просто нажмите /start.",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(func=lambda m: m.text == "Да, готов")
def ask_place(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Таджикистан", "Страны СНГ", "Другое")

    bot.send_message(message.chat.id, "✅ Отлично! \n🌍 Выберите, пожалуйста, откуда вы:", reply_markup=markup)


# === ГЛАВНЫЙ ХЕНДЛЕР ===
@bot.message_handler(func=lambda m: True)
def handle_any(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return

    state = user_data[user_id]

    # 1. Место
    if 'place' not in state:
        if message.text in ["Таджикистан", "Страны СНГ", "Другое"]:
            state['place'] = "СНГ" if message.text == "Страны СНГ" else message.text

            if message.text == "Таджикистан":
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add("Онлайн", "Офлайн (живая встреча)")
                bot.send_message(
                    message.chat.id,
                    "Какой формат вам удобнее? ⚡\n"
                    "Онлайн — удобно из любой точки мира.\n"
                    "Офлайн — живая, тёплая атмосфера.",
                    reply_markup=markup
                )
            else:
                ask_therapy(message.chat.id, state['place'])
        else:
            ask_use_buttons_and_repeat(message, ask_place)
        return

    # 2. Режим (Таджикистан)
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
                bot.send_message(cid, "Онлайн или офлайн?", reply_markup=_)
            )[1], message.chat.id)
        return

    # 3. Терапия
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

    bot.send_message(chat_id, "🎯 Выберите услугу, которая вам подходит:", reply_markup=markup)


def show_offline_therapies(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Офлайн: индивидуальный сеанс")
    markup.add("Офлайн: семейный сеанс (2 чел)")
    markup.add("Офлайн: сеанс на дому")
    markup.add("Регрессивный гипноз (офлайн)")
    markup.add("Бизнес-консультация офлайн (до 3 чел)")
    markup.add("Групповой тренинг")
    markup.add("Я не знаю, что есть что")

    bot.send_message(chat_id, "🏡 Выберите офлайн-услугу :", reply_markup=markup)


@bot.message_handler(func=lambda m: "Я не знаю, что есть что" in m.text)
def send_descriptions(message):
    user_id = message.from_user.id
    if user_id not in user_data or 'place' not in user_data[user_id]:
        bot.send_message(message.chat.id, "Начните с /start")
        return

    place = user_data[user_id]['place']
    is_offline = (place == "Таджикистан" and user_data[user_id].get('mode') == "Офлайн (живая встреча)")

    bot.send_message(message.chat.id, get_therapy_description(place, is_offline), parse_mode='HTML')

    if is_offline:
        show_offline_therapies(message.chat.id)
    else:
        ask_therapy(message.chat.id, place)


def handle_therapy(message):
    user_id = message.from_user.id
    therapy_text = message.text
    place = user_data[user_id]['place']

    price = "Цена не указана"

    if "Онлайн консультация (психология)" in therapy_text:
        price = PRICES['online_psych'].get(place, "—")
    elif "Бизнес-консультация (онлайн)" in therapy_text:
        price = PRICES['business_online'].get(place, "—")
    elif "Регрессивный гипноз (онлайн)" in therapy_text:
        price = PRICES['hypnosis_online'].get(place, "—")
    elif "Курс личностного роста" in therapy_text:
        price = PRICES['course_growth'].get(place, "—")
    elif "индивидуальный сеанс" in therapy_text:
        price = PRICES['offline_individual']['Таджикистан']
    elif "семейный сеанс" in therapy_text:
        price = PRICES['offline_family']['Таджикистан']
    elif "сеанс на дому" in therapy_text:
        price = PRICES['offline_home']['Таджикистан']
    elif "Регрессивный гипноз (офлайн)" in therapy_text:
        price = PRICES['hypnosis_offline']['Таджикистан']
    elif "Бизнес-консультация офлайн" in therapy_text:
        price = PRICES['business_offline']['Таджикистан']
    elif "Групповой тренинг" in therapy_text:
        price = PRICES['group_training']['Таджикистан']

    user_data[user_id]['therapy'] = therapy_text
    user_data[user_id]['price'] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("Отправить контакт", request_contact=True))

    bot.send_message(
        message.chat.id,
        f"<b>🚀 Ваша заявка готова! 🚀</b>\n\n"
        f"🌍 Регион: <b>{place}</b>\n"
        f"🧩 Услуга: <b>{therapy_text}</b>\n"
        f"💰 Стоимость: <b>{price}</b>\n\n"
        f"☎️ Для завершения — отправьте ваш контакт ☎️",
        parse_mode='HTML',
        reply_markup=markup
    )


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        bot.send_message(message.chat.id, "Ошибка. Начните с /start")
        return

    contact = message.contact
    name = contact.first_name + (f" {contact.last_name}" if contact.last_name else "")
    username = f"@{message.from_user.username}" if message.from_user.username else "—"
    phone = contact.phone_number
    user_link = f"<a href='tg://user?id={user_id}'>Перейти к пользователю</a>"

    data = user_data[user_id]

    admin_msg = (
        f"❗ НОВАЯ ЗАЯВКА ❗\n\n"
        f"<b>👤 Имя:</b> {name}\n"
        f"<b>📞 Телефон:</b> {phone}\n"
        f"<b>💎 Username:</b> {username}\n"
        f"<b>🌍 Место:</b> {data['place']}\n"
        f"<b>🧩 Услуга: </b>{data['therapy']}\n"
        f"<b>💰 Цена:</b> {data['price']}\n"
        f"<b>🔗 Ссылка:</b> {user_link}\n"
        f"<b>🆔 ID:</b> <code>{user_id}</code>"
    )

    bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML', disable_web_page_preview=True)

    bot.send_message(
        message.chat.id,
        "🙌 Спасибо! \n🌿 Мы получили вашу заявку и скоро свяжемся с вами. Хорошего дня! ",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )

    del user_data[user_id]


# === WEBHOOK ===
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN.split(':')[0]}"


@app.route('/')
def index():
    return "<h1>Бот запущен и работает стабильно ⚡</h1>"


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403


@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    url = f"https://{request.host}{WEBHOOK_PATH}"
    bot.remove_webhook()
    s = bot.set_webhook(url=url)
    return f"Webhook {'установлен' if s else 'ошибка'}: {url}"


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
