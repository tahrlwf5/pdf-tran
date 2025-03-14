import logging
import os
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from telegram import Update
from bs4 import BeautifulSoup
from googletrans import Translator
import chardet

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ضع توكن البوت الذي تحصل عليه من BotFather هنا
TOKEN = '5153049530:AAG4LS17jVZdseUnGkodRpHzZxGLOnzc1gs'

# إنشاء مثيل للمترجم
translator = Translator()

def start(update, context):
    """إرسال رسالة ترحيبية للمستخدم عند بدء التفاعل مع البوت."""
    update.message.reply_text("مرحباً! أرسل لي ملف HTML لأقوم بترجمته من الإنجليزية إلى العربية مع الحفاظ على التصميم.")

def translate_html(html_content):
    """
    دالة تقوم بترجمة النصوص داخل ملف HTML.
    - تتجاهل ترجمة النصوص داخل وسوم <script> و <style>.
    - تضيف وسم <meta charset="UTF-8"> إلى رأس الصفحة إذا لم يكن موجوداً.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # التأكد من وجود وسم meta charset داخل <head>
    head = soup.find('head')
    if head and not head.find('meta', charset=True):
        meta_tag = soup.new_tag('meta', charset='UTF-8')
        head.insert(0, meta_tag)
    
    # المرور على جميع عناصر النص في الصفحة
    for element in soup.find_all(text=True):
        # تجاهل النصوص داخل وسوم script أو style
        if element.parent.name in ['script', 'style']:
            continue
        if element.strip():
            try:
                translated_text = translator.translate(element, src='en', dest='ar').text
                element.replace_with(translated_text)
            except Exception as e:
                logger.error(f"خطأ أثناء الترجمة: {e}")
                continue

    return str(soup)

def handle_file(update, context):
    """
    دالة للتعامل مع الملفات المرسلة:
    - تتحقق من أن الملف بصيغة HTML.
    - تستخدم chardet لاكتشاف الترميز الصحيح.
    - تقوم بتحميل الملف وترجمته ثم إرسال النسخة المترجمة للمستخدم.
    """
    document = update.message.document
    if document and document.file_name.lower().endswith('.html'):
        file = document.get_file()
        file_bytes = file.download_as_bytearray()
        
        # اكتشاف الترميز الصحيح باستخدام chardet
        detected_encoding = chardet.detect(file_bytes)['encoding']
        try:
            html_content = file_bytes.decode(detected_encoding)
        except Exception as e:
            logger.error(f"خطأ في فك الترميز: {e}")
            update.message.reply_text("تعذر فك ترميز الملف. يرجى التأكد من أن الملف يستخدم ترميزاً مدعوماً.")
            return
        
        # ترجمة محتوى HTML
        translated_html = translate_html(html_content)
        
        # حفظ الملف المترجم مؤقتاً
        translated_file_path = 'translated.html'
        with open(translated_file_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
        
        # إرسال الملف المترجم إلى المستخدم
        update.message.reply_document(document=open(translated_file_path, 'rb'))
        os.remove(translated_file_path)
    else:
        update.message.reply_text("يرجى إرسال ملف بصيغة HTML فقط.")

def main():
    """الدالة الرئيسية لتشغيل البوت."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    logger.info("البوت يعمل الآن...")
    updater.idle()

if __name__ == '__main__':
    main()
