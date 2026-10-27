# 011 - Método tipo Anthropic / Eloundou para SINCO 2019: capacidad teórica por función y capa opcional de uso observado

> **ESTADO: PROPUESTA PENDIENTE DE REVISIÓN HUMANA, CON ENMIENDAS PARCIALMENTE APROBADAS Y APLICADAS (Registro 4, sección 5, 2026-10-19).** El usuario aprobó E-1, E-2, E-3 y E-8 (cita transmitida por el orquestador) y se aplicaron a `docs/decisions/001-definicion-exposicion.md`. **E-4, E-5, E-6 y E-7 siguen PENDIENTES** (E-6 y E-7 modifican `docs/rubric.md` y `docs/glossary.md`, regla 2; E-5 el esquema; E-4 la agregación). El resto del documento (rutas, corrida completa, muestra humana, costos) sigue siendo propuesta y no autoriza gasto, modelo ni dependencias. Lo que contradiga 001 aprobada se escribe como ENMIENDA en la sección 5. **Nota de registro 2026-10-19 (Registro 3, sección 5):** el usuario descartó la capa de uso observado (equivale a U0).

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de las fuentes web: 2026-10-19
- Pedido del usuario (cita textual): "Use a similar method like anthropic. https://www.anthropic.com/research/labor-market-impacts and Eloundou, Tyna, Sam Manning, Pamela Mishkin, and Daniel Rock, 'Gpts are gpts: An early look at the labor market impact potential of large language models,' arXiv preprint arXiv:2303.10130, 2023, 10 but with the SINCO instead in Mexico."
- Revisión 2026-10-19 (verificación contra los PDF): secciones 0, 2, 4.b-4.g, 5, 6-13 corregidas contra los textos completos de ambas fuentes. La sección 4.c fue reescrita. Se añadió el registro de aprobación de la sección 5.
- Revisión 2026-10-19 (Registro 4): se registra la aprobación de E-1, E-2, E-3 y E-8, se aplican a 001 y se actualizan los estados de la sección 5, el riesgo 12, la pregunta 1 y la lista de [NO VERIFICADO]. El resto del texto no cambia.

## 0. Qué se verificó y qué no (leer primero)

**Verificado directamente contra los textos completos** (extraídos de los PDF por el orquestador con `pdftotext`; los PDF no se modificaron y están registrados en `data/raw/manifest.json`):
- **Eloundou et al. (2023)**, arXiv:2303.10130v5, 22-ago-2023, `eloundou_2023_v5_pdf` (sha256 que empieza `af3edd4e`). Cuerpo y apéndices A (rúbrica), B, C y D. **Paginación citada:** la que resulta de contar los saltos de página ("WORKING PAPER") del texto extraído, con p. 1 = portada y resumen; debe cotejarse con el PDF antes de citar páginas en el artículo.
- **Massenkoff y McCrory (2026)**, "Labor market impacts of AI: A new measure and early evidence", Anthropic, 5-mar-2026, `massenkoff_mccrory_2026_pdf` (sha256 que empieza `48c941db`). Paginación citada: la impresa en el pie de página (17 páginas). **El apéndice del informe no está en este PDF** (nota 7, p. 16: "Appendix available here").
- Archivos del proyecto: `CLAUDE.md`, decisiones 001, 003 y 010, `docs/rubric.md` y `docs/glossary.md` (v1), `docs/diccionario_datos_sinco.md`, `docs/sinco_pdf_exploracion.md`, `src/score/README.md`, `src/annotate/README.md`.
- Consultas web de esta revisión (2026-10-19, WebFetch/WebSearch; **resúmenes de una herramienta, no copias literales**, a cotejar por un humano): ficha y carpetas del conjunto de datos de Hugging Face `Anthropic/EconomicIndex`; `data_documentation.md` de su versión 2026-01-15; página de Anthropic sobre geografía del Economic Index; README de `github.com/openai/GPTs-are-GPTs`.

**Limitaciones de la extracción de texto**
- Los símbolos griegos no sobreviven en ninguno de los dos textos (se ven como vacío). Las definiciones de las tres medidas de Eloundou sí se leen, pero **el nombre del símbolo de la tercera (E1 + E2) no es verificable aquí**: el README del repositorio de Eloundou la llama "gamma". La versión previa de 010 y 011 decía "zeta, no gamma" sin base verificable; queda corregido (ver 010 §2.1). Este documento nombra las medidas por su definición.
- Los PDF originales no se inspeccionaron visualmente.

**Sigue sin verificarse**
- Apéndice de Anthropic (fórmula exacta, umbral de "uso suficiente", tratamiento de tareas raras, fuente de la fracción de tiempo por tarea). https://cdn.sanity.io/files/4zrzovbb/website/e5f77fc0e77c0185110b5e4b909602791ae76eae.pdf no se abrió.
- Si `geo_id = "MX"` existe en los datos geográficos del Economic Index y con cuántas conversaciones.
- Cualquier fuente pública de uso de IA por tarea u ocupación en México.
- Las decisiones 005, 008 y 009 (no existen con los nombres que probé; mi herramienta no lista directorios). Lo que sé de ellas viene de 001, 003, 010 y los README.
- `data/processed/*.parquet` no se inspeccionó; los conteos son los de los diccionarios.

## 1. Pregunta

¿Cómo construir para SINCO 2019 una medida de exposición a IA generativa "a la manera de" Eloundou et al. (2023) y de Anthropic (2026), de modo que (i) sea comparable con sus medidas, (ii) no dependa solo del crosswalk top-2 sin validar, (iii) separe con claridad exposición teórica de uso observado, y (iv) respete 001 (aprobada) y la regla de no sugerir pérdida de empleo?

## 2. Qué mide cada fuente (extracción verificada)

### 2.1 Anthropic (Massenkoff y McCrory, 2026), informe completo salvo apéndice

| Aspecto | Lo que dice el informe (página) |
|---|---|
| Nombre y etiqueta | "observed exposure"; el informe la presenta como "a new measure of AI displacement risk" (p. 2). **Este proyecto no usa "riesgo de desplazamiento"**: 001 §4.6 lo prohíbe; se traduce "exposición observada (cobertura de uso externa)". |
| Definición literal | "Our new measure, Observed Exposure, is meant to quantify: of those tasks that LLMs could theoretically speed up, which are actually seeing automated usage in professional settings?" (p. 5). |
| Aspectos que la elevan (p. 5) | Una ocupación tiene mayor exposición si: sus tareas son teóricamente posibles con IA; sus tareas tienen uso significativo en el Anthropic Economic Index; se realizan en contextos de trabajo; tiene mayor proporción de patrones de uso automatizados o implementación por API; y las tareas afectadas son mayor parte del rol. |
| Unidad | Tarea O*NET: "Exposure is typically defined at the task level" y "Our work follows this task-based approach ... before aggregating to occupations" (p. 4). O*NET con "around 800 unique occupations in the US" (p. 4). |
| Fuentes de datos (p. 4) | (1) O*NET; (2) "Our own usage data (as measured in the Anthropic Economic Index)"; (3) estimaciones por tarea de Eloundou et al. (2023). |
| Fechas del uso | Nota 5 (p. 15): "the previous two Anthropic Economic Index datasets, covering usage from August and November 2025"; "For ONET tasks that are highly semantically similar, we split the counts across them." **Inconsistencia interna:** la Fig. 1 (p. 4) dice que sus datos vienen de "the previous four Economic Index reports". No dice cuál aplica a la medida principal. |
| Capacidad teórica | Escala 1 / 0.5 / 0 (p. 5): 1 si un LLM solo puede duplicar la velocidad de la tarea, 0.5 si requiere herramientas o software adicionales construidos sobre el LLM, 0 en otro caso. Nota 4 (p. 15): "directamente expuestas" = completables en la mitad del tiempo con un LLM (límite de entrada de 2,000 palabras, sin acceso a hechos recientes); "expuestas con herramientas" = igual aceleración con un LLM con acceso a software, p. ej. recuperación de información y procesamiento de imágenes. Coincide con la medida E1 + 0.5·E2 de Eloundou. **No dice si usó las etiquetas humanas o las de GPT-4.** El símbolo no es legible en el texto extraído. |
| Cómo combina capacidad y uso (p. 6) | "We count tasks that are theoretically capable with an LLM as covered if they have seen sufficient work-related usage in Claude traffic. We then adjust for how the task is being carried out: fully automated implementations receive full weight, while augmentative use receives half weight. Finally, the task-level coverage measures are averaged to the occupation level weighted by the fraction of time spent on each task." |
| Lo que NO está en el texto | La fórmula ("We give mathematical details in the Appendix", p. 6); el umbral de "sufficient" usage (se menciona "the minimum threshold", p. 8); cómo entra beta (la nota 6, pp. 15-16, pregunta "Should the Eloundou et al. (2023) measure enter as {0, 0.5, 1} or something else?"); cómo se tratan las tareas raras parecidas a las de mucho uso (nota 6); de dónde sale la "time fraction measure" (p. 7). Todo **[NO VERIFICADO]**: apéndice no disponible. |
| Agregación | A ocupación: promedio ponderado por la fracción de tiempo de cada tarea (p. 6). A categoría ocupacional: "averaging to the occupation category weighting by total employment" (p. 7). Ocupación a CPS: el cruce O*NET-SOC a occ1990 usa el crosswalk de Eckhardt y Goldschlag (2025) (nota 8, p. 16). |
| Resultados citados (EE. UU., no comparables con SINCO) | β en Computación y Matemáticas 94 % y Oficina y Administración 90 % de las tareas (p. 7); cobertura observada en Computación y Matemáticas 33 % (p. 7); Programadores 75 %, Representantes de servicio al cliente segundos, Capturistas de datos 67 % (pp. 7-8); 30 % de los trabajadores con cobertura cero "as their tasks appeared too infrequently in our data to meet the minimum threshold" (p. 8); 97 % de las tareas observadas en categorías con β = 0.5 o 1, y las tareas con β = 1 son 68 % del uso y las de β = 0 el 3 % (pp. 4-5, Fig. 1). |
| Relación capacidad-uso | Alta correlación (p. 5); explicaciones propuestas de la brecha: limitaciones del modelo, restricciones legales, requisitos de software, pasos de verificación humana (p. 5). Ejemplo: la tarea "Authorize drug refills..." tiene β = 1 y no se ha observado a Claude haciéndola (p. 5). |
| Validación | Regresión ponderada por empleo contra las proyecciones del BLS 2024-2034: por cada 10 puntos porcentuales de cobertura, la proyección de crecimiento baja 0.6 puntos porcentuales; "the relationship is slight"; "there is no such correlation using the Eloundou et al. measure alone" (p. 9). Correlación de rango de Spearman "exceedingly high" entre distintas resoluciones de las decisiones de juicio (nota 6, pp. 15-16; las cifras están en el apéndice). Características de los trabajadores (CPS, ago-oct 2022): el cuartil superior es 16 puntos porcentuales más probable que sea mujer, gana 47 % más, etc. (p. 9). Desempleo: diferencias en diferencias, cuartil superior de cobertura frente a los de cobertura cero (30 % de los trabajadores), efecto pequeño e insignificante (pp. 10-11); efecto mínimo detectable "on the order of 1 percentage point" (p. 12); contratación de jóvenes de 22 a 25 años: caída de 14 % en la tasa de hallazgo de empleo, "just barely statistically significant" (p. 13). |
| Límites declarados | Del propio informe: la medida "won't capture every channel" (p. 3); "judgment calls ... at every step" (nota 6, p. 15); el uso es solo de Claude ("Our own usage data"); la medida de Eloundou "is linked to LLM capabilities as of early 2023" y podría actualizarse (p. 14); la contratación de jóvenes tiene interpretaciones alternativas y las transiciones laborales pueden estar mal medidas en encuestas (p. 13; nota 11, p. 16); solo datos de EE. UU. |
| Otros países | Una sola mención: "Our task- and occupation-level exposure measures can readily incorporate other usage data, and be extended to different countries. We intend to apply this methodology to new settings over time." (nota 3, p. 15). El informe no presenta datos de ningún otro país. |
| Disponibilidad | "Observed coverage at the task and job level is available at: https://huggingface.co/datasets/Anthropic/EconomicIndex" (p. 14). **El informe no declara licencia.** Ver 4.c para lo que muestra el conjunto de datos. |

### 2.2 Eloundou, Manning, Mishkin y Rock (2023), v5, texto completo

Páginas según la nota de la sección 0.

- **Qué miden:** "exposure" como "whether access to an LLM or LLM-powered system would reduce the time required for a human to perform a specific DWA or complete a task by at least 50 percent" (§3.3, pp. 6-7). Es un "proxy for potential economic impact without distinguishing between labor-augmenting or labor-displacing effects" (p. 2) y "technical feasibility does not guarantee labor productivity or automation outcomes" (p. 3).
- **Rúbrica:** E0, E1, E2 y E3. Texto literal en la sección 5 (E-2), apéndice A.1 (pp. 24-26). Resumen en pp. 6-7.
- **Umbral:** reducción de tiempo de al menos 50 % con calidad equivalente. Es "somewhat arbitrary", "selected for ease of interpretation by annotators", y alto a propósito porque esperaban reducciones reales menores (pp. 7-8). "Equivalent quality" = un tercero, típicamente el receptor, no notaría ni le importaría la ayuda del LLM (p. 7, nota a). En su validación interna, el umbral correspondía de cerca a si un LLM o software basado en LLM podía hacer la parte central o casi toda la tarea (p. 8).
- **Capacidades de imagen y software:** E2 = software desarrollado sobre el LLM; en la rúbrica completa las capacidades de imagen se etiquetan aparte (E3) "to facilitate annotation, though we combine E2 and E3 for all analyses" (p. 7, nota b). En la medida de exposición directa (solo E1) no se consideran capacidades de visión (p. 23).
- **Agregaciones** (p. 8): (i) solo E1, "lower bound"; (ii) E1 + 0.5·E2, el 0.5 "intended to account for exposure when deploying the technology via complementary tools and applications necessitates additional investment"; (iii) E1 + E2, "an upper bound". Si no se especifica, el lector debe asumir la medida (ii) (pp. 8-9; el texto la describe como aquella en que las tareas directamente expuestas cuentan el doble que las que requieren innovación complementaria). Símbolos no legibles en el texto extraído; nombres [NO VERIFICADO] (sección 0).
- **Ponderación:** las tareas *core* pesan el doble que las *supplemental*, con pesos que suman 1 por ocupación (nota al pie de la Tabla 2 en p. 8; nota 6 en p. 11; nota 7 en p. 12). **No todas las tablas y figuras la usan:** Fig. 3, Fig. 5 y Tablas 4-7 usan pesos iguales (pp. 12-18). Un análisis con pesos de importancia de O*NET no cambió los hallazgos de manera significativa, aunque no ponderar por importancia da casos curiosos (barberos) (p. 11).
- **Datos:** O*NET 27.2: 1,016 ocupaciones, 19,265 tareas (descripción de tarea y ocupación), 2,087 DWA (p. 6). Empleo y salario de BLS 2020-2021 y CPS; fuentes que "primarily capture workers who are not self-employed, are documented, and are working in the so-called formal economy" (p. 6).
- **Anotación** (pp. 7-8): humanos: los autores etiquetaron una muestra grande de tareas y los DWA que exigen mucha fisicalidad; anotadores contratados, con experiencia en revisar salidas de modelos de OpenAI, etiquetaron el resto de los DWA y un subconjunto de tareas (nota 5, p. 8); se agrega DWA a tarea y a ocupación. GPT-4 (versión temprana) etiquetó todos los pares tarea-ocupación (no los DWA). La rúbrica de GPT-4 se modificó levemente "to enhance agreement with a set of human labels" (p. 8); en la p. 2 se describe como "a prompt tuned for agreement with a sample of labels from the authors". Las rúbricas de humanos y de GPT-4 difieren a propósito (p. 9).
- **Acuerdo humano-GPT-4** (Tabla 2, p. 8; "agreement" = frecuencia con que coinciden en la anotación; el pie no explica el cálculo para medidas ponderadas):

  | Comparación | Medida | Acuerdo | Pearson |
  |---|---|---|---|
  | GPT-4 R1 vs humanos | E1 | 80.8 % | 0.223 |
  | | E1 + 0.5·E2 | 65.6 % | 0.591 |
  | | E1 + E2 | 82.1 % | 0.654 |
  | GPT-4 R2 vs humanos | E1 | 81.8 % | 0.221 |
  | | E1 + 0.5·E2 | 65.6 % | 0.538 |
  | | E1 + E2 | 79.5 % | 0.589 |
  | GPT-4 R1 vs GPT-4 R2 | E1 | 91.1 % | 0.611 |
  | | E1 + 0.5·E2 | 76.0 % | 0.705 |
  | | E1 + E2 | 82.4 % | 0.680 |

  El pie dice "In the paper we use GPT-4, Rubric 1", pero §3.4.2 dice "we present results from human annotators as our primary results" (p. 9): inconsistencia interna sobre cuál anotación es la principal. A nivel ocupación hablan de "high degree of agreement" (Fig. 2, p. 10) con GPT-4 más bajo que los humanos cerca del extremo superior.
- **Resultados de referencia (EE. UU., no comparables con SINCO):** medias por ocupación para las tres medidas 0.14 / 0.30 / 0.46 (humanos) y 0.14 / 0.34 / 0.55 (GPT-4) (Tabla 3, p. 12); 80 % de los trabajadores en ocupaciones con al menos 10 % de tareas expuestas; 19 % con al menos 50 % (p. 1, p. 11); 34 ocupaciones sin ninguna tarea expuesta (Tabla 11, p. 31).
- **Limitaciones declaradas** (§3.4, pp. 9-10; §6.3, p. 23): etiquetas subjetivas y anotadores "not occupationally diverse"; GPT-4 sensible a redacción, orden, ejemplos, nivel de detalle y definiciones, y "none should be considered the definitive ground truth"; validez del marco por tareas (si falla, "our exposure analysis would largely be invalidated"); anotadores que desconocían las ocupaciones asociadas a cada DWA; medida prospectiva; fuentes de desacuerdo (tareas que exigen cambiar hábitos de varias personas, normas o regulación que piden supervisión humana, tecnología ya existente); foco en EE. UU., que limita la generalización a otros países por organización industrial, infraestructura, regulación, "linguistic diversity" y contexto cultural.
- **Validación frente a otras medidas** (§5, pp. 19-21): asociación positiva con Webb (software), SML y rutina cognitiva; "for the most part" sin correlación con el AIOE de Felten et al. (2018); correlación negativa, condicional, con robots de Webb, rutina manual y la medida de automatización de Frey y Osborne; R² entre 60.7 % y 72.8 % (p. 20).
- **Disponibilidad de etiquetas:** el texto del artículo no menciona publicación de datos. El README del repositorio `github.com/openai/GPTs-are-GPTs` (WebFetch, resumen) dice "Occupation level codes are in occ_level.csv", con calificaciones de GPT-4 y de humanos y las tres medidas; licencia MIT en la barra lateral. **Etiquetas por tarea: no confirmadas.**

### 2.3 Diferencia estructural entre la rúbrica de 001 y la de Eloundou

| | 001 (aprobada, según mi lectura) | Eloundou (A.1, verificado) |
|---|---|---|
| Criterio de E1 | La IA reduce sustancialmente el esfuerzo, pero un **humano ejecuta, supervisa o valida** | El acceso directo al LLM (interfaz tipo ChatGPT o Playground) **solo** reduce el tiempo en al menos la mitad con calidad equivalente |
| Criterio de E2 | La IA (con herramientas razonables) **completa la tarea** | El LLM solo puede no alcanzar la mitad, pero "it is easy to imagine additional software" sobre el LLM que sí |
| Eje que ordena | Rol humano (apoyo frente a ejecución completa) | Qué se necesita para lograr la reducción de tiempo (LLM solo frente a LLM más software) |
| Papel del humano | Define las clases | No define las clases: la tarea de recetar medicamentos se etiqueta E2 aunque "it still requires a human in the loop" (A.1, p. 26) |
| Umbral numérico | Ninguno (001 3.3 y el README de annotate lo señalan) | 50 % del tiempo, calidad equivalente (nota a, p. 7) |
| Referencia del modelo | Sistema de IA con fecha de corte de capacidades | LLM de 2023 con entrada de 2,000 palabras y sin hechos de menos de 1 año (A.1, p. 24) |
| Cuello físico | Campo `physical_bottleneck` | E0 si la tarea no cabe en texto/imagen: "You do not have access to any other physical tools"; E0 si exige "a high degree of human interaction" (A.1, pp. 24-25) |
| Puntaje | E0 0, E1 0.5, E2 1 | E1; E1 + 0.5·E2; E1 + E2 |

No existe un mapeo determinista entre ambas: una tarea puede ser E1 de 001 (humano valida) y E1 de Eloundou (LLM solo ahorra >= 50 %), o E1 de 001 y E2 de Eloundou (el ahorro exige software), o E2 de 001 con E1 o E2 de Eloundou. Es una **hipótesis**; el ejemplo de la p. 26 la refuerza (una tarea con humano que decide es E2 de Eloundou). Se mide con la tabla cruzada de las 9 celdas (12 si se separa EL3) en el piloto.

## 3. Propuesta (resumen)

1. **Capa 1, exposición teórica (la medida principal del proyecto).** Anotación por LLM de cada **función SINCO** (ruta S, nativa, sin crosswalk) y, como contraste, de cada **tarea O*NET** (ruta O, ya prevista en 001 con crosswalk top-2 sin validar). En cada unidad se anotan **dos campos independientes**: `exposure_class` de 001 (E0/E1/E2, sin cambios) y un campo nuevo `eloundou_class` con la rúbrica literal de Eloundou (umbral de 50 % de tiempo), que alimenta las medidas `alfa_S`, `beta_S` y `cota_sup_S`, comparables con la literatura. Requiere la ENMIENDA de la sección 5.
2. **Capa 2, uso observado (opcional, diferida).** Solo con datos de uso verificados y de licencia compatible. Se reporta como **cobertura de uso externa (Claude, tareas O*NET)**, nunca como uso en México. Ver 4.c para lo que existe y lo que no. **Estado (Registro 3, sección 5): descartada por el usuario el 2026-10-19; se mantiene U0.**
3. **Capa 3, escenarios de pérdida de empleo:** fuera de este documento (CLAUDE.md, 001 §4.6).

## 4. Diseño detallado

### 4.a Unidad de análisis y cómo se evita depender solo del crosswalk

| Ruta | Unidad "tarea" | Conteo real | Depende del crosswalk top-2 |
|---|---|---|---|
| S (principal propuesta) | Función SINCO (`sinco_funciones`), con título, descripción y ocupaciones ejemplo como contexto | 3,542 funciones en 457 de 490 grupos (7.75 por grupo) | No |
| O (contraste) | Tarea O*NET (core/supplemental), agregada a `E_o` y llevada a SINCO por el top-2 | Según el universo de O*NET 31.0 (conteo del proyecto **[NO VERIFICADO]**; Eloundou usó 19,265 con O*NET 27.2, p. 6) | Sí, `sin_validar` |

- **Por qué S como principal:** es la única ruta con medición propia sin el eslabón más débil; usa texto mexicano en español; es el análogo más cercano a "tarea" que el catálogo ofrece. Esta ruta es el Método A de 010 ampliado.
- **Qué impide depender solo del crosswalk:** (1) S se calcula sin crosswalk; (2) la ruta O se reporta lado a lado y la discrepancia `E_A - E_O` de 010 (Método C) queda como diagnóstico del crosswalk; (3) la capa de uso observado, si existe, sí requiere crosswalk (el uso está por tarea O*NET) o una vinculación semántica nueva, y por eso queda rotulada como dependiente de ello.
- **Contexto por función** (herencia de 010 §3.1): título del grupo, descripción y ocupaciones ejemplo; `Excluye` fuera del prompt principal; ítems con `afectado_por_errata` omitidos de contexto; 2281 con función fusionada marcada.
- **Residuales:** 33 grupos sin funciones -> NA (`motivo_na = "residual_sin_funciones"`), sin imputación en el caso base (010 §3.3, 003 §4).

### 4.b Rúbrica: tres alternativas y decisión

| Alternativa | Argumentos a favor | En contra |
|---|---|---|
| R1. Adoptar la rúbrica de Eloundou tal cual y reemplazar la de 001 | Máxima comparabilidad con Eloundou y con el beta de Anthropic; umbral operativo (50 % del tiempo) | Contradice 001 y 006; pierde el eje "humano valida / IA ejecuta"; el umbral de tiempo es difícil de aplicar a funciones genéricas de SINCO; la rúbrica de Eloundou describe un LLM de 2023 y fue calibrada con GPT-4 sobre tareas O*NET, no sobre el catálogo mexicano |
| R2. Mantener solo 001 | Sin enmienda; ya probada en el piloto de 40 tareas | No es comparable con las medidas de Eloundou ni con el beta de Anthropic; el README de annotate reconoce que no tiene umbral de tiempo |
| **R3. Anotación dual: 001 + campo `eloundou_class` (propuesta)** | Conserva 001 como medida principal; añade una medida comparable; permite medir empíricamente la relación entre ambas rúbricas; un solo recorrido por el texto | Requiere enmienda a 001 §4.3 y §7; más tokens de salida; riesgo de que un campo contamine el otro dentro de la misma respuesta (se mide con la ablación de la sección 4.g) |

**Decisión propuesta: R3.** (Con la aprobación de E-1, E-2, E-3 y E-8 en el Registro 4, 001 incorpora el campo `eloundou_class` y la ruta S; E-5 a E-7 siguen pendientes.) Las clases del campo nuevo se llaman **EL0 / EL1 / EL2 / EL3** (no "E0/E1/E2") para que nunca se confunda con la escala de 001. EL3 (imagen) se **anota por separado y se funde con EL2 en todas las medidas**, como hace Eloundou (p. 7, nota b). Mapas de puntaje: `alfa_S` = EL1; `beta_S` = EL1 + 0.5·EL2; `cota_sup_S` = EL1 + EL2 (por unidad, y su promedio por grupo). `cota_sup_S` es la tercera medida de Eloundou; el nombre de su símbolo es [NO VERIFICADO] (sección 0). La medida principal del proyecto sigue siendo `E_g` de 001; las `*_S` son medidas **de comparación**.

**Mapeo explícito entre ambas, a verificar (no a asumir):** se publica la tabla cruzada observada `exposure_class x eloundou_class` y no se convierte una escala en otra por regla. Si el humano prefiere una sola anotación, la alternativa es R2 con la regla "comparar rangos, no niveles".

### 4.c Capacidad teórica frente a uso observado: qué se puede hacer en México

**Reescrita con lo verificado.** Todo lo que sigue es propuesta pendiente de revisión humana; no se ejecutó nada. **Nota de registro 2026-10-19 (Registro 3, sección 5):** el usuario descartó la capa de uso observado por falta de datos de México; equivale a U0. Los niveles U1-U4 de 4.c.3 se conservan como registro de lo analizado y no se persiguen.

#### 4.c.1 Cómo se arma la medida de Anthropic y qué pieza se puede replicar con SINCO

Lo que el informe permite reconstruir (pp. 5-7): para cada tarea O*NET hay (a) una capacidad teórica beta en {0, 0.5, 1}; (b) una indicación de si la tarea tiene uso suficiente relacionado con trabajo en el tráfico de Claude y de si ese uso es automatizado (peso 1) o aumentativo (peso 0.5); (c) una fracción del tiempo de la ocupación. La cobertura por ocupación es el promedio de la cobertura por tarea ponderado por (c); las categorías ocupacionales se promedian ponderadas por empleo. La forma exacta de combinar (a) y (b) (¿beta filtra o pondera?) y el umbral de uso están en el apéndice y son **[NO VERIFICADO]**; la nota 6 (pp. 15-16) dice que son decisiones de juicio.

| Pieza de la medida de Anthropic | Qué requiere | ¿Se puede con SINCO hoy? |
|---|---|---|
| (a) Capacidad teórica por tarea | Anotación con la rúbrica de Eloundou | **Sí.** Ruta S (función SINCO) y ruta O (tarea O*NET) con `eloundou_class`. Da `alfa_S`, `beta_S` y `cota_sup_S` por función y por grupo. Es el análogo del área azul de la Fig. 2 (pp. 6-7). |
| (c) Fracción de tiempo por tarea | Datos de tiempo | **No en SINCO:** las funciones no traen tiempo ni importancia; pesos iguales (010 §3.6). En la ruta O, proxies de O*NET (importancia, relevancia, frecuencia) sin garantía de equivalencia: [NO VERIFICADO], igual que en Eloundou, que probó importancia sin cambios significativos (p. 11). |
| (b) Uso suficiente por tarea | Conteos de uso por tarea | **No con datos mexicanos.** Solo uso externo de Claude por tarea O*NET (ver 4.c.2). |
| (b) Modo automatizado/aumentativo | Clasificación de las conversaciones | **No** sin los datos de uso. |
| (b) Contexto laboral | Filtro de las conversaciones | **No** sin los datos de uso. |
| Agregación a categoría por empleo total | Empleo por ocupación | **Parcial:** sí en principio con ENOE (fuente no consultada, "requiere decisión", 001 §10.6); mientras no se decida, solo promedio no ponderado rotulado. |
| Validación contra proyecciones BLS (p. 9) | Proyecciones de empleo por ocupación | **No:** no se identificó un equivalente mexicano verificado. |
| Resultados del mercado laboral con la CPS (pp. 10-13) | Encuesta con ocupación previa de los desempleados | **Fuera del alcance del proyecto** (los escenarios de pérdida van aparte). ENOE no fue consultada. |

**Conclusión sobre qué es replicable sin datos de uso:** solo el lado de la **capacidad teórica** (el "techo"), agregado a grupos SINCO, y su comparación ordinal con las cifras de Eloundou y con el área azul de Anthropic. **No es replicable** la cobertura observada (el área roja), la brecha entre capacidad y uso, la ponderación automatizado/aumentativo, el umbral de uso mínimo ni la validación con proyecciones de empleo. Un detalle importante: el 30 % de trabajadores con "cobertura cero" en Anthropic resulta de que las tareas aparecen poco en sus datos y no alcanzan el umbral mínimo (p. 8), no de beta = 0; por eso "porcentaje de empleo con `alfa_S` = 0" no es un análogo equivalente y no debe presentarse como tal.

**Prohibido sintetizar uso:** no se construye una "cobertura" a partir de la anotación del LLM o de supuestos; sería inventar un dato de uso.

#### 4.c.2 Qué datos de uso existen (verificado 2026-10-19; resúmenes de herramienta, a cotejar)

- **Conjunto de datos del informe.** El informe dice que la cobertura observada a nivel de tarea y ocupación está en https://huggingface.co/datasets/Anthropic/EconomicIndex (p. 14). La ficha dice "Data released under CC-BY, code released under MIT License" (versión de CC-BY no especificada); la etiqueta de metadatos dice "mit". Carpeta `labor_market_impacts/`: `job_exposure.csv` con columnas `occ_code`, `title`, `observed_exposure` (≈ 756 filas; primeras filas leídas, p. ej. "11-1011, Chief Executives, 0.0333") y `task_penetration.csv` con columnas `task`, `penetration` (texto de la tarea, sin código de tarea; 1.89 MB). La ficha no confirma que sean la medida del informe; coinciden en nombre y contenido. **No hay en esos archivos** beta, fracciones de tiempo ni conteos (por las columnas), así que la medida no se puede reconstruir ni auditar a partir de ellos. Qué significa exactamente `penetration`: [NO VERIFICADO] (apéndice).
- **Datos geográficos del Economic Index.** `release_2026_01_15/data_documentation.md`: `geography` puede ser "country", "country-state" o "global"; `geo_id` usa ISO 3166-1; "Minimum Observations: 200 conversations per country, 100 per country-state region"; para Claude.ai hay `onet_task_pct` ("Percentage of geographic total using this task"); los datos de la API de primera parte no tienen desglose geográfico. La página de Anthropic sobre geografía (https://www.anthropic.com/research/economic-index-geography) menciona a Brasil y no a México, y dice que los datos geográficos y de tareas están disponibles para descarga. **Que México aparezca en los datos, con cuántas conversaciones y con cuántas tareas O*NET con cuentas: [NO VERIFICADO].**
- **Uso en México por trabajadores:** no se encontró ni verificó ninguna fuente pública. Candidatas **no consultadas** **[NO VERIFICADO]**: ENDUTIH y ENOE (INEGI), encuestas propias, datos de proveedores de IA. ENDUTIH mide uso de tecnologías de información; no verifiqué que mida uso de IA ni por tarea.

#### 4.c.3 Propuesta concreta de capa de uso para México (escalonada, condicionada)

**Estado 2026-10-19: el usuario descartó esta capa (Registro 3, sección 5). Se mantiene U0.** Lo que sigue se conserva sin cambios como registro de lo analizado y solo se reactivaría con una decisión nueva.

Cada nivel se activa solo si el anterior se aprueba y su prueba de factibilidad pasa. Ninguno se ha ejecutado.

- **U0 (base, recomendada).** Sin capa de uso. El artículo habla solo de exposición teórica (`E_g`, `alfa_S`, `beta_S`, `cota_sup_S`).
- **U1. Cobertura de uso externa importada (EE. UU./global).** Unir `task_penetration.csv` a las tareas de la ruta O por texto normalizado; calcular `penetration` promedio por ocupación O*NET con pesos iguales (sin tiempo); llevarla a SINCO por el crosswalk top-2. Etiqueta obligatoria: "cobertura de uso externa (Claude), `sin_validar` por crosswalk". Pruebas de factibilidad previas: (i) tasa de coincidencia de texto entre `task_penetration.csv` y la versión de O*NET del proyecto (la versión que usó Anthropic: [NO VERIFICADO]); (ii) definición de `penetration` en el apéndice; (iii) comparar el promedio ponderado igual por ocupación con `observed_exposure` de `job_exposure.csv`: un desvío grande indicaría que faltan los pesos de tiempo o la combinación con beta (prueba de reproducibilidad, no de validez).
- **U2. Mezcla de tareas de usuarios en México (descriptiva).** Si los datos geográficos incluyen `geo_id = "MX"` con conteos suficientes, usar `onet_task_pct` de México frente al global para describir qué tareas O*NET predominan en el uso de Claude.ai desde México. Es **uso de usuarios de Claude.ai en México**, autoseleccionados y no representativos de la fuerza de trabajo; no mide empleo ni se pondera por empleo. Con un mínimo de 200 conversaciones por país, es esperable que las celdas por tarea sean escasas ([NO VERIFICADO] hasta mirar los datos). Prueba de factibilidad: descargar `release_2026_01_15` (carpeta de 142 MB según la página), comprobar que existe México y contar tareas con cuentas.
- **U3. Vinculación a funciones SINCO sin top-2.** Repartir el uso entre funciones SINCO semánticamente parecidas a las tareas con uso, como Anthropic reparte cuentas entre tareas O*NET muy parecidas (nota 5, p. 15). Requiere embeddings, que 010 Método B deja como dependencia no aprobada; sin esa aprobación, U3 no existe.
- **U4. Uso de IA por trabajadores en México.** No existe fuente verificada. Requiere decisión nueva y fuente nueva (p. ej. módulo de encuesta); fuera de este documento.

**Nomenclatura obligatoria:** "exposición teórica" para la capa 1; "cobertura de uso externa (Claude, tareas O*NET)" para U1; "mezcla de tareas de usuarios de Claude.ai en México" para U2. Prohibido llamar a cualquiera de ellas riesgo de pérdida de empleo o de desplazamiento.

### 4.d Agregación

**Función -> grupo unitario (ruta S).**
- Medida principal `E_g = (1/n) sum_f e_f`, pesos iguales sobre todas las funciones (SINCO no distingue core/supplemental ni da tiempos). Es la regla de 010 §3.6.
- Medidas de comparación: `alfa_S`, `beta_S`, `cota_sup_S` con los mismos pesos iguales.
- Además: `share_E2`, `share_any` (001), `physical_bottleneck` por grupo, y el mínimo y el máximo entre corridas.
- Sin ponderación por orden de aparición de la función: no hay evidencia de que el orden indique importancia **[NO VERIFICADO]**.
- Grupos con < 3 funciones: `pocas_funciones` (umbral PROVISIONAL de 010).

**Tarea -> ocupación O*NET -> SINCO (ruta O).**
- Principal: 001 §4.4 (core, pesos iguales).
- Variante "tipo Eloundou": core con peso 2 y supplemental con peso 1, normalizados a 1 por ocupación (p. 8 y notas 6-7). Eloundou misma usa pesos iguales en varias figuras y tablas (pp. 12-18).
- Variante "tipo Anthropic": pesos por la fracción de tiempo de cada tarea; la fuente de ese tiempo no está en el texto del informe ("our time fraction measure", p. 7) **[NO VERIFICADO]**. En O*NET podría aproximarse con importancia, relevancia o frecuencia (ya existen `E_o_pond_im`, `E_o_pond_rt` en el módulo score, pero 001 las marca **[NO VERIFICADO]**).
- Llevar `E_o` a SINCO: reglas 1:1, 1:N y N:1 de 001 §4.5 sin cambios.

**Niveles superiores (subgrupo 163, grupo principal 52, división 9).** Como en Anthropic (ocupaciones a categorías ponderadas por empleo total, p. 7) y como exige 003 §1: promedio ponderado por empleo. La fuente (ENOE u otra) "requiere decisión". Mientras tanto: promedio no ponderado rotulado "descriptivo, no ponderado por empleo".

**Comparación con las medidas de Eloundou.** Se calculan sobre el campo `eloundou_class` con las definiciones de la sección 2.2. Diferencias que impiden igualdad de niveles: unidad (función SINCO frente a tarea O*NET y DWA), pesos (iguales frente a core 2:1), modelo anotador y fecha (Sonnet 5.5 en 2026 frente a una versión temprana de GPT-4 y humanos en 2023), el LLM de referencia de la rúbrica (2023, 2,000 palabras), y un catálogo distinto. Se comparan **rangos y concordancia ordinal**, no niveles absolutos.

**Análogo de "trabajadores con cobertura cero".** No es equivalente (ver 4.c.1). Con ponderación por empleo se puede reportar el porcentaje del empleo en grupos con `alfa_S` = 0 como medida de exposición directa nula, nombrada así; con ~8 funciones por grupo y 3 corridas esperar pocos ceros (sin dato); no se fija umbral.

### 4.e Anotadores y trazabilidad (regla 4)

- **Hoy:** subagentes de Claude Code con Sonnet 5.5, sin API; temperatura solicitada pero no controlable (se registra nula con `temperature_note`, como en el piloto); fecha de corte de capacidades = fecha de la corrida (decidido para el piloto, 010/001 §10.3). **Modelo/vía, fecha de corte y presupuesto para la corrida completa siguen "requiere decisión"** (008 §7, según 001 y los README).
- **Prompt nuevo:** `ann-v2-sinco-el` (propuesto), nunca una edición de `ann-v1` (inmutable, con hash). Incluye: rúbrica de 001 y rúbrica de Eloundou **copiada literal** del apéndice A.1 (texto en la sección 5, E-2; si se traduce al español, el prompt traducido es una `prompt_version` distinta), instrucción de clasificar los dos campos de manera independiente y de no corregir uno con base en el otro. Dos observaciones del texto: (i) el preámbulo literal fija un LLM de 2023 (2,000 palabras, sin hechos de menos de un año); aplicarlo literal permite comparar con Eloundou pero mide exposición a ese modelo de referencia, y una versión actualizada del preámbulo sería otro prompt y otra decisión; (ii) Eloundou usó una rúbrica levemente distinta para humanos y para GPT-4 (p. 9); aquí se propone la literal para todos y se registra como desviación.
- **Corridas:** 3 independientes, con orden propio de grupos y funciones por corrida (semilla `seed_base + NN`), sin que los subagentes lean otras corridas (independencia garantizada por el orquestador).
- **Registro por corrida:** `run_id`, `prompt_version`, `prompt_sha256`, modelo, fecha de corrida, fecha de corte, versión del catálogo (`sinco_fuente.sha256`), `temperature`/`temperature_note`. Esquema nuevo (`SincoFunctionAnnotation`: claves `sinco_code`, `orden`; campos `exposure_class`, `eloundou_class`, `physical_bottleneck`, `confidence`, `rationale`). Se implementa solo tras aprobación.
- **Anotador alternativo** (para robustez): un segundo modelo, como hacen Dominski y Lee (2025) según 010. Sin API no es posible hoy; "requiere decisión".
- **Calibración sin contaminar la validación** (Eloundou ajustó la rúbrica de GPT-4 para mejorar el acuerdo con humanos usando un conjunto de etiquetas humanas, pp. 2, 8-9): se separa un conjunto de calibración de 60 funciones (propuesta, sin base de potencia) para ajustar el prompt; la muestra de validación de 300 funciones (sección 4.g) no se usa para ajustar nada y se congela antes de ver las etiquetas del LLM.
- **Cuello práctico:** los subagentes consumen la cuota de sesión de Claude Code; la corrida completa puede necesitar dividirse en tandas y en días. Cifra de la cuota **[NO VERIFICADO]**.

### 4.f Costo estimado (cuenta explícita)

Supuestos heredados de 010 (todos **[NO VERIFICADO]**, no medidos): función ≈ 35 tokens; descripción ≈ 170; título ≈ 12; ejemplos ≈ 3.48 × 6 ≈ 21 por grupo; salida por función ≈ 70 tokens en 010. **Cambios míos:** el prompt fijo sube de 600 a 1,000 tokens (dos rúbricas) y la salida por función sube de 70 a 78 (+8 por el campo `eloundou_class`). Observación nueva: la rúbrica A.1 sola tiene del orden de 650 palabras en inglés (conteo aproximado mío del texto extraído), así que 1,000 tokens para las dos rúbricas probablemente se queda corto; medir antes de presupuestar.

**Ruta S, un grupo por llamada (457 llamadas por corrida):**
- Funciones: 3,542 × 35 = 123,970. Contexto: 457 × (12 + 170 + 21) = 457 × 203 = 92,771. Prompt fijo: 457 × 1,000 = 457,000.
- Entrada por corrida: 123,970 + 92,771 + 457,000 = **673,741** tokens. Tres corridas: **2,021,223** (≈ 2.02 M); llamadas: 457 × 3 = 1,371.
- Salida por corrida: 3,542 × 78 = **276,276**. Tres corridas: **828,828** (≈ 0.83 M).

**Ruta S, 10 grupos por llamada (46 llamadas por corrida):**
- Entrada por corrida: 123,970 + 92,771 + 46 × 1,000 = **262,741**. Tres corridas: **788,223** (≈ 0.79 M). Salida igual: 0.83 M. Llamadas: 46 × 3 = 138. Riesgo de anclaje entre grupos del mismo mensaje (se mide, sección 4.g).

**Piloto de S:** 40 grupos × 7.75 ≈ 310 funciones. Entrada por grupo medio: 673,741 / 457 ≈ 1,474; × 40 ≈ 58,970 por corrida; tres corridas ≈ 176,910 (≈ 0.18 M). Salida: 310 × 78 = 24,180 por corrida; tres corridas = 72,540.

**Ruta O (contraste), todas las tareas, lotes de 40, supuesto de 19,265 tareas** (cifra de Eloundou para O*NET 27.2; la de O*NET 31.0 del proyecto es **[NO VERIFICADO]**; si solo se anotaran core, bajaría en proporción desconocida):
- Llamadas por corrida: 19,265 / 40 ≈ 482. Entrada: 19,265 × 55 = 1,059,575; prompt: 482 × 1,000 = 482,000; total **1,541,575** por corrida; tres corridas **4,624,725** (≈ 4.62 M).
- Salida: 19,265 × 78 = 1,502,670 por corrida; tres corridas **4,508,010** (≈ 4.51 M). Llamadas: 482 × 3 = 1,446.

**Totales S + O (tres corridas):** entrada 2,021,223 + 4,624,725 = **6,645,948** (≈ 6.65 M); salida 828,828 + 4,508,010 = **5,336,838** (≈ 5.34 M); llamadas 1,371 + 1,446 = 2,817.
**Solo S:** ≈ 2.02 M de entrada y 0.83 M de salida (o 0.79 M de entrada con lotes de 10 grupos).
**Capa 2 (uso observado):** sin costo de anotación; U1 y U2 cuestan descarga y uniones; U3 requiere embeddings (010 §4-B).
**Dólares:** no los calculo. Sin API no hay precio por token aplicable y no consulté tarifas; con subagentes el límite es la cuota de sesión. **Revisión humana:** 300 funciones con doble revisión = 600 juicios, más 49 grupos × 2 = 98; horas por juicio: sin dato.

Estos números deben recalcularse con una medición de tokens sobre los datos reales antes de pedir presupuesto (los cinco supuestos no están medidos).

### 4.g Validación

1. **Acuerdo entre corridas** (por campo, por separado para `exposure_class` y `eloundou_class`): kappa de Cohen ponderado cuadrático por pares de corridas; alfa de Krippendorff ordinal entre las tres; acuerdo exacto descriptivo. Por grupo: CCI de `E_g` y rango min-max. Con tres corridas la varianza entre corridas se estima mal y así se reporta. Referencias que no son expectativa para SINCO: piloto O*NET (acuerdo exacto 0.90-0.95 con 40 tareas) y Eloundou (acuerdo humano-GPT-4 de 65.6 % a 82.1 % según la medida, Tabla 2, p. 8).
2. **Muestra humana** (el único contraste independiente del LLM): 300 funciones estratificadas por división y por clase del LLM, doble revisión ciega con la rúbrica, adjudicación por un tercero; se reporta kappa ponderado humano-LLM por campo con IC bootstrap. Más 49 grupos (~10 %) con calificación holística en tres niveles. Quién revisa y con qué guía: **requiere decisión** (mismo vacío que 003 §5.4). Eloundou señala que sus anotadores no eran ocupacionalmente diversos y que las etiquetas de calidad exigen personas con conocimiento de las ocupaciones (§3.4.1, p. 9): criterio para elegir revisores. Tamaño de muestra sin potencia formal.
3. **Réplica de la rúbrica sobre tareas O*NET:** el texto del artículo no menciona publicación de etiquetas, y el repositorio de GitHub declara códigos de **ocupación** (`occ_level.csv`), no de tarea ([NO VERIFICADO] si existen etiquetas por tarea). Por tanto la réplica tarea a tarea sobre las 40 tareas del piloto **no está garantizada**. Alternativa factible: comparar a nivel ocupación el agregado de nuestras tareas anotadas con `occ_level.csv`, con las salvedades de versión de O*NET (27.2 frente a 31.0) y de cobertura (40 tareas del piloto). Las diferencias sistemáticas por cambio de modelo y fecha no son necesariamente error (Anthropic advierte que beta puede estar desactualizado, p. 14).
4. **Comparaciones externas a nivel de grupo SINCO** (convergentes, nunca criterio de aprobación):
   - Puntajes de Eloundou por ocupación O*NET (si `occ_level.csv` se confirma y su licencia lo permite) -> SINCO por crosswalk top-2: hereda el ruido del crosswalk (Spearman, número efectivo de O*NET distintas por N:1).
   - `observed_exposure` de Anthropic por ocupación (`job_exposure.csv`, CC-BY según la ficha) -> SINCO por crosswalk top-2: es **uso externo**, no capacidad; se compara con la ruta O, no con la medida principal, y con las mismas salvedades que U1. (Con la capa de uso descartada, esta comparación queda sin efecto salvo nueva decisión.)
   - Puntajes OIT por CIUO-08 (Gmyrek, Berg, Bescond 2023): exige el puente SINCO -> CIUO-08, aprobado solo en principio en 003 y no implementado; **hasta entonces no hay validación OIT**. Cifras y método de WP 96: **[NO VERIFICADO]**.
   - Frey-Osborne (trasladado a SINCO por 005): convergencia imperfecta. Eloundou reporta correlación negativa, condicional, entre su exposición y la medida de automatización de Frey y Osborne (p. 20), de modo que un signo negativo o nulo no sería anomalía. Para la ruta O la comparación es circular (mismo crosswalk); para la ruta S no lo es respecto del crosswalk, aunque el lado de Frey-Osborne sí trae el ruido del emparejamiento. Sin signo esperado fijado y sin lenguaje de "validación" en el artículo.
5. **Sensibilidad:** mapas inferior y superior de 001; contexto (solo función, con descripción, con ejemplos, con Excluye); una función por llamada frente a lote de grupo (anclaje); idioma del prompt; exclusión de 2281 y de `pocas_funciones`; orden con tres semillas; pesos 2:1 en la ruta O; preámbulo literal frente a preámbulo actualizado (si el humano lo autoriza).
6. **Control negativo:** `physical_bottleneck = true` debe asociarse con menor `E_g` y con menor `alfa_S`; grupos de contraste elegidos por el humano antes de ver resultados. Referencia: Eloundou lista 34 ocupaciones sin ninguna tarea expuesta, casi todas manuales (Tabla 11, p. 31); sirve de ejemplo de contraste, no como lista a fijar.
7. **Intervalos:** (i) entre corridas; (ii) remuestreo de funciones dentro del grupo, que es un **intervalo de sensibilidad**, no de muestreo, porque las funciones son la lista completa (010 §6.6); (iii) crosswalk (solo ruta O): rango de las O*NET emparejadas; (iv) entre rutas. El diseño estadístico formal sigue pendiente (hueco de 001 §10.10); una propuesta bayesiana de error de medición está en la decisión 012 (pendiente de revisión humana).
8. **Reproducibilidad de la agregación de Anthropic (solo si U1 se aprueba):** comparar el promedio de `penetration` por ocupación con `observed_exposure` (4.c.3, prueba iii). (Sin efecto mientras la capa de uso esté descartada.)
9. **Asociaciones con salario, escolaridad o informalidad:** descriptivas (001 §8). No hay análogo verificado de la regresión con proyecciones de empleo.

### 4.h Sesgos y límites para México

- **Informalidad:** el catálogo describe ocupaciones, no su grado de formalidad; la exposición es técnica y no mide adopción ni brecha digital. Eloundou declara que sus datos de empleo cubren sobre todo economía formal (p. 6) y que su foco en EE. UU. limita la generalización, incluso por "linguistic diversity" (p. 23). La literatura regional que reporta mayor exposición en empleos formales y urbanos solo la leí en resumen (001 §3.5).
- **Contenido de O*NET frente a SINCO:** la ruta O hereda el contenido de EE. UU.; la ruta S usa el texto mexicano, pero el modelo anotador conoce el trabajo sobre todo desde texto en inglés y contextos más digitalizados.
- **Traducción:** la ruta O anota hoy el inglés original (no hay traducción); la ruta S anota español nativo; la rúbrica de Eloundou es inglesa. Calibración por idioma **[NO VERIFICADO]**; se prueba con la ablación de idioma del prompt.
- **Funciones más genéricas:** 7.75 funciones por grupo SINCO frente a ~18.96 tareas por ocupación en O*NET 27.2 (19,265 / 1,016, Eloundou p. 6). Promedios más gruesos y riesgo de que enunciados gerenciales se califiquen intermedios; el umbral de 50 % de tiempo es difícil de aplicar a una función abstracta; Eloundou reconoce validez dudosa del marco por tareas cuando las tareas son sub-tareas o precursoras de otras (p. 9). Mitigación: control negativo y distribución de `E_g`.
- **Heterogeneidad intra-grupo:** la lista de funciones es común a todas las ocupaciones del grupo; la medida es del contenido descrito del grupo, no de cada puesto.
- **Sin ponderación por tiempo ni importancia en S**, a diferencia de Anthropic.
- **Tiempo de capacidades:** la medida está fechada; la beta de Eloundou refleja capacidades de principios de 2023 y Anthropic lo señala (p. 14).
- **El anotador LLM no es verdad de referencia:** el acuerdo entre corridas es coherencia, no validez; la muestra humana es lo único independiente.
- **Las cifras de Anthropic son de EE. UU. y de uso de Claude;** no se extrapolan a México (nota 3, p. 15, es la única mención de otros países y es una intención futura).

## 5. ENMIENDA a 001 que requiere esta propuesta (E-1, E-2, E-3 y E-8 APROBADAS y APLICADAS; E-4 a E-7 PENDIENTES)

001 está aprobada. R3 y la ruta S añaden elementos. Texto exacto a insertar si el humano aprueba (no se modifican `rubric.md` ni `glossary.md` hasta entonces; la edición sería una decisión posterior, regla 2). Esta revisión corrigió los errores encontrados en la versión previa de E-1 a E-8; los cambios se señalan en cada punto. **Estado tras el Registro 4:** E-1, E-2, E-3 y E-8 aprobadas por el usuario y aplicadas a 001 (2026-10-19); E-4, E-5, E-6 y E-7 pendientes.

### Registro de aprobación (2026-10-19) [histórico; superado por el Registro 4]

**Hecho reportado, no verificado por mí.** El orquestador me transmitió una instrucción que atribuye al usuario, con esta cita textual: **"Aprobar E1 y E2"**. Yo no recibí ese mensaje del usuario; llegó por el orquestador, y un mensaje de un agente no equivale a la aprobación del usuario. Lo registro como **aprobación reportada por el orquestador, a confirmar por el humano**.

**Ambigüedad.** "E1 y E2" puede referirse a (a) las enmiendas **E-1 y E-2** de esta sección (interpretación del orquestador, que adopto aquí) o (b) las categorías E1/E2 de la rúbrica. Se registra la lectura (a); el humano debe confirmarla. La descripción del orquestador menciona "alfa/beta/zeta"; el nombre de la tercera medida no está verificado (sección 0), y la enmienda lo evita. *(El Registro 4 resuelve esta ambigüedad: el mensaje posterior escribe "E-1, E-2, E-3 y E-8".)*

| Enmienda | Estado (actualizado por el Registro 4) |
|---|---|
| E-1 (ruta S como unidad alternativa) | **APROBADA por el usuario** (Registro 4); **aplicada a 001 §4.2** |
| E-2 (campo `eloundou_class`, rúbrica literal) | **APROBADA por el usuario**, incluida la redacción literal verificada contra el apéndice A.1 de Eloundou v5 (Registro 4); **aplicada a 001 §4.3, punto 5** |
| E-3 (párrafo final de 001 §4.3) | **APROBADA por el usuario**, con las medidas nombradas por su definición (Registro 4); **aplicada a 001 §4.3** |
| E-4 (001 §4.4, agregación) | **PENDIENTE de aprobación** |
| E-5 (001 §7, esquema) | **PENDIENTE de aprobación** |
| E-6 (`docs/rubric.md`) | **PENDIENTE de aprobación**; archivo protegido (regla 2) |
| E-7 (`docs/glossary.md`) | **PENDIENTE de aprobación**; archivo protegido (regla 2) |
| E-8 (001 §3.3, erratum) | **APROBADA por el usuario**, con el símbolo griego de la tercera medida **[NO VERIFICADO]** (Registro 4); **aplicada a 001 §3.3** |

### Registro 3 (2026-10-19): capa de uso observado descartada

**Cita textual del usuario (2026-10-19), tal como me la transmitió el orquestador:** "1. Descartar exposicion empirica porque no tenemos acceso a datos de Mexico." (El mismo mensaje del usuario contiene además la propuesta de calibración bayesiana con la ENOE, que se trata en la decisión 012, pendiente de revisión humana.)

**Qué se registra.**
- La **capa 2 de uso observado queda DESCARTADA por el usuario** por falta de datos de México. Equivale a **U0** (4.c.3): el artículo habla solo de exposición teórica (`E_g`, `alfa_S`, `beta_S`, `cota_sup_S`). U1-U4 no se persiguen; se conservan en 4.c.3 como registro de lo analizado, y solo se reactivarían con una decisión nueva.
- Interpretación (sin ampliar): "exposición empírica" se lee como "exposición observada / uso observado" (la capa 2). Si el usuario se refería a otra cosa, debe indicarlo.
- Consecuencias menores: las comparaciones y pruebas que dependen de la capa de uso (4.g punto 4, segunda viñeta, y punto 8) quedan sin efecto mientras no se reactive; el costo de 4.f no cambia (la capa 2 no tenía costo de anotación).

**Qué NO cambia este registro.** *(Nota: lo que sigue describe el estado en el momento del Registro 3; el Registro 4 lo supera en lo referente a E-1, E-2, E-3 y E-8.)*
- **Las enmiendas E-1 y E-2 siguen SIN confirmación explícita del usuario** respecto de (i) la interpretación de "Aprobar E1 y E2" como las enmiendas E-1 y E-2 y no como las categorías E1/E2 de la rúbrica, y (ii) la redacción literal de E-2. El mensaje del usuario de esta fecha no las menciona. Su estado sigue siendo "aprobación reportada por el orquestador, pendiente de confirmación humana; no aplicadas".
- **E-3 a E-8 siguen PENDIENTES.** El usuario no las resolvió en este mensaje.
- No se modificó 001, `docs/rubric.md` ni `docs/glossary.md`.

**Aplicación efectiva a 001, `rubric.md` y `glossary.md`: NO realizada en el Registro 3.** *(Ejecutada en parte por el Registro 4: los puntos 1 y 2 y las enmiendas E-3 y E-8.)* Si el usuario confirma E-1 y la redacción de E-2, los cambios exactos serían:
1. **001 §4.2 (Unidad de análisis):** añadir al final el texto íntegro de E-1 (ruta S, ruta O, etiqueta de ruta).
2. **001 §4.3 (Escala):** añadir como punto 5 el texto íntegro de E-2 (campo `eloundou_class`, clases EL0-EL3, rúbrica de Eloundou et al. 2023 A.1 con traducción, notas de aplicación y los tres mapas).
3. No se tocan, hasta nueva aprobación: el párrafo final de 001 §4.3 (E-3), §4.4 (E-4), §7 (E-5), `rubric.md` (E-6), `glossary.md` (E-7) y 001 §3.3 (E-8). Consecuencia: tras aplicar solo 1 y 2, `rubric.md` seguiría diciendo "Se anota cada tarea de O*NET", lo que contradice la ruta S de 001 §4.2; el humano debe decidir si aprueba E-6 en el mismo acto.
4. Aplicar el cambio a 001 es una decisión posterior registrada (regla 2); este documento no la ejecuta.

### Registro 4 (2026-10-19): aprobación de E-1, E-2, E-3 y E-8

**Cita textual del usuario, tal como me la transmitió el orquestador (mensaje del usuario, 2026-10-19):** "Avanza con el B1 por el momento. Reporte descriptivo por strato. Para enoe puedes usar el paquete que estoy creando para realizar descargas temporales en R. https://github.com/DiegoSReco/enoeR. Aprobar E-1,E-2, E-3 y E-8".

**Procedencia.** Igual que antes, yo no recibí el mensaje directamente del usuario; el orquestador lo cita como textual. A diferencia de "Aprobar E1 y E2", esta cita nombra las enmiendas con guion (E-1, E-2, E-3, E-8), que sí corresponden a las enmiendas de esta sección. El humano puede cotejarla en el registro de la conversación; si no coincide, las ediciones de 001 deben revertirse.

**Qué se registra.**
- El usuario **APRUEBA E-1, E-2, E-3 y E-8**. Esto confirma la interpretación de que "E-1/E-2" son las enmiendas de esta sección 5 (y no las categorías E1/E2 de la rúbrica), resolviendo la ambigüedad del Registro de aprobación.
- La aprobación de **E-2 incluye la redacción literal** que quedó en esta sección tras la verificación contra Eloundou v5 (apéndice A.1).
- La aprobación de **E-3 y E-8 incluye** que las medidas se nombran **por su definición**: `alfa_S` (EL1), `beta_S` (EL1 + 0.5·EL2) y `cota_sup_S` (EL1 + EL2), con el símbolo griego de la tercera medida **[NO VERIFICADO]** (el README de Eloundou dice "gamma"; los glifos no se leen en el texto extraído).
- **Aplicadas a `docs/decisions/001-definicion-exposicion.md`** (E-1 en §4.2; E-2 como punto 5 de §4.3 con la rúbrica literal y su traducción; E-3 en la oración final del párrafo del mapa numérico de §4.3; E-8 en §3.3) y registradas en la sección "Enmiendas aplicadas" de 001. No se tocaron `docs/rubric.md` ni `docs/glossary.md`.
- En E-3 la ambigüedad de ubicación ("párrafo final de §4.3") se resolvió aplicando el texto donde estaba la oración que reemplaza ("La relación con el estilo alfa/beta/gamma ... es conceptual; no se afirma equivalencia"), ya verificada en 001; el párrafo realmente final de §4.3 (puntajes continuos libres) no cambió.

**PENDIENTES (el usuario no las resolvió):**

| Enmienda | Qué modifica | Por qué sigue pendiente |
|---|---|---|
| E-4 | 001 §4.4 (agregación de la ruta S; variante 2:1 de la ruta O) | El usuario no la mencionó |
| E-5 | 001 §7 (esquema: `eloundou_class`, `sinco_code`, `orden`, `route`) | No mencionada; sin ella no hay decisión que autorice implementar el esquema (regla 7) |
| E-6 | `docs/rubric.md` | Archivo protegido (regla 2); no mencionada |
| E-7 | `docs/glossary.md` | Archivo protegido (regla 2); no mencionada |

**Consecuencia para el proyecto.** Tras aplicar E-1 y E-2 a 001, `docs/rubric.md` seguirá diciendo "Se anota cada tarea de O*NET" (sin la ruta S) y **no tendrá la sección `eloundou_class`** hasta que se apruebe E-6. Entonces la rúbrica operativa y 001 difieren: 001 §4.2-§4.3 ya contienen la ruta S y la rúbrica de Eloundou; `rubric.md` no. Del mismo modo `glossary.md` no define `eloundou_class`, `alfa_S`, `beta_S` ni `cota_sup_S` (E-7), el esquema de 001 §7 no los lista (E-5) y la agregación de la ruta S no está en 001 §4.4 (E-4). Recomendación al humano (no una aprobación): resolver E-4 a E-7 antes del piloto de la ruta S, o decidir expresamente que el piloto se hace con 001 como única fuente normativa.

- **E-1. En 001 §4.2 (Unidad de análisis), añadir:** "Ruta alternativa S: función SINCO (tabla `sinco_funciones`) -> grupo unitario SINCO 2019, sin crosswalk. La ruta tarea O*NET -> O*NET-SOC -> SINCO se conserva como ruta O. Ambas se reportan con su etiqueta de ruta." (Sin cambios respecto de la versión previa. **Estado: APROBADA y APLICADA a 001 §4.2 (Registro 4).**)

- **E-2. En 001 §4.3 (Escala), añadir el punto 5, `eloundou_class` (ordinal EL0/EL1/EL2/EL3).** Texto de la rúbrica: Eloundou, Manning, Mishkin y Rock (2023), arXiv:2303.10130v5, apéndice A.1, pp. 24-26 (paginación según la sección 0), transcrito literalmente. La traducción es mía y busca fidelidad; **si hay diferencia, prevalece el texto en inglés**, y un prompt en español sería una `prompt_version` distinta. *Cambio respecto de la versión previa: antes se parafraseaba desde una fuente secundaria; ahora es el texto del apéndice.* **Estado: APROBADA (incluida esta redacción literal) y APLICADA a 001 §4.3, punto 5 (Registro 4).**

  **Contexto para el anotador (A.1, p. 24).**
  - Original: "Consider the most powerful OpenAI large language model (LLM) This model can complete many tasks that can be formulated as having text input and text output where the context for the input can be captured in 2000 words. The model also cannot draw up-to-date facts (those from <1 year ago) unless they are captured in the input." (La falta de punto tras "(LLM)" viene del texto extraído.)
  - Traducción: "Considera el modelo de lenguaje grande (LLM) más potente de OpenAI. Este modelo puede completar muchas tareas que pueden formularse con entrada de texto y salida de texto, donde el contexto de la entrada cabe en 2000 palabras. El modelo tampoco puede obtener hechos actualizados (los de hace menos de 1 año) a menos que estén incluidos en la entrada."
  - Original: "Assume you are a worker with an average level of expertise in your role trying to complete the given task. You have access to the LLM as well as any other existing software or computer hardware tools mentioned in the task. You also have access to any commonly available technical tools accessible via a laptop (e.g. a microphone, speakers, etc.). You do not have access to any other physical tools or materials."
  - Traducción: "Supón que eres un trabajador con un nivel promedio de experiencia en tu puesto que intenta completar la tarea dada. Tienes acceso al LLM y a cualquier otro software o herramienta de hardware existente que se mencione en la tarea. También tienes acceso a cualquier herramienta técnica de uso común accesible desde una laptop (p. ej., un micrófono, bocinas, etc.). No tienes acceso a ninguna otra herramienta física ni material."
  - Original: "Please label the given task according to the taxonomy below." Traducción: "Etiqueta la tarea dada según la taxonomía de abajo."

  **EL0, sin exposición (A.1, pp. 24-25).**
  - Original: "Label tasks E0 if direct access to the LLM through an interface like ChatGPT or the OpenAI playground cannot reduce the time it takes to complete this task with equivalent quality by half or more. If a task requires a high degree of human interaction (for example, in person demonstrations) then it should be classified as E0."
  - Traducción: "Etiqueta como E0 las tareas en las que el acceso directo al LLM mediante una interfaz como ChatGPT o el playground de OpenAI no puede reducir a la mitad o más el tiempo que toma completar la tarea con calidad equivalente. Si una tarea requiere un alto grado de interacción humana (por ejemplo, demostraciones presenciales), debe clasificarse como E0."

  **EL1, exposición directa (A.1, p. 25).**
  - Original: "Label tasks E1 if direct access to the LLM through an interface like ChatGPT or the OpenAI playground alone can reduce the time it takes to complete the task with equivalent quality by at least half. This includes tasks that can be reduced to: - Writing and transforming text and code according to complex instructions, - Providing edits to existing text or code following specifications, - Writing code that can help perform a task that used to be done by hand, - Translating text between languages, - Summarizing medium-length documents, - Providing feedback on documents, - Answering questions about a document, or - Generating questions a user might want to ask about a document."
  - Traducción: "Etiqueta como E1 las tareas en las que el acceso directo al LLM, mediante una interfaz como ChatGPT o el playground de OpenAI, por sí solo puede reducir al menos a la mitad el tiempo que toma completar la tarea con calidad equivalente. Esto incluye tareas que pueden reducirse a: escribir y transformar texto y código según instrucciones complejas; hacer ediciones a texto o código existente siguiendo especificaciones; escribir código que ayude a realizar una tarea que antes se hacía a mano; traducir texto entre idiomas; resumir documentos de extensión media; dar retroalimentación sobre documentos; responder preguntas sobre un documento; o generar preguntas que un usuario podría querer hacer sobre un documento."

  **EL2, exposición mediante aplicaciones basadas en LLM (A.1, p. 25).**
  - Original: "Label tasks E2 if having access to the LLM alone may not reduce the time it takes to complete the task by at least half, but it is easy to imagine additional software that could be developed on top of the LLM that would reduce the time it takes to complete the task by half. This software may include capabilities such as: - Summarizing documents longer than 2000 words and answering questions about those documents - Retrieving up-to-date facts from the Internet and using those facts in combination with the LLM capabilities - Searching over an organization's existing knowledge, data, or documents and retreiving information" [sic: "retreiving" en el original].
  - Traducción: "Etiqueta como E2 las tareas en las que tener acceso al LLM por sí solo puede no reducir a la mitad, como mínimo, el tiempo que toma completar la tarea, pero es fácil imaginar software adicional, desarrollado sobre el LLM, que sí reduciría a la mitad el tiempo que toma completarla. Ese software puede incluir capacidades como: resumir documentos de más de 2000 palabras y responder preguntas sobre ellos; recuperar hechos actualizados de Internet y usarlos en combinación con las capacidades del LLM; buscar en el conocimiento, los datos o los documentos existentes de una organización y recuperar información."
  - La rúbrica añade cinco "ejemplos de software construido sobre el LLM" (A.1, p. 25: software para una empresa de artículos para el hogar, sugerencias en vivo para agentes de servicio al cliente, resúmenes de jurisprudencia para despachos legales, calificación de ensayos para docentes, resúmenes de noticias con hechos actualizados). El prompt v2 los copia completos del PDF.

  **EL3, exposición dadas capacidades de imagen (A.1, p. 25).**
  - Original: "Suppose you had access to both the LLM and a system that could view, caption, and create images. This system cannot take video media as inputs. This system cannot accurately retrieve very detailed information from image inputs, such as measurements of dimensions within an image. Label tasks as E3 if there is a significant reduction in the time it takes to complete the task given access to a LLM and these image capabilities: - Reading text from PDFs, - Scanning images, or - Creating or editing digital images according to instructions."
  - Traducción: "Supón que tuvieras acceso tanto al LLM como a un sistema que puede ver, subtitular y crear imágenes. Este sistema no puede recibir video como entrada. Este sistema no puede recuperar con exactitud información muy detallada de imágenes de entrada, como las medidas de dimensiones dentro de una imagen. Etiqueta las tareas como E3 si hay una reducción significativa del tiempo que toma completar la tarea dado el acceso a un LLM y a estas capacidades de imagen: leer texto de PDF; escanear imágenes; o crear o editar imágenes digitales según instrucciones."

  **Ejemplos de anotación (A.1, pp. 25-26).** Cinco ejemplos que el prompt v2 copia completos: Inspectors, Testers, Sorters, Samplers, and Weighers (E0; requiere manos u otra corporalidad); Computer and Information Research Scientists (E1); "Schedule dining reservations" (E2; ya existe tecnología de automatización y no está claro qué añade el LLM); "Negotiate purchases or contracts" (E2; exige que mucha gente adopte nuevas herramientas); Allergists and Immunologists, recetar medicamentos (E2; "it still requires a human in the loop using their judgment and knowledge to make the final decision").

  **Definiciones del cuerpo que acompañan la rúbrica (§3.3, pp. 6-7).** "Calidad equivalente": un tercero, típicamente el receptor del producto, no notaría ni le importaría la ayuda del LLM (nota a, p. 7). Umbral: 50 % de reducción de tiempo, elegido por facilidad de interpretación para los anotadores (pp. 7-8). Fusión de EL3 con EL2: "we combine E2 and E3 for all analyses" (nota b, p. 7).

  **Mapas** (definiciones en §3.3, p. 8): `alfa_S` = EL1; `beta_S` = EL1 + 0.5·EL2; `cota_sup_S` = EL1 + EL2, con EL3 contado dentro de EL2. La tercera medida corresponde a la que Eloundou llama "upper bound"; el nombre de su símbolo es [NO VERIFICADO]. `eloundou_class` no equivale a `exposure_class`; no se convierte una escala en otra por regla.

  **Notas de aplicación** (propuestas): (1) el preámbulo describe un LLM de 2023; la versión literal permite comparar con Eloundou y es la propuesta, y cualquier actualización del preámbulo es otra `prompt_version`; (2) la rúbrica se diseñó para tareas y DWA de O*NET; aplicarla a una función SINCO es un cambio de unidad cuyo efecto no está verificado; (3) se guarda la etiqueta cruda EL0-EL3 y las medidas funden EL3 en EL2.

- **E-3. En 001 §4.3, párrafo final.** (**APROBADA y APLICADA, Registro 4**; dependía de E-2.) *Corregido:* la versión previa decía sustituir "alfa/beta/gamma" por "alfa/beta/zeta". **Eso no es verificable** y el README del repositorio de Eloundou usa "gamma"; no se propone ningún cambio de nombre. Texto propuesto y aprobado: "La medida de comparación con Eloundou et al. se calcula con el campo `eloundou_class` (E-2), mediante tres agregaciones definidas: solo EL1; EL1 + 0.5·EL2; EL1 + EL2. `exposure_class` no se interpreta como ninguna de ellas." La oración "La relación con el estilo alfa/beta/gamma de Eloundou et al. es conceptual; no se afirma equivalencia." de 001 se reemplazó por la frase final de arriba (texto exacto de 001 ya verificado al aplicar la enmienda).

- **E-4. En 001 §4.4 (Agregación), añadir** (**PENDIENTE**): "Ruta S: media de pesos iguales sobre todas las funciones del grupo (SINCO no distingue core/supplemental). Ruta O, variante: core con peso 2 y supplemental con peso 1, normalizados a suma 1 por ocupación (Eloundou et al. 2023, p. 8, notas 6-7); Eloundou usa pesos iguales en varias de sus figuras y tablas, de modo que la variante debe declararse en cada resultado." *Añadido:* normalización y la advertencia.

- **E-5. En 001 §7 (esquema)** (**PENDIENTE**), añadir los campos `eloundou_class` (EL0/EL1/EL2/EL3), `sinco_code`, `orden`, `route` (S/O), y la regla "un registro por (`run_id`, `sinco_code`, `orden`) en la ruta S". *Cambio:* `eloundou_class` admite EL3 (etiqueta cruda).

- **E-6. `docs/rubric.md`** (**PENDIENTE**; archivo protegido, regla 2): sustituir la frase inicial "Se anota cada tarea de O*NET" por "Se anota cada tarea de O*NET (ruta O) o cada función SINCO (ruta S)"; añadir sección `eloundou_class` con el texto de E-2. (Sin cambios de fondo.)

- **E-7. `docs/glossary.md`** (**PENDIENTE**; archivo protegido, regla 2): añadir `eloundou_class`, `alfa_S`, `beta_S`, `cota_sup_S`, "ruta S", "ruta O", "exposición teórica", "cobertura de uso externa" y "mezcla de tareas de usuarios de Claude.ai en México". *Cambio:* `cota_sup_S` en lugar de `zeta_S`; términos de la capa de uso añadidos. (Con la capa de uso descartada por el usuario, los dos últimos términos ya no serían necesarios; queda a decisión del humano al resolver E-7.)

- **E-8. 001 §3.3 (erratum editorial)** (**APROBADA y APLICADA, Registro 4**; dependía de E-2). *Corregido:* la versión previa proponía cambiar "gamma" por "zeta". **No hay base verificable para ese cambio** (los símbolos no se leen en el texto extraído; el README del repositorio dice "gamma"). Propuesta aprobada: no cambiar la letra hasta que un humano mire el glifo en el PDF; en su lugar, añadir la definición explícita de las tres medidas (E1; E1 + 0.5·E2; E1 + E2) y quitar la marca [NO VERIFICADO] de la definición de la rúbrica de Eloundou, ahora verificada contra el apéndice A.1. El símbolo de la tercera medida sigue [NO VERIFICADO].

Si el humano no aprueba la enmienda, la alternativa es R2: solo `exposure_class` y la ruta S como contraste de la ruta O, sin las medidas `*_S`. *(Para E-1, E-2, E-3 y E-8 esta alternativa ya no aplica; sigue vigente solo para el resto de la propuesta.)*

## 6. Cómo encaja con 010 y qué cambia

- **Es una variante del Método A de 010**, no un cuarto método independiente: misma unidad (función SINCO), mismo contexto, mismo tratamiento de residuales y erratas, misma agregación igual.
- **Qué cambia respecto de A:** (1) segundo campo `eloundou_class` y las medidas `alfa_S`, `beta_S`, `cota_sup_S` (comparabilidad con la literatura); (2) capa opcional de uso observado externo, separada de la exposición, con niveles U0-U4 (4.c.3) [descartada por el usuario, Registro 3]; (3) variante de ponderación 2:1 y por tiempo en la ruta O; (4) calibración separada de la validación; (5) comparación con etiquetas publicadas de Eloundou a nivel ocupación (la réplica tarea a tarea no está garantizada); (6) nomenclatura estricta teórica frente a uso.
- **Lo que no cambia:** C de 010 sigue siendo el contraste con el crosswalk; B (embeddings) sigue opcional y al final, y es el modo natural de ligar uso por tarea a funciones SINCO sin pasar por el top-2 (U3), tal como Anthropic reparte cuentas entre tareas semánticamente parecidas (nota 5, p. 15). Eso exigiría la dependencia nueva de embeddings, no aprobada.

## 7. Recomendación (pendiente de revisión humana)

1. ~~Confirmar la aprobación reportada de E-1 y E-2...~~ **E-1, E-2, E-3 y E-8: aprobadas y aplicadas (Registro 4).** Falta decidir E-4 a E-7 (con las correcciones de esta revisión), o elegir R2 para esas partes. Mi preferencia es R3: añade un solo campo por unidad y permite medir con datos la relación entre las dos rúbricas en vez de suponerla.
2. La rúbrica literal de Eloundou y las cifras de acuerdo ya están verificadas (E-2 y 2.2). Pendiente de una persona: mirar en el PDF el glifo de la tercera medida; confirmar si existen etiquetas por tarea de Eloundou; cotejar las páginas citadas.
3. Piloto de la ruta S: 40 grupos estratificados, 3 corridas, ≈ 0.18 M tokens de entrada y 0.07 M de salida (con el prompt fijo posiblemente subestimado, 4.f), más la tabla cruzada de las dos rúbricas y 60 funciones de calibración.
4. Capa de uso: **descartada por el usuario (Registro 3); se queda en U0.** El artículo solo habla de exposición teórica. (Antes: quedarse en U0 hasta aprobar pruebas de factibilidad de U1 y U2.)
5. Decidir antes de la corrida completa: fecha de corte, modelo/vía, presupuesto o cuota, fuente de empleo para niveles superiores, revisores humanos.

## 8. Plan por fases (entregables y decisiones humanas)

| Fase | Entregable | Decisión humana necesaria |
|---|---|---|
| 0. Verificación | Hecha para la rúbrica de Eloundou y para el informe de Anthropic sin apéndice. Pendiente: glifo de la tercera medida, apéndice de Anthropic, existencia de México en los datos geográficos, etiquetas por tarea de Eloundou | Quién la hace (acceso al PDF y a los datos) |
| 1. Enmienda | E-1, E-2, E-3 y E-8 aprobadas y aplicadas a 001 (Registro 4). Pendiente: E-4 a E-7 y edición de 001 §4.4 y §7, `rubric.md`, `glossary.md` (decisión posterior) | Aprobar E-4 a E-7 u optar por R2 para esas partes |
| 2. Piloto S | `ann-v2-sinco-el` con hash; 40 grupos; 3 corridas; esquema nuevo; kappa por campo; tabla cruzada | Aprobar el esquema (E-5); fecha de corte = fecha de corrida (ya vale para el piloto) |
| 3. Calibración y muestra humana | 60 funciones de calibración; 300 funciones y 49 grupos revisados | Revisores, guía, horas |
| 4. Corrida completa S | 457 grupos, 3 corridas; `E_g`, `alfa_S`, `beta_S`, `cota_sup_S`, intervalos; residuales NA | Modelo/vía, fecha de corte, presupuesto o cuota |
| 5. Contraste O | Anotación completa de O*NET con el mismo prompt; `E_o`; discrepancia S-O | Alcance (core o todas); estado del crosswalk |
| 6. Validación | Comparación con Eloundou a nivel ocupación, OIT (si hay puente) y Frey-Osborne; control negativo | Puente SINCO -> CIUO-08 (003 B) si se quiere OIT |
| 7. Uso observado (opcional) | **DESCARTADA por el usuario (Registro 3).** Antes: pruebas de factibilidad de U1 y U2 | Solo si se reabre con decisión nueva |
| 8. Niveles superiores | Agregados ponderados por empleo | Fuente de empleo (ENOE u otra); el plan del reporte descriptivo por estratos con ENOE está en el borrador 013 (pendiente) y la discusión en la decisión 012 |

## 9. Riesgos

1. **Aplicar una rúbrica diseñada para tareas O*NET y un LLM de 2023 a funciones SINCO y a un modelo de 2026:** puede dar etiquetas que no son comparables con las de Eloundou. Mitigación: tabla cruzada, sensibilidad del preámbulo, muestra humana.
2. **Contaminación entre campos** en la misma respuesta. Mitigación: ablación (un campo por llamada en 300 funciones) y la tabla cruzada.
3. **Umbral del 50 % en funciones genéricas:** puede producir EL1/EL2 por defecto. Mitigación: control negativo y distribución de `E_g`.
4. **Confundir coherencia con validez:** todas las corridas comparten anotador y rúbrica.
5. **Interpretación pública:** leer exposición teórica o cobertura de uso como pérdida de empleo; Anthropic misma llama "displacement risk" a su medida (p. 2).
6. **Costos sin medir:** los supuestos de tokens no están medidos y la cuota de sesión de los subagentes puede ser el límite real.
7. **Generalización del uso observado:** el uso de Claude de la capa 2 no representa a trabajadores mexicanos; U2 describe usuarios autoseleccionados de Claude.ai. (Riesgo cerrado mientras la capa esté descartada.)
8. **Medida de Anthropic no auditable con los archivos públicos:** sin beta, tiempos ni conteos (por columnas), `job_exposure.csv` solo se puede usar como dato.
9. **Nombre de la tercera medida de Eloundou sin verificar** (gamma o zeta): se nombra por definición.
10. **Reproducibilidad del modelo:** subagentes sin control de temperatura ni semilla.
11. **Datos de segunda mano de esta revisión:** README de GitHub, ficha de Hugging Face y página de geografía vienen de resúmenes de herramienta, no de copias literales.
12. **Aprobación relayada:** la aprobación de E-1 y E-2 llegó primero por el orquestador, con una cita ambigua. El Registro 4 la reemplaza por una cita que nombra E-1, E-2, E-3 y E-8, también relayada por el orquestador; el riesgo residual es que la cita no coincida con el mensaje real del usuario (el humano puede cotejarla). Riesgo nuevo (Registro 4): con E-6 pendiente, `rubric.md` y 001 difieren hasta que se resuelva.

## 10. Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Reemplazar 001 por la rúbrica de Eloundou | Contradice 001/006 y pierde el eje de rol humano (R1) |
| Importar el beta de Eloundou por ocupación y mapearlo a SINCO | Es la alternativa G de 001: no propio y dependiente de crosswalk; solo comparación |
| Usar uso observado de EE. UU. como medida principal en México | No representa a México; mide uso de Claude, no de trabajadores |
| Construir una "cobertura" sintética a partir de la anotación | Sería inventar un dato de uso |
| Ponderar funciones por orden de aparición | Sin evidencia de que indique importancia |
| Puntajes continuos libres | Descartado en 001 §4.3 |
| Capa de uso observado (U1-U4) | **Descartada por el usuario el 2026-10-19 (Registro 3)** por falta de datos de México |

## 11. Preguntas abiertas

1. ~~¿Se confirma la aprobación de E-1 y E-2 (leídas como enmiendas) con la redacción literal de E-2 de la sección 5?~~ **Resuelta en esa parte (Registro 4):** E-1, E-2, E-3 y E-8 aprobadas. Sigue abierta: ¿se aprueban E-4 a E-7 (corregidas), o se prefiere R2 para esas partes?
2. ¿Quién mira el glifo de la tercera medida en el PDF de Eloundou y cotea las páginas citadas?
3. ¿Existen etiquetas por tarea de Eloundou públicas? (El repositorio indica solo códigos por ocupación.) ¿Se acepta la comparación a nivel ocupación?
4. ¿Fecha de corte, modelo/vía y presupuesto o cuota para la corrida completa? ¿Se permite un segundo modelo?
5. ¿Se mantiene el preámbulo literal de 2023 (comparabilidad) o se quiere también una variante actualizada?
6. ¿Fuente de empleo para niveles superiores y para el análogo de "exposición directa nula"? (Ver decisión 012 para la propuesta de cruce con la ENOE y el borrador 013.)
7. ¿Revisores humanos, guía y horas para 300 funciones y 49 grupos?
8. ~~¿Se autorizan las pruebas de factibilidad U1 y U2? ¿Quién abre el apéndice de Anthropic?~~ **Resuelta en la parte de la capa de uso: descartada por el usuario (Registro 3).** El apéndice de Anthropic sigue sin abrirse y solo importa si se quiere citar su fórmula.
9. ~~¿Se autoriza la dependencia de embeddings para U3?~~ **Sin efecto con la capa de uso descartada.** (Los embeddings siguen como Método B opcional de 010.)
10. ¿Alguien puede abrir las decisiones 005, 008 y 009 (nombres reales de archivo) y confirmar mi lectura indirecta?

## 12. Lista de [NO VERIFICADO]

- Nombre del símbolo de la tercera medida de Eloundou (gamma o zeta): glifo ilegible; el README de GitHub dice gamma.
- Páginas citadas de Eloundou (conteo de saltos de página del texto extraído).
- Existencia de etiquetas por tarea de Eloundou; licencia exacta del repositorio (solo "MIT" en la barra lateral).
- Apéndice de Anthropic: fórmula, umbral de uso suficiente, tareas raras, fuente de tiempos por tarea, definición de `penetration`, qué reportes de uso se usaron (dos o cuatro), si el beta es humano o de GPT-4.
- Versión de O*NET que usó Anthropic para sus tareas.
- Presencia de México (`MX`) en los datos geográficos del Economic Index, número de conversaciones y de tareas con cuentas.
- Cualquier fuente pública de uso de IA por tarea u ocupación en México; ENDUTIH y ENOE como candidatas no consultadas (ver 012 para lo poco consultado de ENDUTIH y ENOE, también en resúmenes).
- Cifras de Anthropic y datos de Hugging Face y GitHub leídos vía resumen de herramienta.
- Metodología y cifras de OIT WP 96, AIOE y Webb (heredado de 001 y 010).
- Número de tareas O*NET 31.0 del proyecto; longitud real de funciones; distribución de funciones por grupo; supuestos de tokens; longitud en tokens de las dos rúbricas.
- Texto de las decisiones 005, 008 y 009.
- Cuota de sesión de los subagentes.
- Equivalente mexicano de las proyecciones de empleo del BLS.
- ~~Que "Aprobar E1 y E2" provenga directamente del usuario y que se refiera a las enmiendas E-1 y E-2.~~ Sustituido (Registro 4): que la cita "Aprobar E-1,E-2, E-3 y E-8" provenga directamente del usuario tal como la transmitió el orquestador (no verificable por mí; cotejable en la conversación). La lectura como enmiendas queda confirmada por la grafía "E-1".
- Que "exposición empírica" en el mensaje del usuario del Registro 3 se refiera a la capa de uso observado (lectura mía).

## 13. Fuentes consultadas (2026-10-19)

- Massenkoff, M. y McCrory, P. (5 de marzo de 2026), "Labor market impacts of AI: A new measure and early evidence", Anthropic. PDF local registrado en `data/raw/manifest.json` como `massenkoff_mccrory_2026_pdf` (sha256 que empieza `48c941db`); texto completo (17 páginas, sin apéndice) leído en la extracción de `pdftotext`. URL: https://www.anthropic.com/research/labor-market-impacts . Enlaces que el informe lista y que **no abrí**: apéndice https://cdn.sanity.io/files/4zrzovbb/website/e5f77fc0e77c0185110b5e4b909602791ae76eae.pdf ; O*NET https://www.onetcenter.org/database.html ; BLS https://data.bls.gov/projections/occupationProj .
- Eloundou, Manning, Mishkin, Rock (2023), arXiv:2303.10130v5. PDF local registrado en `data/raw/manifest.json` como `eloundou_2023_v5_pdf` (sha256 que empieza `af3edd4e`); texto completo leído en la extracción de `pdftotext`. URL: https://arxiv.org/abs/2303.10130 .
- Repositorio de Eloundou et al.: https://github.com/openai/GPTs-are-GPTs (WebFetch, resumen de herramienta).
- Anthropic Economic Index, conjunto de datos: https://huggingface.co/datasets/Anthropic/EconomicIndex ; carpeta https://huggingface.co/datasets/Anthropic/EconomicIndex/tree/main/labor_market_impacts ; archivos `job_exposure.csv` y `task_penetration.csv` (encabezado y primeras filas leídos); documentación https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_01_15/data_documentation.md (WebFetch, resúmenes de herramienta).
- Anthropic, página de geografía del Economic Index: https://www.anthropic.com/research/economic-index-geography (WebFetch, resumen de herramienta).
- Documentos del proyecto: `CLAUDE.md`; `docs/decisions/001-definicion-exposicion.md`, `003-requisitos-tablas-sinco.md`, `010-metodos-exposicion-sinco.md`; `docs/rubric.md`; `docs/glossary.md`; `docs/diccionario_datos_sinco.md`; `docs/sinco_pdf_exploracion.md`; `src/score/README.md`; `src/annotate/README.md`.
- Dominski y Lee (2025), OIT WP 96, AIOE, Webb, Frey-Osborne: solo vía 001 y 010, sin consulta nueva.
