# API de solo lectura SINCO 2019 / O*NET (sin scores ni exposicion)

Decision: `docs/decisions/004-api-despliegue.md`. Servidor stdlib: sin paquetes nuevos. Servidor FastAPI: fastapi, starlette, uvicorn (aprobados por el usuario para la opcion B).

## Dos servidores, misma capa de servicio (`service.py`)
| Servidor | Archivo | Dependencias | Comando (desde la raiz) |
|---|---|---|---|
| FastAPI + uvicorn (opcion B de 004; incluye OpenAPI en `/docs`) | `src/api/app.py` | `requirements-api.txt` | `.venv\Scripts\python -m src.api.app --port 8001` |
| stdlib `http.server` (opcion A, conservado) | `src/api/server.py` | ninguna nueva | `python -m src.api.server --port 8000` |

    .venv\Scripts\python -m pip install -r requirements-api-dev.txt   # fastapi, starlette, uvicorn (+ pytest, httpx para pruebas)
    .venv\Scripts\python -m pytest tests/api -q                       # pruebas (TestClient, no usan el crosswalk real)

`python -m src.api.app` solo escucha en loopback; rechaza otro `--host` salvo `SINCO_ALLOW_PUBLIC_BIND=1` (no usar sin decision).
Tambien: `.venv\Scripts\python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001`.

### Endurecimiento (solo `app.py`)
- Solo GET/HEAD; cualquier otro metodo (incl. OPTIONS sin CORS) -> 405 con `Allow: GET, HEAD`.
- CORS desactivado por defecto; `SINCO_CORS_ORIGINS=http://a,http://b` lo habilita solo para esos origenes (GET/HEAD, sin credenciales).
- `TrustedHostMiddleware`: Host permitido = 127.0.0.1/localhost; ampliar con `SINCO_ALLOWED_HOSTS=a,b`.
- Limites: `q` <= 100 caracteres (422), `offset` 0..100000 (422), `limit` se recorta (O*NET 1..200, busqueda SINCO 1..100).
- Cabeceras: nosniff, X-Frame-Options DENY, Referrer-Policy, CSP estricta (`/docs` la relaja solo para cdn.jsdelivr.net, de donde Swagger UI carga su JS), `Cache-Control: no-store`.
- Estaticos: lista blanca bajo `src/api/static/`; se rechazan `..`, `\`, NUL y archivos ocultos.
- Rutas con codigo invalido -> 404 (como antes); parametros mal formados -> 422 `{"error": "parametros invalidos"}`.

## Docker (preparado, no construido: Docker no esta instalado)
`Dockerfile` y `.dockerignore` en la raiz. La imagen no contiene `data/` (ni `data/raw` ni derivados de Frey-Osborne; licencia del PDF sin resolver):
se montan `data/processed` y `data/raw/manifest.json` por volumen de solo lectura (comando en el Dockerfile). Si se quiere evitar
montar las tablas de Frey-Osborne, montar un directorio con solo las tablas que lee `service.py`.

Enlaces directos: `/#4213` (nodo SINCO), `/#onet`, `/#meta`.

## Endpoints (solo GET/HEAD; otro metodo -> 405)
/api/health, /api/meta, /api/sinco/tree, /api/sinco/{codigo}, /api/sinco/search?q=,
/api/onet/occupations?q=&limit=&offset=, /api/onet/occupations/{soc}, /api/crosswalk?sinco_code=&onet_soc_code=, /api/crosswalk/schema

## Crosswalk
Lee `data/processed/crosswalk.parquet` (esquema: sinco_code, onet_soc_code, tipo_relacion, fuente, estado_validacion; opcionales
isco08_code, notas, match_quality, crosswalk_confidence, run_id, y del Metodo A1: modelo, rango, similitud, margen, similitud_alt, rango_alt, modelo_alt, baja_confianza, match_status). Sin archivo: estado `pendiente` ("coincidencias pendientes de crosswalk").
Archivo invalido: `esquema_invalido` y no se muestran filas. Columnas tipo score/exposicion/probabilidad se ignoran.

La interfaz muestra el aviso 'coincidencias automaticas sin validar (Metodo A1, embeddings)' cuando hay filas `sin_validar`, con similitud/rango/margen; la similitud no es una probabilidad.
