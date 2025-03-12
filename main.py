import os
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
from googletrans import Translator
from pdf2docx import Converter
from docx import Document

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

def pdf_to_html(pdf_path: str, html_path: str):
    """
    يقوم بتحويل ملف PDF إلى ملف DOCX ثم إلى HTML.
    """
    docx_path = pdf_path.replace('.pdf', '.docx')
    
    # تحويل PDF إلى DOCX
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()
    
    # قراءة ملف DOCX وإنشاء HTML مبسط
    doc = Document(docx_path)
    html_content = "<html><body>"
    for para in doc.paragraphs:
        html_content += f"<p>{para.text}</p>"
    html_content += "</body></html>"
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # حذف ملف DOCX المؤقت
    os.remove(docx_path)

def handle_file(update: Update, context: CallbackContext):
    document = update.message.document
    if document:
        file_ext = os.path.splitext(document.file_name)[1].lower()
        original_file_path = document.file_name
        file_id = document.file_id
        new_file = context.bot.get_file(file_id)
        new_file.download(custom_path=original_file_path)
        logger.info("تم تحميل الملف إلى %s", original_file_path)
        
        if file_ext == '.html':
            # إذا كان الملف HTML نترجمه مباشرة
            translated_html = translate_html(original_file_path)
            translated_file_path = f"translated_{original_file_path}"
            with open(translated_file_path, 'w', encoding='utf-8') as f:
                f.write(translated_html)
        elif file_ext == '.pdf':
            # إذا كان الملف PDF نقوم بتحويله إلى HTML أولاً ثم نترجمه
            temp_html_path = original_file_path.replace('.pdf', '.html')
            pdf_to_html(original_file_path, temp_html_path)
            translated_html = translate_html(temp_html_path)
            translated_file_path = f"translated_{os.path.splitext(document.file_name)[0]}.html"
            with open(translated_file_path, 'w', encoding='utf-8') as f:
                f.write(translated_html)
            os.remove(temp_html_path)
        else:
            update.message.reply_text("يرجى إرسال ملف بصيغة HTML أو PDF فقط.")
            return
        
        # إرسال الملف المترجم إلى المستخدم
        context.bot.send_document(
            chat_id=update.message.chat_id, 
            document=open(translated_file_path, 'rb')
        )
        
        # حذف الملفات المؤقتة
        os.remove(original_file_path)
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
