import os
import logging
import subprocess
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
    update.message.reply_text("مرحباً، أرسل لي ملف HTML أو PDF لأقوم بتحويله وترجمته من الإنجليزية إلى العربية.")

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

def convert_pdf_to_html(pdf_file_path: str) -> str:
    """
    يستخدم pdf2htmlEX لتحويل ملف PDF إلى HTML.
    يُرجى التأكد من تثبيت pdf2htmlEX على النظام.
    """
    html_file_path = pdf_file_path.replace(".pdf", ".html")
    try:
        subprocess.run(["pdf2htmlEX", pdf_file_path, html_file_path], check=True)
        logger.info("تم تحويل PDF إلى HTML: %s", html_file_path)
        return html_file_path
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تحويل PDF إلى HTML: {e}")
        return None

def handle_file(update: Update, context: CallbackContext):
    document = update.message.document
    if document:
        file_name = document.file_name.lower()
        file_id = document.file_id
        new_file = context.bot.get_file(file_id)
        original_file_path = document.file_name
        new_file.download(custom_path=original_file_path)
        logger.info("تم تحميل الملف إلى %s", original_file_path)

        # إذا كان الملف بصيغة PDF، نقوم بتحويله أولاً إلى HTML
        if file_name.endswith('.pdf'):
            html_file_path = convert_pdf_to_html(original_file_path)
            if not html_file_path:
                update.message.reply_text("حدث خطأ أثناء تحويل ملف PDF إلى HTML.")
                os.remove(original_file_path)
                return
            target_file = html_file_path
            # بعد التحويل يمكن حذف ملف PDF الأصلي إذا أردت
            os.remove(original_file_path)
        elif file_name.endswith('.html'):
            target_file = original_file_path
        else:
            update.message.reply_text("يرجى إرسال ملف بصيغة HTML أو PDF فقط.")
            os.remove(original_file_path)
            return

        # ترجمة محتوى HTML
        translated_html = translate_html(target_file)
        
        # حفظ الملف المترجم
        translated_file_path = f"translated_{os.path.basename(target_file)}"
        with open(translated_file_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
            
        # إرسال الملف المترجم إلى المستخدم
        with open(translated_file_path, 'rb') as f:
            context.bot.send_document(chat_id=update.message.chat_id, document=f)
        
        # حذف الملفات المؤقتة
        os.remove(target_file)
        os.remove(translated_file_path)
    else:
        update.message.reply_text("يرجى إرسال ملف بصيغة HTML أو PDF فقط.")

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
