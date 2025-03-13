import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# Config
API_SECRET = "secret_27IPh66mBqBmKUkN"
TOKEN = "6016945663:AAFqyBCgCguvPzjHDzVNubNH1VCGT7c1j34"  # استبدل به التوكن الخاص بك

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

        # إرسال النتيجة
        result = response.json()
        html_url = result["Files"][0]["Url"]
        html_content = requests.get(html_url).content

        await update.message.reply_document(
            document=InputFile(html_content, filename="converted.html"),
            caption="✅ تم التحويل بنجاح!"
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء التحويل!")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()
