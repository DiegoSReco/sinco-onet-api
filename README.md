# sinco-onet-api

API de solo lectura y diagrama interactivo del catálogo **SINCO 2019** (INEGI) y de las ocupaciones y tareas de **O\*NET**, con un emparejamiento automático SINCO → O\*NET-SOC basado en embeddings.

> **Estado: trabajo en curso.** El emparejamiento está marcado `sin_validar` (no se ha revisado con personas) y varias decisiones metodológicas están pendientes de revisión humana (ver `docs/decisions/`). Esta API **no publica puntajes de exposición ni probabilidades de automatización**.

## Qué contiene

- `src/api/`: API en FastAPI (solo GET/HEAD) y página estática con un sunburst de la jerarquía SINCO, detalle por nodo, catálogo O\*NET y panel de coincidencias.
- `src/ingest/`: ingesta reproducible en R (SINCO desde el PDF oficial de INEGI, tareas de O\*NET, puentes entre clasificaciones).
- `src/match/`: método de emparejamiento SINCO → O\*NET-SOC con embeddings (BGE-M3 y multilingual-e5-large) y diseño de la muestra de revisión.
- `src/annotate/`: esquema, prompt versionado y utilidades del piloto de anotación.
- `docs/decisions/`: decisiones metodológicas (definición de exposición, requisitos de tablas, despliegue, emparejamiento, piloto). Varias están **pendientes de revisión humana** y contienen marcas `[NO VERIFICADO]`.
- `docs/diccionario_datos_*.md`: diccionarios de las tablas.
- `data/processed/`: tablas Parquet del catálogo SINCO, catálogo y tareas de O\*NET y el emparejamiento `crosswalk.parquet`. `data/raw/manifest.json` registra fuentes, versiones y hashes SHA-256 de los datos crudos, que no se redistribuyen.

## Ejecutar la API

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows; en Linux/macOS: source .venv/bin/activate
pip install -r requirements-api.txt
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001
```

Abrir http://127.0.0.1:8001/ (documentación OpenAPI en `/docs`). Más detalle en `src/api/README.md`. Por seguridad, el servidor solo acepta `Host` locales salvo configuración explícita (`SINCO_ALLOWED_HOSTS`).

Pruebas: `pip install -r requirements-api-dev.txt && python -m pytest tests/api -q`.

## Datos y atribuciones

- **SINCO 2019**: Sistema Nacional de Clasificación de Ocupaciones, INEGI. Tablas extraídas del PDF oficial (https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/702825198411.pdf). Las condiciones de reutilización de INEGI no han sido revisadas por el autor de este repositorio.
- **O\*NET** 31.0: O\*NET Resource Center / U.S. Department of Labor, licencia [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Las tablas de este repositorio son una transformación de la base de datos original (formato Parquet, nombres de columnas); no están avaladas por O\*NET ni por el Departamento de Trabajo.
- **Puente O\*NET-SOC 2010 → 2019**: O\*NET Center, CC BY 4.0.
- **No se incluyen** el PDF ni las tablas de probabilidades de computarización de Frey y Osborne (2013), porque su licencia de redistribución no está resuelta. El código para ingerirlas (`src/ingest/05_frey_osborne.R`) sí está, pero requiere que cada usuario obtenga el PDF por su cuenta.

## Qué NO es

- No es una medida de pérdida de empleo ni de adopción tecnológica.
- Las coincidencias SINCO ↔ O\*NET son automáticas, sin validar, y dependen del modelo de embeddings usado; los parámetros son provisionales.
- Las tareas de O\*NET describen ocupaciones de EE. UU. y pueden no reflejar el trabajo real en México.

## Licencia

Código y documentación original: [MIT](LICENSE). Los datos de terceros conservan sus propias condiciones (arriba).
