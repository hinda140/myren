import os
from io import BytesIO
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from PIL import Image
from huggingface_hub import InferenceClient

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# PRIVATE LOCK - leave empty now, add your ID later to make private
# Example: [123456789]
ALLOWED_USER_IDS = []

# Best realistic model
MODEL_ID = "SG161222/Realistic_Vision_V5.1_noVAE"

client = InferenceClient(token=HF_TOKEN)

PROMPT = "photorealistic architectural render, V-Ray quality, realistic PBR materials, natural lighting, soft shadows, 8k, ultra detailed, high quality"
NEGATIVE = "blurry, low quality, cartoon, distorted geometry, deformed"

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ Private bot. Access denied.")
        return

    await update.message.reply_text("⏳ Rendering with Hugging Face... 15 sec... (keeping same geometry)")

    try:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = BytesIO(await photo_file.download_as_bytearray())
        input_image = Image.open(image_bytes).convert("RGB")
        input_image = input_image.resize((768, 768))

        # RENDER - strength 0.35 keeps geometry 100%
        rendered = client.image_to_image(
            image=input_image,
            prompt=PROMPT,
            negative_prompt=NEGATIVE,
            model=MODEL_ID,
            strength=0.35,
            num_inference_steps=30,
            guidance_scale=7.5
        )

        # Send back
        bio = BytesIO()
        rendered.save(bio, format='JPEG')
        bio.seek(0)

        await update.message.reply_photo(photo=bio, caption="✅ Done! Same geometry, photorealistic!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}\nTry again, HF model is loading (wait 30 sec).")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me your SketchUp screenshot and I will render it photorealistically!")

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.COMMAND, start))

print("Bot is running - WAY 1 HF...")
app.run_polling()
