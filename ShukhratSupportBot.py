import telebot
from telebot import types

# 🔐 Твой токен и ID администратора
BOT_TOKEN = '7547480592:AAGI74gexvju7JooRE2PkfsHIOaE_mOfXKE'
ADMIN_ID = 7518403875

bot = telebot.TeleBot(BOT_TOKEN)

price = {
    'Одиночный сеанс': {
        'Америка': '$30',
        'Европа': '€25',
        'Россия': '1800 ₽',
        'Таджикистан': '150 смн',
        'Другое': '$25'
    },
    'Семейный сеанс': {
        'Америка': '$45',
        'Европа': '€40',
        'Россия': '3000 ₽',
        'Таджикистан': '250 смн',
        'Другое': '$40'
    },
    'ПФР': {
        'Америка': '$55',
        'Европа': '€50',
        'Россия': '3600 ₽',
        'Таджикистан': '300 смн',
        'Другое': '$50'
    },
    'Регрессивный гипноз': {
        'Америка': '$45',
        'Европа': '€40',
        'Россия': '3000 ₽',
        'Таджикистан': '250 смн',
        'Другое': '$40'
    },
}

therapy = None
place = None


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
    markup.add('✅ Да, готов(а)', '❌ Нет, позже')
    bot.send_message(
        message.chat.id,
        '👋 Здравствуйте!\n'
        'Я ваш виртуальный помощник, который поможет подобрать подходящий вид терапии.\n'
        'Перед началом мне понадобится немного информации.\n\n'
        'Вы готовы продолжить?',
        reply_markup=markup
    )
    bot.register_next_step_handler(message, place_question_func)


def place_question_func(message):
    if message.text == '✅ Да, готов(а)':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
        markup.add('Америка', 'Россия', 'Европа', 'Таджикистан', 'Другое')
        bot.send_message(message.chat.id, '🌍 Где вы находитесь?', reply_markup=markup)
        bot.register_next_step_handler(message, place_func)
    elif message.text == '❌ Нет, позже':
        bot.send_message(message.chat.id, 'Хорошо, когда будете готовы — напишите /start 😊')
    else:
        bot.reply_to(message, 'Пожалуйста, выберите одну из кнопок.')
        bot.register_next_step_handler(message, place_question_func)


def place_func(message):
    global place
    if message.text in ['Америка', 'Россия', 'Европа', 'Таджикистан', 'Другое']:
        place = message.text
        therapy_question_func(message)
    else:
        bot.reply_to(message, 'Пожалуйста, выберите одну из кнопок.')
        bot.register_next_step_handler(message, place_func)


def therapy_question_func(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
    markup.add(
        'Одиночный сеанс',
        'Семейный сеанс',
        'ПФР',
        'Регрессивный гипноз',
        '🤔 Я не знаю, объясните что есть что'
    )
    bot.send_message(message.chat.id, 'Какой вид терапии вам нужен?', reply_markup=markup)
    bot.register_next_step_handler(message, therapy_func)


def therapy_func(message):
    global therapy
    if message.text in ['Одиночный сеанс', 'Семейный сеанс', 'ПФР', 'Регрессивный гипноз']:
        therapy = message.text
        get_contact_question(message)
    elif message.text == '🤔 Я не знаю, объясните что есть что':
        explanation = (
            "Вот краткое описание видов терапии 👇\n\n"
            "🧘‍♂️ *Одиночный сеанс* — индивидуальная работа один на один с терапевтом. "
            "Помогает разобраться в себе, тревожности, мотивации или эмоциональных состояниях.\n\n"
            "👨‍👩‍👧 *Семейный сеанс* — терапия для пары или семьи. "
            "Особенно подходит, если есть конфликты между родителями или проблемы с ребёнком — "
            "ведь корень часто в отношениях взрослых.\n\n"
            "💫 *ПФР (Психо-Функциональная Разблокировка)* — метод, направленный на снятие внутренних блоков, "
            "подавленных эмоций и зажимов. "
            "Помогает восстановить естественный психологический и телесный баланс.\n\n"
            "🌀 *Регрессивный гипноз* — мягкий гипнотический метод, "
            "помогающий вернуться к прошлым ситуациям и проработать их причины, чтобы снять внутреннее напряжение.\n\n"
            "Теперь выберите, что вам ближе:"
        )
        bot.send_message(message.chat.id, explanation, parse_mode='Markdown')
        therapy_question_func(message)
    else:
        bot.reply_to(message, 'Отвечайте кнопками.')
        bot.register_next_step_handler(message, therapy_func)


def get_contact_question(message):
    cost = price[therapy][place]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_btn = types.KeyboardButton('📱 Отправить контакт', request_contact=True)
    markup.add(contact_btn)
    bot.send_message(
        message.chat.id,
        f'Вы находитесь в: {place}\n'
        f'Выбранный вид терапии: {therapy}\n'
        f'Стоимость: {cost}\n\n'
        'Пожалуйста, отправьте свой контакт для связи:',
        reply_markup=markup
    )


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    contact = message.contact.phone_number
    username = message.from_user.username if message.from_user.username else 'нет'
    user_link = f'tg://user?id={message.from_user.id}'

    bot.send_message(message.chat.id, 'Спасибо! Наш специалист свяжется с вами в ближайшее время 🙌')

    info = (
        f'📞 *Новый клиент:*\n'
        f'👤 Имя: {message.from_user.first_name}\n'
        f'🪪 Username: @{username}\n'
        f'📱 Телефон: {contact}\n'
        f'🌍 Место: {place}\n'
        f'🧩 Терапия: {therapy}\n'
        f'🔗 [Открыть чат]({user_link})'
    )

    bot.send_message(ADMIN_ID, info, parse_mode='Markdown')


bot.polling(none_stop=True)