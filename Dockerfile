# استخدم صورة Python الرسمية
FROM python:3.10-slim

# تثبيت التبعيات الأساسية و wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wget \
    xfonts-base \
    xfonts-75dpi \
    libfontconfig \
    libxrender1 \
    libjpeg62-turbo \
    && wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb \
    && apt-get install -y ./wkhtmltox_0.12.6-1.buster_amd64.deb \
    && rm wkhtmltox_0.12.6-1.buster_amd64.deb

# ضبط المسار لـ wkhtmltopdf
ENV PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin"

# تعيين مجلد العمل
WORKDIR /app

# نسخ الملفات إلى الحاوية
COPY . /app

# تثبيت متطلبات المشروع
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
