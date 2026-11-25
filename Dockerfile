FROM --platform=linux/amd64 python:3.10-slim

# Instala o Chromium nativo (mais estável em containers)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Informa ao sistema onde o Chromium está instalado
ENV CHROME_BINARY=/usr/bin/chromium

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT app:app"]
