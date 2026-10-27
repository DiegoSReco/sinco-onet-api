# Proyecto: Exposición a IA de ocupaciones en México (SINCO 2019)

## Objetivo
Estimar la exposición de cada ocupación de SINCO 2019 a sistemas de IA,
a partir de tareas de O*NET traducidas al español. El resultado principal
es exposición, no pérdida de empleo. Los escenarios de pérdida se reportan
por separado y con supuestos explícitos.

## Reglas
1. Ningún agente calcula scores a mano. Toda cifra sale de un script en src/.
2. No modificar docs/rubric.md ni docs/glossary.md sin decisión registrada en docs/decisions/.
3. Los datos en data/raw/ son inmutables. Registrar hash y fecha en data/raw/manifest.json.
4. Cada corrida de anotación registra prompt_version, modelo, fecha y run_id.
5. Si un entregable no cumple su esquema, escribir un issue en docs/issues/ y detenerse.
6. El texto del artículo solo cita cifras presentes en data/processed/.
7. Ninguna decisión metodológica se implementa sin estar en docs/decisions/.

## Orden de fases
ingest -> crosswalk/translate -> annotate (piloto -> completo) -> consistency -> score -> validate -> dashboard -> paper

## Stack
Python 3.11+, pandas, pyarrow, pydantic, streamlit, pytest.

## Stack por fase (actualizado)
- Ingesta y procesamiento de datos: R (src/ingest/*.R). Ver docs/decisions/002-stack-r.md.
- Anotación de tareas: Python (src/annotate/).
- Ya el date set limpio, Scoring, validación y dashboard: Python, salvo decisión contraria.
- Parquet es el formato de intercambio entre lenguajes.
