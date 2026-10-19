# Decisión 002: ingesta y procesamiento de datos en R

Estado: pendiente de revisión humana

Pregunta: ¿en qué lenguaje se implementan la ingesta, limpieza y validación de datos?

Decisión propuesta: R (tidyverse, arrow, janitor, httr2, digest, enoeR(https://github.com/DiegoSReco/enoeR)) para src/ingest/.
Python se mantiene para anotación de tareas (src/annotate/) y el dashboard (Streamlit), salvo que se decida otra cosa.

Riesgos: dos ecosistemas en el mismo proyecto. Mitigación: los intercambios entre lenguajes se hacen solo por archivos en data/processed/ con esquema fijo (Parquet).
