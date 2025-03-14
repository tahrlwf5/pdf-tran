FROM python:3.10

# تحديد مجلد العمل
WORKDIR /app

# نسخ الملفات إلى الحاوية
COPY . /app

# تثبيت المتطلبات
RUN pip3 install --no-cache-dir -r requirements.txt

# تحميل قاعدة بيانات TextBlob
RUN python -m textblob.download_corpora

# تشغيل البوت
CMD ["python", "bot.py"]
