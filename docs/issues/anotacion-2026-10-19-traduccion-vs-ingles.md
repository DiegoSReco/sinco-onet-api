# Issue: anotar el ingles original o la traduccion al espanol

- Fuente: 001 sec. 6.4 (sugiere anotar ingles y espanol en una submuestra) y sec. 7 (campo `task_text_es`). 001 no decide cual se anota.
- Estado: no existe tabla de traduccion en data/processed/.
- Opcion provisional (implementada): anotar `task_text_en`; `task_text_es` y `translation_version` nulos; `annotated_text_lang='en'`. El esquema y el prompt ya admiten `es`.
- Requiere decision del usuario: (a) anotar ingles; (b) anotar espanol cuando exista traduccion; (c) ambos en una submuestra para medir discrepancia.
