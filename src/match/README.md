# src/match/ - Metodo A1 (embeddings): SINCO 2019 -> O*NET-SOC -> probabilidad de automatizacion (Frey-Osborne)

Implementa la decision `docs/decisions/005-emparejamiento-embeddings.md` (aprobada; alcance minimo R.4):
solo Metodo A, variante A1 (SINCO en espanol contra O*NET en ingles, modelo multilingue). Metodo B no se implementa.

**Estado de los resultados: `sin_validar`.** Todos los parametros (k, delta, tau, cuantiles de bandera) estan en
`config.toml` como "provisional, sin calibrar"; la calibracion exige la muestra de oro humana (005 secc. 8.1, pendiente).
No se publican cifras del articulo con estas salidas (regla 6). La probabilidad de Frey-Osborne se llama siempre
"probabilidad de automatizacion (Frey-Osborne)"; no es exposicion ni riesgo de perdida de empleo (005 R.1b).

## Entorno
- Python 3.14.3 en `.venv/` (ignorado por git). Instalado en el venv: `sentence-transformers`, `torch` (CPU), `transformers`,
  `scikit-learn`, `scipy` (lista cerrada de 005 R.2) mas pandas, pyarrow, pydantic, pytest. Versiones exactas en la tabla de
  corridas (`versiones_librerias`).
- Pesos de modelos en `~/hf_cache` (variable `HF_HOME`, fuera del repositorio): BAAI/bge-m3 (revision
  `5617a9f61b028005a4858fdac845db406aefb181`, `pytorch_model.bin`) y intfloat/multilingual-e5-large (revision
  `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`, `model.safetensors`). Sin APIs de pago, sin faiss, sin statsmodels.

## Uso
```
.venv\Scripts\python -m src.match.run            # ambos modelos, escribe en data/processed/
.venv\Scripts\python -m src.match.run --local    # no consulta la red (solo cache)
.venv\Scripts\python -m src.match.run --salida DIR --solo-modelo bge-m3
.venv\Scripts\python -m pytest tests/match -q
```

## Modulos
| Archivo | Funcion |
|---|---|
| `config.toml`, `config.py` | parametros versionados; su hash se registra por corrida |
| `texts.py` | plantillas `tt-a1-v1` y truncamiento por campo (titulo > ocupaciones > descripcion > funciones) |
| `embed.py` | carga con revision fijada, codificacion L2, hash de matrices, versiones |
| `retrieve.py` | coseno, top-k, conjunto S (rango <= 5 y sim >= top1 - delta), margen, banderas, tipo de relacion |
| `pfo.py` | puente O*NET 2019 -> SOC 2010 -> probabilidad F-O; agregaciones |
| `schemas.py` | esquemas pyarrow/pydantic y verificaciones (regla 5) |
| `run.py` | orquestacion; valida esquemas antes de escribir |

## Que hace
1. Documento SINCO (consulta, un grupo unitario): titulo ampliado + ocupaciones ejemplo + descripcion + funciones
   (los "excluye" no entran). Documento O*NET: titulo + descripcion (sin tareas, sin traduccion). Con e5 se usa el
   prefijo `query: ` en ambos lados (005 5.3). Truncamiento y numero de tokens quedan registrados.
2. Coseno sobre vectores normalizados (490 x 1016, fuerza bruta). Top-k (k = 10) con rango, similitud y margen
   (`sim_top1 - sim_top2`). Conjunto S = candidatos con rango <= 5 y similitud >= top1 - delta (siempre incluye top-1).
3. Banderas: `baja_confianza` (sim_top1 o margen por debajo de un cuantil propio del modelo), `sin_coincidencia`
   (sim_top1 bajo un cuantil bajo; la probabilidad queda NA, 005 5.6), residuales (sin funciones; titulo "Otros/no especificados").
4. Probabilidad F-O: cada O*NET de S -> SOC 2010 (puente) -> probabilidad. Pesos: softmax(sim/tau) dentro de S
   (principal), uniforme (alternativa), minimo, maximo, top-1. Un O*NET con varios SOC 2010 reparte su peso por igual;
   el mismo SOC alcanzado por varios O*NET se colapsa; los SOC sin probabilidad se omiten (se reporta `cobertura_peso_fo`).
   Nada se imputa.
5. Salidas en `data/processed/` (ver `docs/diccionario_datos_match.md`): `crosswalk.parquet`,
   `sinco_probabilidad_fo.parquet`, `match_corridas.parquet`, `match_candidatos.parquet`, `match_sinco_resumen.parquet`,
   `match_cobertura.json`, `match_vectores/*.npy`.

## Decisiones provisionales abiertas (no resueltas por 005)
Ver `docs/issues/metodos-2026-10-19-*.md` (umbrales sin calibrar, multiplicidad del puente, codigos F-O fuera del puente,
residuales, sin coincidencia, cobertura parcial, cuantiles por modelo). Ninguna se resolvio en silencio.

## No implementado (fuera del alcance minimo de 005 R.4)
Metodo B; variantes A2/A3; variante "titulo solo"; diagnostico `cobertura_funciones`; remuestreo de incertidumbre;
ponderacion por empleo de EE. UU.; rerank con LLM; tabla de revision para la muestra de oro (005 no la pide en este alcance).
