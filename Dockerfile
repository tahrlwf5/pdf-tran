FROM python:3.9-slim

# تحديث الحزم وتثبيت wkhtmltopdf
RUN apt-get update && apt-get install -y wkhtmltopdf && rm -rf /var/lib/apt/lists/*

# نسخ ملف requirements.txt وتثبيت المكتبات
COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . /app/

# الأمر لتشغيل البوت
CMD ["python", "bot.py"]
