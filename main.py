import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from googletrans import Translator
from pdfminer.high_level import extract_text

# تهيئة المترجم
translator = Translator()

# أوامر البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text('مرحبًا! أرسل لي ملف HTML أو PDF لأقوم بترجمته إلى العربية.')

def handle_file(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    file_name = update.message.document.file_name
    file.download(file_name)

    if file_name.lower().endswith('.html'):
        handle_html(update, file_name)
    elif file_name.lower().endswith('.pdf'):
        handle_pdf(update, file_name)
    else:
        update.message.reply_text('الملف غير مدعوم. يرجى إرسال ملف HTML أو PDF.')

def handle_html(update: Update, file_name: str):
    with open(file_name, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # ترجمة النص (يمكن تحسين هذه العملية)
    translated = translator.translate(html_content, src='en', dest='ar').text

    # حفظ الملف المترجم
    translated_file_name = f"translated_{file_name}"
    with open(translated_file_name, 'w', encoding='utf-8') as f:
        f.write(translated)

    # إرسال الملف المترجم
    update.message.reply_document(document=open(translated_file_name, 'rb'))

def handle_pdf(update: Update, file_name: str):
    # تحويل PDF إلى نص
    text = extract_text(file_name)
    
    # تحويل النص إلى HTML (مثال بسيط)
    html_content = f"<html><body><pre>{text}</pre></body></html>"
    
    # ترجمة HTML
    translated_html = translator.translate(html_content, src='en', dest='ar').text
    
    # حفظ الملف المترجم
    translated_file_name = f"translated_{file_name.replace('.pdf', '.html')}"
    with open(translated_file_name, 'w', encoding='utf-8') as f:
        f.write(translated_html)
    
    # إرسال الملف المترجم
    update.message.reply_document(document=open(translated_file_name, 'rb'))

def main():
    TOKEN = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
