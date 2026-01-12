import telebot
import schedule
import time
import threading
from flask import Flask 
import os

# --- НАЛАШТУВАННЯ ---
TOKEN = '8236217660:AAHGeDEer-h-CoJKvFwRrd6iFvFPFES6dKg'
TARGET_CHAT_ID = -1001931356645
VIDEO_FILE_ID = 'BAACAgIAAxkBAAMDaWKNbYKtFWObQtVrOlT4PwW4FMkAAm-WAAKFOhhL_uW0ao2rRtw4BA'
TIME_TO_POST = "09:51"
DAILY_PHRASE = "Мері крісмас🎄👙 @Sasik0809"
PING_PHRAZE = "Канєшно🤤"
KEYWORD = "мері крісмас"
KEYWORD2 = "сосав?"

# --- ІНІЦІАЛІЗАЦІЯ
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__) 

# --- БЛОК БОТА ---

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text.lower()

    if KEYWORD in text:
        try:
            bot.send_video(message.chat.id, VIDEO_FILE_ID, caption="👀")
        except Exception as e:
            print(f"Error sending video: {e}")

    elif KEYWORD2 in text:
        try:
            bot.send_message(message.chat.id, PING_PHRAZE)
        except Exception as e:
            print(f"Error sending message: {e}")

def send_daily_message():
    try:
        bot.send_message(TARGET_CHAT_ID, DAILY_PHRASE)
        print("Щоденне повідомлення відправлено!")
    except Exception as e:
        print(f"Timer Error: {e}")

schedule.every().day.at(TIME_TO_POST).do(send_daily_message)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_bot():
    bot.infinity_polling()

# --- БЛОК ВЕБ-СЕРВЕРА ---
@app.route('/')
def index():
    return "Bot is alive!"

def run_flask():
    # Render передає порт автоматично
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- ЗАПУСК ВСЬОГО РАЗОМ ---
if __name__ == "__main__":
    print("Бот запускається...")
    
    t1 = threading.Thread(target=run_scheduler)
    t1.start()

    t2 = threading.Thread(target=run_bot)
    t2.start()

    run_flask()
