import logging
import os
import io
from lxml import html
from googletrans import Translator
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد سجل الأخطاء للتتبع
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن الخاص بالبوت
TELEGRAM_TOKEN = '5153049530:AAG4LS17jVZdseUnGkodRpHzZxGLOnzc1gs'  # استبدل هذا بتوكن البوت الخاص بك

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا، أرسل لي ملف HTML وسأقوم بترجمته من الإنجليزية إلى العربية مع الحفاظ على التصميم."
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    # التأكد من أن الملف بامتداد HTML
    if not document.file_name.lower().endswith('.html'):
        await update.message.reply_text("يرجى إرسال ملف HTML فقط.")
        return

    file_id = document.file_id
    new_file = await context.bot.get_file(file_id)
    
    # إنشاء مجلد للتنزيل إذا لم يكن موجوداً
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", document.file_name)
    await new_file.download_to_drive(custom_path=file_path)
    
    # قراءة محتوى ملف HTML
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        await update.message.reply_text("حدث خطأ أثناء قراءة الملف.")
        return

    # تحليل الملف باستخدام lxml
    try:
        tree = html.fromstring(html_content)
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        await update.message.reply_text("حدث خطأ أثناء تحليل الملف HTML.")
        return

    translator = Translator()

    # المرور على جميع العناصر وتعديل النصوص
    for element in tree.iter():
        # تخطي العناصر التي لا تحتاج للترجمة مثل script و style و noscript
        if element.tag in ['script', 'style', 'noscript']:
            continue
        
        if element.text and element.text.strip():
            try:
                translated_text = translator.translate(element.text, src='en', dest='ar').text
                element.text = translated_text
            except Exception as e:
                logger.error(f"Error translating text '{element.text}': {e}")
        
        if element.tail and element.tail.strip():
            try:
                translated_tail = translator.translate(element.tail, src='en', dest='ar').text
                element.tail = translated_tail
            except Exception as e:
                logger.error(f"Error translating tail text '{element.tail}': {e}")

    # استخراج النص المترجم للملف HTML مع الحفاظ على التصميم
    translated_html = html.tostring(tree, encoding='unicode', pretty_print=True)
    
    # حفظ الملف المترجم
    output_file_path = file_path.replace('.html', '_translated.html')
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
    except Exception as e:
        logger.error(f"Error writing translated file: {e}")
        await update.message.reply_text("حدث خطأ أثناء حفظ الملف المترجم.")
        return

    # إرسال الملف المترجم للمستخدم
    with open(output_file_path, 'rb') as translated_file:
        await update.message.reply_document(document=translated_file, filename=os.path.basename(output_file_path))
    
    # حذف الملفات المؤقتة (اختياري)
    os.remove(file_path)
    os.remove(output_file_path)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.run_polling()

if __name__ == '__main__':
    main()
