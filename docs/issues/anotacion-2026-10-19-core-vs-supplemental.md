# Issue: tareas centrales vs suplementarias

- `task_type` no esta en data/processed/tareas_onet_en.parquet ni en tareas_onet_ratings.parquet. Si esta en Task Statements.txt (zip crudo, hash verificado contra el manifest): 14071 Core, 4349 Supplemental, 418 sin tipo (las mismas 418 que no tienen ratings).
- Accion pedida al agente de datos (no se toca src/ingest): agregar `task_type` a una tabla procesada. Mientras tanto, src/annotate/pilot.py lee el zip crudo en solo lectura.
- 001 4.4 aprueba medida principal con tareas centrales; no dice si se anotan las suplementarias.
- Opcion provisional: anotar todas y guardar `task_type` (permite la variante con suplementarias). Las 418 sin tipo quedan con `task_type` nulo; el esquema lo admite; requiere decision si se anotan o se excluyen. El piloto incluye 28 core, 10 supplemental y 2 sin tipo.
