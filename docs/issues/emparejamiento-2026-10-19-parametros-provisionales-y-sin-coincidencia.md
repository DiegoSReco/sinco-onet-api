# Emparejamiento A1: parametros provisionales y regla de "sin_coincidencia" (requiere decision humana)

Origen: `src/match/` (decision 005, R.4.3 y R.7 "Requiere decision" 8). Corrida `match-A1-20261019T161025-21e0f487` (config `src/match/config.toml`).
Estado: informativo, no bloquea; todos los resultados son `sin_validar`.

## Pregunta
005 deja sin valor numerico delta, tau y los umbrales de baja confianza / sin coincidencia ("se calibran con la muestra de oro"). Para poder ejecutar se usaron valores **provisional, sin calibrar**:

| Parametro | bge-m3 | multilingual-e5-large |
|---|---|---|
| k | 10 | 10 |
| rango maximo del conjunto S | 5 | 5 |
| delta (ventana respecto de top-1) | 0.04 | 0.02 |
| tau (softmax) | 0.05 | 0.02 |
| baja_confianza | sim_top1 por debajo del cuantil 0.10 propio, o margen por debajo del cuantil 0.10 propio | idem |
| sin_coincidencia | sim_top1 por debajo del cuantil 0.05 propio | idem |

Los cosenos de bge-m3 (sim_top1 de 0.55 a 0.85) y de e5 (0.84 a 0.91) no son comparables; por eso delta, tau y los umbrales son por modelo y los umbrales son cuantiles de la distribucion del propio modelo. Los valores de delta y tau se eligieron por la escala observada de cada modelo, no por desempeno.

## Opcion provisional usada
- `match_status = sin_coincidencia` es **relativo**: por construccion marca al 5 % de los grupos con menor similitud (25 de 490 en cada modelo) sin importar si el emparejamiento es bueno o malo. No mide "no existe ocupacion O*NET equivalente".
- Consecuencia visible: entre los 25 "sin_coincidencia" del modelo principal (bge-m3) hay grupos con ocupaciones claramente comparables en O*NET (p. ej. 7121 Albaniles, 7513 pan y reposteria), lo que sugiere un fallo de recuperacion interlingue en oficios mas que ausencia de equivalente. La probabilidad F-O de esos grupos queda NA (005 5.6) pero se conserva el valor sin filtrar en `probabilidad_automatizacion_fo_ponderada_sin_filtro`.
- El modelo principal (`modelo_principal = bge-m3`) es provisional; 005 R.4.2 difiere la eleccion a la muestra de oro. Ambos modelos se escriben en `sinco_probabilidad_fo.parquet`; `crosswalk.parquet` contiene solo el principal (con `similitud_alt`/`rango_alt` del otro).
- Acuerdo entre modelos (de `match_cobertura.json`): top-1 identico en 45.7 % de los 490 grupos; mismo gran grupo SOC (2 digitos) en 67.1 %; Spearman de la probabilidad F-O principal entre modelos 0.84 (n = 396 con valor en ambos). Es evidencia de que el resultado depende del modelo.

## Que se necesita
Calibrar delta, tau y los umbrales con la muestra de oro (005 secc. 8.1, P9), decidir si "sin_coincidencia" debe ser un umbral absoluto calibrado y no un cuantil, y elegir el modelo principal.
