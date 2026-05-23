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


@bot.message_handler(func=lambda message: message.text and "сосав?" in message.text.lower())
def check_ping(message):
    bot.send_message(message.chat.id, "Канєшно🤤")


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
# ==========================================
# 5. СЛУЖБОВІ КОМАНДИ ДЛЯ СТАРОЇ БАЗИ
# ==========================================

@bot.message_handler(commands=['fixdb'])
def fix_database(message):
    if message.from_user.id not in ADMIN_IDS: return
    
    bot.send_message(message.chat.id, "🛠 Починаю глибоку діагностику бази...")
    
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stickers.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 1. Перевірка колонок
        c.execute("PRAGMA table_info(tags)")
        columns = [col[1] for col in c.fetchall()]
        bot.send_message(message.chat.id, f"📊 Колонки в базі: {', '.join(columns)}")
        
        # 2. Рахуємо загальну кількість записів
        c.execute("SELECT COUNT(*) FROM tags")
        total_rows = c.fetchone()[0]
        
        # 3. Рахуємо записи без file_unique_id
        if 'file_unique_id' in columns:
            c.execute("SELECT COUNT(DISTINCT file_id) FROM tags WHERE file_unique_id IS NULL OR file_unique_id = ''")
            needs_fix_count = c.fetchone()[0]
        else:
            needs_fix_count = "Невідомо (немає колонки)"
            
        bot.send_message(message.chat.id, f"📈 Всього тегів у базі: {total_rows}\n⚠️ Унікальних стікерів, яким бракує нового ID: {needs_fix_count}")

        if needs_fix_count == 0 or type(needs_fix_count) == str:
            bot.send_message(message.chat.id, "🛑 Зупиняю роботу: оновлювати нічого, або колонки не існує.")
            conn.close()
            return

        # 4. Пробуємо оновити
        c.execute("SELECT DISTINCT file_id FROM tags WHERE file_unique_id IS NULL OR file_unique_id = ''")
        rows = c.fetchall()
        
        fixed_count = 0
        errors = []
        
        bot.send_message(message.chat.id, "🔄 Звертаюсь до серверів Telegram за новими ID...")
        
        for row in rows:
            fid = row[0]
            try:
                file_info = bot.get_file(fid)
                unique_id = file_info.file_unique_id
                c.execute("UPDATE tags SET file_unique_id = ? WHERE file_id = ?", (unique_id, fid))
                fixed_count += 1
            except Exception as e:
                err_msg = str(e)
                if err_msg not in errors:
                    errors.append(err_msg) # Зберігаємо унікальні помилки, щоб не спамити

        conn.commit()
        conn.close()
        
        # 5. Звіт
        report = f"✅ Успішно оновлено стікерів: {fixed_count} з {needs_fix_count}.\n"
        if errors:
            report += f"\n❌ Помилки від Telegram (чому інші не оновились):\n" + "\n".join(errors)
            
        bot.send_message(message.chat.id, report)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Критична помилка скрипта: {e}")

@bot.message_handler(commands=['dump'])
def dump_stickers(message):
    if message.from_user.id not in ADMIN_IDS: return
    
    bot.send_message(message.chat.id, "📦 Вивантажую всі збережені стікери та їх теги в чат...")
    
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stickers.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT DISTINCT file_id FROM tags")
        rows = c.fetchall()
        
        for row in rows:
            fid = row[0]
            c.execute("SELECT tag FROM tags WHERE file_id = ?", (fid,))
            tags = [t[0] for t in c.fetchall()]
            
            try:
                # Бот фізично надсилає тобі стікер і пише, які теги до нього прив'язані
                bot.send_sticker(message.chat.id, fid)
                bot.send_message(message.chat.id, f"☝️ Теги: {', '.join(tags)}")
                time.sleep(0.3) # Затримка, щоб Телеграм не заблокував бота за спам
            except:
                pass
                
        conn.close()
        bot.send_message(message.chat.id, "✅ Вивантаження бази завершено.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Помилка: {e}")


if __name__ == "__main__":
    # Запускаємо веб-сервер у фоновому потоці для Render
    threading.Thread(target=run_flask).start()
    # Запускаємо самого бота
    bot.infinity_polling(allowed_updates=['message', 'inline_query'])
