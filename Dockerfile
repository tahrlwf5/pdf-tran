FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgobject-2.0-0 \
    gir1.2-gobject-2.0

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
