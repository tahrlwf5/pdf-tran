import os
import asyncio
import tempfile
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# الحصول على المفاتيح من البيئة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY')

async def htmlpdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرسالة الترحيبية مع تعليمات الاستخدام"""
    await update.message.reply_text(
        'مرحبًا! أنا بوت تحويل PDF إلى HTML 📄\n'
        'أرسل لي ملف PDF الآن (الحد الأقصى 5MB)'
    )
    context.user_data['allowed'] = True

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الملفات المرسلة"""
    try:
        # التحقق من الإذن المسبق
        if not context.user_data.get('allowed'):
            await update.message.reply_text("⚠️ الرجاء استخدام الأمر /htmlpdf أولاً")
            return
        
        # إزالة الإذن لمنع الاستخدام المتكرر
        del context.user_data['allowed']

        # التحقق من وجود الملف
        document = update.message.document
        if not document:
            await update.message.reply_text("❌ لم يتم العثور على ملف")
            return

        # التحقق من نوع الملف
        if document.mime_type != 'application/pdf':
            await update.message.reply_text("❌ الملف ليس بصيغة PDF")
            return

        # التحقق من حجم الملف (5MB كحد أقصى)
        if document.file_size > 5 * 1024 * 1024:
            await update.message.reply_text("📦 حجم الملف يتجاوز 5MB!")
            return

        # إرسال رسالة الانتظار
        processing_msg = await update.message.reply_text("⏳ جاري المعالجة...")

        # تنزيل الملف المؤقت
        file = await document.get_file()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # حفظ الملف المؤقت
            pdf_path = os.path.join(tmp_dir, "input.pdf")
            await file.download_to_drive(pdf_path)

            # إنشاء مهمة تحويل في CloudConvert
            job_data = {
                "tasks": {
                    "import-1": {"operation": "import/upload"},
                    "task-1": {
                        "operation": "convert",
                        "input": ["import-1"],
                        "input_format": "pdf",
                        "output_format": "html"
                    },
                    "export-1": {"operation": "export/url", "input": ["task-1"]}
                }
            }
            
            headers = {'Authorization': f'Bearer {CLOUDCONVERT_API_KEY}'}
            response = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_data, headers=headers)
            job = response.json()
            
            if 'data' not in job or 'tasks' not in job['data']:
                raise Exception("Failed to create conversion task")
            
            # رفع الملف إلى CloudConvert
            upload_task = next(t for t in job['data']['tasks'] if t['name'] == 'import-1')
            upload_url = upload_task['result']['form']['url']
            upload_fields = upload_task['result']['form']['parameters']
            
            with open(pdf_path, 'rb') as f:
                requests.post(upload_url, data=upload_fields, files={'file': (document.file_name, f)})
            
            # انتظار اكتمال التحويل
            export_task = next(t for t in job['data']['tasks'] if t['name'] == 'export-1')
            while True:
                task_response = requests.get(
                    f'https://api.cloudconvert.com/v2/tasks/{export_task["id"]}',
                    headers=headers
                )
                task_data = task_response.json()['data']
                
                if task_data['status'] == 'finished':
                    html_url = task_data['result']['files'][0]['url']
                    break
                elif task_data['status'] in ['error', 'cancelled']:
                    await update.message.reply_text("❌ فشل في التحويل!")
                    return
                await asyncio.sleep(2)
            
            # تنزيل الملف الناتج
            html_response = requests.get(html_url)
            output_filename = f"converted_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
            
            # حذف رسالة الانتظار
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id
            )
            
            # إرسال الملف النهائي
            await update.message.reply_document(
                document=html_response.content,
                filename=output_filename,
                caption="✅ تم التحويل بنجاح!"
            )
            
    except Exception as e:
        print(f"Error: {str(e)}")
        await update.message.reply_text("⚠️ حدث خطأ غير متوقع!")

if __name__ == '__main__':
    # تهيئة البوت
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة الأوامر
    app.add_handler(CommandHandler('htmlpdf', htmlpdf_command))  # الأمر الرئيسي
    app.add_handler(MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf))  # التصحيح هنا
    
    # بدء التشغيل
    print("Bot is running...")
    app.run_polling()
