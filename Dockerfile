# استخدم صورة Python الرسمية
FROM python:3.10-slim

# تثبيت التبعيات الأساسية و wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wget \
    xfonts-base \
    xfonts-75dpi \
    && wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6-1.buster_amd64.deb \
    && apt-get -f install -y \
    && rm wkhtmltox_0.12.6-1.buster_amd64.deb

# ضبط المسار لتحديد `wkhtmltopdf`
ENV PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:/usr/local/bin/wkhtmltopdf"

# تعيين مجلد العمل ونسخ الملفات
WORKDIR /app
COPY . /app

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
