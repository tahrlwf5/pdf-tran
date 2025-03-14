import logging
import os
import time
import base64
import requests
import chardet
from datetime import date
import PyPDF2
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
from bs4 import BeautifulSoup, NavigableString
from googletrans import Translator
import arabic_reshaper
from bidi.algorithm import get_display

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد التوكن ومفاتيح API
TELEGRAM_TOKEN = '5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw'
CONVERTIO_API = 'https://api.convertio.co/convert'
API_KEY = '3c50e707584d2cbe0139d35033b99d7c'

# إنشاء مثيل للمترجم
translator = Translator()

# لتتبع عدد الملفات المحولة يومياً لكل مستخدم (user_id: (last_date, count))
user_file_usage = {}

def fix_arabic(text):
    """
    تعيد هذه الدالة تشكيل النص العربي وتصحيح اتجاهه باستخدام arabic-reshaper وpython-bidi.
    """
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

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

    # إذا فشلت طريقة التجميع، نترجم كل جزء على حدة
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

def build_progress_text(progress: int) -> str:
    """
    يبني نص عرض تقدم التحويل مع النسبة وشريط التقدم.
    نستخدم 5 مربعات، حيث ▪️ يمثل المربع الممتلئ و▫️ يمثل المربع الفارغ.
    """
    total_blocks = 5
    filled = int(progress / 20)  # كل 20% يمثل مربعاً
    progress_bar = "▪️" * filled + "▫️" * (total_blocks - filled)
    return f"تم استلام الملف، جارٍ التحويل. يرجى الانتظار... {progress}% {progress_bar}"

def handle_document(update: Update, context: CallbackContext) -> None:
    """
    دالة التعامل مع ملفات PDF:
    - التحقق من حجم الملف (<= 1 ميجابايت).
    - منع إرسال أكثر من ملف في رسالة واحدة.
    - منع ملفات PDF التي تحتوي على أكثر من 5 صفحات.
    - تطبيق حد يومي بواقع 5 ملفات لكل مستخدم.
    - تحويل ملف PDF إلى HTML باستخدام API ثم ترجمة الملف.
    - عرض تحديثات شريط التقدم أثناء عملية التحويل.
    - إرسال الملف الناتج مع كابشن.
    """
    # منع إرسال أكثر من ملف في رسالة واحدة
    if update.message.media_group_id:
        update.message.reply_text("يرجى إرسال ملف واحد فقط في كل رسالة.")
        return

    document = update.message.document
    if not document:
        return

    # قبول ملفات PDF فقط
    if not document.file_name.lower().endswith('.pdf'):
        update.message.reply_text("يرجى إرسال ملف بصيغة PDF فقط.")
        return

    # التحقق من حجم الملف (1 ميجابايت = 1*1024*1024 بايت)
    if document.file_size > 1 * 1024 * 1024:
        update.message.reply_text("حجم الملف أكبر من 1 ميجابايت المسموح به.")
        return

    # التحقق من حد المستخدم اليومي (5 ملفات يومياً)
    user_id = update.message.from_user.id
    today_str = date.today().isoformat()
    if user_id in user_file_usage:
        last_date, count = user_file_usage[user_id]
        if last_date == today_str:
            if count >= 5:
                update.message.reply_text("لقد تجاوزت الحد اليومي لتحويل الملفات (5 ملفات يومياً).")
                return
            else:
                user_file_usage[user_id] = (today_str, count + 1)
        else:
            user_file_usage[user_id] = (today_str, 1)
    else:
        user_file_usage[user_id] = (today_str, 1)

    # تحميل الملف PDF
    file = document.get_file()
    input_filename = 'input.pdf'
    file.download(input_filename)

    # التحقق من عدد الصفحات باستخدام PyPDF2
    try:
        with open(input_filename, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
        if num_pages > 5:
            update.message.reply_text("يرجى إرسال ملف PDF يحتوي على 5 صفحات أو أقل.")
            os.remove(input_filename)
            return
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        update.message.reply_text("حدث خطأ أثناء قراءة الملف.")
        os.remove(input_filename)
        return

    # قراءة الملف وترميزه بصيغة Base64
    with open(input_filename, 'rb') as f:
        file_data = f.read()
    encoded_file = base64.b64encode(file_data).decode('utf-8')

    # تجهيز بيانات الطلب لإرسالها إلى API الخاص بـ Convertio
    payload = {
        "apikey": API_KEY,
        "input": "base64",
        "file": encoded_file,
        "filename": document.file_name,
        "outputformat": "html"
    }

    # بدء عملية التحويل عبر API
    try:
        response = requests.post(CONVERTIO_API, json=payload)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error during conversion initiation: {e}")
        update.message.reply_text("حدث خطأ أثناء بدء عملية التحويل.")
        os.remove(input_filename)
        return

    result = response.json()
    if result.get('code') != 200:
        error_msg = result.get('error', 'خطأ غير معروف.')
        update.message.reply_text(f"خطأ في API التحويل: {error_msg}")
        os.remove(input_filename)
        return

    conversion_id = result['data']['id']
    status_url = f"{CONVERTIO_API}/{conversion_id}/status"

    # إرسال رسالة أولية لعرض تقدم العملية
    progress_message = update.message.reply_text(build_progress_text(0))
    start_time = time.time()
    max_wait_time = 60  # أقصى زمن افتراضي للتقدم (60 ثانية)

    # الاستعلام الدوري لمعرفة حالة عملية التحويل مع تحديث التقدم
    while True:
        time.sleep(2)
        elapsed = time.time() - start_time
        # حساب نسبة مئوية تقريبية
        progress = min(int((elapsed / max_wait_time) * 100), 100)
        try:
            status_resp = requests.get(status_url)
            status_data = status_resp.json()
        except Exception as e:
            logger.error(f"Error checking conversion status: {e}")
            update.message.reply_text("حدث خطأ أثناء التحقق من حالة التحويل.")
            os.remove(input_filename)
            return
        step = status_data.get('data', {}).get('step')
        # تحديث رسالة التقدم
        try:
            context.bot.edit_message_text(chat_id=update.message.chat_id,
                                          message_id=progress_message.message_id,
                                          text=build_progress_text(progress))
        except Exception as e:
            logger.error(f"Error editing progress message: {e}")
        if step == 'finish':
            # تحديث التقدم إلى 100%
            try:
                context.bot.edit_message_text(chat_id=update.message.chat_id,
                                              message_id=progress_message.message_id,
                                              text=build_progress_text(100))
            except Exception as e:
                logger.error(f"Error finalizing progress message: {e}")
            break
        if step == 'error':
            update.message.reply_text("حدث خطأ أثناء التحويل.")
            os.remove(input_filename)
            return

    # الحصول على رابط تحميل الملف المحول
    download_url = status_data['data']['output']['url']
    try:
        download_resp = requests.get(download_url)
        download_resp.raise_for_status()
    except Exception as e:
        logger.error(f"Error downloading converted file: {e}")
        update.message.reply_text("حدث خطأ أثناء تحميل الملف المحول.")
        os.remove(input_filename)
        return

    output_filename = 'output.html'
    with open(output_filename, 'wb') as f:
        f.write(download_resp.content)

    # قراءة محتوى HTML المحول وترجمته
    try:
        with open(output_filename, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        logger.error(f"Error reading converted HTML: {e}")
        update.message.reply_text("حدث خطأ أثناء قراءة الملف المحول.")
        os.remove(input_filename)
        os.remove(output_filename)
        return

    translated_html = translate_html(html_content)
    translated_file_path = 'translated.html'
    with open(translated_file_path, 'w', encoding='utf-8') as f:
        f.write(translated_html)

    # إرسال الملف الناتج مع كابشن
    update.message.reply_document(document=open(translated_file_path, 'rb'),
                                  caption="✅ تم ترجمة الملف بنجاح!")

    # حذف الملفات المؤقتة
    os.remove(input_filename)
    os.remove(output_filename)
    os.remove(translated_file_path)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("مرحباً! يرجى إرسال ملف PDF واحد (بحجم ≤ 1 ميجابايت و 5 صفحات أو أقل).")

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    logger.info("البوت يعمل الآن...")
    updater.idle()

if __name__ == '__main__':
    main()
