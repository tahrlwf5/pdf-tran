import logging
import os
from lxml import html
from textblob import TextBlob
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توكن بوت التليجرام
TELEGRAM_TOKEN = '5153049530:AAG4LS17jVZdseUnGkodRpHzZxGLOnzc1gs'  # ضع التوكن الخاص بك هنا

# دالة بدء البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "مرحبًا! أرسل لي ملف HTML وسأقوم بترجمته من الإنجليزية إلى العربية مع الحفاظ على التصميم."
    )

# دالة معالجة الملفات
def handle_document(update: Update, context: CallbackContext):
    document = update.message.document

    # التأكد من أن الملف بصيغة HTML
    if not document.file_name.lower().endswith('.html'):
        update.message.reply_text("يرجى إرسال ملف HTML فقط.")
        return

    file_id = document.file_id
    new_file = context.bot.get_file(file_id)

    # إنشاء مجلد للتنزيل إذا لم يكن موجودًا
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", document.file_name)
    new_file.download(file_path)

    # قراءة محتوى ملف HTML مع التأكد من UTF-8
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except Exception as e:
        logger.error(f"خطأ أثناء قراءة الملف: {e}")
        update.message.reply_text("حدث خطأ أثناء قراءة الملف.")
        return

    # تحليل الملف باستخدام lxml
    try:
        tree = html.fromstring(html_content)
    except Exception as e:
        logger.error(f"خطأ أثناء تحليل HTML: {e}")
        update.message.reply_text("حدث خطأ أثناء تحليل ملف HTML.")
        return

    # ترجمة النصوص داخل عناصر HTML باستخدام TextBlob
    # ترجمة النصوص داخل عناصر HTML مع كشف اللغة
    for element in tree.iter():
        if element.tag in ['script', 'style', 'noscript']:
            continue  # تجنب تغيير النصوص البرمجية

        if element.text and element.text.strip():
            detected_lang = detect(element.text)  # كشف اللغة
            print(f"🔹 النص: {element.text} | اللغة: {detected_lang}")  # تصحيح الأخطاء

            if detected_lang == "en":  # فقط ترجم إذا كان إنجليزيًا
                try:
                    blob = TextBlob(element.text)
                    element.text = str(blob.translate(to='ar'))
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة النص '{element.text}': {e}")

        if element.tail and element.tail.strip():
            detected_lang = detect(element.tail)
            print(f"🔹 النص: {element.tail} | اللغة: {detected_lang}")

            if detected_lang == "en":
                try:
                    blob = TextBlob(element.tail)
                    element.tail = str(blob.translate(to='ar'))
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة النص '{element.tail}': {e}")

    # استخراج النص المترجم للملف HTML مع الحفاظ على التصميم
    translated_html = html.tostring(tree, encoding='unicode', pretty_print=True)

    # تعديل الترميز ودعم العربية في HTML
    if "<head>" in translated_html:
        translated_html = translated_html.replace("<head>", "<head>\n<meta charset='UTF-8'>\n<meta http-equiv='Content-Language' content='ar'>")

    # حفظ الملف المترجم
    output_file_path = file_path.replace('.html', '_translated.html')
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
    except Exception as e:
        logger.error(f"خطأ أثناء حفظ الملف المترجم: {e}")
        update.message.reply_text("حدث خطأ أثناء حفظ الملف المترجم.")
        return

    # إرسال الملف المترجم للمستخدم
    with open(output_file_path, 'rb') as translated_file:
        update.message.reply_document(document=translated_file, filename=os.path.basename(output_file_path))

    # حذف الملفات المؤقتة
    os.remove(file_path)
    os.remove(output_file_path)

# دالة تشغيل البوت
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
