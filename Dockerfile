# استخدم صورة Python الرسمية
FROM python:3.9-slim

# تثبيت التبعيات الأساسية
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# ضبط متغير البيئة لتجنب مشاكل الإعدادات المحلية
ENV PYTHONUNBUFFERED=1

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الملفات إلى الحاوية
COPY . .

# تشغيل البوت عند تشغيل الحاوية
CMD ["python", "main.py"]
