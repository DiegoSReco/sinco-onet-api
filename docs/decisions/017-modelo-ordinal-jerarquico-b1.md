# 017 - Especificación del modelo ordinal jerárquico de B1 (NumPyro)

- Fecha: 2026-10-22
- Autor: orquestador, a petición del usuario ("implementalo", 2026-10-22), siguiendo 012 §5 (B1, "versión ordinal" y "corrección esencial") y 016.
- Estado: **PROVISIONAL, SIN VALIDAR.** Los valores numéricos de los priors son una propuesta mía, no decisión humana (regla 7). No modifica 001, la rúbrica ni el glosario. Pendiente de revisión humana.

## Modelo
Ítem `f` (función SINCO `sinco_code|orden`; en la ruta O, tarea), grupo `g(f)` (`sinco_code`, u `onet_soc`), división `d(g)` (primer dígito de SINCO; dos primeros dígitos del SOC), anotador `k` (corrida del LLM o revisor humano). Clases ordinales `0<1<2` (E0<E1<E2 o EL0<EL1<EL2).

- Jerarquía: `mu_d ~ N(0, s_d)`, `mu_g ~ N(mu_d, s_g)`, `u_f = mu_g + e_f`, `e_f ~ N(0, 1)`; `s_d, s_g ~ HalfNormal(1)`. La escala latente se fija con `sd(e_f)=1` y la ubicación global con media 0 en `mu_d` (identificabilidad). Pooling parcial; se reporta también un índice sin pooling.
- Cortes de referencia: `c1 ~ N(0, 1.5)`, `gap ~ LogNormal(0.5, 0.5)`; la **clase verdadera** es `z_f = cat(u_f; c1, c1+gap)`.
- Anotadores LLM: `eta_fk = u_f + b_f + d_k`, con los mismos cortes; verosimilitud ordinal logística. `d_k ~ N(0, 0.5)`. **Sin referencia humana** se impone `sum(d_k)=0` y **no hay `b_f`** (con solo corridas de un LLM, `b_f` y `u_f` no se separan): el resultado es consistencia entre corridas, no exactitud.
- **Con referencia humana:** `b_f = s_b * N(0,1)`, `s_b ~ HalfNormal(0.5)` (sesgo común del LLM por función, 012 "corrección esencial"); `d_k` libre; cada revisor `h` tiene cortes propios `(c1_h ~ N(c1, 0.5), gap_h ~ LogNormal(0.5, 0.5))`, sin `b_f` ni `d_h`. La adjudicación es un anotador más (012). Limitación de esta versión: `z_f` se define con `c1` y `gap`, no con los cortes humanos.
- Muestreo: NUTS, 4 cadenas, 1000 de descarte y 1000 muestras (provisional), `init_to_median`; diagnósticos R-hat <= 1.05 y ESS >= 100 sobre hiperparámetros, cortes y sesgos.

## Salidas (`data/processed/calibracion/b1_ordinal_<campo>_*`)
- `grupos`: índice ordinal medio por grupo `mean(z_f)/(C-1)` (media e intervalo creíble 90 %), índice sin pooling y número de funciones.
- `items`: `prob_<clase>` posterior de `z_f`.
- `anotadores`: sesgo `d_k` con intervalo. `diagnosticos` y `meta.json` (entradas, versiones, semilla, etiqueta).
- **No es `E_g` de 001** (eso lo calcula `src/score`); es el índice ordinal medio de la clase latente, para comparar. No se cita en el artículo (regla 6).

## No hecho
Chequeos predictivos posteriores, ajuste por el diseño de muestreo de la muestra humana, efecto de idioma, B1.b (error de matching) y probar el camino con referencia humana con datos reales (no existen).

## Estado de implementación (2026-10-22)
- Código: `src/calibrate/b1_ordinal.py` (v `b1-ordinal-0.1`); prueba sintética `tests/calibrate/test_b1_ordinal.py` (recupera orden de sesgos de anotador y de grupos; pasa).
- Humo sobre el piloto de la ruta O (3 corridas x 40 tareas, un item por grupo SOC): converge (R-hat <= 1.01, ESS >= 460). No es resultado: un item por grupo, sin pooling informativo.
- **Ruta S real NO ejecutada:** solo la corrida `ann-s-v1-2026-10-20-01` tiene Parquet; la 02 y la 03 no estan ensambladas (solo `estado.json` y `run_meta.json`). El modelo exige al menos 2 corridas LLM. Pendiente: completar las corridas (agente de anotacion).
- Camino con referencia humana: implementado, **sin probar** (no hay muestra humana).
