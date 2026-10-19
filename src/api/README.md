# API de solo lectura SINCO 2019 / O*NET (sin exposicion; con probabilidad F-O rotulada y NO validada)

Decision: `docs/decisions/004-api-despliegue.md`. Servidor stdlib: sin paquetes nuevos. Servidor FastAPI: fastapi, starlette, uvicorn (aprobados por el usuario para la opcion B).

## Dos servidores, misma capa de servicio (`service.py`)
| Servidor | Archivo | Dependencias | Comando (desde la raiz) |
|---|---|---|---|
| FastAPI + uvicorn (opcion B de 004; incluye OpenAPI en `/docs`) | `src/api/app.py` | `requirements-api.txt` | `.venv\Scripts\python -m src.api.app --port 8001` |
| stdlib `http.server` (opcion A, conservado) | `src/api/server.py` | ninguna nueva | `python -m src.api.server --port 8000` |

    .venv\Scripts\python -m pip install -r requirements-api-dev.txt   # fastapi, starlette, uvicorn (+ pytest, httpx para pruebas)
    .venv\Scripts\python -m pytest tests/api -q                       # pruebas (TestClient; usan copias temporales de las tablas, nunca escriben en data/)

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
/api/onet/occupations?q=&limit=&offset=, /api/onet/occupations/{soc}, /api/crosswalk?sinco_code=&onet_soc_code=, /api/crosswalk/schema,
/api/probabilidad, /api/probabilidad/{codigo}, /api/download/conteo, /api/download/dataset (ver abajo)

## Crosswalk
Lee `data/processed/crosswalk.parquet` (esquema: sinco_code, onet_soc_code, tipo_relacion, fuente, estado_validacion; opcionales
isco08_code, notas, match_quality, crosswalk_confidence, run_id, y del Metodo A1: modelo, rango, similitud, margen, similitud_alt, rango_alt, modelo_alt, baja_confianza, match_status). Sin archivo: estado `pendiente` ("coincidencias pendientes de crosswalk").
Archivo invalido: `esquema_invalido` y no se muestran filas. Columnas tipo score/exposicion/probabilidad se ignoran.

La interfaz muestra el aviso 'coincidencias automaticas sin validar (Metodo A1, embeddings)' cuando hay filas `sin_validar`, con similitud/rango/margen; la similitud no es una probabilidad.

## Probabilidad de automatizacion (Frey-Osborne) y descarga del dataset
Regla vigente (cambio pedido por el usuario el 2026-10-19: "usa probabilidades en el repo"; el registro formal esta en
`docs/decisions/009-top2-api-descarga-y-probabilidad.md`, que este README no edita): la **unica** probabilidad admitida es la
"probabilidad de automatizacion (Frey-Osborne)", siempre rotulada asi y con `estado_validacion = sin_validar` ("NO validada"). No es exposicion
a IA, ni riesgo de perdida de empleo, ni una estimacion para Mexico. **La exposicion y los scores siguen prohibidos** en endpoints e interfaz.
Fuente: `data/processed/sinco_probabilidad_fo.parquet` (una fila por modelo y grupo unitario; el modelo principal lo marca `es_modelo_principal`).
Si el archivo no existe (p. ej. repo publico solo con codigo y docs), el estado es `no_disponible` / "probabilidad no disponible", las columnas de
probabilidad se omiten de las descargas y la interfaz muestra un estado vacio explicito, igual que el crosswalk pendiente.

- `GET /api/probabilidad?q=&sinco_prefix=&division=&nivel=&modelo=&solo_con_probabilidad=&limit=&offset=`: listado paginado (`limit` 1..200, `offset` 0..100000) con
  `estado`, `etiqueta`, `aviso`, `que_es`, `que_no_es`, `modelo_principal`, `modelos_disponibles` y `resultados`.
- `GET /api/probabilidad/{codigo}?modelo=`: la de un grupo (`estado`: `disponible`, `sin_fila` para niveles que no son grupo unitario, `no_disponible`).
- `GET /api/sinco/{codigo}` agrega la llave `probabilidad_automatizacion_fo` (mismo contenido) y las coincidencias incluyen `onet_titulo`; `/api/meta` informa su estado.
- Columnas de probabilidad (por SINCO, repetidas en sus 2 filas): `probabilidad_automatizacion_fo` (media ponderada por similitud, softmax sobre los 2 candidatos),
  `_media_uniforme`, `_min`, `_max`, `_top1`, `n_candidatos`, `cobertura_peso_fo`, `cobertura_fo`, `motivo_na` (causa del NA: `sin_coincidencia` o `sin_probabilidad_fo`),
  `probabilidad_es_na`, `probabilidad_estado_validacion`. Son NA cuando `match_status = sin_coincidencia` o el SOC 2010 alcanzado no tiene valor Frey-Osborne.

### Descarga: `GET /api/download/dataset`
Una fila por (grupo SINCO, O*NET emparejado), sin filtros = dataset completo (980 filas con el crosswalk top-2 actual). Columnas: `sinco_code, sinco_titulo, nivel, division,
rango, onet_soc_code, onet_titulo, similitud, margen, modelo, tipo_relacion, match_status, baja_confianza, estado_validacion, fuente, run_id` + probabilidad (si existe la tabla).
`similitud` es un coseno, no una probabilidad.

| Parametro | Valores | Notas |
|---|---|---|
| `formato` | `csv` (defecto), `json`, `parquet` | otro valor -> 422 |
| `sinco_prefix` | 1 a 4 digitos (`[1-9][0-9]{0,3}`) | codigo o prefijo SINCO |
| `division` | 1..9 | |
| `nivel` | `division`, `grupo_principal`, `subgrupo`, `grupo_unitario` | el dataset solo tiene grupos unitarios: otros niveles -> 0 filas |
| `q` | texto, <= 100 caracteres | insensible a acentos, igual que `/api/sinco/search` (min. 2 caracteres) |
| `rango_max` | 1 o 2 | 1 = solo el mejor match |
| `solo_con_probabilidad` | bool | excluye SINCO con NA; sin tabla de probabilidad -> 409 |
| `modelo` | modelo principal por defecto | el no principal sale de `match_candidatos.parquet` (mismo run, top-2); desconocido -> 422 |

`GET /api/download/conteo` acepta los mismos parametros y devuelve cuantas filas tendria la descarga (lo usa la interfaz).
Errores: 422 parametros invalidos, 409 crosswalk pendiente / probabilidad pedida pero no disponible. HEAD funciona; otro metodo -> 405.

Procedencia y seguridad de las descargas:
- Aviso: cabecera `X-Atribucion` ("O*NET (USDOL/ETA, CC BY 4.0); SINCO 2019 (INEGI); Frey y Osborne (2013/2017). Resultados de emparejamiento automatico NO validados.")
  en los tres formatos; ademas JSON trae `meta` (filtros, atribucion, run_id, estado de la probabilidad, columnas) y Parquet lleva `atribucion` y `meta` en los metadatos del esquema.
  El CSV no lleva comentarios en el cuerpo (rompen lectores); la cabecera HTTP no sobrevive a "guardar como", asi que la interfaz repite el aviso junto al boton.
- Otras cabeceras: `X-Filas`, `X-Filas-Truncadas`, `X-Probabilidad` (`disponible`/`no_disponible`).
- `Content-Disposition: attachment; filename="sinco_onet_completo.<ext>"` o `sinco_onet_filtrado.<ext>`: nombre fijo, nunca derivado de la entrada.
- Tope de `TOPE_FILAS_DESCARGA = 50000` filas (hoy el maximo posible es 980); la respuesta se arma en memoria (< 1 MB) y `X-Filas-Truncadas: true` avisa si se recorta.
- CSV en UTF-8 con BOM (Excel). **Inyeccion de formulas**: toda celda de TEXTO cuyo primer caracter visible sea `=`, `+`, `-`, `@`, tab o CR se prefija con una comilla simple `'`
  (OWASP CSV injection); las columnas numericas y booleanas no se alteran. JSON y Parquet conservan el valor original.
- Los mismos limites de endurecimiento (solo GET/HEAD, hosts, CSP, `no-store`); nada se escribe en `data/`. El Dockerfile y el hosting no se tocaron (pendiente).

Interfaz: el detalle de cada grupo unitario muestra los 2 matches (titulo O*NET, similitud, rango, margen) y un bloque "Probabilidad de automatizacion (Frey-Osborne)" con etiqueta "NO validada"
y un tooltip (?) que explica que es y que NO es. El menu "Descargar" (encabezado) ofrece dataset completo o filtrado con la seleccion actual (division, codigo, texto), `rango_max`, formato y conteo previo.

## Resumen de coincidencias: `GET /api/resumen[?modelo=]` y pestana "Resumen"
Pestana inicial de la pagina principal (el sunburst, O*NET y Fuentes siguen en sus pestanas; `/#sinco` abre el sunburst). Todas las cifras las calcula `service.resumen()` a partir de
`crosswalk.parquet` (modelo principal), `sinco.parquet`, `onet_ocupaciones.parquet` y `sinco_probabilidad_fo.parquet`; ni el HTML ni el JS llevan cifras fijas. Solo GET/HEAD, mismo endurecimiento.
- `modelo`: principal por defecto (bge-m3). El alterno (multilingual-e5-large) sale de `match_candidatos` (pares top-2) y `match_sinco_resumen` (estado); no trae `tipos_relacion`. Desconocido -> 422.
- Estado de un grupo = `match_status` de su fila de rango 1: `ok`, `baja_confianza`, `sin_coincidencia`. "Con match" = ok + baja_confianza.
- Respuesta: `estado` (`disponible` | `pendiente` sin crosswalk | `esquema_invalido`; en esos casos solo `mensaje`, sin KPIs), `etiqueta_aviso`, `modelo`, `modelos_disponibles`, `run_id`,
  `kpis` (grupos_unitarios, con_match y %, con_match_confiable, baja_confianza, sin_coincidencia, onet_total, onet_distintas_emparejadas (distintas en el top-2 de grupos con coincidencia) y %,
  similitud_rango1_media/mediana, pares_top2, tipos_relacion), `por_estado`, `por_division` (division 1-9, nombre, total, ok, baja_confianza, sin_coincidencia),
  `histograma_similitud_rango1` (bins de 0.05) y `probabilidad_automatizacion_fo` (solo disponibilidad: n_con_valor, n_na, causas_na; sin la tabla -> `estado: no_disponible`, "probabilidad no disponible").
- Sin llaves de exposicion ni score; la unica llave de probabilidad es `probabilidad_automatizacion_fo` (rotulada, NO validada). Aviso visible: coincidencias automaticas NO validadas; probabilidad F-O != exposicion a IA.
- Interfaz: tarjetas KPI, barras apiladas por division (clic -> sunburst en esa division), barras por estado e histograma, en HTML/CSS propios (sin CDN; CSP sin cambios). Azul = con coincidencia, naranja rayado = baja confianza,
  gris = sin coincidencia (no se depende solo del color: leyenda, valores en las barras, `aria-label` y "Ver como tabla"). Tema claro/oscuro segun el sistema (`prefers-color-scheme`).
- Pruebas: `tests/api/test_resumen.py`.
