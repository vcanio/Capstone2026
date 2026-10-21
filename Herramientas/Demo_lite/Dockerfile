FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    YOLO_CONFIG_DIR=/app/.runtime/config MPLCONFIGDIR=/app/.runtime/config/matplotlib \
    YOLO_AUTOINSTALL=false OMP_NUM_THREADS=2

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home vision

WORKDIR /app
COPY requirements.txt requirements-docker.txt ./
# El índice CPU contiene ruedas para amd64 y arm64; no instala CUDA.
RUN python -m pip install torch==2.5.1 torchvision==0.20.1 \
        --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements-docker.txt \
    && python -m pip check

# Los módulos portátiles calculan la raíz con parents[2].
WORKDIR /app/Walmart_Vision
ENV YOLO_CONFIG_DIR=/app/Walmart_Vision/.runtime/config \
    MPLCONFIGDIR=/app/Walmart_Vision/.runtime/config/matplotlib
COPY --chown=10001:10001 app.py inferencia.py interfaz.html modelos.json \
    ocupacion_paulo.py gondola_bordes.py ./
COPY --chown=10001:10001 modelos/ ./modelos/
RUN mkdir -p .runtime/config && chown -R 10001:10001 .runtime
USER 10001:10001
# Comprueba versiones, manifiesto y hashes de los pesos al construir.
RUN python app.py --check

EXPOSE 8095
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('VISION_PORT', '8095') + '/api/health', timeout=3).read()"
CMD ["python", "app.py", "--host", "0.0.0.0", "--device", "cpu"]
