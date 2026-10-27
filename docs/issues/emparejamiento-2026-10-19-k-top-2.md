# Emparejamiento A1: candidatos reducidos al top-2 (interpretacion a confirmar)

Origen: `src/match/` (decision 005 5.4/5.7). Corrida `match-A1-20261019T214743-e98c06c4`. Estado: informativo; todo `sin_validar`.
Esta solicitud no esta registrada aun en `docs/decisions/` (regla 7): otro agente debe registrarla; este issue no la sustituye.

## Instruccion del usuario (cita)
"Antes solo utiliza los embeddings mas altos (2 primeros)... Continua con la asignacion de probabilidad".

## Interpretacion aplicada (a confirmar)
- top-2 = los dos O*NET-SOC con mayor similitud por grupo SINCO, **para cada modelo**. El principal (bge-m3) alimenta `crosswalk.parquet`;
  e5 queda como comparacion. `k_top = 2` en `config.toml` reemplaza el conjunto S por umbrales (`delta`, `rango_max_conjunto`).
- La probabilidad de automatizacion (Frey-Osborne) = media ponderada por softmax(sim/tau) sobre esos 2 (tau sin cambio, sigue sin calibrar), mas media
  uniforme, min, max, top-1. Banderas y cuantiles sin cambio. Se conserva el top-10 en `match_candidatos`.
- Alternativas no tomadas: top-2 por la union de ambos modelos; top-2 por rango tras promediar modelos.

## Efectos observados (de `match_cobertura.json` y comparacion con la corrida anterior)
- Con 2 candidatos el top-1 no cambia (0 de 490 grupos en ambos modelos); cambia el peso y el conjunto de SOC alcanzados.
- bge-m3: probabilidad en 426 grupos (antes 431); NA: 25 sin_coincidencia + 39 sin_probabilidad_fo (antes 34). Pearson 0.959 / Spearman 0.942 vs la anterior (n = 417).
- e5: 416 (antes 435); Pearson 0.917 / Spearman 0.902 (n = 408).
- Con solo 2 candidatos, el margen entre ellos es pequeno en muchos grupos (mediana 0.021 en bge-m3): el peso softmax queda cercano a 50/50 y el
  segundo candidato puede ser de otra familia ocupacional. Es una limitacion de la regla, no un error.

## Pendiente
Confirmacion humana de la interpretacion; registro en `docs/decisions/`; decidir cuando actualizar el repositorio publico (version anterior del crosswalk publicada);
las fichas de la muestra de oro se generaron con los candidatos de la corrida anterior.
