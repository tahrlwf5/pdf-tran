import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ضع هنا توكن بوت التليجرام الخاص بك
TELEGRAM_TOKEN = "6016945663:AAHjacRdRfZ2vUgS2SLmoFgHfMdUye4l6bA"

# API Secret من ConvertAPI
CONVERTAPI_SECRET = "secret_IeaPYONWS1Xf1Re4"

# تهيئة logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "مرحباً! أرسل لي ملف PDF أو DOCX وسأقوم بتحويله إلى HTML باستخدام convertapi.com."
    )

async def convert_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    file_name = document.file_name.lower()

    if not (file_name.endswith('.pdf') or file_name.endswith('.docx')):
        await update.message.reply_text("❌ يرجى إرسال ملف PDF أو DOCX فقط.")
        return

    # تحميل الملف من تليجرام
    file = await document.get_file()
    os.makedirs("downloads", exist_ok=True)
    local_path = os.path.join("downloads", file_name)
    await file.download_to_drive(local_path)
    await update.message.reply_text("📤 تم استلام الملف، جارٍ تحويله إلى HTML...")

    # تحديد نوع التحويل بناءً على امتداد الملف
    convert_type = "pdf" if file_name.endswith('.pdf') else "docx"

    # استدعاء دالة التحويل
    html_file_path = convert_file(local_path, convert_type)
    if html_file_path:
        await update.message.reply_text("✅ تم التحويل بنجاح، يتم إرسال الملف...")
        with open(html_file_path, 'rb') as html_file:
            await update.message.reply_document(document=html_file)
    else:
        await update.message.reply_text("⚠️ حدث خطأ أثناء عملية التحويل. تحقق من نوع الملف وحاول مرة أخرى.")

def convert_file(file_path: str, convert_type: str) -> str:
    """
    ترسل هذه الدالة الملف إلى ConvertAPI لتحويله إلى HTML.
    """
    url = f"https://v2.convertapi.com/convert/{convert_type}/to/html?Secret={CONVERTAPI_SECRET}"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'File': f}
            response = requests.post(url, files=files)
        
        response_json = response.json()
        
        # 🛑 طباعة الاستجابة في السجل لمعرفة ما الخطأ
        logger.info("🔍 ConvertAPI Response: %s", response_json)

        if response.status_code != 200 or "Files" not in response_json:
            logger.error("🚨 API Error: %s", response_json)
            return None
        
        file_url = response_json["Files"][0].get("Url")
        if not file_url:
            logger.error("❌ No URL found in API response: %s", response_json)
            return None

        # تحميل ملف HTML
        html_response = requests.get(file_url)
        output_file = file_path.rsplit('.', 1)[0] + '.html'
        with open(output_file, 'wb') as f:
            f.write(html_response.content)

        return output_file
    except Exception as e:
        logger.exception("Exception during file conversion:")
        return None

def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, convert_document))

    # بدء البوت باستخدام polling
    app.run_polling()

if __name__ == '__main__':
    main()
