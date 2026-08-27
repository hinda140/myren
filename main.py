import os, asyncio, io
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient
from PIL import Image
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# FREE model for SketchUp -> Realistic
 MODEL = "timbrooks/instruct-pix2pix"
client = InferenceClient(token=HF_TOKEN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Send me SketchUp screenshot - I will make it photorealistic! ✨")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Got it! Rendering photorealistic... ⏳ 20 sec")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = io.BytesIO()
        await file.download_to_memory(img_bytes)
        img_bytes.seek(0)
        image = Image.open(img_bytes).convert("RGB")
        
        # Render with AI
        prompt = "photorealistic architecture, ultra detailed, 8k, realistic lighting"
        result = client.image_to_image(image, prompt=prompt, model=MODEL)
        
        # Send back
        out_bio = io.BytesIO()
        result.save(out_bio, format="JPEG")
        out_bio.seek(0)
        await update.message.reply_photo(photo=out_bio, caption="✅ Here is your photorealistic render!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}\nCheck HF_TOKEN is valid")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot is running - WAY 1 HF...")
    app.run_polling()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot running")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    run_bot()
