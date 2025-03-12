import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from googletrans import Translator
from bs4 import BeautifulSoup
import subprocess
import os
import weasyprint

# استبدل 'YOUR_TELEGRAM_BOT_TOKEN' برمز API الخاص ببوتك
TOKEN = '6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8'

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="أرسل لي ملف HTML أو PDF لترجمته.")

def translate_html(update, context):
    file_id = update.message.document.file_id
    file_info = context.bot.get_file(file_id)
    downloaded_file = context.bot.download_file(file_info.file_path)
    file_name = "input.html"
    with open(file_name, "wb") as f:
        f.write(downloaded_file)

    with open(file_name, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    translator = Translator()
    for text in soup.find_all(text=True):
        if text.strip():
            try:
                translated_text = translator.translate(text, dest='ar').text
                text.replace_with(translated_text)
            except Exception as e:
                print(f"Translation error: {e}")

    output_file_name = "translated.html"
    with open(output_file_name, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    # Convert HTML to PDF
    pdf_file_name = "translated.pdf"
    weasyprint.HTML(output_file_name).write_pdf(pdf_file_name)

    context.bot.send_document(chat_id=update.effective_chat.id, document=open(pdf_file_name, 'rb'))
    os.remove(file_name)
    os.remove(output_file_name)
    os.remove(pdf_file_name)

def translate_pdf(update, context):
    file_id = update.message.document.file_id
    file_info = context.bot.get_file(file_id)
    downloaded_file = context.bot.download_file(file_info.file_path)
    pdf_file_name = "input.pdf"
    with open(pdf_file_name, "wb") as f:
        f.write(downloaded_file)

    # Convert PDF to HTML
    html_file_name = "output.html"
    subprocess.run(["pdf2htmlEX", pdf_file_name, html_file_name])

    # Translate HTML
    with open(html_file_name, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    translator = Translator()
    for text in soup.find_all(text=True):
        if text.strip():
            try:
                translated_text = translator.translate(text, dest='ar').text
                text.replace_with(translated_text)
            except Exception as e:
                print(f"Translation error: {e}")

    translated_html_file_name = "translated.html"
    with open(translated_html_file_name, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    # Convert translated HTML to PDF
    output_pdf_file_name = "translated.pdf"
    weasyprint.HTML(translated_html_file_name).write_pdf(output_pdf_file_name)

    context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_pdf_file_name, 'rb'))
    os.remove(pdf_file_name)
    os.remove(html_file_name)
    os.remove(translated_html_file_name)
    os.remove(output_pdf_file_name)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("text/html"), translate_html))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), translate_pdf))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
