FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/models \
    HF_HUB_DISABLE_XET=1

# ffmpeg подстраховывает декодирование видео-контейнеров,
# которые встроенный в faster-whisper PyAV может не поддержать;
# --no-install-recommends исключает GTK/X11/PulseAudio и прочий GUI-балласт,
# который apt иначе тянет вместе с ffmpeg (экономит ~650MB и время сборки)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser && \
    mkdir -p /models && chown -R appuser:appuser /app /models
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8001/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
