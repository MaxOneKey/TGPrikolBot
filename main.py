import telebot
import schedule
import time
import threading
import os
import requests
import re # для пошуку шаблонів тексту
from flask import Flask

# --- НАЛАШТУВАННЯ ---
TOKEN = '8236217660:AAHGeDEer-h-CoJKvFwRrd6iFvFPFES6dKg'
TARGET_CHAT_ID = -1001931356645
VIDEO_FILE_ID = 'BAACAgIAAxkBAAMDaWKNbYKtFWObQtVrOlT4PwW4FMkAAm-WAAKFOhhL_uW0ao2rRtw4BA'
TIME_TO_POST = "09:51"

# Статуси користувачів
USER_STATUSES = {
    123456789: "👑 Адмін",
}
DEFAULT_STATUS = "👤 Гість"

# --- КЛАС ВАЛЮТ І КОНВЕРТЕРА ---
class CurrencyProvider:
    CURRENCY_MAP = {
        'usd': 'USD', 'долар': 'USD', 'доларів': 'USD', 'баксів': 'USD', '$': 'USD',
        'eur': 'EUR', 'євро': 'EUR', '€': 'EUR',
        'uah': 'UAH', 'гривня': 'UAH', 'гривень': 'UAH', 'грн': 'UAH'
    }

    @staticmethod
    def get_data():
        """Отримує свіжі дані з НБУ та ПриватБанку"""
        try:
            # НБУ
            nbu_resp = requests.get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json", timeout=5).json()
            # Приват
            pb_resp = requests.get("https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5", timeout=5).json()
            return nbu_resp, pb_resp
        except Exception as e:
            print(f"API Error: {e}")
            return None, None

    @staticmethod
    def get_rates_message(target_currency=None):
        """Формує повідомлення. Якщо target_currency=None, показує все."""
        nbu_data, pb_data = CurrencyProvider.get_data()
        
        if not nbu_data or not pb_data:
            return "❌ Помилка отримання даних."

        # Парсимо НБУ
        usd_nbu = next((i["rate"] for i in nbu_data if i["cc"] == "USD"), 0)
        eur_nbu = next((i["rate"] for i in nbu_data if i["cc"] == "EUR"), 0)

        # Парсимо Приват (з конвертацією в float для округлення)
        usd_pb = next((i for i in pb_data if i['ccy'] == 'USD'), {'buy': '0', 'sale': '0'})
        eur_pb = next((i for i in pb_data if i['ccy'] == 'EUR'), {'buy': '0', 'sale': '0'})
        
        # Округлюємо Приват
        usd_buy = float(usd_pb['buy'])
        usd_sale = float(usd_pb['sale'])
        eur_buy = float(eur_pb['buy'])
        eur_sale = float(eur_pb['sale'])

        msg = ""
        
        # Логіка формування тексту
        if target_currency == 'USD' or target_currency is None:
            msg += (f"🇺🇸 *Долар (USD):*\n"
                    f"🏦 НБУ: {usd_nbu:.2f} грн\n"
                    f"🏪 Приват: {usd_buy:.2f} / {usd_sale:.2f}\n\n")

        if target_currency == 'EUR' or target_currency is None:
            msg += (f"🇪🇺 *Євро (EUR):*\n"
                    f"🏦 НБУ: {eur_nbu:.2f} грн\n"
                    f"🏪 Приват: {eur_buy:.2f} / {eur_sale:.2f}")
        
        if msg == "": 
             return "💰 Курс валют оновлено."
             
        return f"💰 *Курс валют:*\n\n{msg}"

    @staticmethod
    def convert_currency(amount, from_curr_raw, to_curr_raw):
        """Логіка калькулятора"""
        from_code = CurrencyProvider.CURRENCY_MAP.get(from_curr_raw.lower())
        to_code = CurrencyProvider.CURRENCY_MAP.get(to_curr_raw.lower())

        if not from_code or not to_code:
            return None 

        nbu_data, _ = CurrencyProvider.get_data()
        if not nbu_data: return "❌ Помилка API"

        rate_from = 1.0 if from_code == 'UAH' else next((i["rate"] for i in nbu_data if i["cc"] == from_code), None)
        rate_to = 1.0 if to_code == 'UAH' else next((i["rate"] for i in nbu_data if i["cc"] == to_code), None)

        if not rate_from or not rate_to:
            return "❌ Не знайшов курс для конвертації."

        result = (amount * rate_from) / rate_to
        return f"💱 *Конвертація (по НБУ):*\n{amount:.2f} {from_code} = `{result:.2f} {to_code}`"

# --- ГОЛОВНИЙ КЛАС БОТА ---
class MyBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.my_message_ids = []
        schedule.every().day.at(TIME_TO_POST).do(self.send_daily_message)
        self.register_handlers()

    def remember_message(self, sent_message):
        if sent_message:
            self.my_message_ids.append(sent_message.message_id)
            if len(self.my_message_ids) > 100: self.my_message_ids.pop(0)

    def register_handlers(self):
        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            text = message.text.lower()
            chat_id = message.chat.id
            user_id = message.from_user.id
            name = message.from_user.first_name

            print(f"✍️ ПИШЕ: {name} | ID: {user_id} | Текст: {text}")

            # 1. КОНВЕРТЕР (Regex)
            # Шукає шаблони типу: "100 доларів в євро", "500 грн у бакси"
            # (\d+[.,]?\d*) - число (може бути дробовим)
            # ([а-яА-Яa-zA-Z$]+) - перша валюта
            # (?:в|у|in|to) - прийменник
            # ([а-яА-Яa-zA-Z$]+) - друга валюта
            pattern = r"(\d+[.,]?\d*)\s+([а-яА-Яa-zA-Z$]+)\s+(?:в|у|in|to)\s+([а-яА-Яa-zA-Z$]+)"
            match = re.search(pattern, text)
            
            if match:
                amount = float(match.group(1).replace(',', '.'))
                curr_from = match.group(2)
                curr_to = match.group(3)
                
                result_text = CurrencyProvider.convert_currency(amount, curr_from, curr_to)
                if result_text:
                    msg = self.bot.send_message(chat_id, result_text, parse_mode="Markdown")
                    self.remember_message(msg)
                    return 
                    
            # 2. ПРОСТИЙ КУРС
            if "долар" in text or "usd" in text:
                msg = self.bot.send_message(chat_id, CurrencyProvider.get_rates_message('USD'), parse_mode="Markdown")
                self.remember_message(msg)
            elif "євро" in text or "eur" in text: # elif щоб не дублювало, якщо написали "долар і євро"
                msg = self.bot.send_message(chat_id, CurrencyProvider.get_rates_message('EUR'), parse_mode="Markdown")
                self.remember_message(msg)
            elif "курс" in text: # Якщо просто слово "курс" без уточнення
                msg = self.bot.send_message(chat_id, CurrencyProvider.get_rates_message(None), parse_mode="Markdown")
                self.remember_message(msg)

            # 3. ID
            if text in ["id", "айді", "мій id"]:
                msg = self.bot.reply_to(message, f"🆔 Твій ID: `{user_id}`", parse_mode="Markdown")
                self.remember_message(msg)

            # 4. ВІДЕО
            if "мері крісмас" in text:
                try:
                    msg = self.bot.send_video(chat_id, VIDEO_FILE_ID, caption="👀")
                    self.remember_message(msg)
                except Exception as e: print(e)

            # 5. ТЕКСТ
            if "сосав?" in text:
                try:
                    msg = self.bot.send_message(chat_id, "Канєшно🤤")
                    self.remember_message(msg)
                except Exception as e: print(e)

            # 6. СТАТУС
            if "статус" in text:
                status = USER_STATUSES.get(user_id, DEFAULT_STATUS)
                msg = self.bot.send_message(chat_id, f"👤 *{name}*, статус: `{status}`", parse_mode="Markdown")
                self.remember_message(msg)

    def send_daily_message(self):
        try:
            msg = self.bot.send_message(TARGET_CHAT_ID, "Мері крісмас🎄👙 @Sasik0809")
            self.remember_message(msg)
            print("Щоденне повідомлення відправлено!")
        except Exception as e:
            print(f"Daily Message Error: {e}")

    def start(self):
        self.bot.infinity_polling()

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
