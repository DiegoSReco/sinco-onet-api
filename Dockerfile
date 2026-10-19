# API de solo lectura SINCO/O*NET (FastAPI). NO construida ni probada: Docker no esta instalado en esta maquina.
# La imagen NO contiene data/ (ni data/raw ni datos derivados de Frey-Osborne). Montar por volumen de solo lectura:
#   docker run --rm -p 127.0.0.1:8001:8001 \
#     -v "$PWD/data/processed:/app/data/processed:ro" \
#     -v "$PWD/data/raw/manifest.json:/app/data/raw/manifest.json:ro" sinco-api
# Aviso: data/processed incluye tablas derivadas de Frey-Osborne que la API no lee ni sirve; para no montarlas,
# preparar un directorio con solo las tablas listadas en tests/api/test_api.py (TABLAS) y, opcional, crosswalk.parquet.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Solo la API (el .dockerignore excluye el resto de src/ y todo data/).
COPY src/__init__.py src/__init__.py
COPY src/api src/api

RUN useradd --system --no-create-home app && mkdir -p data/processed data/raw
USER app

EXPOSE 8001
# 0.0.0.0 es el interior del contenedor; publicar solo en loopback (-p 127.0.0.1:8001:8001) salvo decision distinta.
# Hosts permitidos: ajustar SINCO_ALLOWED_HOSTS (y SINCO_CORS_ORIGINS si se necesita CORS) al desplegar.
ENV SINCO_ALLOWED_HOSTS=127.0.0.1,localhost
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8001", "--no-server-header"]
