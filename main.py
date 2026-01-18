import telebot
import schedule
import time
import threading
import os
import requests
from flask import Flask
from telebot.types import MessageReactionUpdated

# --- НАЛАШТУВАННЯ ---
TOKEN = '8236217660:AAHGeDEer-h-CoJKvFwRrd6iFvFPFES6dKg'
TARGET_CHAT_ID = -1001931356645
VIDEO_FILE_ID = 'BAACAgIAAxkBAAMDaWKNbYKtFWObQtVrOlT4PwW4FMkAAm-WAAKFOhhL_uW0ao2rRtw4BA'
TIME_TO_POST = "09:51" 

# СТАТУСИ 
USER_STATUSES = {
    1859027118: "Уважаємий",
    1428109401: "Уважаємий",
    1809715140: "Уважаємий",
    1360063280: "Уважаємий",
    994207641: "Уважаємий",
    6676149475: "Дирявий водолаз",
    913802232: "Уважаємий",
}
DEFAULT_STATUS = "👤 Гість"

# --- КЛАС ВАЛЮТ ---
class CurrencyProvider:
    @staticmethod
    def get_rates():
        try:
            nbu_resp = requests.get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json", timeout=5).json()
            usd_nbu = next((i["rate"] for i in nbu_resp if i["cc"] == "USD"), 0)
            eur_nbu = next((i["rate"] for i in nbu_resp if i["cc"] == "EUR"), 0)

            pb_resp = requests.get("https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5", timeout=5).json()
            usd_pb = next((i for i in pb_resp if i['ccy'] == 'USD'), {'buy':0, 'sale':0})
            eur_pb = next((i for i in pb_resp if i['ccy'] == 'EUR'), {'buy':0, 'sale':0})

            return (f" *Курс валют:*\n"
                    f" НБУ: 🇺🇸 {usd_nbu:.2f} | 🇪🇺 {eur_nbu:.2f}\n"
                    f" Приват: 🇺🇸 {usd_pb['buy']}/{usd_pb['sale']} | 🇪🇺 {eur_pb['buy']}/{eur_pb['sale']}")
        except:
            return "❌ Помилка отримання курсу."

# --- БОТ ---
class MyBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        # СПИСОК ПАМ'ЯТІ
        self.my_message_ids = []
        
        #schedule.every().day.at(TIME_TO_POST).do(self.send_daily_message)
        self.register_handlers()

    def remember_message(self, sent_message):
        if sent_message:
            self.my_message_ids.append(sent_message.message_id)
            # Тримаємо в пам'яті тільки останні 100 повідомлень
            if len(self.my_message_ids) > 100:
                self.my_message_ids.pop(0)

    def register_handlers(self):
        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            text = message.text.lower()
            chat_id = message.chat.id
            user_id = message.from_user.id
            name = message.from_user.first_name

            print(f"✍️ ПИШЕ: {name} | ID: {user_id} | Текст: {text}")

            # 1. Команда для дізнавання ID (тимчасова)
            if text in ["id", "айді", "мій id"]:
                msg = self.bot.reply_to(message, f"🆔 Твій ID: `{user_id}`", parse_mode="Markdown")
                self.remember_message(msg)
                return

            # 2. ВІДЕО
            if "мері крісмас" in text:
                try:
                    msg = self.bot.send_video(chat_id, VIDEO_FILE_ID, caption="👀")
                    self.remember_message(msg)
                except Exception as e: print(e)

            # 3. ТЕКСТ
            if "сосав?" in text:
                try:
                    msg = self.bot.send_message(chat_id, "Канєшно🤤")
                    self.remember_message(msg)
                except Exception as e: print(e)

            # 4. ВАЛЮТА
            if any(w in text for w in ["долар", "євро", "курс"]):
                msg = self.bot.send_message(chat_id, CurrencyProvider.get_rates(), parse_mode="Markdown")
                self.remember_message(msg)

            # 5. СТАТУС
            if "статус" in text:
                status = USER_STATUSES.get(user_id, DEFAULT_STATUS)
                msg = self.bot.send_message(chat_id, f"👤 *{name}*, статус: `{status}`", parse_mode="Markdown")
                self.remember_message(msg)

        # ОБРОБКА РЕАКЦІЙ (Тільки на свої)
        @self.bot.message_reaction_handler(func=lambda message: True)
        def handle_reactions(reaction: MessageReactionUpdated):
            # Перевіряємо, чи ID повідомлення є у нашому списку "своїх"
            if reaction.message_id in self.my_message_ids:
                # Перевіряємо, чи це НОВА реакція (а не зняття старої)
                if reaction.new_reaction:
                    try:
                        self.bot.send_message(reaction.chat.id, "Бачу реакцію на моєму повідомленні! Дякую 😎")
                    except Exception as e:
                        print(f"Reaction send error: {e}")
            else:
                print(f"Ігнорую реакцію на чуже повідомлення (ID: {reaction.message_id})")

#    def send_daily_message(self):
#       try:
#           msg = self.bot.send_message(TARGET_CHAT_ID, "Мері крісмас🎄👙 @Sasik0809")
#           self.remember_message(msg)
#           print("Щоденне повідомлення відправлено!")
#       except Exception as e:
#           print(f"Daily Message Error: {e}")

    def start(self):
        self.bot.infinity_polling(allowed_updates=['message', 'message_reaction'])

# --- ВЕБ-СЕРВЕР ---
app = Flask(__name__)
@app.route('/')
def index(): return "Bot is working..."

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- ЗАПУСК ---
if __name__ == "__main__":
    my_bot = MyBot()
    threading.Thread(target=run_scheduler).start()
    threading.Thread(target=my_bot.start).start()
    run_flask()

