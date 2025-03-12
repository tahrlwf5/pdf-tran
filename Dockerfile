# استخدم صورة رسمية مبنية على Python (مثلاً Python 3.9-slim)
FROM python:3.9-slim

# تحديث الحزم وتثبيت pdf2htmlEX مع تبعياته
RUN apt-get update && apt-get install -y \
    pdf2htmlEX \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات وتثبيت مكتبات البايثون
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . /app

# تشغيل البوت عند بدء الحاوية
CMD ["python", "main.py"]
