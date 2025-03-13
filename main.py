import os
import tempfile
import requests
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

# إعدادات API
API_KEY = "8w1h7uM6OoOWw5Lidqf1FJU0r5ZBzHRo"
API_URL = "https://api.mconverter.eu/convert"  # تأكد من الرابط حسب وثائق الموقع

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق من أن الملف DOCX
    document = update.message.document
    if not (document.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" 
            or document.file_name.endswith('.docx')):
        await update.message.reply_text("❌ يُرجى إرسال ملف DOCX صالح.")
        return

    # إنشاء مجلد مؤقت
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # تنزيل الملف
            file = await document.get_file()
            docx_path = os.path.join(tmp_dir, "input.docx")
            await file.download_to_destination(docx_path)  # الطريقة الصحيحة في الإصدارات الحديثة
            
            # إرسال الطلب إلى API
            with open(docx_path, 'rb') as f:
                response = requests.post(
                    API_URL,
                    files={'file': f},
                    data={'apikey': API_KEY, 'outputformat': 'html'}
                )
            
            # معالجة الاستجابة
            if response.status_code == 200:
                html_path = os.path.join(tmp_dir, "output.html")
                with open(html_path, 'wb') as f:
                    f.write(response.content)
                
                await update.message.reply_document(
                    document=html_path,
                    caption="✅ تم التحويل بنجاح!"
                )
            else:
                await update.message.reply_text(f"❌ فشل التحويل: {response.text}")
        
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ غير متوقع: {str(e)}")

if __name__ == "__main__":
    TOKEN = "6016945663:AAFqyBCgCguvPzjHDzVNubNH1VCGT7c1j34"  # استبدل بتوكن البوت الخاص بك
    app = Application.builder().token(TOKEN).build()
    
    # إضافة Handler للملفات
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("✅ البوت يعمل...")
    app.run_polling()
