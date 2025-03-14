import logging
import os
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from bs4 import BeautifulSoup, NavigableString
from googletrans import Translator
import chardet
import arabic_reshaper
from bidi.algorithm import get_display
import pdfkit

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ضع توكن البوت الذي تحصل عليه من BotFather هنا
TOKEN = '5153049530:AAG4LS17jVZdseUnGkodRpHzZxGLOnzc1gs'

# إنشاء مثيل للمترجم
translator = Translator()

def fix_arabic(text):
    """
    تعيد هذه الدالة تشكيل النص العربي وتصحيح اتجاهه باستخدام arabic-reshaper وpython-bidi.
    """
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def start(update, context):
    """رسالة ترحيب للمستخدم عند بدء التفاعل مع البوت."""
    update.message.reply_text("مرحباً! أرسل لي ملف HTML لأقوم بترجمته من الإنجليزية إلى العربية مع الحفاظ على التصميم.")

def translate_text_group(text_group):
    """
    تقوم هذه الدالة بتجميع مجموعة من أجزاء النص معًا باستخدام فاصل مميز لترجمتها مرة واحدة.
    بعد الترجمة يتم تقسيم النص المترجم بناءً على الفاصل وإعادة تطبيق الفراغات الأصلية مع إصلاح اتجاه النص العربي.
    """
    marker = "<<<SEP>>>"
    combined = marker.join(segment.strip() for segment in text_group)
    try:
        translated_combined = translator.translate(combined, src='en', dest='ar').text
        translated_combined = fix_arabic(translated_combined)
    except Exception as e:
        logger.error(f"خطأ أثناء ترجمة المجموعة: {e}")
        translated_combined = None

    if translated_combined:
        parts = translated_combined.split(marker)
        if len(parts) == len(text_group):
            final_parts = []
            for orig, part in zip(text_group, parts):
                leading_spaces = orig[:len(orig) - len(orig.lstrip())]
                trailing_spaces = orig[len(orig.rstrip()):]
                final_parts.append(leading_spaces + part + trailing_spaces)
            return final_parts

    result = []
    for segment in text_group:
        try:
            t = translator.translate(segment.strip(), src='en', dest='ar').text
            t = fix_arabic(t)
        except Exception as e:
            logger.error(f"خطأ أثناء ترجمة الجزء: {e}")
            t = segment
        leading_spaces = segment[:len(segment) - len(segment.lstrip())]
        trailing_spaces = segment[len(segment.rstrip()):]
        result.append(leading_spaces + t + trailing_spaces)
    return result

def process_parent_texts(parent):
    """
    تقوم هذه الدالة بمعالجة محتويات عنصر HTML (parent) لتجميع النصوص المتجاورة وترجمتها معاً،
    ثم إعادة توزيع النصوص المترجمة مع الحفاظ على ترتيبها الأصلي.
    """
    new_contents = []
    group = []
    for child in parent.contents:
        if isinstance(child, NavigableString):
            group.append(str(child))
        else:
            if group:
                translated_group = translate_text_group(group)
                for text in translated_group:
                    new_contents.append(NavigableString(text))
                group = []
            new_contents.append(child)
    if group:
        translated_group = translate_text_group(group)
        for text in translated_group:
            new_contents.append(NavigableString(text))
    parent.clear()
    for item in new_contents:
        parent.append(item)

def translate_html(html_content):
    """
    تقوم هذه الدالة بترجمة محتوى HTML مع:
    - إضافة وسم <meta charset="UTF-8"> داخل <head> إذا لم يكن موجوداً.
    - معالجة جميع العناصر (باستثناء وسوم script و style) لتجميع النصوص وترجمتها.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    head = soup.find('head')
    if head and not head.find('meta', charset=True):
        meta_tag = soup.new_tag('meta', charset='UTF-8')
        head.insert(0, meta_tag)
    
    for tag in soup.find_all():
        if tag.name in ['script', 'style']:
            continue
        if any(isinstance(child, NavigableString) and child.strip() for child in tag.contents):
            process_parent_texts(tag)
    
    return str(soup)

def handle_file(update, context):
    """
    دالة التعامل مع الملفات:
    - تتحقق من أن الملف بصيغة HTML.
    - تستخدم مكتبة chardet لاكتشاف الترميز.
    - تقوم بتحميل الملف وترجمته ثم إرسال النسخة المترجمة للمستخدم بصيغتين (HTML و PDF).
    """
    document = update.message.document
    if document and document.file_name.lower().endswith('.html'):
        file = document.get_file()
        file_bytes = file.download_as_bytearray()
        
        detected_encoding = chardet.detect(file_bytes)['encoding']
        try:
            html_content = file_bytes.decode(detected_encoding)
        except Exception as e:
            logger.error(f"خطأ في فك الترميز: {e}")
            update.message.reply_text("تعذر فك ترميز الملف. يرجى التأكد من أن الملف يستخدم ترميزاً مدعوماً.")
            return
        
        translated_html = translate_html(html_content)
        
        # حفظ الملف المترجم بصيغة HTML
        translated_html_path = 'translated.html'
        with open(translated_html_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
        
        # تحويل HTML إلى PDF باستخدام pdfkit مع تحديد مسار wkhtmltopdf داخل Docker
        translated_pdf_path = 'translated.pdf'
        try:
            config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
            pdfkit.from_string(translated_html, translated_pdf_path, configuration=config)
        except Exception as e:
            logger.error(f"خطأ أثناء تحويل HTML إلى PDF: {e}")
            update.message.reply_text("حدث خطأ أثناء تحويل الملف إلى PDF.")
            return
        
        update.message.reply_document(document=open(translated_html_path, 'rb'), filename="translated.html")
        update.message.reply_document(document=open(translated_pdf_path, 'rb'), filename="translated.pdf")
        
        os.remove(translated_html_path)
        os.remove(translated_pdf_path)
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
