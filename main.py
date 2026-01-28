import telebot
import schedule
import time
import threading
import os
import requests
import re
import random
from datetime import datetime, timedelta
from flask import Flask

TOKEN = '8236217660:AAHGeDEer-h-CoJKvFwRrd6iFvFPFES6dKg'
TARGET_CHAT_ID = -1001931356645
VIDEO_FILE_ID = 'BAACAgIAAxkBAAMDaWKNbYKtFWObQtVrOlT4PwW4FMkAAm-WAAKFOhhL_uW0ao2rRtw4BA'
OPA_VIDEO_ID = 'BAACAgIAAxkBAANOaXJ6Z11C29jVykIzNaiTCSz3rOQAAluOAAIBppFLR_s0rYZukBs4BA'
TIME_TO_POST = "09:51"

GIF_LIST = [
    "CgACAgQAAx0Ccx4p5QABASk4aWzxsSRrcDY34MRdJ9RsqI_XIoUAArYFAAJ7uMRRcSP58pCaqwo4BA",
    "CgACAgQAAxkBAAMfaW0gX88ZG0pTvVOTpPOvCRABJfsAArQFAALocZxQMvdQ6R_M2rI4BA",
    "CgACAgIAAxkBAAMgaW0gX-5p75-gCoYioGrPwYK34VoAAvpVAAIk0OBIfZVWi1X6PbM4BA",
    "CgACAgIAAxkBAAMQaW0gX4bhWHc8Xdh1bDPhWd3Bba0AAkFQAAJyS5lLqZOanPaHfQc4BA",
    "CgACAgQAAxkBAAMRaW0gX9IhPjzZaShll7eMBxpT0QUAAq8FAAJm4RxTGDHXik6ety44BA",
    "CgACAgQAAxkBAAMSaW0gX83p_vLsiHEDbi08NQup4oAAAr8FAALxPpRRm1E5Y3paoOc4BA",
    "CgACAgIAAxkBAAMTaW0gX9JRBKyu-l_ltMskOpcVk-UAAi8oAAJWHMhKwQ_0RlGtudM4BA",
    "CgACAgIAAxkBAAMUaW0gX_SFHiRowbHWMqhJUwzfq1YAAuxIAAKYOolIYDVftDvWASY4BA",
    "CgACAgIAAxkBAAMVaW0gX97nWq6QySlVuJ7Hvu6z8DkAAhcmAALtNWlJL2Vtp5TwUbg4BA",
    "CgACAgIAAxkBAAMWaW0gX1vKUx6uJ9BCELB2ul10LAUAAqI8AAKQxcBJaiJgtAEaRwg4BA",
    "CgACAgIAAxkBAAMXaW0gXy2jsxTLXaVV-zzgotN6ZlkAAuRpAAIZd_lKsa3-sfYcXok4BA",
    "CgACAgIAAxkBAAMYaW0gXzgbzI2juLcF07iTgsyDBtoAArZUAAJKH0FJVBgx_NfnN_E4BA",
    "CgACAgQAAxkBAAMZaW0gX9fCfMZNerEZJTHKFlKGdwsAAnYPAALbSylSdKqt4ZNhaKI4BA",
    "CgACAgIAAxkBAAMaaW0gX3sv9tKOClZhb1n5JCDx1YIAAjo1AALhy4BI3aULWbkb5HE4BA",
    "CgACAgIAAxkBAAMbaW0gXwjDiHa_SZMsnz76W12R87oAAsE2AAKM8ZlKQlrQqClMlNM4BA",
    "CgACAgIAAxkBAAMcaW0gX3rg0zLZK8zOA0zliNha9n8AAtpCAAJGlylLc2y9qRq3eiQ4BA",
    "CgACAgIAAxkBAAMdaW0gXxQdiQpsZCchd9U18g5lyxgAApFQAAJ8o_hLJkeQBZi08hM4BA",
    "CgACAgIAAxkBAAMeaW0gX9Cvq6fMWcN3m7jrVq1DCEEAAogyAAJsVolIzdiy8wABNM0iOAQ",
    "CgACAgQAAxkBAANJaW0o-7jGS3-GvcnUE47RfoxfymsAApIDAALVZ8VTRpgDCjR8cP84BA",
    "CgACAgIAAxkBAANIaW0o-9Kymtmzf1R_3lWlTlUlI_AAAi11AAKFAAGZSUdO8p8EdfWVOAQ",
    "CgACAgIAAxkBAANKaW0o-zxZFiBrXWgYUBd99SBQ7eYAAnFoAAIgunBJcNMKEEfdido4BA",
    "CgACAgIAAxkBAANPaXKIyVVu5fzgKlD6hepXM6262rgAAvuOAAIBppFLAVH5NnrLLYY4BA",
    "CgACAgQAAxkBAANXaXKK7wABF8d67ArOZ2flbK2wIqjFAALuGwACCPYRUHtkD1Jip9UPOAQ",
    "CgACAgIAAxkBAANbaXKMSfn2cbn2VfSwmPHwR3cQRDYAAjyPAAIBppFLSn8WcXm1NL04BA",
    "CgACAgIAAxkBAANdaXKMWqrOafT6gnzmvM7IlUPmXh8AAj2PAAIBppFLJN0uubSIMNA4BA"
]

STICKER_PACKS = [
    "kakashkaslonareal_by_fStikBot",
    "zalupkogeneral_by_fStikBot",
    "Zalupines_by_fStikBot",
    "Funny_Amaranth_Swordtail_by_fStikBot"
]

USER_STATUSES = {
    1859027118: "Уважаємий",
    1428109401: "Уважаємий",
    1809715140: "Уважаємий",
    1360063280: "Уважаємий",
    994207641: "Уважаємий",
    6676149475: "Дирявий водолаз",
    913802232: "Уважаємий",
}
DEFAULT_STATUS = "Гість"

class CurrencyProvider:
    CURRENCY_MAP = {
        'usd': 'USD', '$': 'USD', 'usdt': 'USD', 'юсд': 'USD',
        'долар': 'USD', 'долара': 'USD', 'доларів': 'USD', 'долари': 'USD',
        'бакс': 'USD', 'бакса': 'USD', 'баксів': 'USD', 'бакси': 'USD',
        'eur': 'EUR', '€': 'EUR', 'евро': 'EUR',
        'євро': 'EUR', 'євра': 'EUR', 'єврів': 'EUR',
        'uah': 'UAH', '₴': 'UAH',
        'гривня': 'UAH', 'гривні': 'UAH', 'гривень': 'UAH', 'грн': 'UAH'
    }

    @staticmethod
    def get_data():
        try:
            nbu_resp = requests.get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json", timeout=5).json()
            pb_resp = requests.get("https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5", timeout=5).json()
            return nbu_resp, pb_resp
        except Exception as e:
            print(f"API Error: {e}")
            return None, None

    @staticmethod
    def get_rates_message(target_currency=None):
        nbu_data, pb_data = CurrencyProvider.get_data()
        
        if not nbu_data or not pb_data:
            return "❌ Помилка отримання даних."

        usd_nbu = next((i["rate"] for i in nbu_data if i["cc"] == "USD"), 0)
        eur_nbu = next((i["rate"] for i in nbu_data if i["cc"] == "EUR"), 0)

        usd_pb = next((i for i in pb_data if i['ccy'] == 'USD'), {'buy': '0', 'sale': '0'})
        eur_pb = next((i for i in pb_data if i['ccy'] == 'EUR'), {'buy': '0', 'sale': '0'})
        
        usd_buy = float(usd_pb['buy'])
        usd_sale = float(usd_pb['sale'])
        eur_buy = float(eur_pb['buy'])
        eur_sale = float(eur_pb['sale'])

        msg = ""
        
        if target_currency == 'USD' or target_currency is None:
            msg += (f"*Долар (USD):*\n"
                    f"🏦 НБУ: {usd_nbu:.2f} грн\n"
                    f"🏪 Приват: {usd_buy:.2f} / {usd_sale:.2f}\n\n")

        if target_currency == 'EUR' or target_currency is None:
            msg += (f"*Євро (EUR):*\n"
                    f"🏦 НБУ: {eur_nbu:.2f} грн\n"
                    f"🏪 Приват: {eur_buy:.2f} / {eur_sale:.2f}")
        
        if msg == "": 
             return "💰 Курс валют оновлено."
             
        return f"💰 *Курс валют:*\n\n{msg}"

    @staticmethod
    def convert_currency(amount, from_curr_raw, to_curr_raw):
        from_clean = from_curr_raw.lower().strip()
        to_clean = to_curr_raw.lower().strip()
        from_code = CurrencyProvider.CURRENCY_MAP.get(from_clean)
        to_code = CurrencyProvider.CURRENCY_MAP.get(to_clean)

        if not from_code: return f"🤷‍♂️ Я не знаю валюту: `{from_clean}`"
        if not to_code: return f"🤷‍♂️ Я не знаю валюту: `{to_clean}`"

        nbu_data, _ = CurrencyProvider.get_data()
        if not nbu_data: return "❌ Помилка API НБУ"

        rate_from = 1.0 if from_code == 'UAH' else next((i["rate"] for i in nbu_data if i["cc"] == from_code), None)
        rate_to = 1.0 if to_code == 'UAH' else next((i["rate"] for i in nbu_data if i["cc"] == to_code), None)

        if not rate_from or not rate_to: return "❌ Не знайшов курс для такої конвертації."

        result = (amount * rate_from) / rate_to
        return f"💱 *Конвертація (по НБУ):*\n{amount:.2f} {from_code} = `{result:.2f} {to_code}`"

class MyBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.my_message_ids = []

        self.number_cooldowns = {} #рандом число
        
        self.bot_id = int(TOKEN.split(':')[0]) 
        self.last_sender_id = None

        self.random_gif_time = self.generate_random_time()
        print(f"GIF Time: {self.random_gif_time}")

        self.random_sticker_time = self.generate_random_time()
        print(f"Sticker Time: {self.random_sticker_time}")
        
        schedule.every().minute.do(self.check_random_gif)
        schedule.every().minute.do(self.check_random_sticker)
#        schedule.every().day.at(TIME_TO_POST).do(self.send_daily_message)

        self.register_handlers()

    def generate_random_time(self):
        hour = random.randint(10, 21) 
        minute = random.randint(0, 59)
        return f"{hour:02d}:{minute:02d}"

    def check_random_gif(self):
        current_time = time.strftime("%H:%M")
        
        if current_time == self.random_gif_time:
            if self.last_sender_id == self.bot_id:
                print("Skip GIF (Spam protection)")
                now = datetime.now()
                future_time = now + timedelta(minutes=30)
                self.random_gif_time = future_time.strftime("%H:%M")
                print(f"New GIF Time: {self.random_gif_time}")
                return

            self.send_random_gif()
            self.random_gif_time = self.generate_random_time()
            print(f"Next GIF: {self.random_gif_time}")

    def check_random_sticker(self):
        current_time = time.strftime("%H:%M")
        
        if current_time == self.random_sticker_time:
            if self.last_sender_id == self.bot_id:
                print("Skip Sticker (Spam protection)")
                now = datetime.now()
                future_time = now + timedelta(minutes=30)
                self.random_sticker_time = future_time.strftime("%H:%M")
                print(f"New Sticker Time: {self.random_sticker_time}")
                return

            self.send_random_sticker()
            self.random_sticker_time = self.generate_random_time()
            print(f"Next Sticker: {self.random_sticker_time}")

    def send_random_gif(self):
        try:
            gif_id = random.choice(GIF_LIST)
            msg = self.bot.send_animation(TARGET_CHAT_ID, gif_id, caption="")
            self.remember_message(msg)
        except Exception as e:
            print(f"Random Gif Error: {e}")

    def send_random_sticker(self):
        try:
            pack_name = random.choice(STICKER_PACKS)
            sticker_set = self.bot.get_sticker_set(pack_name)
            
            if sticker_set and sticker_set.stickers:
                random_sticker = random.choice(sticker_set.stickers)
                msg = self.bot.send_sticker(TARGET_CHAT_ID, random_sticker.file_id)
                self.remember_message(msg)
                print(f"Sticker sent from: {pack_name}")
            else:
                print(f"Pack error: {pack_name}")
                
        except Exception as e:
            print(f"Sticker Error: {e}")

    def remember_message(self, sent_message):
        if sent_message:
            self.my_message_ids.append(sent_message.message_id)
            if len(self.my_message_ids) > 100: self.my_message_ids.pop(0)
            self.last_sender_id = self.bot_id

    def register_handlers(self):
        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            if not message.text: return
            text = message.text.lower()
            chat_id = message.chat.id
            user_id = message.from_user.id
            name = message.from_user.first_name

            self.last_sender_id = user_id
            print(f"User: {name} | Text: {text}")

            if text == "хуй":
                now = datetime.now()
                last_used = self.number_cooldowns.get(user_id)

                if last_used and now - last_used < timedelta(hours=12):
                    remaining = timedelta(hours=12) - (now - last_used)
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    msg = self.bot.send_message(chat_id, f"Блять ти шо вобще? Время ше не пройшло, подожди ше {hours} год {minutes} хв.")
                    self.remember_message(msg)
                    return

                random_num = round(random.uniform(-30.0, 40.0), 1)
                
                comment = ""
                if random_num < 0:
                    comment = "Хуй в жопі, пітушара блять🥶"
                elif random_num == 0:
                    comment = "🫤"
                elif 0.1 <= random_num <= 1.0:
                    comment = "Ахаха лох єбаний🤣"
                elif 1.1 <= random_num <= 5.0:
                    comment = "Ну парінь це якось не серйозно😒"
                elif 5.1 <= random_num <= 10.0:
                    comment = "Ніплох"
                elif 10.1 <= random_num <= 17.0:
                    comment = "Нармалди😎"
                elif 17.1 <= random_num <= 30.0:
                    comment = "Оце болтяра😯"
                elif 30.1 <= random_num <= 50.0:
                    comment = "Вотетаніхуясібє😨"

                msg = self.bot.send_message(chat_id, f"👨🏿 {name}, твій хуй: {random_num} см\n {comment} ")
                self.remember_message(msg)
                
                self.number_cooldowns[user_id] = now
                return

            if text == "ч г":
                self.bot.send_message(chat_id, f"Г: {self.random_gif_time}")
                return

            if text == "ч с":
                self.bot.send_message(chat_id, f"C: {self.random_sticker_time}")
                return

            pattern = r"(\d+[.,]?\d*)\s*([а-яА-Яa-zA-Z$€]+)\s+(?:в|у|in|to)\s+([а-яА-Яa-zA-Z$€]+)"
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

            if re.search(r"\bопа+\b", text):
                try:
                    msg = self.bot.send_video(chat_id, OPA_VIDEO_ID, caption="")
                    self.remember_message(msg)
                except Exception as e: print(e)

            if text == "курс":
                msg = self.bot.send_message(chat_id, CurrencyProvider.get_rates_message(None), parse_mode="Markdown")
                self.remember_message(msg)
            elif text in ["usd", "долар", "dollar", "$"]:
                msg = self.bot.send_message(chat_id, CurrencyProvider.get_rates_message('USD'), parse_mode="Markdown")
                self.remember_message(msg)
            elif text in ["eur", "євро", "euro", "€"]:
                msg = self.bot.send_message(chat_id, CurrencyProvider.get_rates_message('EUR'), parse_mode="Markdown")
                self.remember_message(msg)
            
            if text in ["id", "айді", "мій id"]:
                msg = self.bot.reply_to(message, f"Твій ID: `{user_id}`", parse_mode="Markdown")
                self.remember_message(msg)

            if "мері крісмас" in text:
                try:
                    msg = self.bot.send_video(chat_id, VIDEO_FILE_ID, caption="👀")
                    self.remember_message(msg)
                except Exception as e: print(e)

            if "сосав?" in text:
                try:
                    msg = self.bot.send_message(chat_id, "Канєшно🤤")
                    self.remember_message(msg)
                except Exception as e: print(e)

            if "статус" in text:
                status = USER_STATUSES.get(user_id, DEFAULT_STATUS)
                msg = self.bot.send_message(chat_id, f"👤 *{name}*, статус: `{status}`", parse_mode="Markdown")
                self.remember_message(msg)
            
            if "гіф" in text:
                self.send_random_gif()
            if "стікер" in text:
                self.send_random_sticker()

#    def send_daily_message(self):
#        try:
#            msg = self.bot.send_message(TARGET_CHAT_ID, "Мері крісмас🎄👙 @Sasik0809")
#            self.remember_message(msg)
#            print("Daily message sent")
#        except Exception as e:
#            print(f"Daily Message Error: {e}")

    def start(self):
        self.bot.infinity_polling()

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

if __name__ == "__main__":
    my_bot = MyBot()
    threading.Thread(target=run_scheduler).start()
    threading.Thread(target=my_bot.start).start()
    run_flask()








