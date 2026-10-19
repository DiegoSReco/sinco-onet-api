# Diccionario de datos: emparejamiento Metodo A1 (data/processed/, generado por src/match/run.py)

Decision de referencia: `docs/decisions/005-emparejamiento-embeddings.md`. **Todas las salidas son `estado_validacion = sin_validar`**
y sus parametros son "provisional, sin calibrar" (`src/match/config.toml`). La probabilidad de Frey-Osborne se nombra
"probabilidad de automatizacion (Frey-Osborne)"; no es exposicion ni riesgo de perdida de empleo. Ninguna cifra es calculada a mano:
todo sale de `python -m src.match.run`. Los conteos de cobertura de cada corrida estan en `match_cobertura.json`.

## crosswalk.parquet (esquema de la decision 004)
Una fila por par (sinco_code, onet_soc_code) del conjunto candidato S del **modelo principal** (config `modelo_principal`,
provisional). Sin columnas de score, exposicion ni probabilidad (la API las ignoraria; una prueba lo verifica).
| Columna | Tipo | Descripcion |
|---|---|---|
| sinco_code | texto | grupo unitario SINCO 2019 (existe en `sinco`) |
| onet_soc_code | texto | O*NET-SOC 2019 (existe en `onet_ocupaciones`) |
| tipo_relacion | texto | 1:1, 1:N, N:1, M:N sobre el grafo de pares de S (decision 003) |
| fuente | texto | `semiautomatico_embeddings_A1_<modelo>` (no es correspondencia oficial) |
| estado_validacion | texto | siempre `sin_validar` |
| notas | texto | resumen legible: rango, similitud, margen, estado, aviso de parametros provisionales |
| run_id | texto | corrida que lo genero (ver `match_corridas`) |
| modelo | texto | modelo principal |
| rango | entero | rango del candidato en el top-k del modelo (1 = mejor) |
| similitud | real | coseno SINCO-O*NET (no es probabilidad) |
| margen | real | `sim_top1 - sim_top2` del grupo SINCO (igual en todas sus filas) |
| similitud_alt, rango_alt, modelo_alt | real, entero, texto | coseno y rango del mismo par segun el otro modelo (comparacion) |
| baja_confianza | logico | bandera relativa a cuantiles del modelo (sin calibrar) |
| match_status | texto | `ok`, `baja_confianza` o `sin_coincidencia` |
`isco08_code`, `match_quality`, `crosswalk_confidence` no se llenan (no hay ISCO; la calidad requiere revision humana).

## sinco_probabilidad_fo.parquet (una fila por modelo x grupo unitario SINCO)
Probabilidad de automatizacion (Frey-Osborne) trasladada a SINCO 2019 mediante emparejamiento. Cifra principal = media ponderada por
similitud (softmax(sim/tau) en S). Alternativas segun 005 5.7. Las cinco columnas de probabilidad son NA cuando
`match_status = sin_coincidencia` (005 5.6); el valor sin ese filtro se conserva en `..._ponderada_sin_filtro`.
| Columna | Descripcion |
|---|---|
| run_id, modelo, es_modelo_principal | identificacion de la corrida; el principal es provisional |
| sinco_code, titulo | grupo unitario |
| probabilidad_automatizacion_fo | media ponderada por similitud (principal) |
| ..._media_uniforme, ..._min, ..._max, ..._top1 | media uniforme sobre S, minimo y maximo entre los SOC 2010 alcanzados, valor del top-1 |
| ..._ponderada_sin_filtro | la principal sin aplicar el NA por `sin_coincidencia` |
| motivo_na | `sin_coincidencia`, `sin_probabilidad_fo` o vacio |
| n_candidatos | tamano de S |
| n_soc2010, n_soc2010_con_fo | SOC 2010 distintos alcanzados via puente; los que tienen probabilidad F-O |
| cobertura_peso_fo | fraccion del peso de S que llega a un SOC con probabilidad (0-1) |
| cobertura_fo | completa / parcial / ninguna |
| match_status, baja_confianza, sim_top1, margen | de la recuperacion |
| top1_onet_soc_code, top1_socs | O*NET top-1 y su(s) SOC 2010 |
| n_sinco_mismo_top1_soc | N:1: cuantos SINCO comparten el mismo SOC 2010 de su top-1 (para clusters, 005 5.6) |
| bandera_multi_soc2010 | algun O*NET de S cae en varios SOC 2010 (ver issue) |
| bandera_sin_puente, onet_sin_puente | algun O*NET de S no esta en el puente 2019 -> 2010 |
| bandera_soc_sin_fo | algun SOC 2010 alcanzado no esta en la tabla F-O |
| residual_sin_funciones, residual_por_titulo | grupo residual (sin funciones SINCO / titulo "Otros", "no especificados") |
| estado_validacion, etiqueta | `sin_validar`; "probabilidad de automatizacion (Frey-Osborne)" |

## match_corridas.parquet (una fila por corrida x modelo; regla 4 y 005 R.2)
run_id, modelo, hf_id, revision_modelo (commit de 40 caracteres), fecha (UTC), metodo, text_template_version, seed, normalizacion (L2),
max_length, n_truncados_sinco, n_truncados_onet, dispositivo, dtype, hash_matriz_sinco, hash_matriz_onet, hash_matriz_similitud
(sha256 de la matriz float32), hash_config (sha256 de config.toml), parametros (JSON: k, delta, tau, cuantiles y umbrales calculados),
estado_parametros, estado_validacion, hashes_insumos (JSON con sha256 de los 9 Parquet de entrada), versiones_librerias (JSON),
segundos_embedding, n_sinco, n_onet.

## match_candidatos.parquet (top-k completo, ambos modelos; nada se descarta)
run_id, modelo, sinco_code, onet_soc_code, rango (1-10), similitud, dif_con_top1, en_conjunto (pertenece a S), margen_sinco.

## match_sinco_resumen.parquet (modelo x SINCO)
run_id, modelo, sinco_code, sim_top1, sim_top2, margen, n_conjunto, bandera_sim_top1_baja, bandera_margen_bajo, baja_confianza,
match_status, n_tokens_texto, texto_truncado, campos_truncados, residual_sin_funciones, residual_por_titulo, estado_validacion.

## match_cobertura.json
Conteos y distribuciones calculados por el script (cobertura por modelo, banderas, umbrales, cuantiles de similitud y margen, codigos F-O fuera del puente,
O*NET sin puente, acuerdo top-1 entre modelos, Spearman de la probabilidad entre modelos). Fuente de las cifras citables (regla 6) una vez validadas.

## match_vectores/*.npy
Vectores float32 L2 (`<modelo>_sinco.npy`: 490 x 1024, `<modelo>_onet.npy`: 1016 x 1024), en orden ascendente de codigo.
