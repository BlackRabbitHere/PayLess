FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md requirements.lock ./
COPY src ./src
RUN pip install --require-hashes -r requirements.lock && pip install --no-deps . \
    && playwright install --with-deps chromium \
    && useradd --create-home --uid 10001 scraper \
    && mkdir -p /app/data && chown -R scraper:scraper /app/data \
    && chmod -R a+rX /root/.cache/ms-playwright \
    && mv /root/.cache/ms-playwright /opt/ms-playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
USER scraper
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "payment_scraper.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
