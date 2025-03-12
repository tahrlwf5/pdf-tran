import os
import logging
import pdfkit
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pdf2docx import Converter
from docx import Document
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# استبدل `YOUR_BOT_TOKEN` بتوكن البوت الخاص بك
TOKEN = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"

# إعداد خيارات PDFKit (لتحديد مسار wkhtmltopdf)
pdf_options = {
    "enable-local-file-access": None
}

# دالة ترجمة النصوص مع الحفاظ على التصميم
def translate_html_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    translator = GoogleTranslator(source="en", target="ar")

    for element in soup.find_all(text=True):
        if element.strip():  # تجنب النصوص الفارغة
            try:
                translated_text = translator.translate(element)
                element.replace_with(translated_text)
            except Exception as e:
                logger.error(f"خطأ في الترجمة: {e}")

    return str(soup)

# تحويل PDF إلى HTML، ترجمته، ثم تحويله إلى PDF
def pdf_to_translated_pdf(pdf_path, output_pdf_path):
    docx_path = pdf_path.replace(".pdf", ".docx")
    html_path = pdf_path.replace(".pdf", ".html")

    # تحويل PDF إلى DOCX
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()

    # تحويل DOCX إلى HTML مترجم
    doc = Document(docx_path)
    html_content = "<html><body>"
    for para in doc.paragraphs:
        translated_text = GoogleTranslator(source="en", target="ar").translate(para.text)
        html_content += f"<p>{translated_text}</p>"
    html_content += "</body></html>"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # تحويل HTML إلى PDF
    pdfkit.from_file(html_path, output_pdf_path, options=pdf_options)

    # تنظيف الملفات المؤقتة
    os.remove(docx_path)
    os.remove(html_path)

    return output_pdf_path

# تحويل HTML إلى PDF مع الحفاظ على التصميم
def html_to_translated_pdf(html_path, output_pdf_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    translated_html_content = translate_html_content(html_content)
    translated_html_path = html_path.replace(".html", "_translated.html")

    with open(translated_html_path, "w", encoding="utf-8") as f:
        f.write(translated_html_content)

    # تحويل HTML إلى PDF
    pdfkit.from_file(translated_html_path, output_pdf_path, options=pdf_options)

    # تنظيف الملفات المؤقتة
    os.remove(translated_html_path)

    return output_pdf_path

# معالجة ملفات PDF
async def handle_pdf(update: Update, context):
    file = update.message.document
    if not file.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ يرجى إرسال ملف PDF فقط!")
        return

    await update.message.reply_text("📥 جاري تحميل الملف...")
    pdf_path = file.file_name
    output_pdf_path = pdf_path.replace(".pdf", "_translated.pdf")

    pdf_file = await file.get_file()
    await pdf_file.download_to_drive(pdf_path)

    try:
        translated_pdf_path = pdf_to_translated_pdf(pdf_path, output_pdf_path)
        await update.message.reply_text("✅ تم تحويل وترجمة الملف بنجاح!")

        with open(translated_pdf_path, "rb") as f:
            await update.message.reply_document(f)

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحويل: {e}")

    os.remove(pdf_path)
    os.remove(translated_pdf_path)

# معالجة ملفات HTML
async def handle_html(update: Update, context):
    file = update.message.document
    if not file.file_name.endswith(".html"):
        await update.message.reply_text("❌ يرجى إرسال ملف HTML فقط!")
        return

    await update.message.reply_text("📥 جاري تحميل الملف...")
    html_path = file.file_name
    output_pdf_path = html_path.replace(".html", "_translated.pdf")

    html_file = await file.get_file()
    await html_file.download_to_drive(html_path)

    try:
        translated_pdf_path = html_to_translated_pdf(html_path, output_pdf_path)
        await update.message.reply_text("✅ تم ترجمة الملف وتحويله إلى PDF بنجاح!")

        with open(translated_pdf_path, "rb") as f:
            await update.message.reply_document(f)

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء الترجمة: {e}")

    os.remove(html_path)
    os.remove(translated_pdf_path)

# أمر /start
async def start(update: Update, context):
    await update.message.reply_text("👋 مرحبًا! أرسل لي ملف **PDF أو HTML** وسأقوم بترجمته إلى العربية وتحويله إلى **PDF**.")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_html))

    app.run_polling()

if __name__ == "__main__":
    main()
