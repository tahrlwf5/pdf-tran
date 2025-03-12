import os
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
from googletrans import Translator
import pdfkit  # مكتبة جديدة مضافة

# إعدادات إضافية لـ pdfkit
path_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'  # تعديل المسار حسب نظامك
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

translator = Translator()

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً، أرسل لي ملف HTML لأقوم بترجمته من الإنجليزية إلى العربية وتحويله لـ PDF.")

def translate_html(file_path: str) -> str:
    """ترجمة محتوى HTML مع الحفاظ على الهيكل"""
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    
    for element in soup.find_all(text=True):
        if element.parent.name not in ['script', 'style'] and element.strip():
            try:
                translated = translator.translate(element, src='en', dest='ar').text
                element.replace_with(translated)
            except Exception as e:
                logger.error(f"خطأ في الترجمة: {e}")
                continue
    return str(soup)

def handle_file(update: Update, context: CallbackContext):
    if update.message.document.file_name.endswith('.html'):
        try:
            # تنزيل الملف
            file_id = update.message.document.file_id
            downloaded_file = context.bot.get_file(file_id)
            original_path = 'temp.html'
            downloaded_file.download(original_path)
            
            # ترجمة المحتوى
            translated_html_content = translate_html(original_path)
            
            # حفظ HTML المترجم مؤقتاً
            translated_html_path = 'translated.html'
            with open(translated_html_path, 'w', encoding='utf-8') as f:
                f.write(translated_html_content)
            
            # تحويل إلى PDF
            pdf_path = 'output.pdf'
            pdfkit.from_file(
                translated_html_path,
                pdf_path,
                configuration=config,
                options={'encoding': 'UTF-8'}
            )
            
            # إرسال PDF
            with open(pdf_path, 'rb') as f:
                update.message.reply_document(document=f)
            
            # تنظيف الملفات المؤقتة
            for path in [original_path, translated_html_path, pdf_path]:
                if os.path.exists(path):
                    os.remove(path)
                    
        except Exception as e:
            logger.error(f"خطأ رئيسي: {e}")
            update.message.reply_text("حدث خطأ أثناء المعالجة. يرجى المحاولة لاحقاً.")
    else:
        update.message.reply_text("❗ يرجى إرسال ملف HTML صالح (امتداد .html)")

def main():
    token = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
