FROM ubuntu:20.04

# تحديث النظام وتثبيت التبعيات اللازمة لبناء pdf2htmlEX
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    poppler-utils \
    poppler-data \
    fontforge \
    libfontforge-dev \
    libcairo2-dev \
    libpoppler-cpp-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# بناء pdf2htmlEX من المصدر
RUN git clone --depth 1 https://github.com/pdf2htmlEX/pdf2htmlEX.git /opt/pdf2htmlEX && \
    cd /opt/pdf2htmlEX && \
    cmake . && make && make install && \
    rm -rf /opt/pdf2htmlEX

# تثبيت Python والأدوات المطلوبة
RUN apt-get install -y python3 python3-pip

# ضبط بيئة العمل
WORKDIR /app

# نسخ المتطلبات وتثبيت مكتبات بايثون
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود البوت وتشغيله
COPY . /app
CMD ["python3", "main.py"]
