import os
import logging
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
    update.message.reply_text("مرحباً، أرسل لي ملف HTML لأقوم بترجمته من الإنجليزية إلى العربية. \n البوت تابع ل@i2pdfbot \n@ta_ja199 لاستفسار راسل ")

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
        update.message.reply_text("✅ جاري معالجة الملف، يرجى الانتظار...")

        file_id = document.file_id
        new_file = context.bot.get_file(file_id)
        original_file_path = document.file_name
        new_file.download(custom_path=original_file_path)
        logger.info("تم تحميل الملف إلى %s", original_file_path)
        
        # ترجمة محتوى HTML
        translated_html = translate_html(original_file_path)
        
        # حفظ الملف المترجم
        translated_file_path = f"translated_{original_file_path}"
        with open(translated_file_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
            
        # إرسال الملف المترجم إلى المستخدم
        context.bot.send_document(
            chat_id=update.message.chat_id, 
            document=open(translated_file_path, 'rb')
        )

        # إرسال الرسالة الإضافية بعد إرسال الملف
        update.message.reply_text("🔄 قم بتحويل هذا الملف إلى البوت الرئيسي لكي يتحول إلى PDF: @i2pdfbot")
        
        # حذف الملفات المؤقتة
        os.remove(original_file_path)
        os.remove(translated_file_path)
    else:
        update.message.reply_text("❌ يرجى إرسال ملف بصيغة HTML فقط.")

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
