# src/score/ - metodo de exposicion (decision 001 sec. 4.3-4.5)

Estado: codigo y pruebas con datos sinteticos. **No hay resultados**: hoy solo existe el piloto (40 tareas, 40 ocupaciones de 1016).
Ninguna cifra de este modulo se cita en el articulo hasta correr sobre anotacion completa (regla 6).

## Archivos
- `exposicion.py`: funciones puras + CLI. `config.toml`: umbrales y rutas (valores PROVISIONAL marcados).
- El mapa E0/E1/E2 -> 0/0.5/1 y sus variantes **no estan aqui**: se leen de `src/annotate/config.toml` (`[mapa_numerico]`).
- Pruebas: `tests/score/test_exposicion.py` (`.venv\Scripts\python -m pytest tests/score`).

## Flujo
1. `cargar_anotaciones(rutas)`: una o varias corridas `run_*.parquet` (esquema `Annotation`); falla con `EsquemaIncumplido` ante filas invalidas, `(run_id, task_id)` repetido o metadatos inconsistentes dentro de un run_id.
2. `puntaje_tarea` / `agregar_puntajes_tarea`: `e_t` principal, inferior y superior.
3. `agregar_onet` (POR CORRIDA): `E_o` (tareas core, pesos iguales), `E_o_inferior`, `E_o_superior`, `E_o_todas` (core + suplementarias + sin tipo), `E_o_pond_im` / `E_o_pond_rt` (ponderadas por IM / RT de `tareas_onet_ratings`; **[NO VERIFICADO]** en 001), `share_E2`, `share_any` (sobre core), `n_*`, `cobertura_tareas` (= anotadas / tareas O*NET del universo). Ocupaciones sin core anotado: NA con `motivo_na`.
4. `resumen_entre_corridas` (**PROVISIONAL**): media, min, max por ocupacion entre corridas. Ver issue.
5. `agregar_sinco` (POR CORRIDA): `E_sinco` = media uniforme de `E_o` de las O*NET emparejadas elegibles; `E_sinco_min/max` = cota de ambiguedad del crosswalk; `n_onet_mapped`, `n_onet_con_anotacion`, `cobertura_onet`, `crosswalk_type`, `crosswalk_confidence` (derivado de `match_status`, el crosswalk no trae esa columna), `motivo_na`. Pares `sin_coincidencia` no cuentan como emparejados. **NA** si `cobertura_onet < umbral_onet_sinco` (`cobertura_insuficiente`) o si no hay pares usables (`sin_coincidencia`). Lee `crosswalk.parquet` en tiempo de ejecucion (no asume cuantos pares por grupo).
6. `ejecutar` / CLI: escribe en `data/processed/` `exposicion_ocupacion_onet`, `exposicion_ocupacion_onet_corridas`, `exposicion_sinco`, `exposicion_sinco_corridas` (.parquet, esquema pydantic -> pyarrow) y `exposicion_meta.json` (run_ids, prompt_version, modelos, fechas, version de rubrica, mapas, umbrales, sha256 de entradas y config).

## CLI
```
.venv\Scripts\python -m src.score.exposicion [--anotaciones ...] [--crosswalk ...] [--universo-tareas ...] [--ratings ...] [--salida-dir ...] [--permitir-piloto] [--sobrescribir]
```
Codigos de salida: 0 ok; 2 rechazado por piloto; 3 entrada fuera de esquema (escribe issue en `docs/issues/`, regla 5); 4 salidas ya existen.
Se considera piloto (config `[piloto]`, PROVISIONAL) si: run_id empieza con `piloto`/`dryrun`/`dry-run`, modelo `dry-run-sim`, o la cobertura del universo (ocupaciones o tareas) es < 0.95. Con `--permitir-piloto` los archivos llevan sufijo `_PILOTO` y cada fila `etiqueta = "PILOTO, NO RESULTADO"`. Salidas normales: `"PROVISIONAL, SIN VALIDAR"`.

## Que falta para correr con datos completos
Corrida completa de anotacion (decision 008 sec. 7: modelo, presupuesto, n corridas, idioma/traduccion, fecha de corte), tratamiento de las 418 tareas sin tipo, decision sobre agregacion entre corridas, umbrales de cobertura, pesos del crosswalk y revision del crosswalk (hoy `sin_validar`). Ver `docs/issues/score-2026-10-19-*.md`.
