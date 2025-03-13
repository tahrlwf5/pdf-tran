import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# Config
API_SECRET = "secret_27IPh66mBqBmKUkN"  # استبدل بمفتاح API الخاص بك
TOKEN = "6016945663:AAFqyBCgCguvPzjHDzVNubNH1VCGT7c1j34"  # استبدل بتوكن البوت الخاص بك

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل ملف PDF أو DOCX لتحويله إلى HTML.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        return
    
    doc = update.message.document
    filename = doc.file_name or ""

    if not (filename.endswith('.pdf') or filename.endswith('.docx')):
        await update.message.reply_text("❗ الملف يجب أن يكون PDF أو DOCX!")
        return

    try:
        # تنزيل الملف
        file = await doc.get_file()
        content = await file.download_as_bytearray()

        # تحويل الصيغة
        convert_format = "pdf" if filename.endswith('.pdf') else "docx"
        api_url = f"https://v2.convertapi.com/convert/{convert_format}/to/html?Secret={API_SECRET}"
        
        response = requests.post(
            api_url,
            files={"File": (filename, bytes(content))}
        )
        response.raise_for_status()

        # معالجة الرد
        result = response.json()
        if not result.get('Files') or not result['Files'][0].get('Url'):
            await update.message.reply_text("❌ فشل التحويل: لم يتم العثور على ملف ناتج.")
            return

        # تنزيل HTML الناتج
        html_url = result['Files'][0]['Url']
        html_response = requests.get(html_url)
        html_response.raise_for_status()

        # إرسال النتيجة
        await update.message.reply_document(
            document=InputFile(html_response.content, filename="converted.html"),
            caption="✅ تم التحويل بنجاح!"
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء الاتصال بـ convertapi.com.")
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        await update.message.reply_text("❌ فشل التحويل: استجابة غير متوقعة من convertapi.com.")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling(drop_pending_updates=True)
