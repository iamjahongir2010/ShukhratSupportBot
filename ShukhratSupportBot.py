import os
import telebot
from telebot import types
from flask import Flask, request

# ======================
# Настройки (через Render env vars)
# ======================
BOT_TOKEN = os.getenv('BOT_TOKEN') or 'PUT_YOUR_TOKEN_HERE'
ADMIN_ID = int(os.getenv('ADMIN_ID')) if os.getenv('ADMIN_ID') else None

if BOT_TOKEN is None:
    raise SystemExit('Error: BOT_TOKEN is not set')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ----------------------
# Цены и услуги (обновлённые)
# ----------------------
price = {
    'Онлайн консультации (по психологии)': {
        'Таджикистан': '150 смн/час',
        'СНГ': '≈2500 ₽/час',
        'Другое': '≈35 $/час'
    },
    'Бизнесс консультация (онлайн)': {
        'Таджикистан': '300 смн/час',
        'СНГ': '≈3500 ₽/час',
        'Другое': '≈70 $/час'
    },
    'Регрессивный гипноз (онлайн)': {
        'Таджикистан': '500 смн/1-1.5ч',
        'СНГ': '≈5000 ₽/час',
        'Другое': '≈100 $/сеанс'
    },
    'Офлайн (Таджикистан)': {
        'Индивидуальный сеанс': '150 смн/час',
        'Семейный (2 чел)': '250 смн/час',
        'Сеанс на дому': '100 смн + 250 смн/час',
        'Регрессивный гипноз 1ч': '600 смн/час',
        'Регрессивный гипноз 1-2ч': '800 смн/1-2ч',
        'Регрессивный гипноз 2-3ч': '1000 смн/2-3ч'
    },
    'Бизнесс (офлайн, Таджикистан)': {
        'До 3 человек': '300 смн/час'
    },
    'Групповые тренинги (офлайн, Таджикистан)': {
        'За 1 человека': '50 смн',
        'Тренинг (1.5-2ч)': '1000 смн/занятие'
    }
}

# ----------------------
# Хранилище состояний пользователей (in-memory)
# Для продакшена — заменить на БД / кеш
# ----------------------
user_data = {}  # {chat_id: {'region':..., 'mode': 'онлайн'/'офлайн', 'therapy':...}}

# ----------------------
# Вспомогательные функции
# ----------------------

def set_user(chat_id, key, value):
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id][key] = value


def get_user(chat_id, key, default=None):
    return user_data.get(chat_id, {}).get(key, default)


def format_price_for_selection(region, therapy_key):
    # region: 'Таджикистан'/'СНГ'/'Другое'
    # therapy_key: one of the top-level keys in price or offline keys
    if therapy_key.startswith('Офлайн') or therapy_key.startswith('Бизнесс (офлайн') or therapy_key.startswith('Групповые'):
        # offline uses separate dict keys only for Таджикистан
        items = price.get(therapy_key, {})
        text = ''
        for k, v in items.items():
            text += f"• {k}: {v}\n"
        return text
    else:
        p = price.get(therapy_key, {}).get(region)
        return p or 'Цена по запросу'

# ----------------------
# Бот хендлеры
# ----------------------

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    # Сбросим состояние
    user_data.pop(chat_id, None)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('🇹🇯 Таджикистан', '🌍 Страны СНГ', '🌎 Другое')

    msg = bot.send_message(chat_id, 'Привет! Где вы находитесь? Выберите регион:', reply_markup=markup)
    bot.register_next_step_handler(msg, region_chosen)


def region_chosen(message):
    chat_id = message.chat.id
    text = message.text
    if text == '🇹🇯 Таджикистан':
        set_user(chat_id, 'region', 'Таджикистан')
        # спросим онлайн/офлайн
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add('Онлайн', 'Офлайн')
        msg = bot.send_message(chat_id, 'Вы в Таджикистане — Вы хотите онлайн или офлайн консультацию?', reply_markup=markup)
        bot.register_next_step_handler(msg, tajik_mode_chosen)
    elif text == '🌍 Страны СНГ':
        set_user(chat_id, 'region', 'СНГ')
        set_user(chat_id, 'mode', 'Онлайн')
        show_therapy_options(message)
    elif text == '🌎 Другое':
        set_user(chat_id, 'region', 'Другое')
        set_user(chat_id, 'mode', 'Онлайн')
        show_therapy_options(message)
    else:
        msg = bot.reply_to(message, 'Пожалуйста, выберите одну из кнопок.')
        bot.register_next_step_handler(msg, region_chosen)


def tajik_mode_chosen(message):
    chat_id = message.chat.id
    text = message.text
    if text in ['Онлайн', 'Офлайн']:
        set_user(chat_id, 'mode', text)
        show_therapy_options(message)
    else:
        msg = bot.reply_to(message, 'Пожалуйста, используйте кнопки.')
        bot.register_next_step_handler(msg, tajik_mode_chosen)


def show_therapy_options(message):
    chat_id = message.chat.id
    mode = get_user(chat_id, 'mode')

    # формируем список доступных услуг в зависимости от режима
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    if mode == 'Онлайн':
        options = [
            'Онлайн консультации (по психологии)',
            'Бизнесс консультация (онлайн)',
            'Регрессивный гипноз (онлайн)',
            '🤔 Объясните виды'
        ]
    else:  # Офлайн — только для Таджикистана
        options = [
            'Индивидуальный сеанс',
            'Семейный (2 чел)',
            'Сеанс на дому',
            'Регрессивный гипноз 1ч',
            'Регрессивный гипноз 1-2ч',
            'Регрессивный гипноз 2-3ч',
            'Бизнесс (офлайн)',
            'Групповые тренинги',
            '🤔 Объясните виды'
        ]

    for opt in options:
        markup.add(opt)

    msg = bot.send_message(chat_id, 'Выберите услугу:', reply_markup=markup)
    bot.register_next_step_handler(msg, therapy_chosen)


def therapy_chosen(message):
    chat_id = message.chat.id
    text = message.text
    mode = get_user(chat_id, 'mode')
    region = get_user(chat_id, 'region')

    if text == '🤔 Объясните виды':
        explanation = ''
        if mode == 'Онлайн':
            explanation = (
                'Онлайн консультации — психологическая помощь по видеосвязи\n'
                'Бизнесс консультация (онлайн) — консультация по бизнесу/стратегии\n'
                'Регрессивный гипноз (онлайн) — работа с подсознанием и новыми установками\n'
            )
        else:
            explanation = (
                'Индивидуальный сеанс — обычная очная консультация\n'
                'Семейный (2 чел) — работа с двумя участниками\n'
                'Сеанс на дому — визит к клиенту (есть фикс + часовая ставка)\n'
                'Регрессивный гипноз — углублённая очная сессия\n'
                'Бизнесс (офлайн) — бизнес-консультация до 3 человек\n'
                'Групповые тренинги — массовые занятия\n'
            )
        msg = bot.send_message(chat_id, explanation)
        bot.register_next_step_handler(msg, therapy_chosen)
        return

    # проверяем корректность выбора
    valid_online = [
        'Онлайн консультации (по психологии)',
        'Бизнесс консультация (онлайн)',
        'Регрессивный гипноз (онлайн)'
    ]

    valid_offline = [
        'Индивидуальный сеанс', 'Семейный (2 чел)', 'Сеанс на дому',
        'Регрессивный гипноз 1ч', 'Регрессивный гипноз 1-2ч', 'Регрессивный гипноз 2-3ч',
        'Бизнесс (офлайн)', 'Групповые тренинги'
    ]

    if (mode == 'Онлайн' and text not in valid_online) or (mode == 'Офлайн' and text not in valid_offline):
        msg = bot.reply_to(message, 'Пожалуйста, выберите одну из кнопок.')
        bot.register_next_step_handler(msg, therapy_chosen)
        return

    set_user(chat_id, 'therapy', text)

    # показываем цену
    if mode == 'Онлайн':
        region = region or 'Другое'
        cost = format_price_for_selection(region, text)
        resp = f'Вы выбрали: {text}\nРегион: {region}\nСтоимость: {cost}\n\nОтправьте контакт для связи.'
    else:
        cost_block = format_price_for_selection('Таджикистан', 'Офлайн (Таджикистан)')
        # для офлайн используем конкретную выбранную опцию
        if text in price['Офлайн (Таджикистан)']:
            cost = price['Офлайн (Таджикистан)'][text]
            resp = f'Вы выбрали: {text}\nСтоимость: {cost}\n\nОтправьте контакт для связи.'
        else:
            # групповые/бизнес случай
            if text == 'Бизнесс (офлайн)':
                cost = price['Бизнесс (офлайн, Таджикистан)']['До 3 человек']
                resp = f'Вы выбрали: {text}\nСтоимость: {cost}\n\nОтправьте контакт для связи.'
            elif text == 'Групповые тренинги':
                cost = price['Групповые тренинги (офлайн, Таджикистан)']['За 1 человека']
                resp = f'Вы выбрали: {text}\nСтоимость: {cost}\n\nОтправьте контакт для связи.'
            else:
                resp = 'Выбранная опция: {text}. Стоимость уточняется. Отправьте контакт для связи.'

    # Кнопка отправки контакта
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_btn = types.KeyboardButton('📱 Отправить контакт', request_contact=True)
    markup.add(contact_btn)
    msg = bot.send_message(chat_id, resp, reply_markup=markup)
    # не регистрируем next step — дальше обработка по content_types=['contact']


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    contact = message.contact.phone_number
    username = message.from_user.username or 'нет'
    region = get_user(chat_id, 'region')
    mode = get_user(chat_id, 'mode')
    therapy = get_user(chat_id, 'therapy')

    bot.send_message(chat_id, 'Спасибо! Наш специалист свяжется с вами в ближайшее время 🙌')

    info = (
        f'📞 Новый клиент:\n'
        f'👤 Имя: {message.from_user.first_name}\n'
        f'🪪 Username: @{username}\n'
        f'📱 Телефон: {contact}\n'
        f'🌍 Регион: {region}\n'
        f'🔎 Режим: {mode}\n'
        f'🧩 Услуга: {therapy}\n'
        f'🔗 tg://user?id={chat_id}'
    )

    # отправляем админу
    try:
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, info, parse_mode='Markdown')
    except Exception as e:
        print('Error sending admin message:', e)

# ----------------------
# Webhook: установка и обработка
# ----------------------

PORT = int(os.environ.get('PORT', 5000))
HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
WEBHOOK_URL = f"https://{HOSTNAME}/" if HOSTNAME else None

if WEBHOOK_URL:
    try:
        print('Setting webhook to', WEBHOOK_URL)
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
    except Exception as e:
        print('Webhook set error:', e)
else:
    print('WARNING: RENDER_EXTERNAL_HOSTNAME is not set — webhook URL is unknown')

@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    print('POST received')
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running.'

if __name__ == '__main__':
    print('Starting Flask server...')
    app.run(host='0.0.0.0', port=PORT)
