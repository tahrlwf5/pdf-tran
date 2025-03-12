# استخدام صورة رسمية لـ Python
FROM python:3.9-slim

# تعيين مسار العمل داخل الحاوية
WORKDIR /app

# تثبيت الحزم المطلوبة مسبقًا
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    pdf2htmlex \
    && rm -rf /var/lib/apt/lists/*

# نسخ الملفات إلى الحاوية
COPY requirements.txt .
COPY bot.py .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تعيين المنفذ الذي سيتم تشغيل التطبيق عليه
ENV PORT=8080

# تشغيل البوت عند بدء الحاوية
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main.py"]
