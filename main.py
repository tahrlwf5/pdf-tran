import os
import logging
import pdfkit
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# استبدل `YOUR_BOT_TOKEN` بتوكن البوت الخاص بك
TOKEN = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"

# تحديد مسار `wkhtmltopdf`
config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")

# دالة ترجمة النصوص
def translate_text(text):
    translator = GoogleTranslator(source="en", target="ar")
    return translator.translate(text)

# دالة تحويل HTML إلى PDF بعد الترجمة
def html_to_translated_pdf(html_path, output_pdf_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # ترجمة النصوص داخل HTML
    for element in soup.find_all(text=True):
        translated_text = translate_text(element)
        element.replace_with(translated_text)

    translated_html_path = html_path.replace(".html", "_translated.html")
    with open(translated_html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    # تحويل HTML إلى PDF
    pdfkit.from_file(translated_html_path, output_pdf_path, configuration=config)

    # حذف الملف المؤقت
    os.remove(translated_html_path)

    return output_pdf_path

# معالجة ملفات HTML
async def handle_html(update: Update, context):
    file = update.message.document
    if not file.file_name.endswith(".html"):
        await update.message.reply_text("❌ يرجى إرسال ملف HTML فقط!")
        return

    await update.message.reply_text("📥 جاري تحميل الملف...")

    html_path = file.file_name
    output_pdf_path = html_path.replace(".html", "_translated.pdf")

    # تحميل الملف
    html_file = await file.get_file()
    await html_file.download_to_drive(html_path)

    try:
        # تحويل HTML إلى PDF مترجم
        translated_pdf_path = html_to_translated_pdf(html_path, output_pdf_path)
        await update.message.reply_text("✅ تم ترجمة الملف وتحويله إلى PDF بنجاح!")

        # إرسال ملف PDF المترجم
        with open(translated_pdf_path, "rb") as f:
            await update.message.reply_document(f)

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء الترجمة: {e}")

    # تنظيف الملفات المؤقتة
    os.remove(html_path)
    os.remove(translated_pdf_path)

# أمر /start
async def start(update: Update, context):
    await update.message.reply_text("👋 مرحبًا! أرسل لي ملف **HTML** وسأقوم بترجمته إلى العربية وتحويله إلى **PDF**.")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_html))

    app.run_polling()

if __name__ == "__main__":
    main()
