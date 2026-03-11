import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8690782724:AAEmcspxm2RqioaD-zBqgzwqi40Jg-sjwxA"
ANTHROPIC_API_KEY = "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"

SYSTEM_PROMPT = "Ты профессиональный Suno AI агент. Помогаешь: 1) создавать style tags промты для Suno на английском 2) писать промты для Suno Studio с тегами [Verse][Chorus][Bridge] 3) писать тексты песен 4) советовать аранжировки. Отвечай на русском."

user_histories = {}

def ask_claude(messages):
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514", "max_tokens": 1000, "system": SYSTEM_PROMPT, "messages": messages})
    return r.json()["content"][0]["text"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Привет! Я твой Suno AI агент\n\n🎵 /song — промт для песни\n🎛 /studio — Suno Studio\n✍️ /lyrics — текст песни\n🎼 /arrangement — аранжировка\n🗑 /clear — очистить историю")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("🗑 Очищено!")

async def song_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Опиши песню — жанр, настроение, тему:")

async def studio_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎛 Опиши песню для Suno Studio:")

async def lyrics_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ О чём песня? Жанр и язык:")

async def arrangement_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎼 Опиши идею для аранжировки:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": update.message.text})
    msg = await update.message.reply_text("🎵 Создаю...")
    try:
        reply = ask_claude(user_histories[user_id])
        user_histories[user_id].append({"role": "assistant", "content": reply})
        await msg.delete()
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
    except Exception as e:
        await msg.delete()
        await update.message.reply_text(f"Ошибка: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("song", song_mode))
    app.add_handler(CommandHandler("studio", studio_mode))
    app.add_handler(CommandHandler("lyrics", lyrics_mode))
    app.add_handler(CommandHandler("arrangement", arrangement_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
