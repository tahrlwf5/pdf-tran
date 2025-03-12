FROM python:3.9-slim

# 1. تثبيت التبعيات النظامية الأساسية
RUN apt-get update && apt-get install -y \
    wget \
    git \
    cmake \
    g++ \
    pkg-config \
    libpoppler-dev \
    libpoppler-cpp-dev \
    libfontconfig1-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. تنزيل وتثبيت pdf2htmlEX من إصدار ثابت
RUN git clone --depth 1 --branch "v0.18.8-poppler-22.04.0" \
    https://github.com/coolwanglu/pdf2htmlEX.git /tmp/pdf2htmlEX \
    && mkdir -p /tmp/pdf2htmlEX/build \
    && cd /tmp/pdf2htmlEX/build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. \
    && make \
    && make install \
    && rm -rf /tmp/pdf2htmlEX

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
