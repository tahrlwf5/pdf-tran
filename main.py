import os
import logging
import pdfkit
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
from googletrans import Translator

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء مثيل للمترجم
translator = Translator()

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "مرحباً، أرسل لي ملف HTML لأقوم بترجمته من الإنجليزية إلى العربية وتحويله إلى PDF."
    )

def translate_html(file_path: str) -> str:
    """
    تقرأ الملف، تقوم بتحليل الـ HTML وترجمة النصوص من الإنجليزية إلى العربية.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    
    # المرور على جميع العقد النصية وترجمتها
    for element in soup.find_all(text=True):
        original_text = element.strip()
        if original_text:
            try:
                # ترجمة النص من الإنجليزية إلى العربية
                translated_text = translator.translate(original_text, src='en', dest='ar').text
                element.replace_with(translated_text)
            except Exception as e:
                logger.error(f"حدث خطأ أثناء الترجمة: {e}")
    return str(soup)

def handle_file(update: Update, context: CallbackContext):
    document = update.message.document
    if document and document.file_name.endswith('.html'):
        # تحميل الملف
        file_id = document.file_id
        new_file = context.bot.get_file(file_id)
        original_file_path = document.file_name
        new_file.download(custom_path=original_file_path)
        logger.info("تم تحميل الملف إلى %s", original_file_path)
        
        # ترجمة محتوى HTML
        translated_html = translate_html(original_file_path)
        
        # حفظ الملف المترجم كملف HTML مؤقت
        temp_translated_html_path = f"translated_{original_file_path}"
        with open(temp_translated_html_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
            
        # تحويل الملف المترجم من HTML إلى PDF باستخدام pdfkit
        base_name = os.path.splitext(original_file_path)[0]
        translated_pdf_path = f"translated_{base_name}.pdf"
        try:
            pdfkit.from_file(temp_translated_html_path, translated_pdf_path)
        except Exception as e:
            update.message.reply_text(f"حدث خطأ أثناء تحويل HTML إلى PDF: {e}")
            os.remove(original_file_path)
            os.remove(temp_translated_html_path)
            return
        
        # إرسال ملف PDF المترجم إلى المستخدم
        context.bot.send_document(
            chat_id=update.message.chat_id, 
            document=open(translated_pdf_path, 'rb')
        )
        
        # حذف الملفات المؤقتة
        os.remove(original_file_path)
        os.remove(temp_translated_html_path)
        os.remove(translated_pdf_path)
    else:
        update.message.reply_text("يرجى إرسال ملف بصيغة HTML فقط.")

def main():
    # ضع هنا توكن البوت الخاص بك
    token = "6334414905:AAGdBEBDfiY7W9Nhyml1wHxSelo8gfpENR8"
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
