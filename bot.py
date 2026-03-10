import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — профессиональный Suno AI агент и музыкальный продюсер. Помогаешь пользователю:

1. ПРОМТЫ ДЛЯ SUNO — создаёшь style tags на английском для генерации музыки
   Формат: жанр, настроение, инструменты, темп, вокал через запятую
   Пример: "dreamy indie pop, melancholic female vocals, jangly guitar, lo-fi, 90s aesthetic"

2. SUNO STUDIO — пишешь полные промты со структурными тегами:
   [Intro], [Verse], [Pre-chorus], [Chorus], [Bridge], [Outro]
   [Guitar solo], [Beat drop], [Whispered], [Build up]

3. ТЕКСТЫ ПЕСЕН — пишешь тексты на русском или английском с разметкой структуры

4. АРАНЖИРОВКИ — советуешь инструментовку, динамику, слои звука

Всегда выдавай готовый промт отдельным блоком для удобного копирования.
Отвечай на русском языке если не просят иначе."""

user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 *Привет! Я твой Suno AI агент*\n\n"
        "Помогу тебе создавать музыку в Suno:\n\n"
        "🎵 /song — промт для песни\n"
        "🎛 /studio — промт для Suno Studio\n"
        "✍️ /lyrics — написать текст песни\n"
        "🎼 /arrangement — советы по аранжировке\n"
        "🗑 /clear — очистить историю чата\n\n"
        "Или просто напиши что хочешь создать!",
        parse_mode="Markdown"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("🗑 История очищена! Начнём заново.")

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode_text: str):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await handle_message_with_text(update, context, mode_text)

async def song_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Режим: *Промт для Suno*\nОпиши какую песню хочешь создать — жанр, настроение, тему:", parse_mode="Markdown")

async def studio_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎛 Режим: *Suno Studio*\nОпиши песню и я создам полную структуру с тегами [Verse][Chorus] и текстом:", parse_mode="Markdown")

async def lyrics_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Режим: *Текст песни*\nОпиши о чём должна быть песня, жанр и язык:", parse_mode="Markdown")

async def arrangement_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎼 Режим: *Аранжировка*\nОпиши свою идею и я помогу с инструментовкой и звуком:", parse_mode="Markdown")

async def handle_message_with_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    user_id = update.effective_user.id
    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": text})

    thinking_msg = await update.message.reply_text("🎵 Создаю...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )
        reply = response.content[0].text
        user_histories[user_id].append({"role": "assistant", "content": reply})

        await thinking_msg.delete()

        if len(reply) > 4000:
            parts = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        await thinking_msg.delete()
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_message_with_text(update, context, update.message.text)

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
