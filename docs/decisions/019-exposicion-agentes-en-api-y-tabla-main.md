# 019 - Exposición del método de agentes en la API y tabla MAIN

- Fecha: 2026-10-23
- Autor: orquestador, por instrucción del usuario (cita abajo). Sigue 018 (método Eloundou sin humanos) y modifica la política de 004/009 sobre exposición en la API.
- Estado: **PROVISIONAL.** Todo lo que se muestra es "exposición teórica por anotación de modelos, sin validar". No es exposición medida, ni riesgo de pérdida de empleo, ni una estimación para México.

## Instrucción del usuario (2026-10-23, antes de dormir)
> "Agrega en la API sinco onet la exposición que se encontró con el método de agentes, agrega por clave de SINCO el resultado de los modelos. En el panel principal agrega los resultados de comparación de modelo, sesgo de estimación, etc. Crea un tabla MAIN con los resultados de todo el trabajo, por id de SINCO. Ahi podemos observar SINCO matched por embeddings con probabilidad en Onet, SINCO con su anotación de expocicion de los tres modelos. El script que uses para ello se llamará main_sinco_comp_table.py." "Aprueblo lo necesario."

## Qué cambia
1. **Se levanta la prohibición** de 004/009 ("la exposición y los scores siguen prohibidos en endpoints e interfaz") **solo** para la exposición del método de agentes de 018, con las etiquetas de abajo. La guardia `PROHIBIDAS` sobre las columnas del crosswalk no cambia: el crosswalk sigue sin admitir columnas de exposición; la exposición vive en una tabla aparte.
2. **Tabla MAIN** (`data/processed/main_sinco_comp_table.parquet`, más CSV y `_meta.json`), una fila por grupo unitario SINCO (490), generada por `src/main_sinco_comp_table.py` (regla 1: toda cifra sale de un script).
3. **API:** nuevos endpoints de solo lectura `/api/exposicion`, `/api/exposicion/{codigo}`, `/api/modelos/comparacion` y `/api/download/main`; la clave `exposicion_agentes` en `/api/sinco/{codigo}` y en `/api/conexiones/{codigo}`; estado en `/api/meta`.
4. **Interfaz:** una pestaña "Modelos" con la comparación entre modelos, el sesgo por modelo (B1) y la sensibilidad al preámbulo, y una tarjeta de exposición en el detalle de cada grupo.

## Definiciones (todas de scripts)
- **Índice ordinal medio por modelo** (`exp_idx_<modelo>`, `el_idx_<modelo>`): por función, E0=0, E1=0.5, E2=1 (o EL0=0, EL1=0.5, EL2=1 con EL3 fundida en EL2, como en 012/017); se promedia sobre las funciones del grupo y sobre las 2 corridas del modelo. **No es `E_g` de 001** ni `alfa_S`/`beta_S`/`cota_sup_S` (siguen pendientes de `src/score`); es el mismo índice de comparación de 017.
- **Participaciones por clase** (`exp_E0_<modelo>` etc.): fracción de funciones del grupo en cada clase, promedio de las 2 corridas.
- **Medida entre modelos:** media simple con pesos iguales de las medias por modelo, tomando los modelos no excluidos por la regla de 018 R1.3 (kappa < 0.40 frente a ambos restantes; el resultado de la regla se lee de `acuerdo_modelos.json`). Se reportan siempre los tres valores por modelo y el rango min-max (S6). Esto aplica la regla preespecificada de 018 R1.3 (el usuario delegó P7 al agente de métodos); no la sustituye.
- **B1:** `b1_*_idx`, `_lo`, `_hi` vienen del ajuste ordinal con `unidad = modelo` (017 + 018), intervalo al 90 %. "Consistencia entre corridas, no exactitud."
- **Emparejamiento con O*NET:** modelo de embeddings principal (`bge-m3`), top-2 con `similitud` (coseno) y `margen`. La **"probabilidad"** que se muestra es el `peso_softmax` entre los dos candidatos, `softmax(similitud / tau)` con `tau` de `src/match/config.toml` (provisional, sin calibrar), la misma ponderación que ya usa la agregación de Frey-Osborne (005 §5.7). **No es una probabilidad calibrada de que el emparejamiento sea correcto**; es un peso relativo entre los 2 candidatos. Se rotula así en la API y en la interfaz.
- **Frey-Osborne** conserva su etiqueta de 009: "probabilidad de automatización (Frey-Osborne), NO validada".

## Etiquetas obligatorias (API, interfaz y descargas)
"Exposición teórica por anotación de modelos (Haiku, Sonnet, Opus), sin validar. Mide consistencia entre modelos, no exactitud. Los tres modelos son de la misma familia: el sesgo común no es identificable. No es riesgo de pérdida de empleo ni una estimación para México." `estado_validacion = sin_validar`.

## Qué no se hace
- **Corrección (2026-10-26):** el índice `exp_idx_<modelo>` **sí es** la medida principal de 001 (promedio de `exposure_class` con el mapa 0 / 0.5 / 1) con pesos iguales por función; lo que sigue pendiente es la regla formal de agregación de la ruta S (001, E-4). `alfa_S`, `beta_S` y `cota_sup_S` (001, E-3) se agregaron a la tabla MAIN como columnas derivadas de los repartos por clase. Donde esta decisión dice "no es `E_g`", léase "no incluye aún la agregación formal E-4".
- No se designa un modelo "mejor"; no se mezcla la variante `ann-s-v2` (solo Sonnet) en la tabla MAIN; las 6 corridas base son las de 018.
- No se cita ninguna cifra en el artículo (regla 6) hasta que el usuario lo decida; la API es de exploración.
- La muestra humana (015 §3.10), el preregistro 013 y la ENOE siguen sin tocarse.

## Riesgos
- Una cifra de exposición visible en una interfaz tiende a leerse como resultado. Mitigación: etiqueta fija en cada tarjeta y descarga, y el rótulo "sin validar".
- Los 33 grupos unitarios sin funciones en el PDF salen con exposición vacía (NA), no imputada.
- La API ya declaraba solo lectura y loopback; no cambia.
