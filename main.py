import logging
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import json
import os
import random
from datetime import datetime, timedelta

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Настроим логирование для httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

# ID администратора
ADMIN_ID = 5815876536

# Токен бота
TOKEN = "7263696629:AAHsATED3c82dmKMpHLGxNztCcOPZKl0tQI"

# Файл для хранения данных пользователей
DATA_FILE = 'user_data.json'

# Загрузка данных пользователей из файла
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохранение данных пользователей в файл
def save_user_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Хранение данных пользователей
user_data = load_user_data()

# Функция для создания клавиатуры с кнопками
def create_confirmation_keyboard(action: str, user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data=f"{action}_confirm_{user_id}"),
            InlineKeyboardButton("Нет", callback_data=f"{action}_cancel_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция для создания кнопки со ссылкой
def create_link_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("↩️ Основной бот", url="https://t.me/SkyRuShop_Bot")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username if update.effective_user.username else "пользователь"

    if user_id not in user_data:
        user_data[user_id] = {
            'username': username,
            'level': 1,
            'points': 0,
            'last_farm_time': (datetime.now() - timedelta(hours=3)).isoformat(),  # Позволяем сразу фармить
            'last_game_time': (datetime.now() - timedelta(hours=4)).isoformat()   # Позволяем сразу играть
        }
        save_user_data(user_data)

    commands = (
        "*Добро пожаловать!* 🎉\n\n"
        "Список команд:\n"
        "🟢 /start - Начать взаимодействие с ботом\n"
        "🌾 /farm - Получить скаи\n"
        "📊 /stats - Посмотреть свои статистики\n"
        "⚔️ /buff - Прокачать уровень\n"
        "ℹ️ /info - Узнать информацию о стоимости уровней\n"
        "🎲 /rul - Угадай число и получи скаи\n"
        "🏆 /top - Топ 5 игроков по количеству скаев\n"
    )

    await update.message.reply_text(commands, parse_mode=ParseMode.MARKDOWN, reply_markup=create_link_keyboard())

# Функция фарма очков
async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if user_id not in user_data:
        await update.message.reply_text('Сначала выполните команду /start.')
        return

    user = user_data[user_id]
    now = datetime.now()

    # Проверка времени последнего фарма
    last_farm_time = datetime.fromisoformat(user['last_farm_time'])
    wait_time = last_farm_time + timedelta(hours=3) - now
    if wait_time > timedelta(0):
        hours, remainder = divmod(wait_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        await update.message.reply_text(
            f'⏳ Вы можете фармить только раз в 3 часа. Осталось ждать: {int(hours)}ч {int(minutes)}м {int(seconds)}с.'
        )
        return

    # Получение скаев
    points = user['level']
    user['points'] += points
    user['last_farm_time'] = now.isoformat()
    save_user_data(user_data)
    await update.message.reply_text(f'🎉 Вы получили {points} скаев! У вас сейчас {user["points"]} скаев.')

# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if user_id not in user_data:
        await update.message.reply_text('Сначала выполните команду /start.')
        return

    user = user_data[user_id]
    stats_message = (
        f"👤 *Логин:* {user['username']}\n"
        f"☁️ *Всего скаев:* {user['points']}\n"
        f"📃 *Ваш уровень:* {user['level']}"
    )
    await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)

# Функция прокачки уровня
async def buff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if user_id not in user_data:
        await update.message.reply_text('Сначала выполните команду /start.')
        return

    user = user_data[user_id]
    next_level_cost = user['level'] * 10

    if user['points'] < next_level_cost:
        await update.message.reply_text(f'❌ У вас недостаточно скаев для повышения уровня. Нужно {next_level_cost} скаев.')
        return

    # Повышение уровня
    user['points'] -= next_level_cost
    user['level'] += 1
    save_user_data(user_data)

    await update.message.reply_text(f'🎉 Поздравляем! Вы повысили уровень до {user["level"]}. У вас осталось {user["points"]} скаев.')

# Команда /info
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    level_costs = {level: level * 10 for level in range(2, 11)}
    info_message = "*Цены за уровни:*\n"
    for level, cost in level_costs.items():
        info_message += f"Уровень {level}: {cost} скаев\n"
    await update.message.reply_text(info_message, parse_mode=ParseMode.MARKDOWN)

# Команда /top
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Сортировка пользователей по количеству скаев в порядке убывания
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['points'], reverse=True)[:5]

    top_message = "<b>Топ 5 игроков по количеству скаев:</b>\n"
    for rank, (user_id, user_info) in enumerate(sorted_users, start=1):
        top_message += f"{rank}. @{user_info['username']} - {user_info['points']} скаев\n"

    if not sorted_users:
        top_message = "⛔ Топ 5 игроков пуст."

    await update.message.reply_text(top_message, parse_mode=ParseMode.HTML)


# Команда /ban
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Команда должна быть ответом на сообщение пользователя, которого вы хотите забанить.")
        return

    user_to_ban = update.message.reply_to_message.from_user.id
    keyboard = create_confirmation_keyboard('ban', user_to_ban)

    await update.message.reply_text(
        f"Вы уверены, что хотите забанить пользователя {user_to_ban}?",
        reply_markup=keyboard
    )

# Команда /unban
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Команда должна быть ответом на сообщение пользователя, которого вы хотите разбанить.")
        return

    user_to_unban = update.message.reply_to_message.from_user.id
    keyboard = create_confirmation_keyboard('unban', user_to_unban)

    await update.message.reply_text(
        f"Вы уверены, что хотите разбанить пользователя {user_to_unban}?",
        reply_markup=keyboard
    )

# Команда /mute
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Команда должна быть ответом на сообщение пользователя, которого вы хотите замутить.")
        return

    user_to_mute = update.message.reply_to_message.from_user.id
    keyboard = create_confirmation_keyboard('mute', user_to_mute)

    await update.message.reply_text(
        f"Вы уверены, что хотите замутить пользователя {user_to_mute}?",
        reply_markup=keyboard
    )

# Команда /unmute
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Команда должна быть ответом на сообщение пользователя, которого вы хотите размутить.")
        return

    user_to_unmute = update.message.reply_to_message.from_user.id
    keyboard = create_confirmation_keyboard('unmute', user_to_unmute)

    await update.message.reply_to_message(
        f"Вы уверены, что хотите размутить пользователя {user_to_unmute}?",
        reply_markup=keyboard
    )

# Обработчик подтверждения действий админа
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    action, decision, user_id = query.data.split('_')

    if decision == 'confirm':
        if action == 'ban':
            await context.bot.ban_chat_member(update.effective_chat.id, int(user_id))
            await query.edit_message_text(f"✅ Пользователь {user_id} был забанен.")
        elif action == 'unban':
            await context.bot.unban_chat_member(update.effective_chat.id, int(user_id))
            await query.edit_message_text(f"✅ Пользователь {user_id} был разбанен.")
        elif action == 'mute':
            until_date = datetime.now() + timedelta(days=1)
            permissions = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(update.effective_chat.id, int(user_id), permissions, until_date=until_date)
            await query.edit_message_text(f"✅ Пользователь {user_id} был замучен на 1 день.")
        elif action == 'unmute':
            permissions = ChatPermissions(can_send_messages=True)
            await context.bot.restrict_chat_member(update.effective_chat.id, int(user_id), permissions)
            await query.edit_message_text(f"✅ Пользователь {user_id} был размучен.")
    else:
        await query.edit_message_text("❌ Действие отменено.")

# Команда /rul
async def rul(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if user_id not in user_data:
        await update.message.reply_text('Сначала выполните команду /start.')
        return

    user = user_data[user_id]
    now = datetime.now()

    # Проверка времени последней игры
    last_game_time = datetime.fromisoformat(user['last_game_time'])
    wait_time = last_game_time + timedelta(hours=4) - now
    if wait_time > timedelta(0):
        hours, remainder = divmod(wait_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        await update.message.reply_text(
            f'⏳ Вы можете играть в эту игру только раз в 4 часа. Осталось ждать: {int(hours)}ч {int(minutes)}м {int(seconds)}с.'
        )
        return

    user['last_game_time'] = now.isoformat()
    save_user_data(user_data)

    await update.message.reply_text('Я загадал число от 1 до 10. Попробуйте угадать!')

    number_to_guess = random.randint(1, 10)
    context.user_data['number_to_guess'] = number_to_guess

# Обработчик сообщений для угадывания числа
async def guess_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if 'number_to_guess' not in context.user_data:
        return  # Если число не загадано, ничего не делаем

    try:
        guess = int(update.message.text)
    except ValueError:
        return  # Если введено не число, ничего не делаем

    number_to_guess = context.user_data['number_to_guess']

    if guess == number_to_guess:
        user_data[user_id]['points'] += 10
        save_user_data(user_data)
        await update.message.reply_text('🎉 Поздравляем! Вы угадали число и получили 10 скаев.')
    else:
        await update.message.reply_text(f'❌ Неверно. Я загадал число {number_to_guess}.')

    del context.user_data['number_to_guess']  # Удаляем загаданное число после попытки

# Основная функция
def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("farm", farm))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("buff", buff))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("rul", rul))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), guess_number))

    app.run_polling()

if __name__ == "__main__":
    main()
