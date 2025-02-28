import telebot
import time
import logging

# Замените 'YOUR_TELEGRAM_BOT_TOKEN' на токен вашего бота
BOT_TOKEN = 'Вот сдесь токен вашего бота'
# Замените 'YOUR_ADMIN_ID' на ID администратора
ADMIN_ID = YOUR_ADMIN_ID

bot = telebot.TeleBot(BOT_TOKEN)

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Словарь для хранения данных о пользователях
user_data = {}

# --- Обработчики команд ---

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}  # Initialize user's data
    bot.send_message(chat_id, "Приветствую! Сначала введите username человека (без @), с которым вы хотели бы провести 8 марта:")
    bot.register_next_step_handler(message, get_person_username)

def get_person_username(message):
    chat_id = message.chat.id
    username = message.text.strip()  # Remove leading/trailing spaces
    user_data[chat_id]['person_username'] = username

    # **Важно:** Проверка существования username сложна и ненадежна.  Обычно делают так:
    # 1. Пытаются получить информацию о пользователе по username через Telegram API (bot.get_chat).
    # 2. Если API возвращает ошибку "user not found", считаем, что username не существует.
    # **Проблема:**  Telegram ограничивает частоту запросов к API.  Если бот будет часто проверять username, его могут заблокировать.
    # **Лучший вариант:**  НЕ проверять username, а просто сохранить его.  Администратор сам сможет проверить, правильный ли username указал пользователь.

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    item_obichno = telebot.types.KeyboardButton("Обычно")
    item_interesno = telebot.types.KeyboardButton("Интересно")
    item_epicheski = telebot.types.KeyboardButton("Эпически")
    markup.add(item_obichno, item_interesno, item_epicheski)

    bot.send_message(chat_id, f"Спасибо! Теперь выберите варианты, как вы хотите провести 8 марта?", reply_markup=markup)


# --- Обработчик текстовых сообщений (для кнопок) ---

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    if text == "Обычно":
        user_data[chat_id]['choice'] = "Обычно"
        bot.send_message(chat_id, "Вы получите просто подарок от того человека, кто вам это отправил: цветы + небольшой презент.")
        time.sleep(5)
        bot.send_message(chat_id, "Не забудьте поблагодарить его, он очень вас ценит))")
        time.sleep(5)
        send_final_message(chat_id, "Приятного свидания", chat_id)

    elif text == "Интересно":
        user_data[chat_id]['choice'] = "Интересно"
        bot.send_message(chat_id, "Вы получите от человека который вам это отправил: Цветы и поход на фильм в этот же день.")
        time.sleep(5)
        bot.send_message(chat_id, "Проведите приятно время пообщайтесь о том что вы чувствуете к этому человеку, это поможет вам в будущем.")
        time.sleep(5)
        send_final_message(chat_id, "Приятного свидания", chat_id)

    elif text == "Эпически":
        user_data[chat_id]['choice'] = "Эпически"
        markup = telebot.types.InlineKeyboardMarkup()
        item_more = telebot.types.InlineKeyboardButton(text="Хотите узнать что еще?", callback_data="more_epicheski")
        markup.add(item_more)
        bot.send_message(chat_id, "Вы получите от человека, который вам это отправил: Цветы + презент + поход на фильм ->", reply_markup=markup)

    else:
        bot.send_message(chat_id, "Пожалуйста, используйте кнопки для выбора.")
        logging.warning(f"User {chat_id} sent invalid input: {text}")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    if call.data == "more_epicheski":
        bot.send_message(chat_id, "Раз вы решились то вы точно очень любите этого человека и хотите с ним того что идем ценником 18+")
        time.sleep(5)
        bot.send_message(chat_id, "Как только вы увидели это сообщение админ сообщит через несколько минут о вашем выборе и сообщит ему")
        time.sleep(5)
        send_final_message(chat_id, "Приятного свидания", chat_id)


# Функция отправки финального сообщения и уведомления админа
def send_final_message(chat_id, message, user_chat_id):
    bot.send_message(chat_id, message)
    logging.info(f"User {chat_id} reached the end of scenario.")

    person_username = user_data[chat_id].get('person_username', 'Не указан')
    user_choice = user_data[chat_id].get('choice', 'Не сделан')


    chat_link = f"https://t.me/{person_username}" if person_username != 'Не указан' else "Username не указан"


    try:
        user = bot.get_chat(chat_id)
        if user.username:
            user_link = f"https://t.me/{user.username}"  # Ссылка на профиль пользователя
        else:
            user_link = f"tg://user?id={chat_id}"  # Deeplink, если нет username
    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Error getting user info: {e}")
        user_link = f"ID: {chat_id}"  # Если не можем получить инфо, используем ID



    message_to_admin = (
        f"Пользователь {user_link} выбрал: {user_choice}.\n" # Используем user_link
        f"Предпочитает провести 8 марта с: {person_username}.\n"
        f"Ссылка на пользователя (если указан username): {chat_link}"
    )

    try:
        bot.send_message(ADMIN_ID, message_to_admin)
        logging.info(f"Sent notification to admin about user {chat_id}")

    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Error getting user info or sending message to admin: {e}")
        if "blocked" in str(e):
            logging.warning(f"Bot is blocked by user {chat_id}")
        elif "user not found" in str(e):
            logging.warning(f"User {chat_id} not found.")
        else:
            logging.error(f"Unhandled Telegram API error: {e}")
    except Exception as e:
        logging.error(f"General error sending message to admin: {e}")


# --- Запуск бота ---

if __name__ == '__main__':
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
