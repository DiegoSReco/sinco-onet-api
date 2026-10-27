# 020 - Exposición en la muestra de la ENOE: 2022T3 y 2025T3

- Fecha: 2026-10-26
- Autor: orquestador, por instrucción del usuario (cita abajo). Aplica 013 con las desviaciones de la sección 3; no modifica 001, `docs/rubric.md` ni `docs/glossary.md`.
- Estado: **PROVISIONAL.** El pre-registro 013 **no está firmado**. Este plan se fija **antes de calcular** cualquier exposición por estrato, pero el análisis es **exploratorio con plan previo, no confirmatorio**. Resultados sin validar.

## 1. Instrucción del usuario (2026-10-26)
> "Siguiente etapa exposición en la muestra de la ENOE. Utiliza mi paquete creado y las funciones (https://github.com/DiegoSReco/enoeR/); puedes utilizar enoe_join para merge de SDEM y COE1T. Vamos a medir la exposición en dos puntos en el tiempo: tercer trimestre de 2022 y tercer trimestre de 2025. El join hazlo a nivel persona. La variable que puede medir el tipo y tarea de ocupación según SINCO es la P3 del COE1T [...] Tienes todo el permiso. Output una tabla con la exposición de la muestra completa de los dos periodos y un script con el análisis de medida de exposición por muestra." Corrección posterior: "el script tiene que ser en R porque enoeR sirve en R".

La variable P3 corresponde a la pregunta del cuestionario: "Si ... tiene más de un trabajo, hablemos del principal. ¿Cuáles son las tareas o funciones principales que ... desempeña en su trabajo?"

## 2. Estado de las compuertas de 013
| Compuerta | Estado |
|---|---|
| G1 exposición congelada | **Cumplida el 2026-10-26** al correr `src/ingest/06_enoe.R`: se escribe `data/processed/enoe/exposicion_congelada.json` con el SHA-256 de `main_sinco_comp_table.parquet` **antes** de descargar. Si la tabla cambia después, el script se detiene |
| G2 pre-registro firmado | **No cumplida.** El usuario autoriza explícitamente avanzar. El análisis se rotula "exploratorio con plan previo" |
| G3 definiciones del humano | **Parcial:** el usuario fijó trimestres (2022T3 y 2025T3), nivel de unión (persona) y variable de ocupación (COE1T P3). Informalidad y estratos las fija la sección 4, con lo que se declara |

Restricciones de 013 que siguen vigentes: no publicar microdatos (`data/raw/*` y `data/processed/*` están en `.gitignore`, incluida `data/processed/enoe/`); no calibrar nada con la ENOE (la exposición no se modifica); no imputar ocupaciones faltantes; no usar la exposición como riesgo de pérdida de empleo ni leer diferencias entre estratos como diferencias dentro de la ocupación (es composición ocupacional).

## 3. Desviaciones de 013 (declaradas)
1. **Un trimestre por periodo**, no el año completo (013 §4.3, opción 4): hay estacionalidad. Se compara el mismo trimestre calendario con tres años de distancia.
2. **Cruza la edición** ENOE-N (2022T3) con la ENOE (2025T3): posible cambio de cuestionario, marco o factores [NO VERIFICADO].
3. **Exposición congelada:** la "medida principal" de 013 §3 se toma de la tabla MAIN (decisión 019) y es `exp_idx_media_modelos`: el promedio de `exposure_class` con el mapa 0 / 0.5 / 1 de 001, con pesos iguales por función (la regla formal de agregación de la ruta S, 001 E-4, sigue pendiente), y media simple de los tres modelos según 018 R1.3 (ningún modelo excluido). Medidas de comparación de 001 E-3: `alfa_S`, `beta_S`, `cota_sup_S`, también medias entre modelos. Sensibilidad: cada modelo por separado (Haiku, Sonnet, Opus), con su rango, y el índice B1.
4. **Incertidumbre de medición reducida a sensibilidad:** no se simula B1 ni se remuestrean corridas (013 §9.2). Se reporta el rango entre los tres modelos como intervalo de sensibilidad, no de confianza.
5. **Sin muestra humana:** la exposición mide consistencia entre modelos, no exactitud (018).

## 4. Plan de análisis (fijado antes de calcular)
**Unión.** `enoeR::enoe_load(año, trim, tables = c("sdem", "coe1t"))` y `enoeR::enoe_join(level = "person")`: una fila por persona, claves de INEGI. La tabla de salida conserva **toda la muestra** de los dos periodos; el filtro de población se aplica en el análisis, no en la unión.

**Ocupación.** `p3` de COE1T (ocupación principal). Se une por código exacto de 4 dígitos con el grupo unitario SINCO 2019 de la tabla MAIN. **No se usa puente 2011 a 2019** (013 §4.2). La versión de SINCO de cada trimestre se verifica por el porcentaje de códigos presentes en el catálogo; si un periodo resultara con otra versión, se declara y no se mezcla.

**Cobertura (se reporta siempre, ponderada):** (a) código en el catálogo y con medida; (b) grupo del catálogo sin funciones (33), sin medida; (c) código inexistente en el catálogo; (d) ausente o "no especificado". Ninguna se imputa.

**Población y ponderación.** Personas ocupadas con entrevista completa y residentes habituales (reglas de INEGI: las variables exactas se fijan con el diccionario al leer los datos y se documentan en el script), con el factor de expansión trimestral. Todas las estimaciones son ponderadas.

**Estadísticos (013 §7, subconjunto), por periodo y por estrato:**
1. Media ponderada de cada medida; cuantiles ponderados p10, p25, p50, p75, p90 (inverso de la ecdf ponderada, sin interpolación).
2. Proporción de ocupados con medida principal ≥ 0.25, ≥ 0.50 y ≥ 0.75 (umbrales de 013 §7, fijados antes de ver resultados).
3. Distribución ponderada por **división SINCO** (composición) y cobertura.
4. Diferencia 2025T3 menos 2022T3 de la media, con intervalo.

**Estratos (limitados a esta lista):** total; sexo; grupos de edad (15-24, 25-34, 35-44, 45-54, 55-64, 65 o más); escolaridad (hasta primaria, secundaria, media superior, superior); formal e informal (la variable de empleo informal de INEGI en SDEM, verificada en el diccionario); entidad federativa (32); división SINCO. Cruces: ninguno (los demás serían exploratorios y se rotularían).

**Incertidumbre de diseño.** Bootstrap reescalado (Rao y Wu): dentro de cada estrato de diseño se remuestrean n-1 unidades primarias de muestreo con reemplazo y se reescalan los factores; B = 200 réplicas, semilla fija. Intervalos de percentil al 90 %. Si las tablas no traen estrato de diseño y UPM, se reportan solo estimaciones puntuales y se dice. **Supresión:** no se reporta una celda con menos de 30 observaciones sin ponderar ni con coeficiente de variación superior a 30 %. Los dos periodos no comparten viviendas (11 trimestres de distancia con un panel de 5 visitas), por lo que la diferencia se trata con réplicas independientes.

**Lectura obligatoria.** La exposición es constante dentro de un grupo SINCO: toda diferencia entre estratos o entre periodos es **composición ocupacional** medida con una exposición fija, no un cambio en la exposición de ninguna ocupación. Las diferencias entre 2022T3 y 2025T3 no dicen nada sobre desplazamiento ni sobre el avance de la IA.

## 5. Salidas (todas fuera del repositorio público)
- `data/processed/enoe/enoe_exposicion_personas_2022T3_2025T3.parquet`: **la tabla de la muestra completa** de los dos periodos, una fila por persona, con la exposición asignada a quien tiene ocupación con medida.
- `data/processed/enoe/enoe_exposicion_resumen.csv`: estadísticos por periodo y estrato, con intervalos y supresión.
- `data/processed/enoe/enoe_exposicion_cobertura.csv`: cobertura de la unión con el catálogo.
- `data/processed/enoe/enoe_integridad.json` y `exposicion_congelada.json`.
- Scripts en R: `src/ingest/06_enoe.R` y `src/enoe/exposicion_enoe.R`.

## 6. Riesgos
- **Código de ocupación:** si `p3` no viene a 4 dígitos o no es SINCO 2019 en algún trimestre, la cobertura será baja y se reportará tal cual.
- **Doble uso de los datos:** se mitiga con el congelamiento y el plan fijado aquí; si se cambia algo tras ver resultados, se registra como desviación.
- **Lectura indebida:** cifras de exposición de personas ocupadas se leen fácilmente como riesgo de empleo. Todas las salidas llevan el rótulo de la decisión 019.
- **Términos de uso de INEGI para el microdato:** siguen sin verificarse; por eso los datos no se publican ni se redistribuyen.

## Anexo A (2026-10-26): lo verificado al leer los datos, antes de calcular exposición por estrato
Controles de integridad hechos antes de calcular (número de filas, tipos, validez de códigos); no se miró ninguna exposición por estrato.
- **Unión:** `enoeR::enoe_join(level = "person")` sobre `sdem` y `coe1t`: una fila por persona. Llaves de INEGI que usa `enoe_join`: `ent, con, v_sel, n_hog, h_mud, n_ren`, más `cd_a`, `tipo`, `mes_cal` cuando existen en ambas tablas; con todas ellas no hay filas duplicadas. Con solo las primeras siete aparecen falsos duplicados, por lo que cualquier otra unión debe usar las llaves completas. Conteos en `data/processed/enoe/enoe_integridad.json`.
- **Ocupación `p3`:** viene como número de 4 dígitos (por ejemplo 4211) y solo existe para los ocupados (`clase2 == 1`). Se une por código exacto con el grupo unitario SINCO 2019.
- **Versión de SINCO:** el 100 % de los ocupados de ambos trimestres tiene un `p3` presente en el catálogo SINCO 2019, lo que confirma esa versión en 2022T3 (ENOE-N) y en 2025T3 (ENOE). No se usa ningún puente.
- **Población objetivo:** `clase2 == 1` (ocupado), `r_def == 0` (entrevista completa), `c_res` en 1 o 3 (residentes) y `eda >= 15`. Son las reglas de elegibilidad de INEGI que usa `enoeR` (con 12 años como límite inferior de elegibilidad; aquí se fija 15 años para la población ocupada, el estándar de los indicadores laborales).
- **Ponderación y diseño:** `fac_tri` (factor trimestral), `est_d_tri` (estrato de diseño) y `upm` (unidad primaria de muestreo) existen en SDEM y se usan para el bootstrap reescalado.
- **Estratos:** `sex` (1 hombre, 2 mujer); `eda` en grupos; `ent` (32 entidades); `emp_ppal` (1 informal, 2 formal; la lectura 1 = informal es consistente con una tasa de informalidad ponderada cercana a la oficial, **pendiente de confirmar con el diccionario de INEGI**); `cs_p13_1` agrupada como hasta primaria (0 a 2), secundaria (3), media superior (4 a 6) y superior (7 a 9) (**agrupación provisional**: normal y carrera técnica caen en media superior); división SINCO = primer dígito de `p3`.
- **Intervalos:** son **solo de diseño muestral** (bootstrap reescalado, B = 200, 90 %). No incluyen la incertidumbre de medición de la exposición; el rango entre los tres modelos (`rango_E_modelos`) es un indicador de sensibilidad, no un intervalo. Los cuantiles se reportan sin intervalo.
- **Celdas:** se aplica la supresión de 013 (menos de 30 observaciones o coeficiente de variación mayor a 30 %); en esta corrida todas las celdas fueron publicables.
