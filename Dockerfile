FROM python:3.11-slim

# ffmpeg ve diğer gerekli paketleri kur
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python bağımlılıklarını kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulamayı kopyala
COPY . .

# Dizinleri oluştur ve izin ver
RUN mkdir -p outputs uploads && chmod 755 outputs uploads

# Port 8000'i expose et
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000').read()" || exit 1

# Uygulamayı çalıştır
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
