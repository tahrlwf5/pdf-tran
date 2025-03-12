import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pdf2docx import Converter
from docx import Document
from deep_translator import GoogleTranslator

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# استبدل `YOUR_BOT_TOKEN` بتوكن البوت الخاص بك
TOKEN = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"

# دالة ترجمة النص من الإنجليزية إلى العربية
def translate_text(text):
    translator = GoogleTranslator(source="en", target="ar")
    return translator.translate(text)

# دالة تحويل PDF إلى HTML
def pdf_to_html(pdf_path, html_path):
    docx_path = pdf_path.replace(".pdf", ".docx")

    # تحويل PDF إلى DOCX
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()

    # تحويل DOCX إلى HTML
    doc = Document(docx_path)
    html_content = "<html><body>"
    for para in doc.paragraphs:
        translated_text = translate_text(para.text)  # ترجمة الفقرات
        html_content += f"<p>{translated_text}</p>"
    html_content += "</body></html>"

    # حفظ HTML المترجم
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # إزالة ملف DOCX المؤقت
    os.remove(docx_path)

    return html_path

# دالة ترجمة HTML
def translate_html(html_path, translated_html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    translated_content = translate_text(content)

    with open(translated_html_path, "w", encoding="utf-8") as f:
        f.write(translated_content)

    return translated_html_path

# معالجة ملفات PDF
async def handle_pdf(update: Update, context):
    file = update.message.document
    if not file.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ يرجى إرسال ملف PDF فقط!")
        return

    await update.message.reply_text("📥 جاري تحميل الملف...")
    pdf_path = file.file_name
    html_path = pdf_path.replace(".pdf", "_translated.html")

    # تحميل الملف
    pdf_file = await file.get_file()
    await pdf_file.download_to_drive(pdf_path)

    try:
        # تحويل PDF إلى HTML وترجمته
        translated_html_path = pdf_to_html(pdf_path, html_path)
        await update.message.reply_text("✅ تم تحويل وترجمة الملف بنجاح!")

        # إرسال ملف HTML المترجم
        with open(translated_html_path, "rb") as f:
            await update.message.reply_document(f)

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحويل: {e}")

    # تنظيف الملفات المؤقتة
    os.remove(pdf_path)
    os.remove(translated_html_path)

# معالجة ملفات HTML
async def handle_html(update: Update, context):
    file = update.message.document
    if not file.file_name.endswith(".html"):
        await update.message.reply_text("❌ يرجى إرسال ملف HTML فقط!")
        return

    await update.message.reply_text("📥 جاري تحميل الملف...")
    html_path = file.file_name
    translated_html_path = html_path.replace(".html", "_translated.html")

    # تحميل الملف
    html_file = await file.get_file()
    await html_file.download_to_drive(html_path)

    try:
        # ترجمة ملف HTML
        translate_html(html_path, translated_html_path)
        await update.message.reply_text("✅ تم ترجمة الملف بنجاح!")

        # إرسال ملف HTML المترجم
        with open(translated_html_path, "rb") as f:
            await update.message.reply_document(f)

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء الترجمة: {e}")

    # تنظيف الملفات المؤقتة
    os.remove(html_path)
    os.remove(translated_html_path)

# أمر /start
async def start(update: Update, context):
    await update.message.reply_text("👋 مرحبًا! أرسل لي ملف **PDF أو HTML** وسأقوم بترجمته إلى العربية.")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_html))

    app.run_polling()

if __name__ == "__main__":
    main()
