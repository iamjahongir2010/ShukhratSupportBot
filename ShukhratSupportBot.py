import telebot
from telebot import types
import os
from flask import Flask, request

# 🔐 Токен и ID администратора
BOT_TOKEN = '7547480592:AAGI74gexvju7JooRE2PkfsHIOaE_mOfXKE'
ADMIN_ID = 7518403875  # замени при необходимости

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/"

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

user_data = {}

# 💰 Прайс-лист
price = {
    "Онлайн консультации (психология)": {
        "Таджикистан": "150 смн/час",
        "СНГ": "2500₽/час (эквивалент)",
        "Другое": "35$/час (эквивалент)"
    },
    "Бизнес консультация (онлайн)": {
        "Таджикистан": "300 смн/час",
        "СНГ": "3500₽/час (эквивалент)",
        "Другое": "70$/час (эквивалент)"
    },
    "Регрессивный гипноз (онлайн)": {
        "Таджикистан": "500 смн/1–1.5 часа",
        "СНГ": "5000₽/час (эквивалент)",
        "Другое": "100$/час (эквивалент)"
    },
    "Офлайн консультации (живые)": {
        "Индивидуальный сеанс": "150 смн/час",
        "Семейный сеанс (2 чел)": "250 смн/час",
        "На дому": "100 смн выезд + 250 смн/час",
        "Регрессивный гипноз": "600 смн/час, 800 смн/1–2ч, 1000 смн/2–3ч"
    },
    "Бизнес консультации (офлайн)": "300 смн/час (до 3 человек)",
    "Групповые тренинги": "50 смн с человека / 1000 смн за 1.5–2 часа"
}

# 🚀 Flask webhook
@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200


# 🧠 Старт
@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Таджикистан', 'СНГ', 'Другое')
    bot.send_message(message.chat.id, "🌍 Выберите ваш регион:", reply_markup=markup)
    bot.register_next_step_handler(message, region_choice)


def region_choice(message):
    region = message.text
    user_data[message.chat.id]['region'] = region
    if region == "Таджикистан":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add('Онлайн', 'Офлайн')
        bot.send_message(message.chat.id, "💬 Выберите формат консультации:", reply_markup=markup)
        bot.register_next_step_handler(message, tajik_format)
    elif region in ["СНГ", "Другое"]:
        choose_therapy(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите одну из кнопок.")
        bot.register_next_step_handler(message, region_choice)


def tajik_format(message):
    format_choice = message.text
    if format_choice not in ["Онлайн", "Офлайн"]:
        bot.send_message(message.chat.id, "Выберите кнопкой.")
        bot.register_next_step_handler(message, tajik_format)
        return
    user_data[message.chat.id]['format'] = format_choice
    choose_therapy(message)


def choose_therapy(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    region = user_data[message.chat.id].get('region')
    if region == "Таджикистан" and user_data[message.chat.id].get('format') == "Офлайн":
        markup.add("Офлайн консультации (живые)", "Бизнес консультации (офлайн)", "Групповые тренинги")
    else:
        markup.add("Онлайн консультации (психология)", "Бизнес консультация (онлайн)", "Регрессивный гипноз (онлайн)")
    bot.send_message(message.chat.id, "🧩 Выберите тип сеанса:", reply_markup=markup)
    bot.register_next_step_handler(message, show_price)


def show_price(message):
    therapy = message.text
    chat_id = message.chat.id
    user_data[chat_id]['therapy'] = therapy
    region = user_data[chat_id].get('region')
    format_choice = user_data[chat_id].get('format')

    text = f"🧾 *{therapy}*\n"

    if region == "Таджикистан" and format_choice == "Офлайн":
        if isinstance(price[therapy], dict):
            for k, v in price[therapy].items():
                text += f"▫️ {k}: {v}\n"
        else:
            text += f"💰 {price[therapy]}"
    else:
        cost = price.get(therapy, {}).get(region)
        text += f"💰 {cost}"

    bot.send_message(chat_id, text, parse_mode='Markdown')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    contact_btn = types.KeyboardButton('📱 Отправить контакт', request_contact=True)
    markup.add(contact_btn)
    bot.send_message(chat_id, "📞 Пожалуйста, отправьте ваш контакт:", reply_markup=markup)


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    data = user_data.get(chat_id, {})
    contact = message.contact.phone_number
    username = message.from_user.username or 'нет'
    user_link = f"tg://user?id={message.from_user.id}"

    bot.send_message(chat_id, "Спасибо! Наш специалист свяжется с вами скоро 🙌")

    info = (
        f"📩 *Новый клиент:*\n"
        f"👤 Имя: {message.from_user.first_name}\n"
        f"🪪 Username: @{username}\n"
        f"📱 Телефон: {contact}\n"
        f"🌍 Регион: {data.get('region')}\n"
        f"🧩 Терапия: {data.get('therapy')}\n"
        f"🏠 Формат: {data.get('format', '-')}\n"
        f"🔗 [Открыть чат]({user_link})"
    )

    bot.send_message(ADMIN_ID, info, parse_mode='Markdown')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))