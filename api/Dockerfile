FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Tesseract OCR engine with English data
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user (uid 1000). The photo folder must be writable by this uid.
RUN useradd --create-home --uid 1000 vault \
    && mkdir -p /data/photos \
    && chown vault:vault /data/photos
USER vault

EXPOSE 8000
CMD ["sh", "start.sh"]
