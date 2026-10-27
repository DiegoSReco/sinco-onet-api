# Emparejamiento A1: grupos SINCO residuales, N:1 y reproducibilidad numerica

Origen: `src/match/` (corrida `match-A1-20261019T161025-21e0f487`). No bloquea; todo `sin_validar`.

## Residuales (005 5.6, P11)
- 005 fija NA con `match_status = sin_coincidencia` para el caso base, pero **no define "residual"**. Provisional: se marcan dos banderas, sin cambiar el valor: `residual_sin_funciones` (33 grupos sin funciones, los que el diccionario de datos llama residuales) y `residual_por_titulo` (34; titulo que empieza con "Otros/Otras" o contiene "no especificadas"/"n.c.p."; coinciden en 32). No hay un grupo 9999 aparte de "Ocupaciones no especificadas" (9999), que queda marcado.
- Los residuales **no** reciben NA por ser residuales; solo por la regla general. En bge-m3, de los 33 sin funciones: 26 `ok`, 3 `baja_confianza`, 4 `sin_coincidencia` (los 4 con NA). No se evaluo si su top-1 es una ocupacion "All Other". Pendiente decidir si deben ir a NA fijo o a imputacion marcada (P11, sensibilidad no implementada: no se imputa nada).

## N:1
- Muchos grupos SINCO comparten el mismo SOC 2010 de top-1 (en bge-m3, 298 de 490 grupos comparten su `top1_socs` con al menos otro; maximo 13). Se reporta `n_sinco_mismo_top1_soc` para clusters (005 5.6). Las correlaciones con la exposicion deben agruparse por SOC compartido.

## Reproducibilidad numerica
- Con la misma semilla, el mismo orden de textos y el mismo tamano de lote, dos codificaciones dan el mismo hash (prueba `tests/match/test_determinismo.py`, CPU, float32). Con lotes distintos (p. ej. recodificar un subconjunto), los vectores difieren ~1e-7 (coseno minimo 0.99999994 en una muestra de 25 grupos con e5), por lo que el hash de la matriz es comparable solo entre corridas completas con la misma configuracion. 005 4.3 ya advertia de esta posibilidad ([NO VERIFICADO] hasta ahora).
- Los vectores de e5 vienen de la corrida de humo con el mismo codigo, textos y revision (huella verificada por `--reusar-vectores`); en `match_corridas` aparece `vectores_desde_cache = True` para ese modelo.
