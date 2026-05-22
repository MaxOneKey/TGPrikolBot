import telebot
import os
import sqlite3
import threading
from telebot import types
from flask import Flask

# Наполегливо рекомендую перенести токен у змінні середовища Render!
TOKEN = os.environ.get('BOT_TOKEN')
TOKEN = '8236217660:AAHGeDEer-h-CoJKvFwRrd6iFvFPFES6dKg'
ADMIN_IDS = [1859027118, 913802232]

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Створюємо файл бази та таблицю автоматично при запуску, якщо їх немає
def init_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stickers.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tags (tag TEXT, file_id TEXT)')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 1. КОМАНДА ДЛЯ ЗБЕРЕЖЕННЯ БАЗИ ДАНИХ
# ==========================================
@bot.message_handler(commands=['backup'])
def send_backup(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stickers.db')
    if os.path.exists(db_path):
        with open(db_path, 'rb') as doc:
            bot.send_document(
                message.chat.id, 
                doc, 
                caption="📦 Ось твоя актуальна база стікерів (`stickers.db`).\n\n"
                        "Збережи її, якщо плануєш оновлювати бота на Render.",
                parse_mode="Markdown"
            )
    else:
        bot.send_message(message.chat.id, "❌ Файл бази даних ще не створено або він порожній.")


# ==========================================
# 2. УПРАВЛІННЯ СТІКЕРАМИ (АДМІНКА)
# ==========================================
@bot.message_handler(commands=['add', 'del', 'edit', 'look'])
def admin_commands(message):
    if message.from_user.id not in ADMIN_IDS:
        return 
    
    command = message.text.split()[0]
    msg = bot.send_message(message.chat.id, "Надішли стікер:")
    bot.register_next_step_handler(msg, process_sticker_step, command)

def process_sticker_step(message, command):
    if message.content_type != 'sticker':
        bot.send_message(message.chat.id, "Це не стікер. Операцію скасовано.")
        return

    file_id = message.sticker.file_id
    
    if command == '/add':
        text_prompt = "Введи тег(и) для ДОДАВАННЯ (через кому):"
    elif command == '/del':
        text_prompt = "Введи тег(и) для ВИДАЛЕННЯ (через кому),\nАБО напиши слово 'все', щоб повністю видалити цей стікер з бази:"
    elif command == '/edit':
        text_prompt = "Введи НОВІ теги для цього стікера (всі старі будуть стерті, вводь через кому):"
    elif command == '/look':
        text_prompt = "Напиши букву щоб продовжити"
    if "сосав?" in text:
        try:
            msg = self.bot.send_message(chat_id, "Канєшно🤤")
            self.remember_message(msg)
        except Exception as e: print(e)
            
    msg = bot.send_message(message.chat.id, text_prompt)
    bot.register_next_step_handler(msg, process_tags_step, command, file_id)

def process_tags_step(message, command, file_id):
    if message.content_type != 'text':
        bot.send_message(message.chat.id, "Треба текст. Операцію скасовано.")
        return
        
    tags = [t.strip().lower() for t in message.text.split(',') if t.strip()]
    user_text = message.text.lower().strip()
    
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stickers.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        if command == '/add':
            for tag in tags:
                c.execute("INSERT INTO tags (tag, file_id) VALUES (?, ?)", (tag, file_id))
            bot.send_message(message.chat.id, f"Додано нові теги: {', '.join(tags)}")

        elif command == '/del':
            if user_text == 'все':
                c.execute("DELETE FROM tags WHERE file_id = ?", (file_id,))
                bot.send_message(message.chat.id, "🗑 Стікер та всі його теги видалено з бази.")
            else:
                for tag in tags:
                    c.execute("DELETE FROM tags WHERE file_id = ? AND tag = ?", (file_id, tag))
                bot.send_message(message.chat.id, f"🗑 Видалено теги: {', '.join(tags)}")

        elif command == '/edit':
            c.execute("DELETE FROM tags WHERE file_id = ?", (file_id,))
            for tag in tags:
                c.execute("INSERT INTO tags (tag, file_id) VALUES (?, ?)", (tag, file_id))
            bot.send_message(message.chat.id, f"Теги стікера змінено на: {', '.join(tags)}")

        elif command == '/look':
            c.execute("SELECT tag FROM tags WHERE file_id = ?", (file_id,))
            rows = c.fetchall()
            if rows:
                tags_list = ", ".join([row[0] for row in rows])
                bot.send_message(message.chat.id, f"Теги стікера:\n{tags_list}")
            else:
                bot.send_message(message.chat.id, "Стікера немає в базі (тегів не знайдено).")

        conn.commit()
        conn.close()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка бази даних: {e}")


# ==========================================
# 3. ІНЛАЙН ПОШУК СТІКЕРІВ
# ==========================================
@bot.inline_handler(func=lambda query: len(query.query.strip()) > 1)
def handle_inline_stickers(inline_query):
    search_term = inline_query.query.lower().strip()
    
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stickers.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT file_id FROM tags WHERE tag LIKE ?", (f'%{search_term}%',))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return 
    
        matched_file_ids = [row[0] for row in rows]
        results = []
       
        for idx, file_id in enumerate(list(set(matched_file_ids))[:50]): 
            results.append(
                types.InlineQueryResultCachedSticker(
                    id=str(idx),
                    sticker_file_id=file_id
                )
            )

        bot.answer_inline_query(inline_query.id, results, cache_time=1, is_personal=True)
        
    except Exception as e:
        print(f"Inline Query Error: {e}")


# ==========================================
# 4. ЗАПУСК БОТА ТА СЕРВЕРА
# ==========================================
@app.route('/')
def index(): 
    return "Sticker Bot is running..."

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Запускаємо веб-сервер у фоновому потоці для Render
    threading.Thread(target=run_flask).start()
    # Запускаємо самого бота
    bot.infinity_polling(allowed_updates=['message', 'inline_query'])
