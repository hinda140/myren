import os
import asyncio
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me SketchUp screenshot - I will convert to photorealistic render! 🏠✨")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Got it! Rendering... ⏳ 10 sec")
    # your render logic here - keep your existing code
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        # download and process with HF...
        await update.message.reply_text("Done! Here's your render (add your HF logic)")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def run_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot is running - WAY 1 HF...")
    app.run_polling()

# Dummy web server for Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    run_bot()
