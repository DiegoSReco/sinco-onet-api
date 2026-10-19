# src/annotate/ - anotacion de tareas O*NET (fase annotate)

Estado: preparacion y piloto de 40 tareas. Decision del usuario: modelo Claude Sonnet 5.5, SIN API (sin clave ni gasto); anotan subagentes de Claude Code (modo `subagent.py`). Existe ademas el cliente simulado `dry-run`. La corrida completa (`--sample full`) esta deshabilitada.

Base: `docs/rubric.md` v1, `docs/glossary.md` v1, decision 001 (4.3, 4.4, 7) y 006.

## Archivos
- `config.toml` / `config.py`: parametros (semilla, piloto, reintentos, mapa numerico, decisiones pendientes marcadas "requiere decision").
- `schemas.py`: `ModelOutput` (lo que devuelve el modelo) y `Annotation` (registro por `run_id`, `task_id`), esquema Arrow y lectura/escritura Parquet con revalidacion.
- `prompts/v1.md` + `prompt.py`: prompt `ann-v1`; `guardar_doc` escribe `docs/prompts/ann-v1.md` (inmutable por version).
- `providers.py`: `LLMProvider` abstracto, `DryRunProvider`; `crear()` falla con proveedores reales.
- `pilot.py`: tabla de tareas y seleccion reproducible del piloto.
- `runner.py`: corrida independiente, reintentos, issues, n corridas. `run.py`: CLI.

## Comandos (desde la raiz, con `.venv\Scripts\python`)

    python -m src.annotate.pilot                       # regenera data/processed/annotations/piloto_tareas.parquet
    python -m src.annotate.run --run-id R --model M --temperature 0.0 --n-runs 2   # dry-run -> annotations/dryrun/
    python -m pytest tests/annotate -q

## Reglas implementadas
- Una anotacion por (run_id, task_id); validacion estricta (`extra=forbid`, tipos estrictos); sin puntajes continuos.
- El mapa E0/E1/E2 -> 0/0.5/1 esta solo en `config.toml`; este modulo no lo aplica ni agrega nada (eso es de `score`).
- Salida del modelo: JSON puro; si es invalido se reintenta (`max_reintentos_formato`); fallos de API con backoff exponencial acotado (`max_reintentos_api`, `backoff_max_s`). Una tarea que no se logra anotar NO se inventa: se registra en `docs/issues/anotacion-{run_id}.md`. Si el Parquet no cumple el esquema se escribe el issue y se lanza excepcion.
- Independencia: cada corrida tiene `run_id` `{base}-{NN}`, semilla `seed_base+NN`, proveedor nuevo y orden de tareas propio; no lee otras corridas. Un Parquet de corrida no se sobrescribe.
- El prompt no declara umbral de tiempo (001 3.3 [NO VERIFICADO]). La fecha de corte de capacidades es parametro (`[capacidades].fecha_corte = "requiere decision"`); con proveedor real el CLI se niega a correr mientras siga pendiente.
- Las salidas `dry-run` (modelo `dry-run-sim`) son ruido determinista para probar el pipeline; no son resultados.

## Decisiones provisionales (ver docs/issues/anotacion-2026-10-19-*.md)
1. Texto anotado: ingles original (no existe traduccion); `task_text_es` nulo.
2. Modelo, proveedor, temperatura, fecha de corte y presupuesto: sin definir.
3. `task_type`: no esta en las tablas procesadas; se lee del zip crudo (solo lectura). 418 tareas sin tipo.
4. Se anotan todas las tareas (core y suplementarias) marcando `task_type`; la medida principal usara core (la decide `score`).
5. El prompt incluye el titulo de la ocupacion O*NET como contexto.

## Modo subagente (sin API, sin red) - `subagent.py`
Decisiones del usuario: 3 corridas independientes, texto en ingles, fecha de corte = fecha de la corrida (parametro explicito), temperatura 1.0 solicitada pero NO controlable en subagentes (se registra `temperature = nulo` y `temperature_note = "solicitada 1.0, no controlable; valor por defecto de la sesion"`; `seed` nulo). No se requiere clave.

    python -m src.annotate.subagent export --date 2026-10-19          # escribe pilot_inputs/<run_id>.json (3 corridas)
    # cada subagente escribe pilot_outputs/<run_id>.jsonl (formato en el JSON de entrada, clave `formato_salida`)
    python -m src.annotate.subagent import --run-id <run_id>          # valida y escribe pilot/run_<run_id>.parquet

- Entrada: prompt `ann-v1` con la fecha de corte rellenada (prompts/v1.md y su hash no cambian), 40 tareas en orden propio por corrida (semilla `seed_base+NN`).
- Salida: una linea JSON por tarea con `task_id` (solo identificador) y las 4 claves de `ModelOutput`. Se necesita `task_id` para enlazar la linea con la tarea.
- Import: validacion estricta; no hay reintento. Lineas invalidas, duplicadas, con task_id ajeno o tareas faltantes se listan como no anotadas en `docs/issues/anotacion-<run_id>.md`; nunca se inventan. Si el hash del prompt cambio desde el export, falla.
- Los subagentes no deben leer otras corridas ni archivos `pilot_outputs/` ajenos (independencia); eso lo garantiza el orquestador, no el codigo.
