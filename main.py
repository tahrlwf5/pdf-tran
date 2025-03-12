import os
import pdfkit
import tempfile
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

TOKEN = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"

def translate_html(html_content):
    """ترجمة محتوى HTML من الإنجليزية إلى العربية مع الحفاظ على التصميم."""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup.find_all(string=True):
        if tag.parent.name not in ["script", "style"]:
            tag.replace_with(GoogleTranslator(source="en", target="ar").translate(tag))
    return str(soup)

def handle_html(update: Update, context: CallbackContext):
    """استقبال ملفات HTML، ترجمتها، وإرسالها للمستخدم."""
    file = context.bot.get_file(update.message.document.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_html:
        file.download(temp_html.name)
        with open(temp_html.name, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        translated_html = translate_html(html_content)

        translated_file = temp_html.name.replace(".html", "_translated.html")
        with open(translated_file, "w", encoding="utf-8") as f:
            f.write(translated_html)

        context.bot.send_document(update.message.chat_id, document=open(translated_file, "rb"))
        os.remove(translated_file)

def handle_pdf(update: Update, context: CallbackContext):
    """استقبال ملفات PDF، تحويلها إلى HTML، ترجمتها، ثم تحويلها إلى PDF وإرسالها للمستخدم."""
    file = context.bot.get_file(update.message.document.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        file.download(temp_pdf.name)
        html_output = temp_pdf.name.replace(".pdf", ".html")

        subprocess.run(["pdf2htmlEX", "--zoom", "1.3", temp_pdf.name, html_output])

        with open(html_output, "r", encoding="utf-8") as f:
            html_content = f.read()

        translated_html = translate_html(html_content)

        translated_html_file = html_output.replace(".html", "_translated.html")
        with open(translated_html_file, "w", encoding="utf-8") as f:
            f.write(translated_html)

        pdf_output = translated_html_file.replace(".html", "_translated.pdf")
        pdfkit.from_file(translated_html_file, pdf_output)

        context.bot.send_document(update.message.chat_id, document=open(pdf_output, "rb"))

        os.remove(temp_pdf.name)
        os.remove(html_output)
        os.remove(translated_html_file)
        os.remove(pdf_output)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحبًا! أرسل لي ملف HTML أو PDF لترجمته إلى العربية.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("text/html"), handle_html))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
