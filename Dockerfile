FROM python:3.9-slim

# تثبيت التبعيات النظامية المطلوبة
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    g++ \
    libpoppler-dev \
    libfontconfig1-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libpng-dev \
    libtiff-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# تنزيل وتثبيت pdf2htmlEX من المصدر
RUN git clone --depth 1 --branch master https://github.com/coolwanglu/pdf2htmlEX.git /tmp/pdf2htmlEX \
    && mkdir -p /tmp/pdf2htmlEX/build \
    && cd /tmp/pdf2htmlEX/build \
    && cmake .. \
    && make \
    && make install \
    && rm -rf /tmp/pdf2htmlEX

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
