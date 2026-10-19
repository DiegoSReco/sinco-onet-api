# sinco-onet-api

API de solo lectura y diagrama interactivo del catálogo **SINCO 2019** (INEGI) y de las ocupaciones y tareas de **O\*NET**, con un emparejamiento automático SINCO → O\*NET-SOC basado en embeddings.

> **Estado: trabajo en curso.** El emparejamiento (los 2 O\*NET-SOC más similares por grupo SINCO) está marcado `sin_validar` (no se ha revisado con personas) y varias decisiones metodológicas están pendientes de revisión humana (ver `docs/decisions/`). La API muestra y permite descargar la **probabilidad de automatización (Frey-Osborne)**, claramente rotulada como no validada. **No publica puntajes de exposición a IA**: esa medida aún no se ha calculado.

## Qué contiene

- `src/api/`: API en FastAPI (solo GET/HEAD) y página estática con un resumen de KPIs, un sunburst de la jerarquía SINCO, detalle por nodo, catálogo O\*NET, panel de coincidencias con su probabilidad de automatización (Frey-Osborne), y descarga del dataset completo o filtrado (CSV, JSON, Parquet).
- `src/score/`: módulo para calcular exposición (rúbrica 001); todavía no se ha ejecutado sobre datos completos.
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
- **Probabilidad de automatización (Frey-Osborne)**: la tabla `data/processed/sinco_probabilidad_fo.parquet` y `match_cobertura.json` contienen probabilidades de computarización de Frey y Osborne trasladadas a grupos unitarios SINCO mediante el emparejamiento automático. **Es una medida de automatización de ocupaciones de EE. UU., no de exposición a IA ni de riesgo de pérdida de empleo en México, y depende de un emparejamiento sin validar.** Fuente original (cítese siempre):
  - Frey, C. B. y Osborne, M. A. (2013). *The Future of Employment: How susceptible are jobs to computerisation?* Oxford Martin School, Universidad de Oxford (documento de trabajo, 17 de septiembre de 2013). https://www.oxfordmartin.ox.ac.uk/publications/the-future-of-employment
  - Frey, C. B. y Osborne, M. A. (2017). The future of employment: How susceptible are jobs to computerisation? *Technological Forecasting and Social Change*, 114, 254-280. https://doi.org/10.1016/j.techfore.2016.08.019
  - Los autores y Oxford Martin no declaran una licencia de redistribución en el documento de trabajo que se consultó. **El autor de este repositorio publica estas probabilidades derivadas asumiendo ese riesgo y se compromete a retirarlas si algún titular de derechos lo solicita** (abrir un *issue* en este repositorio).
  - **No se incluyen** el PDF de Frey y Osborne ni la tabla cruda de 702 ocupaciones por código SOC. El código para extraerla (`src/ingest/05_frey_osborne.R`) sí está, pero cada usuario debe obtener el PDF por su cuenta.
- **Antecedente metodológico**: Ceballos Mina, O. E. y Guadarrama Gómez, H. (2025). La automatización del empleo en México y sus efectos sobre las disparidades salariales. *Desarrollo y Sociedad*, núm. 100. https://doi.org/10.13043/DYS.100.1. Adapta las probabilidades de Frey y Osborne a ocupaciones del SINCO; el texto consultado no describe cómo se hizo el emparejamiento.

## Qué NO es

- No es una medida de pérdida de empleo ni de adopción tecnológica.
- Las coincidencias SINCO ↔ O\*NET son automáticas, sin validar, y dependen del modelo de embeddings usado (el acuerdo del top-1 entre BGE-M3 y multilingual-e5-large es de 45.7 %); los parámetros son provisionales.
- La probabilidad de automatización (Frey-Osborne) no es exposición a IA: mide la susceptibilidad de ocupaciones de EE. UU. a la computarización, trasladada por un emparejamiento automático.
- Las tareas de O\*NET describen ocupaciones de EE. UU. y pueden no reflejar el trabajo real en México.

## Licencia

Código y documentación original: [MIT](LICENSE). Los datos de terceros conservan sus propias condiciones (arriba).
