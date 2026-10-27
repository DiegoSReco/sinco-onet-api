# 018 - Marco de Eloundou sin anotación humana: Haiku, Sonnet y Opus como anotadores

> **ESTADO: PROPUESTA, PENDIENTE DE REVISIÓN HUMANA.** No implementa nada, no autoriza gasto, API, modelos ni corridas, y no modifica 001, `docs/rubric.md` ni `docs/glossary.md` (regla 2). Lo que contradiga decisiones aprobadas (015 M2, M28, M29, M38) se marca como enmienda propuesta (sección 8). Todos los umbrales numéricos son PROVISIONALES y míos.

- Fecha: 2026-10-22
- Autor: agente de métodos
- Fecha de consulta de las fuentes web: 2026-10-22
- Relacionada con: 001 (§4.3, §8), 011 (§2.2, §4.e, §4.g), 012 (§5 B1, "corrección esencial"), 015 (M2, M27, M28, M29, M38, §3.4, §3.9, §3.10), 016, 017.
- Pedido del usuario (2026-10-22, cita textual): "tomamos el framework de Eloundou [rúbrica E0 sin exposición / E1 exposición directa con LLM, reducción de tiempo >= 50% con calidad equivalente / E2 LLM+ con software adicional, incluida generación de imágenes; medidas alfa=E1, beta=E1+0.5*E2, zeta/gamma=E1+E2; comparación GPT-4 vs humano con acuerdo % y Pearson por rúbrica y ponderación]. Pero no tendremos human annotations y en lugar de utilizar GPT-4 utilizaremos tres modelos: Haiku y Sonnet; Opus evaluará los." (La última frase es ambigua; ver sección 1.)

## 0. Qué se leyó y qué no

Leído: CLAUDE.md; decisiones 001, 012, 016, 017; 011 (líneas 1-275 de 474: §0-§5 parcial, incluye §2.2, §4.e-§4.g); 015 (líneas 1-323 de 418: tabla maestra, E-4 a E-7, §3 completa); `docs/rubric.md` v2, `docs/glossary.md` v2, `src/calibrate/README.md`, `src/annotate/README.md`. No leí el resto de 011 ni de 015 (§4 en adelante, despliegue), ni el código de `src/annotate/` ni de `src/calibrate/b1_ordinal.py`; lo que digo de ellos viene de los README y de 017 (**[NO VERIFICADO]** contra el código). No inspeccioné `data/processed/`.

Consultas web de hoy (resúmenes de herramienta, no copias literales): página de modelos de Anthropic (IDs y precios), Panickssery et al. (2024) y Kim et al. (2025), solo resultados de búsqueda.

## 1. Pregunta 1: qué significa "Opus evaluará los"

| Lectura | Qué haría Opus | Veredicto |
|---|---|---|
| L1. Anotador independiente adicional | Recibe el mismo prompt `ann-s-v1`, ciego, y etiqueta cada función igual que Haiku y Sonnet | **Recomendada** |
| L2. Juez/adjudicador de desacuerdos Haiku-Sonnet | Ve las etiquetas (y justificaciones) de Haiku y Sonnet y decide | No recomendada como medida de registro |
| L3. Árbitro de calidad de justificaciones | Puntúa `rationale` de los otros dos | No recomendada; no mide exposición |
| L4. "Verdad de referencia" que sustituye a los humanos | Sus etiquetas se usan como `--referencia` | **Rechazada** |

**Por qué L1.**
1. Es la única lectura compatible con 017: cada modelo es un anotador `k` con sesgo `d_k`, y ninguno es verdad. Opus entra al modelo como un anotador más.
2. L2 y L4 introducen circularidad: el adjudicador de la misma familia, que ve las salidas de sus pares, produce una etiqueta que se trata como verdad y luego se "valida" contra ella. Los dos riesgos documentados son sesgo de autopreferencia del juez (Panickssery, Bowman y Feng, 2024: los evaluadores LLM puntúan más alto sus propias salidas; el experimento fue en resumen de textos, y yo vi solo el resumen) y que los jueces inflan la exactitud de modelos del mismo proveedor o arquitectura (Kim et al., 2025, abstract/búsqueda). Ninguno de los dos estudios es sobre clasificación ordinal de tareas laborales: son analogías, no evidencia directa.
3. L3 es útil como diagnóstico de la calidad del texto, pero una justificación bien escrita no demuestra una etiqueta correcta.
4. Si el usuario quiere de todos modos un adjudicador (L2), puede existir como **análisis secundario rotulado** (sección 3.4), nunca como entrada de B1 ni como `clase_humana`.

**Pregunta imprescindible al usuario (P1):** ¿"Opus evaluará los" significa L1 (Opus anota igual que los demás), L2 (Opus adjudica desacuerdos), o L3/L4? Mi recomendación es L1; sin su respuesta no hay prompt ni esquema de la corrida de Opus.

## 2. Pregunta 2: opinión crítica, qué se puede y qué no se puede afirmar

### 2.1 Se puede afirmar (con rótulo "consistencia entre modelos, no exactitud")
- Reproducibilidad: cuánto coinciden las corridas de un mismo modelo y cuánto coinciden modelos distintos con el mismo prompt.
- Sensibilidad de la medida al modelo: cuánto cambian `E_g`, `alfa_S`, `beta_S`, `cota_sup_S` al sustituir un modelo por otro; sesgo relativo (¿Haiku califica más alto que Opus?) vía `d_k` (017).
- Estructura: dónde se concentra el desacuerdo (divisiones SINCO, `physical_bottleneck`, funciones genéricas).
- Rango plausible de la medida **entre modelos**, como intervalo de sensibilidad.

### 2.2 NO se puede afirmar
1. **Exactitud.** Que dos o tres modelos coincidan no dice que acierten. Evidencia verificada en 011 §2.2 (Tabla 2 de Eloundou, p. 8): GPT-4 R1 contra GPT-4 R2 tuvo acuerdo 91.1 % y Pearson 0.611 en E1, pero GPT-4 contra humanos 80.8 % y Pearson 0.223. La consistencia interna superó con holgura la concordancia con el criterio humano. Esa es la razón por la que Eloundou tuvo humanos, y por la que aquí ningún estadístico entre modelos puede ocupar su lugar.
2. **Que Opus sea "mejor" por ser más grande y más caro.** No consulté ningún benchmark sobre esta tarea. Es una hipótesis, no un dato. Los precios (sección 6) no son calidad.
3. **Independencia.** Haiku, Sonnet y Opus son de la misma familia (Anthropic): datos, posentrenamiento y sesgos probablemente compartidos. Kim et al. (2025) reportan errores más correlacionados entre modelos del mismo proveedor (resumen de búsqueda, otra tarea). Tratar tres modelos de la misma familia como tres jueces independientes es el error que 012 llama "corrección esencial", aplicado a modelos y no solo a corridas.
4. **Que las medidas reproduzcan a Eloundou.** El preámbulo de la rúbrica fija un LLM de OpenAI de 2023 (011 §4.e); aquí los anotadores son modelos de 2026 que no son ese modelo. La comparación con las cifras de Eloundou es de rangos, no de niveles (015 §3.11).
5. **Validez de constructo.** Sin referencia humana, las asociaciones con Frey-Osborne u otras fuentes (sección 4) no son validación.

### 2.3 Cómo se trata en B1 (016/017)
- Cada modelo es un anotador con `d_k` propio. Sin referencia humana: `sum(d_k) = 0` y sin `b_f` (017). Con tres modelos de la misma familia, `d_k` mide sesgo **relativo entre modelos**; el sesgo común de la familia es **no identificable** y se declara como tal.
- Opus **no** se pasa como `--referencia` ni como `clase_humana`. Si luego existe una muestra humana (sección 7, P2), los revisores entran como anotadores con cortes propios (017) y Opus sigue siendo un anotador.
- Los posteriores de B1 con corridas del mismo modelo tratadas como independientes son falsamente precisos (README de calibrate). Por eso la unidad de anotador recomendada es `modelo` (moda por ítem de sus corridas), no `corrida`; con tres modelos, esto da 3 vistas. Si en `b1_ordinal.py` existe esa opción, **[NO VERIFICADO]**.
- Rótulo en toda salida: "consistencia entre modelos de una misma familia, no exactitud".

## 3. Diseño propuesto

### 3.1 Qué cambia y qué no respecto de 001/011/015

| Elemento | Estado |
|---|---|
| `exposure_class` (001) y `eloundou_class` (E-2), campos independientes (R3 de 011) | **Sin cambio**; ambos se siguen anotando |
| Rúbrica literal de Eloundou, EL3 anotada y fundida en EL2 en las medidas | Sin cambio. Coincide con lo que dice el usuario ("E2 ... incluida generación de imágenes") |
| `alfa_S`, `beta_S`, `cota_sup_S` (símbolo griego de la tercera: **[NO VERIFICADO]**; el usuario escribe "zeta/gamma") | Sin cambio de definición; se mantiene el nombre por definición |
| Ruta S (función SINCO, español original), pesos iguales, 33 residuales NA | Sin cambio |
| Prompt `ann-s-v1`, inmutable; mismo texto para los tres modelos | Sin cambio. El modelo se distingue por el campo `model`, no por `prompt_version` |
| Comparación "GPT-4 vs humano" | **Sustituida** por modelo vs modelo (sección 4), con rótulo de consistencia |
| Anotador único Sonnet 5.5, sin segundo modelo | **Enmienda** a 015 M2 y M38 (sección 8) |
| "No tendremos anotación humana" | **Posible conflicto** con 015 M29 y §3.10 (revisor 1 = el usuario, 300 funciones + 49 grupos). Ver P2 |

**Ambigüedad de nomenclatura.** El usuario escribe "E0/E1/E2" para Eloundou; en el proyecto E0/E1/E2 son `exposure_class` y las de Eloundou son EL0-EL3. La propuesta supone que se refiere a `eloundou_class`. **Pregunta P3:** ¿Eloundou pasa a ser la medida principal (en lugar de `exposure_class`/`E_g` de 001 §4.3-§4.4)? Si sí, es una enmienda mayor a 001, `rubric.md` y `glossary.md` (sección 8, E-9); este documento no la asume. Argumento para no hacerlo: la rúbrica de Eloundou está calibrada a un LLM de 2023 y a O*NET; `exposure_class` ya existe, ya se corrió y su propio criterio es neutral respecto del modelo.

### 3.2 Unidad, esquema y trazabilidad (regla 4)
- Unidad: función SINCO (ruta S), 3,542 funciones en 457 grupos (conteos de 015, no recalculados). Ruta O sigue diferida (015 §3.2).
- Esquema: el de 015 (E-5/E-5b), un registro por (`run_id`, `sinco_code`, `orden`), con `model` distinto por registro de corrida. `run_id` debe llevar el modelo para no colisionar: propuesta `ann-s-v1-<fecha>-<alias_modelo>-NN` (el patrón hoy visible en 017 es `ann-s-v1-2026-10-20-01`; si el código lo permite, **[NO VERIFICADO]**). Cada registro conserva `prompt_version`, `prompt_sha256`, `model`, `run_date`, `capability_cutoff`, `batch_id`, `attempt`, `temperature_*`.
- IDs de modelo verificados hoy (platform.claude.com, 2026-10-22): `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`. En las corridas por subagente, el ID efectivo que usa Claude Code **[NO VERIFICADO]**: se registra el que reporte el entorno, no el que yo suponga.
- Mismo lote, orden y semilla por modelo (`seed_base + k`): lotes y orden distintos por corrida (015 §3.4). Los tres modelos ven lo mismo en el mismo formato; la independencia entre modelos la garantiza el orquestador, no una barrera técnica (como en 015).

### 3.3 Número de corridas
- **Recomendado: 3 corridas por modelo (9 anotaciones por función).** Permite estimar la varianza dentro de modelo y separarla de la varianza entre modelos. Sonnet ya tiene 3 planificadas; 017 reporta solo la corrida 01 ensamblada (02 y 03 pendientes).
- **Mínimo defendible: 2 por modelo.** Con 1 por modelo no se puede estimar ruido intra-modelo y el desacuerdo entre modelos se confunde con ruido de muestreo.
- **Temperatura/esfuerzo.** Según la página de modelos (hoy), los tres usan razonamiento adaptativo y el esfuerzo por defecto difiere: `high` en Sonnet 5.5 y `medium` en Haiku 5.5 y Opus 5.5. Esa diferencia por defecto confunde "modelo" con "esfuerzo". Si hay API, fijar el esfuerzo igual en los tres y registrarlo; con subagentes no es controlable y se registra como tal (`temperature_controlled = false`). Si el parámetro `temperature` está soportado en estos modelos: **[NO VERIFICADO]**.
- Haiku y Opus por subagente (015 M2: sin API): que Claude Code permita fijar el modelo del subagente a Haiku u Opus y bajo qué cuota: **[NO VERIFICADO]**. Es P4.

### 3.4 Papel opcional de Opus como adjudicador (solo si el usuario insiste en L2)
- Corre después de cerrar y congelar las 9 anotaciones, solo sobre funciones con desacuerdo, sin ver nombres de modelos.
- Resultado en tabla aparte, rotulado "adjudicación por modelo, no es verdad"; no entra a B1 ni a medidas de registro.
- Se reporta la tasa con que Opus adjudica a favor de su propia corrida previa frente a las de Haiku/Sonnet (diagnóstico de autopreferencia). Si es alta, el análisis se descarta.

## 4. Qué sustituye a la comparación humano-GPT-4 de Eloundou

Todo se rotula **"consistencia entre modelos, no exactitud"**. Scripts en `src/` (regla 1); esta decisión no contiene cifras.

| Sustituto | Qué se calcula | Rótulo / límite |
|---|---|---|
| S1. Acuerdo ponderado entre pares de modelos | Kappa de Cohen ponderado cuadrático por par (Haiku-Sonnet, Haiku-Opus, Sonnet-Opus) sobre la moda por modelo, para `exposure_class` y para `eloundou_class` (EL3 fundida y 4 clases crudas) | Coincidencia, no exactitud |
| S2. Alfa de Krippendorff ordinal | Entre los 3 modelos y entre las 9 corridas; la diferencia mide cuánto del desacuerdo es intra-modelo | Solo reporte |
| S3. Réplica del formato de la Tabla 2 de Eloundou | Para cada una de alfa/beta/cota_sup: acuerdo % y Pearson por par de modelos a nivel función. Definición del cálculo del acuerdo ponderado: 011 §2.2 señala que el pie de Eloundou no la explica; se define aquí y se declara | Ni los números ni los niveles son comparables con GPT-4 vs humano |
| S4. Correlación a nivel grupo | Spearman y Pearson de `alfa_S`, `beta_S`, `cota_sup_S` y `E_g` por par de modelos, sobre los 457 grupos | Idem |
| S5. Sensibilidad a la rúbrica | Tabla cruzada `exposure_class x eloundou_class` por modelo; diferencia entre rúbricas frente a diferencia entre modelos. "Rúbrica 1 vs 2" de Eloundou son dos variantes de prompt de GPT-4 (011 §2.2); aquí el análogo disponible son las dos rúbricas del proyecto, y, si el usuario lo autoriza, el preámbulo de 2023 frente a uno actualizado (otro `prompt_version`, 015 M39) | Si se corre la variante de preámbulo, es otra decisión |
| S6. Intervalo entre modelos | Mínimo-máximo de las medias por modelo de `E_g` y de las `*_S`, junto al intervalo entre corridas y al de B1 | Es un intervalo de sensibilidad, no de confianza |
| S7. Fuentes externas ya presentes | Frey-Osborne (rotulada "probabilidad de automatización, NO validada", glosario v2): Eloundou reporta correlación negativa condicional con esa medida (011 §2.2, p. 20), así que un signo nulo o negativo no es anomalía; sin signo preespecificado y sin lenguaje de validación. Comparación con `occ_level.csv` de Eloundou si existe y la licencia lo permite (015 M37; existencia **[NO VERIFICADO]**) | Convergente, nunca criterio de aprobación; hereda el ruido del emparejamiento |
| S8. Control negativo | `physical_bottleneck = true` asociado a menor exposición, en cada modelo; grupos de contraste elegidos por el usuario antes de ver resultados (015 §3.9) | Chequeo de cordura |

**Por qué ningún S sustituye a humanos.** Todos miden coincidencia entre generadores relacionados. Solo la muestra humana (015 §3.10) es independiente de la familia de modelos, y aun ella es un revisor, no verdad.

## 5. Diseño estadístico del acuerdo y entrada en B1 ordinal (017)

1. **Anotadores.** 3 modelos × 3 corridas. Dos niveles de análisis:
   - Nivel A (principal para B1): `unidad = modelo`, 3 anotadores, moda por ítem y modelo; con 3 corridas el empate solo ocurre si salen tres clases distintas (ítem ausente en ese anotador, como en el README de calibrate).
   - Nivel B (diagnóstico): 9 anotadores de corrida, solo para medir varianza intra-modelo. No se usa como si fueran 9 independientes.
2. **Opus en el modelo.** Anotador `k=3` con `d_k` libre sujeto a `sum(d_k)=0`; sin `b_f` (017). Sin tratamiento especial: ni peso mayor ni referencia. Si el usuario exige que Opus pese más, es una decisión explícita con supuesto declarado (no la recomiendo: nada que yo haya visto lo respalda para esta tarea).
3. **Robustez.** Dejar un modelo fuera (3 ajustes): estabilidad de los índices por grupo y de los terciles; con/sin Haiku, con/sin Opus. Comparar con la media simple de modelos (sin B1).
4. **Dos fuentes de incertidumbre separadas:** intra-modelo (entre corridas), inter-modelo (S6), y la de B1 al 90 % (config). La incertidumbre por sesgo común de la familia no se estima y se declara como límite.
5. **Qué se reporta.** S1-S8; `d_k` con intervalo; ítems y grupos con mayor desacuerdo; tabla cruzada de rúbricas por modelo; diagnósticos R-hat y ESS (015 §3.9: R-hat <= 1.05, ESS >= 100); y `physical_bottleneck`.
6. **Umbrales PROVISIONALES (míos, a fijar por el humano).**
   - Kappa ponderado por par >= 0.60 para usar un campo en cifras principales: heredado de 015 M27 (a su vez provisional).
   - Si algún par cae por debajo de 0.40 (valor mío, sin respaldo en la literatura que consulté): no se agrega ese modelo a la medida principal; se reporta aparte y se investiga el prompt. Si el par más bajo involucra a Haiku, la conclusión es "Haiku no sirve con este prompt", no "el campo es inválido".
   - Sin umbral para alfa de Krippendorff (reporte), como en 015.
   - La medida de registro (modelo o combinación de modelos) la elige el humano **antes** de ver resultados. Elegir el modelo que más se parece a los otros es un camino de bifurcación (012 §4.5).

## 6. Costo aproximado (aritmética sobre supuestos no medidos)

Base: tokens de 011 §4.f, ruta S con 10 grupos por lote, por corrida: 262,741 de entrada y 276,276 de salida (supuestos **[NO VERIFICADO]** de 011: 011 mismo advierte que el prompt fijo de 1,000 tokens probablemente se queda corto, y no incluyen tokens de razonamiento adaptativo).

Precios de lista verificados hoy (platform.claude.com, modelos): Haiku 5.5 "desde" 0.10 USD / 0.50 USD por millón de tokens de entrada/salida; Sonnet 5.5 2 / 10; Opus 5.5 4 / 20; la API por lotes tiene 50 % de descuento (según la misma página). La página no detalla qué condiciones activan el precio "desde" de Haiku.

| Modelo | Por corrida (USD, lista) | 3 corridas (USD, lista) |
|---|---|---|
| Haiku 5.5 | ~0.16 | ~0.49 |
| Sonnet 5.5 | ~3.29 | ~9.86 |
| Opus 5.5 | ~6.58 | ~19.73 |
| Total | | **~30** (sin lotes por API, sin razonamiento, sin prompt real) |

Es una cota inferior y orden de magnitud, no un presupuesto. **El proyecto no usa API** (015 M2, M28): con subagentes el costo no es en dinero sino en cuota de sesión, cuya cifra se desconoce (**[NO VERIFICADO]**) y que aumentaría al triple respecto de Sonnet solo. Costo humano evitado: ninguno; las horas del revisor (349 juicios, 015 §3.10) siguen sin estimar.

## 7. Preguntas abiertas para el humano

**Imprescindibles**
- **P1.** ¿Qué es "Opus evaluará los"? Recomiendo L1 (anotador independiente).
- **P2.** "No tendremos human annotations": ¿se renuncia también a la muestra de 300 funciones + 49 grupos con el usuario como revisor 1 (015 M29, §3.10)? Si se renuncia, el proyecto solo puede afirmar consistencia entre modelos y el artículo debe decirlo en el resumen. Si es solo la anotación masiva de Eloundou lo que no se tendrá, una muestra humana pequeña de un revisor es lo único que aporta algo independiente. Recomiendo conservarla aunque sea pequeña.

**Importantes**
- **P3.** ¿Eloundou pasa a medida principal (enmienda a 001) o se mantiene como comparación junto a `exposure_class`?
- **P4.** ¿Se permite correr Haiku y Opus por subagente (cuota) o se levanta la restricción de "sin API" (015 M2, M28, requiere decisión nueva y presupuesto)?
- **P5.** ¿3 o 2 corridas por modelo? ¿Y se completan primero las corridas 02 y 03 de Sonnet (017)?
- **P6.** ¿Se corre la variante de preámbulo actualizado (S5)? Sería otro `prompt_version`.
- **P7.** ¿Quién elige, antes de ver resultados, la medida de registro entre modelos?

## 8. Enmiendas propuestas (no aplicadas)

- **E-9a (015 M2/M38).** Sustituir "un solo modelo, sin segundo anotador" por "tres modelos de la misma familia (Haiku 5.5, Sonnet 5.5, Opus 5.5), mismo prompt, 3 corridas cada uno", con la vía que decida P4. Estado: propuesta.
- **E-9b (015 §3.11, rótulo).** Añadir el rótulo obligatorio "consistencia entre modelos de una misma familia; no es exactitud ni validación" a tablas y figuras mientras no exista referencia humana.
- **E-9c (solo si P3 = sí).** Cambio de medida principal en 001 §4.3-§4.4, `rubric.md` y `glossary.md`. No redacto texto: depende de la respuesta.
- **Glosario.** Si se adopta L1, posible término "anotador LLM" y "consistencia entre modelos". Propuesta, sin texto final.

## 9. Riesgos

1. **Sesgo compartido** de la misma familia: acuerdo alto con exactitud baja (Tabla 2 de Eloundou lo muestra con un solo modelo). Mitigación: rótulos, muestra humana (P2), no usar Opus como verdad.
2. **Autopreferencia / circularidad** si Opus adjudica (L2). Mitigación: L1; diagnóstico de 3.4.
3. **Confusión de modelo con esfuerzo** (esfuerzo por defecto distinto, hoy). Mitigación: fijarlo o registrarlo.
4. **Preámbulo anacrónico**: la rúbrica describe un LLM de OpenAI de 2023; cada modelo lo interpreta distinto. Mitigación: S5; comparar rangos.
5. **Bifurcación** al elegir modelo/combinación tras ver resultados. Mitigación: P7.
6. **Costo en cuota** triple o más; riesgo de corridas incompletas (017 ya muestra dos pendientes). Mitigación: orden por corridas completas (015 §3.7).
7. **Falsa precisión de B1** si se tratan corridas como independientes. Mitigación: `unidad = modelo`.
8. **Vacío de validez**: el artículo solo podría hablar de "exposición según modelos de IA", no de exposición de ocupaciones. Mitigación: lenguaje del resumen y de la sección de límites.

## 10. Lista de [NO VERIFICADO]

- Código de `src/annotate/` y `src/calibrate/b1_ordinal.py` (opción `unidad = modelo`, patrón de `run_id`, campo `model`): lectura solo por README y 017.
- ID efectivo del modelo en subagentes de Claude Code y posibilidad de fijar Haiku u Opus; soporte del parámetro `temperature` en los tres modelos; condiciones del precio "desde" de Haiku.
- Tokens de 011 §4.f, incluido el razonamiento adaptativo; cuota de sesión.
- Nombre del símbolo griego de la tercera medida de Eloundou (el usuario escribe "zeta/gamma").
- Existencia de `occ_level.csv` y su licencia, y de etiquetas por tarea (015 M37).
- Que Opus supere a Sonnet o Haiku en esta tarea; ningún benchmark consultado.
- Panickssery et al. (2024) y Kim et al. (2025): solo resúmenes de búsqueda; no abrí los PDF. Sus resultados son de otras tareas.
- Resto de 011 (líneas 276-474) y 015 (324-418), no leídos.

## 11. Fuentes (consultadas 2026-10-22)

- Anthropic, "Models overview" (IDs, precios, esfuerzo por defecto, retiro): https://platform.claude.com/docs/en/models/overview (redirigido desde docs.anthropic.com).
- Panickssery, Bowman, Feng (2024), "LLM Evaluators Recognize and Favor Their Own Generations", arXiv:2404.13076; NeurIPS 2024: https://arxiv.org/abs/2404.13076 (resumen vía búsqueda).
- Kim, Garg, Peng, Garg (2025), "Correlated Errors in Large Language Models", ICML 2025: https://proceedings.mlr.press/v267/kim25e.html y https://arxiv.org/pdf/2506.07962 (resumen vía búsqueda).
- Eloundou, Manning, Mishkin, Rock (2023), arXiv:2303.10130: verificada en 011 contra el PDF registrado (`eloundou_2023_v5_pdf`); no reconsultada aquí.
- Archivos del proyecto listados en la sección 0.

## Registro 1 (2026-10-22): respuestas del usuario y decisiones operativas

Sigue **pendiente de revisión humana** (ninguna decisión de este registro está aprobada por mí). El usuario aprobó llevar a cabo la tarea. Aclaración posterior suya: la clasificación se hace sobre las funciones/tareas de SINCO y sus descripciones (tablas parquet de SINCO, ruta S), no sobre O*NET; es consistente con 3.1 y 3.2.

### R1.1 Respuestas y lectura (cita textual del usuario)
| N.º | Respuesta | Lectura del agente |
|---|---|---|
| 1 | "Acepto Anotador independiente" | P1 = L1. Opus es un anotador más, ciego, con `ann-s-v1`; sin adjudicación ni referencia. |
| 2 | "renuncio que el artículo sea de consistencias entre modelos" | **AMBIGUA**, ver R1.2. |
| 3 | "Eloundou como medida de comparación" | P3 = comparación junto a `exposure_class`. E-9c no se activa; 001, `rubric.md` y `glossary.md` no cambian. |
| 4 | "Haiku y Opus como subagentes" | P4 = subagentes (cuota), sin API. Que Claude Code fije esos modelos sigue **[NO VERIFICADO]**; se registra el ID que reporte el entorno. |
| 5 | "2 corridas por modelo" | P5 = 2 por modelo (mínimo defendible de 3.3). La corrida Sonnet `-03`, ya exportada, **queda sin usar** (no entra a ningún cálculo). |
| 6 | "Se corre" | P6 = sí, variante de preámbulo, ver R1.4. |
| 7 | "agente métodos toma la mejor decision" | P7 delegada; ver R1.3. Sigue siendo propuesta mía, sujeta a revisión humana. |

Corridas base (6; nombres fijos): `ann-s-v1-2026-10-20-01` y `-02` (Sonnet); `ann-s-v1-2026-10-22-haiku-01` y `-02`; `ann-s-v1-2026-10-22-opus-01` y `-02`. Todas con `ann-s-v1`, sin modificarlo.

### R1.2 Respuesta 2: ambigüedad y qué se hace mientras tanto
Dos lecturas posibles: (a) el usuario renuncia a la muestra humana (015 M29, §3.10), es decir, a toda validación independiente; (b) el usuario rechaza que el artículo se limite a consistencia entre modelos (quiere otro enfoque o apoyo adicional). Son casi opuestas en sus consecuencias. No elijo.
- La anotación no depende de la respuesta: las 6 corridas y la variante del R1.4 se ejecutan igual.
- Se mantienen los rótulos "consistencia entre modelos, no exactitud" (E-9b) y la prohibición de lenguaje de validación hasta que se aclare.
- La muestra humana de 015 M29 no se programa ni se descarta.
- **Pregunta abierta P2b (imprescindible antes de redactar el artículo):** ¿renuncia a la muestra humana, o rechaza que el artículo se limite a consistencia entre modelos? Si es (b), ¿qué evidencia independiente acepta?

### R1.3 P7: medida de registro entre modelos (regla preespecificada, antes de ver resultados)
**Decisión propuesta.** La medida de registro de `E_g`, `alfa_S`, `beta_S` y `cota_sup_S` por grupo es la **media simple, con pesos iguales, de las medias por modelo** (cada media por modelo es el promedio de sus 2 corridas, calculado por script en `src/`), tomando los modelos que no queden excluidos por la regla. La regla se evalúa por campo (`exposure_class` para `E_g`; `eloundou_class` para las `*_S`).
- **Regla de exclusión.** Un modelo se excluye del campo si su kappa ponderado cuadrático medio (sobre los pares de corridas entre modelos) es **< 0.40 frente a AMBOS** modelos restantes. Si es bajo frente a uno solo, no se excluye y se marca. Un kappa intra-modelo bajo (entre sus 2 corridas) solo se marca, no excluye.
- **Si quedan menos de 2 modelos:** la medida de registro no se define; se reportan los tres valores por modelo y no se elige uno. No hay respaldo "el mejor modelo".
- **Siempre se reportan** los valores por modelo y el rango min-max (S6); no se sustituye la medida de registro tras ver datos.
- **Sensibilidad preespecificada (no alternativa):** excluir la corrida Sonnet `-01` (ver R1.5).
- **Umbrales provisionales (míos):** kappa >= 0.60 para cifras principales (heredado de 015 M27); 0.40 para excluir; B1 (017) sigue con `unidad = modelo` y no se reemplaza.
- **Justificación.** (i) No hay benchmark visto que ordene a los modelos en esta tarea (2.2.2), así que ponderar o elegir un "central" (Sonnet) sería arbitrario. (ii) La media evita elegir según qué modelo se parece más a los otros (012 §4.5). (iii) Pesos iguales no fingen independencia: el sesgo común de la familia sigue sin identificarse (2.2.3). (iv) La exclusión solo ocurre ante desacuerdo con ambos pares, lo que apunta a fallo del modelo con este prompt y no a una diferencia legítima.
- **Riesgo.** Un promedio de modelos correlacionados puede dar falsa seguridad; el umbral 0.40 es mío y sin respaldo en la literatura consultada.

### R1.4 P6: variante de preámbulo (ann-s-v2)
- **Prompt nuevo `ann-s-v2`.** `ann-s-v1` no se modifica. Diferencia única: en el bloque C se reemplaza el primer párrafo del preámbulo literal ("Consider the most powerful OpenAI large language model (LLM)..."). Quedan idénticos los bloques A, B, D, E, las definiciones E0-E3, los ejemplos, el formato y las variables. Cambia también el rótulo "ann-s-v1" por "ann-s-v2" en el SYSTEM; el resto, no.
- **Qué evita:** el anacronismo del LLM de OpenAI de 2023 (011 §4.e). Se conservan los límites de 2000 palabras y de hechos de menos de un año porque definen la frontera E1/E2; los textos de E2 siguen refiriéndose a "2000 words".
- **Texto propuesto del párrafo (sustituye al original; el orquestador crea el archivo):**
  > Consider a general-purpose large language model (LLM) of the kind you are, as available on the capability cutoff date, accessed through a chat interface. This model can complete many tasks that can be formulated as having text input and text output where the context for the input can be captured in 2000 words. The model also cannot draw up-to-date facts (those from <1 year ago) unless they are captured in the input.
- **Corridas (mínimo útil): 1 modelo (Sonnet) x 2 corridas**, `ann-s-v2-<fecha>-sonnet-01` y `-02`, tras las 6 base. Dos corridas permiten comparar el cambio v1 a v2 contra el ruido entre corridas del propio v1. Haiku y Opus no se corren en v2 (cuota).
- **Análisis (solo S5; no entra a la medida de registro):** kappa de `eloundou_class` v1 contra v2, comparado con kappa entre las corridas v1 de Sonnet. Control: `exposure_class` no depende del párrafo; su cambio estima el ruido residual.
- **Límites.** Un solo modelo no dice si el efecto es general; el cambio de redacción puede afectar también a E1/E2 por el término "of the kind you are" (auto-referencia). Son hipótesis a revisar.

### R1.5 Desviación operativa: entrega del lote por archivo
**Hecho a registrar.** Por cuota y tamaño de contexto, los subagentes de Haiku, Sonnet `-02` y Opus recibirán el lote leyéndolo de un archivo de texto único con el mensaje del lote, y escribirán su JSONL en un archivo (herramientas Read y Write solo para eso). La corrida Sonnet `-01` lo recibió dentro del mensaje.
- **Impacto en comparabilidad.** (1) Sonnet `-01` vs `-02` confunde canal y corrida: parte de su desacuerdo puede ser del canal. (2) Tasa de rechazo (JSONL inválido, ids faltantes o repetidos) puede variar por canal. (3) El texto debe ser idéntico; no verifiqué cómo lo generará el orquestador. (4) Con herramientas, un subagente podría leer otros archivos; se limita por instrucción, no por barrera técnica.
- **Controles propuestos.** Campo `delivery` (`message` o `file`) por corrida y registro; hash SHA-256 del texto del lote en archivo igual al hash del mensaje equivalente de `-01`; reporte de tasa de rechazo por corrida y canal; comparar kappa Sonnet `-01` vs `-02` con el de las parejas intra-modelo de Haiku y Opus (ambas por archivo) y publicar la diferencia sin interpretarla como efecto causal; sensibilidad sin `-01` (R1.3). Si la tasa de rechazo difiere de forma notable entre canales (umbral no fijado, sin dato), se registra un issue en `docs/issues/` (regla 5).
- **Riesgo residual.** El canal no se puede separar del modelo en Haiku y Opus (siempre archivo); el efecto de canal solo es estimable en Sonnet.

## Registro 2 (2026-10-23): ejecución, implementación y desviaciones (sin cifras; las cifras salen de los scripts)

### R2.1 Qué se ejecutó
- **Anotación completa:** 6 corridas base (Sonnet 2, Haiku 2, Opus 2; `ann-s-v1`) y 2 corridas de la variante (`ann-s-v2`, Sonnet `-01` y `-02`), todas por subagentes, sin API. Cada corrida pasó la validación de 015 §3.9 (`ruta_s validar`, archivos `validacion_*.json` en `data/processed/annotations/ruta_s/`). La corrida `ann-s-v1-2026-10-20-03` de Sonnet nunca se usó y el medidor la cuenta en el total.
- **Acuerdo entre modelos:** `python -m src.calibrate.acuerdo_modelos` (S1, S2, S4, S5, S6, S8 y la regla de exclusión de R1.3), salida `data/processed/calibracion/acuerdo_modelos.json` e `indice_por_grupo_*.csv`. La regla de exclusión se evaluó por campo, con las reglas de R1.3 sin cambios; el resultado está en el JSON.
- **Sensibilidad al preámbulo (S5, R1.4):** `python -m src.calibrate.sensibilidad_preambulo`, salida `sensibilidad_preambulo.json`. No entra a la medida de registro.
- **B1 ordinal (017) con `unidad = modelo`:** `eloundou_class` y `exposure_class`, salidas `b1_ordinal_<campo>_modelo_*`. Rótulo en `meta.json`: "PROVISIONAL, SIN VALIDAR"; lectura "consistencia entre corridas, NO exactitud". Lo no medible sigue sin medirse: el sesgo común de la familia Anthropic.

### R2.2 Implementación y supuestos que no estaban escritos
1. **Moda por modelo con 2 corridas.** 018 §5 hablaba de 3 corridas. Con 2, cualquier desacuerdo entre las corridas de un modelo es un empate; siguiendo §5 ("ítem ausente en ese anotador"), ese ítem queda ausente para ese modelo. Consecuencias que se declaran: (a) B1 `unidad = modelo` ve más a menudo los ítems fáciles; (b) el kappa calculado **sobre la moda** (`kappa_sobre_moda`) queda inflado por esa selección y **no** debe citarse; la cifra de referencia para umbrales es el kappa medio de pares de corridas. Es una decisión mía de implementación, pendiente de revisión humana.
2. **`ann-s-v2.md`** es `ann-s-v1.md` con el primer párrafo del preámbulo reemplazado por el texto de R1.4 y el rótulo cambiado; `ann-s-v1` no se tocó. `ruta_s export` ganó la opción `--prompt-version`.
3. **Sonnet v2** lleva `model = "sonnet (alias de subagente Claude Code; ID efectivo no verificado)"`, distinto del texto de las corridas v1 de Sonnet (`claude-sonnet-5-5 (subagente Claude Code)`). No se verificó que sea el mismo modelo.
4. **Herramientas del orquestador:** `orquesta_s` (`preparar`, `importar`, `ciclo`) y `progreso`; no anotan ni calculan exposición.

### R2.3 Desviaciones y hechos operativos
- **Canal por archivo** (R1.5) para Haiku, Opus y Sonnet v2 y la corrida `-02` de Sonnet; la `-01` fue por mensaje. El texto de instrucciones del subagente para Haiku, Opus y Sonnet v2 incluye "cuenta cuántos son antes de escribir" y "ningún function_id repetido"; la corrida `-01` y la `-02` de Sonnet v1 no lo llevaban. El efecto no está medido.
- **Cortes de cuota (429)** en tres ocasiones; los lotes interrumpidos no cuentan como intento (015 §3.7). Los archivos que alcanzaron a escribirse antes del corte pasaron por la misma validación.
- **Incidente de orquestación:** `ruta_s reanudar` devolvió a pendiente **todos** los lotes en curso de la corrida, no solo uno; se restauraron con `preparar` (mismos nombres de intento) sin intentos nuevos. Un lote de `ann-s-v2-...-02` se importó con un aviso del subagente sobre su propio conteo; la salida tiene el número de filas esperado y pasó la validación de ids.
- **Dos intentos de lote rechazados** en Haiku `-01` (ids faltante y repetido) y reintentados con un subagente nuevo; la respuesta cruda no se editó.

### R2.4 Lo que NO se hizo / sigue abierto
- No se corrieron B1 Gibbs ni B1 NumPyro categórico sobre la ruta S, ni la robustez "dejar un modelo fuera" (§5.3), ni S3 (Tabla 2), S7 (Frey-Osborne) ni las medidas `alfa_S`, `beta_S`, `cota_sup_S`, `E_g` (son de `src/score`).
- **P7:** la medida de registro la sigue eligiendo el humano; este registro no la fija.
- **P2b** (respuesta 2 del usuario) sigue ambigua.
- Sin cambios: muestra humana (015 §3.10), firma del preregistro 013, descarga de la ENOE.
- Pruebas: `tests/score/test_exposicion.py` (2 casos) fija `rubrica_version == "1"` y falla porque `docs/rubric.md` del árbol de trabajo ya está en versión 2 (cambio previo a esta ejecución); `tests/match/test_determinismo.py` falló por memoria del equipo (Windows 1455) al cargar el modelo de embeddings. Ninguno se tocó.
