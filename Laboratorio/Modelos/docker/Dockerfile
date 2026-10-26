FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    YOLO_CONFIG_DIR=/app/.config-modelo MPLCONFIGDIR=/app/.config-modelo/matplotlib

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY Laboratorio/Modelos/docker/requirements.txt /tmp/panel-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/panel-requirements.txt

WORKDIR /app
COPY Laboratorio/Modelos/*.py Laboratorio/Modelos/panel.html /app/Laboratorio/Modelos/
COPY Laboratorio/Modelos/static/ /app/Laboratorio/Modelos/static/
COPY Laboratorio/Reproducibilidad/*.py /app/Laboratorio/Reproducibilidad/
COPY Laboratorio/Datos/*.py /app/Laboratorio/Datos/
EXPOSE 8090
CMD ["python", "-u", "Laboratorio/Modelos/panel_modelos.py", "--host", "0.0.0.0"]
