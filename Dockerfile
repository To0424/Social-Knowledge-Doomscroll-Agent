FROM python:3.12-slim

WORKDIR /app

# System deps for Playwright Chromium + curl for Ollama health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
        libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
        libasound2 libxshmfence1 libxfixes3 fonts-noto-color-emoji \
        curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

COPY . .
RUN chmod +x entrypoint.sh

# Auth volume mount point (for persisted X session cookies)
VOLUME /app/auth

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
