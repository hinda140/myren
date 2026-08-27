import os, asyncio, io, tempfile
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient
from PIL import Image

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

client = InferenceClient(token=HF_TOKEN, provider="hf-inference")
MODEL = "timbrooks/instruct-pix2pix"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Send SketchUp - photorealistic render!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Rendering... 30 sec ⏳")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        buf = io.BytesIO()
        await file.download_to_memory(buf)
        buf.seek(0)
        image = Image.open(buf).convert("RGB")
        image.thumbnail((768, 768))
        
        # Save to temp file for HF
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            image.save(tmp.name, format="JPEG")
            tmp_path = tmp.name
            
        prompt = "make it photorealistic, modern architecture interior, realistic lighting, ultra detailed, 8k"
        result = client.image_to_image(tmp_path, prompt=prompt, model=MODEL)
        
        out = io.BytesIO()
        result.save(out, format="JPEG")
        out.seek(0)
        await update.message.reply_photo(photo=out, caption="✅ Photorealistic render!")
        os.remove(tmp_path)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot running")
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
