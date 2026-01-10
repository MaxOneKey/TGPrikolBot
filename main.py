import telebot
import schedule
import time
import threading
from flask import Flask 
import os

# --- НАЛАШТУВАННЯ ---
TOKEN = '8236217660:AAHGeDEer-h-CoJKvFwRrd6iFvFPFES6dKg'
TARGET_CHAT_ID = -100123456789
VIDEO_FILE_ID = 'BAACAgIAAxkBAAMDaWKNbYKtFWObQtVrOlT4PwW4FMkAAm-WAAKFOhhL_uW0ao2rRtw4BA'
TIME_TO_POST = "09:00"
DAILY_PHRASE = "Мері крісмас🎄👙"
KEYWORD = "мері крісмас"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__) 

# --- БЛОК БОТА ---
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if KEYWORD in message.text.lower():
        try:
            bot.send_video(message.chat.id, VIDEO_FILE_ID, caption="Хіхіхіха")
        except Exception as e:
            print(f"Error: {e}")

def send_daily_message():
    try:
        bot.send_message(TARGET_CHAT_ID, DAILY_PHRASE)
    except Exception as e:
        print(f"Timer Error: {e}")

schedule.every().day.at(TIME_TO_POST).do(send_daily_message)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_bot():
    bot.infinity_polling()

# --- БЛОК ВЕБ-СЕРВЕРА (Щоб Render не спав) ---
@app.route('/')
def index():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# --- ЗАПУСК ВСЬОГО РАЗОМ ---
if __name__ == "__main__":

    t1 = threading.Thread(target=run_scheduler)
    t1.start()

    t2 = threading.Thread(target=run_bot)
    t2.start()

    run_flask()