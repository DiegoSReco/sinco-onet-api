# 004 - API de solo lectura y diagrama SINCO / O*NET: framework y despliegue

> **ESTADO: APROBADA POR EL USUARIO (2026-10-19). DECISIÓN VIGENTE: opción B (FastAPI + starlette + uvicorn)** (ver Registro 3). La opción A (servidor de biblioteca estándar) queda como servidor de respaldo mientras exista. Hosting público: requiere decisión. Registro 4 (columnas opcionales del Método A1 y dependencia transitiva): pendiente de confirmación del usuario.
> Fecha: 2026-10-19. No calcula exposicion ni scores. No decide metodologia de crosswalk (regla 7 de CLAUDE.md).

## Registro de aprobación (1)

Cita textual del usuario (2026-10-19): "Aprobado 004, 001 y 003. La solicitud de la tabla no la necesitamos ya estan las tablas del catálogo".

Lo que se aprobó entonces (registrado por el agente de métodos): la **opción A** de esta decisión (la recomendada y ya implementada): capa de servicio en Python, servidor HTTP de solo lectura con la biblioteca estándar (`http.server`), página estática, entrada Parquet y salida JSON, despliegue local. **Cero paquetes nuevos** en la opción A. Este registro reemplazó la nota anterior que señalaba la ambigüedad del "Apruebo" previo. El estado vacío del panel de coincidencias y el contrato de `crosswalk.parquet` se mantienen. (Superado en cuanto a FastAPI por el Registro 3.)

## Registro 2 (2026-10-19): aprobación de pendientes e incluyendo uvicorn

Cita textual del usuario: "Si, aprobar pendientes incluyendo uvicorn."

- **uvicorn aprobado como dependencia** (ya estaba instalado, versión 0.54.0 según el entorno verificado). En ese momento no aprobaba FastAPI ni starlette; uvicorn solo corre aplicaciones ASGI y no tenía uso en la opción A.
- "Aprobar pendientes" se aplicó a las preguntas abiertas de esta decisión con recomendación explícita en el documento. Las que no tienen recomendación concreta siguen como "requiere decisión"; no se inventan valores.

## Registro 3 (2026-10-19): el usuario elige la opción B (FastAPI)

Citas textuales del usuario: "Continua con: Exposicion, Crosswalk y matching, Despliegue (continua con la opcion B 'FastApi'). Si es necesario crea un repositorio en mi cuenta de github para el despliegue." y, ante opciones, eligió el repositorio "Público, solo código y docs" (ver decisión 007).

Registro (sin ampliar):
- **Opción B elegida.** Quedan **aprobados `fastapi`, `starlette` y `uvicorn`**. Se aprueba además `httpx` **solo como dependencia de pruebas** (para `TestClient`), si hace falta; no como dependencia de ejecución.
- **Decisión vigente: B.** La opción A (servidor `http.server`, `src/api/server.py`) queda como **servidor de respaldo mientras exista**; no se requiere mantenerlo ni extenderlo.
- **Pregunta abierta "migrar a la opción B": RESUELTA** (sí).
- La capa de servicio pura (`src/api/service.py`) se mantiene como lógica de negocio independiente del servidor; las rutas de FastAPI deben ser una capa delgada sobre ella (migración estimada en ~50 líneas de rutas, según el análisis de esta decisión; no verificado por mí).
- Las restricciones de diseño se mantienen: solo GET, sin escritura en `data/raw/` ni `data/processed/`, lista blanca de columnas por endpoint, ningún endpoint devuelve scores, exposición ni valoraciones de `tareas_onet_ratings`, y el contrato de `crosswalk.parquet`. Los endpoints se conservan; FastAPI aportará OpenAPI automático.
- **Hosting público sigue "requiere decisión"** (opciones D, E o B+E; autenticación, CORS, costo no verificado, licencias). La elección de B no equivale a aprobar hosting público ni a publicar datos. El repositorio público contiene solo código y docs (decisión 007).
- No verifiqué versiones ni compatibilidad de fastapi/starlette/httpx con Python 3.14.3; el implementador debe registrarlas y comprobarlas. La instalación la hace el implementador, no esta decisión.
- Ambigüedad: el usuario dijo "FastApi"; starlette es dependencia transitiva de FastAPI y se aprobó explícitamente por claridad (instrucción del coordinador).

## Registro 4 (2026-10-19): ampliación del esquema del crosswalk y dependencia transitiva — PENDIENTE DE CONFIRMACIÓN DEL USUARIO

Hechos reportados por el coordinador (no verificados por mí; no leí el código ni el Parquet):
1. **El agente de la API añadió columnas opcionales del Método A1 (005) al esquema del crosswalk:** `modelo`, `rango`, `similitud`, `margen`, `similitud_alt`, `rango_alt`, `modelo_alt`, `baja_confianza`, `match_status`.
2. **pip trajo `opentelemetry-api` como dependencia transitiva de fastapi.**

Registro y reservas:
- **La ampliación del esquema NO está aprobada por el usuario**; queda "pendiente de confirmación". Hasta que se confirme, estas columnas deben tratarse como una propuesta del agente de la API.
- Tensión con el contrato de esta decisión: el contrato dice que el esquema "no admite columnas de score, exposición ni probabilidad". Las columnas nuevas (`similitud`, `margen`, `rango`) son medidas de similitud de embeddings del emparejamiento, no scores de exposición ni probabilidades de Frey-Osborne; son las que 005 §4.2 y §5.4 exigen conservar ("nada se descarta en silencio"). Aun así, la lista blanca y la prueba automática que detecta nombres tipo score/exposure/prob deben revisarse para que `similitud`/`baja_confianza` no disparen falsos positivos ni se confundan con scores. **Requiere confirmación.**
- Consistencia con 005: `match_status` y `baja_confianza` coinciden con los nombres de 005 §5.4 y §5.6; `modelo`/`modelo_alt` implican la comparación BGE-M3 frente a multilingual-e5-large (005 §5.3), con registro de modelo y revisión (005 R.2); `rango_alt` y `similitud_alt` serían los de la variante alternativa. Esas correspondencias son mi lectura de los nombres, no lo verifiqué en el código.
- Regla 4: cada fila debe seguir llevando `run_id`; el registro completo de la corrida (revisión del modelo, `text_template_version`, semilla, hashes) no cabe en las columnas del crosswalk y debe estar en otro artefacto.
- Los resultados del emparejamiento siguen marcados NO validados (005 R.4); la API debe mostrarlos con ese rótulo.
- **`opentelemetry-api`:** dependencia transitiva de fastapi, **no aprobada explícitamente** (el usuario aprobó fastapi, starlette, uvicorn y httpx solo para pruebas). Las dependencias transitivas de un paquete aprobado se consideran incluidas por defecto en la práctica, pero no hay una regla del proyecto que lo diga: **pendiente de confirmación**. No la verifiqué (no sé qué versión ni quién la requiere). Debe constar en la lista de versiones instaladas (y, si aplica, en `requirements`/lockfile), y revisarse la superficie de seguridad (riesgo 6).
- Preguntas para el usuario: (a) ¿confirma la ampliación del esquema con esas columnas? (b) ¿acepta `opentelemetry-api` como transitiva?

## Pregunta
Como se sirve, para visualizacion, la jerarquia SINCO 2019 (con su texto por nodo) y el catalogo O*NET (ocupaciones y tareas), con un espacio para las coincidencias SINCO-O*NET que hoy no existen.

## Entorno verificado (2026-10-19, `python --version` = 3.14.3, sin `-I`)
Disponibles: pandas 3.0.6, pyarrow 26.0.0, pydantic 2.14.1, pytest 9.1.1, streamlit 1.66.0, uvicorn 0.54.0.
NO disponibles (a esa fecha, antes del Registro 3): fastapi, starlette, flask, plotly, httpx. No hay Docker. Node 18+ existe pero no se usa.
Aprobados por el proyecto (CLAUDE.md / 002 / esta decision): pandas, pyarrow, pydantic, streamlit, pytest (Python); arrow, janitor, httr2, testthat (R); uvicorn, fastapi, starlette y (solo pruebas) httpx.

## Recomendacion (original; vigente la opcion B segun el Registro 3)
1. **Capa de servicio pura** (`src/api/service.py`): funciones Python que leen los Parquet con pyarrow/pandas y devuelven dicts validados con pydantic. Es la logica de negocio; no depende del servidor.
2. **Servidor HTTP de solo lectura con la libreria estandar** (`http.server.ThreadingHTTPServer`, `src/api/server.py`): solo GET; cualquier otro metodo responde 405. Sirve `/api/*` (JSON) y la pagina estatica `/`. **Cero paquetes nuevos**, arranca con `python -m src.api.server`. (Ahora servidor de respaldo; el vigente es FastAPI.)
3. **Diagrama**: pagina estatica unica (HTML + JS + SVG propios, sin CDN ni librerias): sunburst de la jerarquia SINCO (4 niveles, clic = zoom), panel de detalle por nodo (descripcion, ocupaciones ejemplo, funciones, incluye/excluye con referencias, pagina del PDF) y vista de ocupaciones O*NET (busqueda, descripcion, tareas). Panel "Coincidencias SINCO - O*NET" con estado vacio explicito: *coincidencias pendientes de crosswalk* mientras no exista `data/processed/crosswalk.parquet`.
4. **Formato de datos**: Parquet de entrada (intercambio acordado, decision 002) y JSON de salida. La API no escribe nada en `data/raw/` ni `data/processed/`.
5. **Despliegue**: local primero (`uvicorn` con la app FastAPI, o el servidor de respaldo). Hosting publico despues, solo si el usuario lo decide: ver alternativas.

### Contrato del crosswalk (esquema declarado; no se inventa contenido)
`data/processed/crosswalk.parquet`, una fila por par (sinco_code, onet_soc_code):

| Columna | Tipo | Regla |
|---|---|---|
| sinco_code | texto | existe en `sinco.parquet` |
| onet_soc_code | texto | existe en `onet_ocupaciones.parquet` |
| tipo_relacion | texto | uno de `1:1`, `1:N`, `N:1`, `M:N` (definicion en 003) |
| fuente | texto | procedencia declarada (p. ej. `inegi`, `semiautomatico`, `manual`); sin valor por defecto |
| estado_validacion | texto | `sin_validar`, `validado`, `rechazado` |

Columnas opcionales aceptadas y mostradas tal cual si existen (no requeridas): `isco08_code`, `notas`, `match_quality`, `crosswalk_confidence`, `run_id`. Esto permite que el emparejamiento propuesto por el agente de metodos (005, embeddings) escriba el mismo archivo despues, con su `run_id`, sin cambiar la API. (Ampliacion propuesta por el agente de la API, pendiente de confirmacion: ver Registro 4.) Si el archivo existe pero no cumple el esquema, la API responde `estado: "esquema_invalido"` con la causa y NO muestra filas (regla 5). El esquema no admite columnas de score, exposicion ni probabilidad: si aparecen, se ignoran y se informa.
Un generador provisional de candidatos NO se implementa aqui (decision metodologica; lo cubre 005).

### Endpoints (todos GET, sin escritura)
`/api/health`, `/api/meta` (hash y version de fuentes, estado del crosswalk), `/api/sinco/tree`, `/api/sinco/{codigo}`, `/api/sinco/search?q=`, `/api/onet/occupations?q=&limit=&offset=`, `/api/onet/occupations/{soc}`, `/api/crosswalk?sinco_code=&onet_soc_code=`, `/api/crosswalk/schema`. Ningun endpoint devuelve scores, exposicion ni las valoraciones (importancia/frecuencia/relevancia) de `tareas_onet_ratings`.

## Alternativas

| Opcion | Ventajas | Costos / riesgos |
|---|---|---|
| A. stdlib `http.server` + pyarrow/pandas/pydantic + pagina estatica (**implementada; ahora servidor de respaldo**) | 0 paquetes nuevos; cumple limites; portable; facil de probar | No es un framework: sin OpenAPI automatico, sin async, ni endurecimiento para internet. Adecuada para local/red interna, no para trafico publico |
| B. FastAPI + starlette + uvicorn (**ELEGIDA por el usuario, Registro 3; vigente**) | Estandar de facto; OpenAPI/Swagger automatico; validacion con pydantic directa | Requiere instalar `fastapi` y `starlette` (uvicorn ya esta); httpx solo para pruebas. La capa de servicio ya esta separada, migrar son ~50 lineas de rutas. Compatibilidad con Python 3.14.3 no verificada |
| C. Streamlit (ya aprobado) | Aprobado en CLAUDE.md; rapido para tablas | Es dashboard, no API; sunburst interactivo requeriria plotly/altair (altair viene con streamlit pero no verificado); CLAUDE.md reserva `dashboard/` a una fase posterior |
| D. Sitio 100 % estatico (JSON precalculado en GitHub Pages / Netlify) | Hosting gratis y sin servidor; ideal para publico | No es una API dinamica; hay que regenerar JSON al cambiar datos; el JSON publico expone los datos (SINCO y O*NET son publicos, pero revisar licencia O*NET: CC BY 4.0 con atribucion) |
| E. Docker + hosting (Fly.io/Render/Cloud Run) | Reproducible, escalable | Docker no esta instalado; costo mensual (nivel gratuito limitado, ~0-7 USD/mes para una instancia pequena; no verificado hoy); requiere decidir autenticacion y CORS |

Ruta: B en local ahora. Para publicar: B+E (API publica) o D (exportar los JSON a estatico); ambas requieren decision humana y revision de licencias (decision 007).

## Paquetes y aprobaciones
- **Aprobados:** `fastapi`, `starlette`, `uvicorn`; `httpx` solo para pruebas (`TestClient`). Opcional para despliegue: `gunicorn` o similar: **no aprobado**.
- `opentelemetry-api` (transitiva de fastapi): pendiente de confirmacion (Registro 4).
- Opcion A: ninguno nuevo.

## Riesgos y mitigaciones
1. Mostrar coincidencias que parezcan oficiales: estado vacio explicito, columnas `fuente` y `estado_validacion` obligatorias, y aviso permanente de "no es una correspondencia oficial" cuando `fuente` no sea INEGI.
2. Fuga de exposicion/scores: lista blanca de columnas por endpoint y prueba automatica que falla si aparecen nombres tipo score/exposure/prob. Con FastAPI, el esquema OpenAPI automatico no debe exponer campos fuera de la lista blanca (usar modelos de respuesta pydantic explicitos). Revisar que las columnas del Registro 4 no produzcan falsos positivos.
3. Servidor expuesto a internet: con B es mas defendible que `http.server`, pero no se publica ninguna instancia sin decidir hosting, autenticacion, CORS y licencias (ver 007).
4. Licencia/atribucion: O*NET (CC BY 4.0, atribucion a USDOL/ETA) y SINCO (INEGI, termino de libre uso, citar fuente). Incluir atribucion en la pagina.
5. Rendimiento: 11 tablas Parquet pequenas (<20 MB en memoria); se cargan una vez y se cachean; solo lectura.
6. Aprobar dependencias nuevas (y sus transitivas, p. ej. opentelemetry-api) aumenta la superficie de mantenimiento y de seguridad: fijar versiones y registrarlas.

## Preguntas abiertas para el humano (estado tras el Registro 4)
1. FastAPI (opcion B) y uvicorn. **RESUELTA: aprobados (Registro 3).** Pregunta de migrar a B: **resuelta (si).**
2. Publico objetivo: local/interno o publico en internet. **Local primero aprobado.** Hosting publico (D, E o B+E): **requiere decision**; no se inventa.
3. Idioma de la interfaz. **APROBADO: espanol** (como esta implementado).
4. Quien alimenta `crosswalk.parquet` y con que `fuente`/`estado_validacion` iniciales. **APROBADO segun el contrato de esta decision y 005 R.4.7:** el emparejamiento de 005 escribe el archivo con `fuente` declarada (p. ej. `semiautomatico`), `estado_validacion = sin_validar` y `run_id`, sin columnas de score.
5. Atribucion y licencias en la pagina (riesgo 4). **APROBADO el valor recomendado:** incluir atribucion a O*NET (CC BY 4.0, USDOL/ETA) y a INEGI. El texto exacto de la atribucion y la licencia del PDF de Frey-Osborne (si algun dia se muestra) **requieren decision**.
6. Hosting publico con datos, autenticacion, CORS y costos: **requiere decision** (ver 007).
7. (Nueva, Registro 4) Confirmar la ampliacion del esquema del crosswalk con las columnas del Metodo A1 y aceptar `opentelemetry-api` como transitiva: **pendiente de confirmacion del usuario.**
