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

## Corrida completa, ruta S (decision 015 sec. 3) - `ruta_s.py`, `ruta_s_validacion.py`, `prompts/ann-s-v1.md`
Unidad: la funcion SINCO (espanol original). Campos por funcion: `exposure_class` (E0/E1/E2), `eloundou_class` (EL0-EL3, rubrica A.1 literal en ingles con los 10 ejemplos copiados del PDF `eloundou_2023_v5_pdf`), `physical_bottleneck`, `confidence`, `rationale` (<= 25 palabras; solo aviso). Esquema: `AnnotationS` / `ModelOutputS` en `schemas.py` (el esquema de la ruta O no cambia). Parametros en `config.toml [ruta_s]`. `ann-s-v1` es inmutable: cualquier cambio es `ann-s-v2` (el hash del prompt se verifica al importar). Los 33 grupos sin funciones no entran (NA); los ejemplos de 5115 y el `Excluye` no van en el prompt; el item fusionado de 2281 (`2281-08`) se anota y se marca `item_fusionado` en los metadatos.

### Archivos (`data/processed/annotations/ruta_s/`)
- `inputs/<run_id>/<batch_id>.json`: lote autocontenido (system_prompt, user_prompt por grupo, funciones, formato, `mensaje_subagente`). Lo lee SOLO el orquestador.
- `<run_id>/estado.json` (por lote: pendiente|en_curso|ok|invalido|fallido, intentos, hashes, historial), `run_meta.json`, `intentos/<batch>_aK.txt` (respuesta cruda de cada intento; nunca se borra), `salida/<batch>.json` (lote validado), `parquet/run_<run_id>.parquet`.

### Comandos (con `.venv\Scripts\python -m src.annotate.ruta_s ...`)
`export --corridas 3 --fecha AAAA-MM-DD` | `estado [--run-id R] [--detalle]` | `mensaje --run-id R --lote L001` | `iniciar` | `importar --run-id R [--lote L001 --respuesta ARCHIVO]` | `interrumpir` | `reanudar` | `ensamblar` | `validar --run-ids R1 R2 R3` (exit 2 si no se acepta).

### Protocolo del orquestador (por corridas completas: corrida 1, luego 2, luego 3; hasta 4 lotes en paralelo)
1. `estado` para ver pendientes. Por cada lote `pendiente` o `invalido` (con intentos < 3): `iniciar --run-id R --lote L` (devuelve el numero de intento) y `mensaje --run-id R --lote L` para obtener el texto.
2. Lanzar un subagente NUEVO (tipo `general-purpose`, modelo sonnet) cuyo prompt es EXACTAMENTE:

       Eres un anotador de exposicion a IA. Esta tarea es independiente: no uses herramientas, no leas ni escribas archivos, no consultes otras anotaciones ni otras corridas. Todo el contenido esta en este mensaje. Responde unicamente con el JSONL pedido al final, sin bloques de codigo ni texto adicional.

       <salida literal del comando `mensaje` para ese lote>

3. Guardar la respuesta final del subagente, sin editarla, en un archivo temporal y ejecutar `importar --run-id R --lote L --respuesta ARCHIVO` (la copia a `intentos/L_aK.txt`, la valida y actualiza `estado.json`). El orquestador NO corrige, completa ni reordena nada de la respuesta.
4. Lote invalido: reintento con subagente nuevo y la misma entrada, hasta 2 reintentos (3 intentos). Cada intento invalido agrega una linea al issue `docs/issues/anotacion-ruta-s-<run_id>.md`. Tercer fallo: lote `fallido`, la corrida queda `detenida` y se espera decision humana. Limite de cuota o error de herramienta: `interrumpir` (no cuenta como intento) y pausa; al reanudar, `reanudar` pasa `en_curso` a `pendiente`.
5. Independencia: cada subagente recibe solo su lote dentro del mensaje (que no contiene run_id ni rutas); el orquestador no reutiliza ni muestra respuestas de otras corridas. La independencia la garantiza el orquestador, no una barrera tecnica; temperatura no controlable (se registra `temperature_controlled = false`).
6. Pausas (015 3.7.7): tras los primeros 10 lotes de la corrida 1 si > 10 % salio invalido al primer intento; al completar la corrida 1 (cobertura 100 %); al completar la corrida 3, antes del acuerdo.
7. Cuando todos los lotes de una corrida estan `ok`, `importar` (o `ensamblar`) escribe el Parquet. Al terminar las 3: `validar --run-ids R1 R2 R3`. Se niega a aceptar corridas incompletas; no calcula exposicion agregada.
