# Diccionario de datos: anotacion (src/annotate/)

## data/processed/annotations/piloto_tareas.parquet (40 filas; meta en piloto_tareas.meta.json)
| columna | tipo | descripcion |
|---|---|---|
| task_id | str | Task ID de O*NET (con onet_soc forma la clave) |
| onet_soc | str | codigo O*NET-SOC (NN-NNNN.NN) |
| onet_title | str | titulo de la ocupacion (onet_ocupaciones.parquet) |
| task_text_en | str | texto original (tareas_onet_en.parquet) |
| task_text_es | null | sin traduccion aun |
| task_type | str/null | core / supplemental / nulo (418 tareas sin tipo en O*NET 31.0); fuente: Task Statements.txt del zip crudo |
| importance_im, relevance_rt | float/null | escalas IM y RT de tareas_onet_ratings.parquet (nulas si no hay ratings) |
| major_group | str | 2 primeros digitos del SOC |
| stratum | str | core / supplemental / sin_tipo |

## data/processed/annotations/run_{run_id}.parquet (un registro por run_id, task_id; clase `Annotation`)
| columna | tipo | descripcion |
|---|---|---|
| run_id | str | `{base}-{NN}` |
| prompt_version, prompt_sha256 | str | version y hash del archivo de prompt |
| model | str | modelo anotador (`dry-run-sim` en pruebas) |
| run_date | date | fecha de la corrida |
| onet_version | str | version de O*NET (31.0) |
| onet_soc, task_id | str | identificadores |
| task_text_en, task_text_es | str / nulo | textos; es nulo mientras no exista traduccion |
| translation_version | str/nulo | version de traduccion |
| annotated_text_lang | en/es | texto que vio el modelo |
| task_type | core/supplemental/nulo | tipo de tarea O*NET |
| exposure_class | E0/E1/E2 | clase ordinal; sin puntaje numerico |
| physical_bottleneck | bool | cuello de botella fisico |
| confidence | alta/media/baja | confianza |
| rationale | str (<=600) | justificacion breve |
| capability_cutoff | str/nulo | fecha de corte (nulo mientras "requiere decision") |
| temperature | float/nulo | nulo cuando no es controlable (subagentes) |
| temperature_note | str/nulo | p. ej. `solicitada 1.0, no controlable; valor por defecto de la sesion` |
| seed | int/nulo | nulo en modo subagente (no aplica) |

Las corridas de prueba estan en `annotations/dryrun/` y no son resultados.

## Modo subagente
- `annotations/pilot_inputs/<run_id>.json`: run_id, prompt_version, prompt_sha256, model, run_date, capability_cutoff, annotated_text_lang, onet_version, order_seed, temperature_note, system_prompt (con fecha de corte), formato_salida, tareas[] (task_id, onet_soc, onet_title, task_text_en, task_type, user_prompt).
- `annotations/pilot_outputs/<run_id>.jsonl` (lo produce el anotador): una linea por tarea: `task_id`, `exposure_class`, `physical_bottleneck`, `confidence`, `rationale`.
- `annotations/pilot/run_<run_id>.parquet`: clase `Annotation` completa, con model `claude-sonnet-5-5 (subagente Claude Code)`.
