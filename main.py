import os, asyncio, io, requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "runwayml/stable-diffusion-v1-5"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Send SketchUp - I make photorealistic!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Rendering photorealistic... 25 sec ⏳")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        buf = io.BytesIO()
        await file.download_to_memory(buf)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
        img.thumbnail((768, 768))
        
        # Convert to bytes for HF
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        # HF image-to-image needs image + prompt via inference
        # We use img2img with prompt
        data = img_byte_arr.getvalue()
        # Call with prompt as parameter
        response = requests.post(
            API_URL,
            headers=headers,
            params={"prompt": "photorealistic architecture, modern interior, ultra realistic, 8k, professional lighting, detailed"},
            data=data,
            timeout=60
        )
        
        if response.status_code != 200:
            await update.message.reply_text(f"HF Error {response.status_code}: {response.text[:200]}")
            return
            
        out = io.BytesIO(response.content)
        await update.message.reply_photo(photo=out, caption="✅ Your photorealistic render!")
        
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
