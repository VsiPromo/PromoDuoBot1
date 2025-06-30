# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
import sqlite3
# === Налаштування ===
TOKEN = '8184241735:AAFR2l26xI1U_GOh39RCPX5hBtvGnsUAIuQ'
CHANNELS = ['@Vsi_PROMO', '@uaclub_casinoman']
REWARD_PER_REF = 4
WITHDRAW_LIMIT = 100

# === База даних ===
conn = sqlite3.connect('promo_duo.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invited_by INTEGER,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()

# === Перевірка підписки ===
def check_subscriptions(user_id, context):
    for channel in CHANNELS:
        member = context.bot.get_chat_member(channel, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            return False
    return True

# === /start ===
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    args = context.args

    if not check_subscriptions(user_id, context):
        buttons = [[InlineKeyboardButton("Підписатись на канали", url=ch)] for ch in CHANNELS]
        update.message.reply_text("Підпишись на всі канали, щоб користуватись ботом:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if args:
        inviter_id = int(args[0])
        if inviter_id != user_id:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO users (user_id, invited_by, balance) VALUES (?, ?, 0)", (user_id, inviter_id))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REWARD_PER_REF, inviter_id))
                conn.commit()
    else:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

    context.bot.send_message(chat_id=user_id, text=f"Привіт, {user.first_name}!")
Запрошуй друзів та отримуй по 4 грн за кожного!
context.bot.send_message(chat_id=user_id, text=f"Твоє посилання: https://t.me/PromoDuoBot?start={user_id}")


# === /balance ===
def balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    bal = row[0] if row else 0
    msg = f"👛 Твій баланс: {bal} грн
"
    if bal >= WITHDRAW_LIMIT:
        msg += "✅ Ти можеш вивести кошти. Надішли /withdraw"
    else:
        msg += f"🔒 Виведення доступне при {WITHDRAW_LIMIT} грн"
    update.message.reply_text(msg)

# === /withdraw ===
def withdraw(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    bal = row[0] if row else 0
    if bal < WITHDRAW_LIMIT:
        update.message.reply_text("🔒 Виведення доступне при 100 грн")
        return

    update.message.reply_text("💳 Введи номер картки або платіжної системи для виплати")
    return

# === Отримання платіжних реквізитів ===
def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] >= WITHDRAW_LIMIT:
        admin_id = 7262164512
        context.bot.send_message(admin_id, f"🔔 Запит на виведення\n👤 @{update.effective_user.username}\nID: {user_id}\n💰 Сума: {row[0]} грн\n📤 Реквізити: {text}")
        update.message.reply_text("✅ Заявка на виплату надіслана адміну. Очікуй підтвердження!")

# === Основний запуск ===
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("withdraw", withdraw))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
