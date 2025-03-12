FROM ubuntu:20.04

# تحديث النظام وتثبيت التبعيات الأساسية
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:pdf2htmlex/ppa \
    && apt-get update \
    && apt-get install -y pdf2htmlEX \
    && rm -rf /var/lib/apt/lists/*

# تثبيت Python والأدوات اللازمة
RUN apt-get install -y python3 python3-pip

# ضبط بيئة العمل
WORKDIR /app

# نسخ المتطلبات وتثبيت المكتبات
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود وتشغيل البوت
COPY . /app
CMD ["python3", "main.py"]
