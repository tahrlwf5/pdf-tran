import logging
import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from bs4 import BeautifulSoup
from googletrans import Translator

# إعداد تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ضع هنا توكن البوت الخاص بك
TOKEN = "6016945663:AAHjacRdRfZ2vUgS2SLmoFgHfMdUye4l6bA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'مرحباً! أرسل لي ملف HTML باللغة الإنجليزية وسأقوم بترجمته إلى العربية.'
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    # التحقق من نوع الملف (يجب أن يكون ملف HTML)
    if document.mime_type != 'text/html':
        await update.message.reply_text('الرجاء إرسال ملف HTML فقط.')
        return

    file_id = document.file_id
    new_file = await context.bot.get_file(file_id)
    
    # إنشاء مجلد لتحميل الملفات إن لم يكن موجوداً
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{document.file_name}"
    await new_file.download_to_drive(file_path)
    await update.message.reply_text('تم تحميل الملف، جاري الترجمة...')

    # قراءة محتوى الملف
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # تحليل محتوى HTML باستخدام BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    translator = Translator()

    # ترجمة النصوص داخل عناصر HTML مع تجاهل الوسوم غير المراد ترجمتها
    for element in soup.find_all(text=True):
        if element.parent.name in ['script', 'style']:
            continue
        text = element.strip()
        if text:
            try:
                translation = translator.translate(text, src='en', dest='ar')
                element.replace_with(translation.text)
            except Exception as e:
                logger.error(f"خطأ في الترجمة: {e}")

    translated_html = str(soup)
    output_path = f"downloads/translated_{document.file_name}"
    # حفظ الملف المترجم
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated_html)

    # إرسال الملف المترجم للمستخدم
    with open(output_path, 'rb') as f:
        await update.message.reply_document(
            document=InputFile(f, filename=f"translated_{document.file_name}")
        )

    await update.message.reply_text('تم الترجمة وإرسال الملف المترجم.')
    # حذف الملفات المؤقتة (اختياري)
    os.remove(file_path)
    os.remove(output_path)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
