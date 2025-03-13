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

# قم بتعديل معرف المشرف هنا أو من خلال متغير بيئي
ADMIN_ID = os.getenv("ADMIN_ID", "5198110160")  # تأكد من وضع المعرف الصحيح

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    # إرسال رسالة ترحيب للمستخدم
    update.message.reply_text("مرحباً، أرسل لي ملف HTML لأقوم بترجمته من الإنجليزية إلى العربية.")
    # إرسال إشعار للمشرف مع بيانات المستخدم (معرف المستخدم واسم المستخدم إن وجد)
    admin_message = f"دخل المستخدم:\nمعرف المستخدم: {user.id}\nالاسم: {user.first_name} {user.last_name if user.last_name else ''}\nاسم المستخدم: @{user.username if user.username else 'غير متوفر'}"
    context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

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
                translated_text = translator.translate(original_text, src='en', dest='ar').text
                element.replace_with(translated_text)
            except Exception as e:
                logger.error(f"حدث خطأ أثناء الترجمة: {e}")
    return str(soup)

def handle_file(update: Update, context: CallbackContext):
    document = update.message.document
    if document and document.file_name.endswith('.html'):
        # التحقق من حجم الملف (أقصى حجم 2MB)
        if document.file_size > 2 * 1024 * 1024:
            update.message.reply_text("❌ حجم الملف أكبر من 2MB. يرجى إرسال ملف بحجم أصغر.")
            return

        file_id = document.file_id
        new_file = context.bot.get_file(file_id)
        original_file_path = document.file_name
        new_file.download(custom_path=original_file_path)
        logger.info("تم تحميل الملف إلى %s", original_file_path)
        
        # إبلاغ المستخدم بأنه جاري ترجمة الملف
        update.message.reply_text("جاري ترجمة ملفك انتظر بعض دقائق...")
        
        # ترجمة محتوى HTML
        translated_html = translate_html(original_file_path)
        
        # حفظ الملف المترجم
        translated_file_path = f"translated_{original_file_path}"
        with open(translated_file_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
            
        # إرسال الملف المترجم مع Caption
        caption_text = ("✅ تم الترجمة بنجاح!\n"
                        "قم بإعادة توجيه هذا الملف للبوت الرئيسي لتحويله إلى PDF: @i2pdfbot \n"
                        "@ta_ja199 للاستفسار")
        context.bot.send_document(
            chat_id=update.message.chat_id, 
            document=open(translated_file_path, 'rb'),
            caption=caption_text
        )
        
        # حذف الملفات المؤقتة
        os.remove(original_file_path)
        os.remove(translated_file_path)
    else:
        update.message.reply_text("يرجى إرسال ملف بصيغة HTML فقط.")

def main():
    # ضع هنا توكن البوت الخاص بك
    token = "8060810536:AAEaV76YpcZyIxI4Qb_taVMG1ijn8hVYHt0"
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
