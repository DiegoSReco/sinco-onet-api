# 010 - Tres métodos para medir exposición a IA generativa usando las descripciones de trabajo del propio SINCO 2019

> **ESTADO: PENDIENTE DE REVISIÓN HUMANA.** Es una propuesta. No se implementa nada, no modifica 001, `docs/rubric.md` ni `docs/glossary.md` (regla 2) y no autoriza gasto, modelo ni dependencias. Donde un método se aparta de 001 se dice exactamente en qué (secciones "Compatibilidad con 001").

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de todas las fuentes web: 2026-10-19
- Revisión 2026-10-19 (verificación contra los PDF): la sección 2.1 (Eloundou) y la sección 6.4 se corrigieron contra el texto completo de arXiv:2303.10130v5, extraído del PDF registrado en `data/raw/manifest.json` (`eloundou_2023_v5_pdf`). Ver los cambios en 2.1 y 6.4. Además, nota en la pregunta abierta 1 (sección 9) sobre la aprobación reportada de E-1 (011 §5).

## 0. Alcance, insumos y límites de verificación

**Leído:** `CLAUDE.md`; decisiones 001, 003, 006 (solo cabecera); `docs/rubric.md` y `docs/glossary.md` (versión 1); `docs/diccionario_datos_sinco.md`; `docs/sinco_pdf_exploracion.md`; `docs/diccionario_datos_anotacion.md`; `src/annotate/README.md`, `src/annotate/config.toml`, `src/annotate/prompts/v1.md`; `src/score/README.md`.

**Verificación posterior (misma fecha):** el texto completo de Eloundou et al. (2023) v5, incluidos los apéndices, fue leído en la extracción con `pdftotext` hecha por el orquestador (el PDF no se modificó). Paginación citada: la que resulta de contar los saltos de página del texto extraído (p. 1 = portada con resumen); debe cotejarse contra el PDF antes de citar páginas en el artículo. **Limitación de la extracción:** los símbolos griegos (alfa, beta, tercera letra) no sobreviven en el texto extraído.

**No pude abrir:** las decisiones 005, 008 y 009. Probé varios nombres de archivo (mi herramienta no lista directorios) y no existen con esos nombres. Lo que sé de ellas viene solo de lo que citan 001, 003, el glosario y los README (005 = Método A de emparejamiento SINCO -> O*NET por embeddings, resultado "sin_validar"; 008 §7 = modelo, presupuesto, n corridas, idioma y fecha de corte "requieren decisión"; 009 = módulo de exposición con crosswalk top-2). Todo lo que dependa de su texto exacto es **[NO VERIFICADO]**.

**No pude inspeccionar `data/processed/*.parquet`** (mi herramienta no lee Parquet ni ejecuta código). Las cuentas de abajo usan únicamente los conteos documentados en `diccionario_datos_sinco.md` y `sinco_pdf_exploracion.md`. Marco **[NO VERIFICADO]**: longitud real en palabras de funciones y descripciones, distribución de funciones por grupo (mínimo, máximo), contenido de la nota de la página 230 de la fe de erratas, número total de tareas O*NET 31.0 del proyecto, y qué grupos tienen pocas funciones.

**Conteos reales usados (documentados):**

| Elemento | Conteo |
|---|---|
| Grupos unitarios SINCO 2019 | 490 |
| Grupos unitarios con descripción | 490 (100 %) |
| Funciones (ítems) | 3,542 en 457 grupos (media = 3,542 / 457 = 7.75 por grupo) |
| Grupos residuales sin funciones | 33 (490 - 457) |
| Ocupaciones ejemplo | 1,642 en 472 grupos (media = 1,642 / 472 = 3.48) |
| Incluye / Excluye | 22 / 931 (total 953); 22 grupos con incluye, 398 con excluye |
| Fe de erratas | 3 notas: ejemplos de 5115, clave del Excluye de 9111, nota de p. 230 sin código |
| Piloto de anotación O*NET | 40 tareas, 3 corridas, acuerdo exacto 0.90-0.95 (según el encargo) |

## 1. Pregunta

001 define exposición sobre tareas O*NET (EE. UU.) llevadas a SINCO con un crosswalk top-2 que hoy está `sin_validar`. El PDF de SINCO trae texto propio (descripción, funciones, ejemplos, incluye/excluye). ¿Se puede medir exposición con ese texto, de modo que la medida sea mexicana por construcción y no dependa (o dependa menos) del crosswalk? ¿Con qué método y cómo se validaría?

## 2. Literatura consultada (solo lo verificado)

Cada línea indica qué se leyó. Lo demás es **[NO VERIFICADO]**.

1. **Eloundou, Manning, Mishkin, Rock (2023)**, arXiv:2303.10130v5 (22-ago-2023). **Verificado contra el texto completo** (cuerpo y apéndices A-D). Páginas según la nota de la sección 0. Lo que dice el texto:
   - **Rúbrica.** Etiquetas **E0** (sin exposición), **E1** (exposición directa), **E2** (exposición mediante aplicaciones basadas en LLM) y **E3** (exposición con capacidades de imagen). El texto literal está en 011 §5, E-2 (apéndice A.1, pp. 24-26). Resumen en §3.3 (pp. 6-7). E3 se etiqueta aparte "to facilitate annotation, though we combine E2 and E3 for all analyses" (p. 7, nota b). En el resumen del cuerpo, las capacidades de imagen se cuentan dentro de E2 y se dice que visión e imagen "were only included in our definition of LLM-powered software" (p. 7); y en §6.3 se aclara que la medida de exposición directa no consideró capacidades de visión (p. 23).
   - **Umbral.** Reducción de tiempo de **al menos 50 %** con calidad equivalente. Los autores lo describen como "somewhat arbitrary", elegido "for ease of interpretation by annotators" y alto a propósito porque esperaban que la reducción real fuera menor (pp. 7-8). "Calidad equivalente" = un tercero, típicamente el receptor del producto, no notaría ni le importaría la ayuda del LLM (p. 7, nota a).
   - **Agregaciones** (p. 8): (i) la medida E1, "cota inferior" de la proporción de tareas expuestas; (ii) E1 + 0.5·E2; (iii) E1 + E2, "cota superior". **Nombres de los símbolos: [NO VERIFICADO].** Los glifos griegos no se ven en el texto extraído. Mi versión anterior de este documento decía "zeta (no gamma como escribió 001)" sin base verificable: la consulta al README de `github.com/openai/GPTs-are-GPTs` (WebFetch, 2026-10-19, resumen de herramienta) lo llama alfa, beta y **gamma**. Por tanto 001 no está probado como erróneo. Hasta que una persona mire el glifo en el PDF, este proyecto nombra las medidas por su definición (E1; E1 + 0.5·E2; E1 + E2). 011 usa "alfa", "beta" y "cota superior".
   - **Ponderación.** Las tareas *core* pesan el doble que las *supplemental*, con pesos que suman 1 por ocupación: así se calculan la Tabla 3, la Fig. 2 y la Tabla 9 (p. 8 pie de Tabla 2; p. 11 nota 6; p. 12 nota 7; p. 21). **No todas las figuras y tablas lo usan:** Fig. 3, Fig. 5 y Tablas 4-7 usan pesos iguales (pp. 12-18). También corrieron un análisis con las puntuaciones de importancia de O*NET sin cambios significativos, y reconocen que no ponderar por importancia da resultados curiosos (p. ej. barberos con exposición razonablemente alta) (p. 11).
   - **Datos.** O*NET 27.2, 1,016 ocupaciones, **19,265 tareas**, 2,087 DWA (p. 6). Datos de empleo y salario de BLS 2020-2021 y CPS, que "primarily capture workers who are not self-employed, are documented, and are working in the so-called formal economy" (p. 6).
   - **Anotación** (pp. 7-8). Humanos: los autores etiquetaron los DWA que exigen mucha fisicalidad; anotadores contratados con experiencia en revisar salidas de modelos etiquetaron el resto de los DWA y un subconjunto de tareas (nota 5, p. 8); luego agregan DWA a tarea y a ocupación. GPT-4 (versión temprana) etiquetó **todos los pares tarea-ocupación**, no los DWA; la rúbrica se modificó levemente para mejorar el acuerdo con etiquetas humanas (pp. 2, 8). La rúbrica de humanos y la de GPT-4 difieren a propósito (p. 9, §3.4.2). La mención en la p. 1 de que en el momento del etiquetado ChatGPT/Playground incluían la familia GPT-3.5 y no GPT-4 describe el LLM de referencia de la rúbrica, no al anotador.
   - **Acuerdo humano-GPT-4** (Tabla 2, p. 8; el pie define "agreement" como la frecuencia con que coinciden en la anotación, p. ej. E0, E1 o E2, y no explica cómo se calcula para las medidas ponderadas):

     | Comparación | Medida | Acuerdo | Pearson |
     |---|---|---|---|
     | GPT-4 Rúbrica 1 vs humanos | E1 | 80.8 % | 0.223 |
     | | E1 + 0.5·E2 | 65.6 % | 0.591 |
     | | E1 + E2 | 82.1 % | 0.654 |
     | GPT-4 Rúbrica 2 vs humanos | E1 | 81.8 % | 0.221 |
     | | E1 + 0.5·E2 | 65.6 % | 0.538 |
     | | E1 + E2 | 79.5 % | 0.589 |
     | GPT-4 R1 vs GPT-4 R2 | E1 | 91.1 % | 0.611 |
     | | E1 + 0.5·E2 | 76.0 % | 0.705 |
     | | E1 + E2 | 82.4 % | 0.680 |

     Los autores dicen que usan GPT-4 Rúbrica 1 (pie de la Tabla 2), pero §3.4.2 afirma "we present results from human annotators as our primary results" (p. 9): hay una inconsistencia interna del artículo sobre cuál anotación es la principal. A nivel ocupación hablan de "alto acuerdo" (Fig. 2, p. 10) y dicen que cerca del extremo alto GPT-4 tiende a dar valores menores que los humanos (Fig. 2).
   - **Resultados de referencia** (no comparables con SINCO): medias a nivel ocupación 0.14 / 0.30 / 0.46 (humanos) y 0.14 / 0.34 / 0.55 (GPT-4) (Tabla 3, p. 12); 80 % de los trabajadores en ocupaciones con al menos 10 % de tareas expuestas y 19 % con al menos 50 % (resumen, p. 1; §4.1, p. 11).
   - **Limitaciones declaradas** (§3.4, pp. 9-10; §6.3, p. 23): (a) etiquetas subjetivas y anotadores "not occupationally diverse"; (b) los resultados de GPT-4 son sensibles a redacción de la rúbrica, orden y composición del prompt, ejemplos, nivel de detalle y definiciones; "none should be considered the definitive ground truth"; (c) validez del marco por tareas ("our exposure analysis would largely be invalidated" si falla); (d) los anotadores humanos desconocían las ocupaciones asociadas a cada DWA, lo que produjo discrepancias, y se recogieron etiquetas adicionales en pares con desacuerdo importante; (e) medida prospectiva y sujeta a cambio; (f) fuentes de desacuerdo: tareas que exigen cambiar hábitos de varias personas (reuniones, negociaciones), tareas con norma o regulación de supervisión humana, y tareas con tecnología ya existente que las automatiza; (g) foco en EE. UU., que limita la generalización a otros países por organización industrial, infraestructura, regulación, "linguistic diversity" y contexto cultural; (h) la exposición es técnica y no distingue entre efectos que aumentan o desplazan trabajo (p. 2), y "technical feasibility does not guarantee labor productivity or automation outcomes" (p. 3).
   - **Consecuencia para este proyecto:** las E1/E2 de 001 (E1 = IA apoya y humano valida; E2 = IA completa la tarea) **no son las E1/E2 de Eloundou** (directo con el LLM solo frente a con software construido encima). Además, en un ejemplo del apéndice la tarea de recetar medicamentos se etiqueta E2 aun cuando exige un humano que decida (p. 26): la presencia de un humano en el ciclo no separa E1 de E2 en Eloundou. 001 §4.3 ya dice que no afirma equivalencia; aquí se refuerza: no comparar niveles absolutos con sus cifras.
2. **Felten, Raj, Seamans (2021)**, SMJ 42(12). Registro de Princeton (001). Método **solo por fuentes secundarias** (resultados de búsqueda, 2026-10-19): aplicaciones de IA de EFF cruzadas, mediante una matriz construida por crowdsourcing (Mechanical Turk), con 52 habilidades de O*NET; pesos por nivel e importancia de la habilidad; medida relativa y agnóstica sobre sustitución o complemento. No leí el artículo. Fuente secundaria: https://sites.bu.edu/tpri/2021/06/02/occupational-industry-and-geographic-exposure-to-artificial-intelligence-a-novel-dataset-and-its-potential-uses . **[NO VERIFICADO]** contra el texto original. Eloundou (pp. 5 y 19) describe a Felten et al. (2018, 2023) como vinculación de capacidades de IA con habilidades ocupacionales de O*NET: coincide en lo general, no verifica los detalles.
3. **Gmyrek, Berg, Bescond (OIT, WP 96, 21 de agosto de 2023)**: la página de la OIT confirma título, fecha y conclusión (aumento más que automatización; mayor efecto en ingresos altos por el empleo administrativo, con sesgo de género). **No pude leer su metodología** (la página no la trae; el PDF no fue accesible). Su actualización **WP 140** (página https://www.ilo.org/node/706766) describe: muestra de tareas de la clasificación polaca (29,753 tareas), encuesta a ~1,640 trabajadores que calificaron 2,861 tareas (52,558 datos), consulta a expertos tipo Delphi, y un asistente de IA que predice puntajes para tareas de la documentación técnica de la CIUO-08; cuatro gradientes de exposición. No dice qué modelo usaron ni validaciones numéricas. Hecho relevante para este proyecto: la OIT puntúa tareas de **documentación técnica de la CIUO-08** (texto de clasificación, no tareas O*NET), el antecedente más cercano a anotar el texto de un catálogo de ocupaciones. Cifras y metodología de WP 96: **[NO VERIFICADO]**.
4. **Webb (2020)**: método por traslape textual entre tareas O*NET y patentes de IA (NLP); los puntajes son relativos al promedio, no una fracción de tareas sustituibles, y no predicen dirección (Brookings y ficha NBER, vía resultados de búsqueda). Detalle del procedimiento (pares verbo-sustantivo) **[NO VERIFICADO]**. Es el antecedente conceptual de medir exposición por similitud de texto (Método B), no de anotación. Eloundou (p. 19) lo resume como mapeo de descripciones de tareas a descripciones de avances tecnológicos en patentes.
5. **AI-OCI** (Awuah-Gyasi y Estrada, AIES 2025; vol. 8, núm. 1, pp. 238-248; página https://ojs.aaai.org/index.php/AIES/article/view/36545): según el resumen que devolvió la búsqueda, incrusta (embeddings) más de 19,000 tareas ocupacionales y 338 capacidades de IA, y reporta correlaciones fuertes con AIOE y con el beta de GPT-4. Solo resumen; no pude leer el texto (el PDF vino en binario). Es el antecedente más cercano al Método B. Detalles de validación **[NO VERIFICADO]**.
6. **Dominski y Lee (2025)**, arXiv 2507.08244 (leído el resumen y la parte inicial): puntúan cada tarea O*NET con ChatGPT-4o y Claude 3.5 Sonnet siguiendo a Eloundou (razonamiento, estimación 0-100 %, confianza), ponderan por relevancia de la tarea, y validan con correlaciones entre modelos; reconocen que el acuerdo entre modelos no prueba exactitud y que no hay verdad de referencia. Antecedente de anotación con LLM y de acuerdo entre modelos.
7. **Frey y Osborne (2013)** y **América Latina** (Gmyrek, Winkler, Garganta 2024; Ceballos y Guadarrama 2025): ver 001 §3, que no repito. Eloundou (p. 19) resume a Frey y Osborne (2017) como etiquetado experto de potencial de automatización en un conjunto de ocupaciones O*NET con alta confianza más un clasificador probabilístico para el resto (descripción de segunda mano, no lectura del original). No encontré (búsqueda del 2026-10-19) un trabajo que construya exposición a IA generativa directamente con las descripciones de funciones de SINCO ni de otro catálogo nacional latinoamericano; la búsqueda con términos de "embeddings, descripciones de ocupaciones, sin crosswalk" no devolvió un caso exacto (lo más cercano: AI-OCI, que no dice si usa CIUO). Ausencia de evidencia, no evidencia de ausencia.

## 3. Elementos comunes a los tres métodos

### 3.1 Qué texto del SINCO se usa y cómo

| Campo | Conteo | Rol propuesto |
|---|---|---|
| Descripción | 490 | Contexto para el anotador; en los residuales, única unidad posible (sec. 3.3) |
| Funciones | 3,542 en 457 | **Unidad "tarea" de SINCO** (A y B) |
| Ocupaciones ejemplo | 1,642 en 472 | Contexto breve (título del grupo + ejemplos). Se excluyen los ítems con `afectado_por_errata` (5115) |
| Incluye (22) | 22 | Contexto opcional; ablación |
| Excluye (931) | 931 | **No** entra al prompt principal: describe lo que pertenece a otros grupos y puede contaminar la clase. Ablación: ¿cambia la clase al añadirlo? |
| Glosario (21) | 21 | No se usa por ítem; consulta humana |

### 3.2 Erratas y casos de extracción

- Las tablas conservan el texto original (la fe de erratas no se aplica en tablas; aplicarla es decisión de metodología, según `sinco_pdf_exploracion.md`). Propuesta: las funciones no están afectadas por las tres notas conocidas; los ejemplos de 5115 y el Excluye de 9111 no entran al prompt principal (un grupo cada uno, impacto marginal). La nota de la página 230 no tiene código y no sé qué corrige: **[NO VERIFICADO]**.
- 2281: una función quedó fusionada con la siguiente (`notas_extraccion`). Se anota como un ítem y se marca `item_fusionado`; sensibilidad: excluirlo.

### 3.3 Los 33 grupos residuales sin funciones

Son "Otros ... no clasificados" y 9999; por definición carecen de contenido específico, y su descripción es genérica. Propuesta:
1. **Medida principal: `E = NA`, `motivo_na = "residual_sin_funciones"`**. No se imputa en el caso base (coherente con 003 §4, que no imputa por defecto).
2. Sensibilidad opcional, marcada `imputado` y excluida de los intervalos de las demás unidades: anotación holística de la descripción (1 ítem) o media del subgrupo padre. No debe presentarse como medición del grupo.

### 3.4 Escala y mapeo (compatible con 001 §4.3)

Los tres métodos terminan en el mismo objeto: por unidad de texto, `exposure_class` E0/E1/E2 con `physical_bottleneck`, `confidence` y `rationale`, mapeado por `src/annotate/config.toml [mapa_numerico]` a 0/0.5/1 (más límites inferior y superior). Sin puntajes continuos libres del anotador. El método B produce un promedio ponderado de clases de vecinos (derivado, no escrito por un anotador); se reporta también la clase modal para comparar con A.

### 3.5 Trazabilidad (regla 4)

Todo prompt nuevo es una versión nueva (`ann-v2-sinco` propuesto), no una edición de `ann-v1` (inmutable, hash registrado). Cada corrida: `run_id`, `prompt_version`, `prompt_sha256`, modelo, fecha de corrida, fecha de corte de capacidades (parámetro), versión del catálogo (`sinco_fuente.sha256`), `temperature`/`temperature_note`. Para B además: modelo y versión de embeddings, hash del conjunto de referencia, k, kernel y semilla.

### 3.6 Agregación a grupo unitario y niveles superiores (A y B; C hereda)

- `E_g = sum_f(e_f) / n_f` con pesos iguales sobre todas las funciones del grupo; más `share_E2` y `share_any`. No existe la distinción core/supplemental en SINCO, así que todas las funciones pesan igual (**apartamiento de 001 §4.4**, ver cada método).
- Grupos con menos de 3 funciones: se marcan `pocas_funciones` (umbral PROVISIONAL, sin base empírica; la distribución real es **[NO VERIFICADO]**).
- Niveles superiores (subgrupo 163, grupo principal 52, división 9): 003 §1 exige promedios ponderados por empleo, nunca promedios simples de códigos. La fuente de empleo (ENOE) no fue consultada y "requiere decisión" (001 §10.6). Mientras no exista, se reporta el promedio no ponderado de grupos hijos con la etiqueta "descriptivo, no ponderado por empleo" y no se interpreta como exposición del empleo del nivel. Los 33 residuales (NA) no entran al promedio y se reporta cuántos hijos aportan.

### 3.7 Sesgos que comparten los tres

- **Idioma:** A y B anotan SINCO en español nativo; la anotación de O*NET (piloto) es en inglés. Calibración de la rúbrica por idioma **[NO VERIFICADO]**; se prueba con la ablación de la sec. 6.
- **Granularidad:** una función SINCO es más genérica que una tarea O*NET. Cálculo de contraste: 19,265 tareas / 1,016 ocupaciones = 18.96 tareas por ocupación (cifras de Eloundou, O*NET 27.2, p. 6, verificadas; la cifra para 31.0 del proyecto es **[NO VERIFICADO]**) frente a 7.75 funciones por grupo SINCO. Menos ítems y más abstractos implican promedios más gruesos y riesgo de que enunciados gerenciales ("planear, organizar, dirigir") se califiquen E1 por defecto. No comparar niveles absolutos entre la ruta SINCO y la ruta O*NET; comparar rangos y concordancia ordinal.
- **Heterogeneidad intra-grupo:** un grupo unitario agrupa ocupaciones distintas; la lista de funciones es común a todas. La medida es exposición del *contenido descrito del grupo*, no de cada puesto.
- **Informalidad:** SINCO describe ocupaciones en México, incluidas las que se dan en la informalidad **[NO VERIFICADO que el catálogo las trate distinto]**; la exposición es técnica, no refleja adopción ni brecha digital (001 §6.2). Eloundou advierte que sus datos de empleo cubren sobre todo economía formal (p. 6).
- **México frente a EE. UU.:** A y B miden el contenido descrito por el catálogo mexicano; eso mejora la pertinencia pero el modelo anotador conoce el trabajo sobre todo a partir de texto en inglés y de contextos con más digitalización.
- **Anotador LLM:** sesgo documentado por Eloundou (sensibilidad a redacción y orden, §3.4.2, p. 9). Mitigaciones: 3 corridas con orden propio por corrida, muestra humana.

## 4. Los tres métodos

### Método A - Anotación directa con LLM de las funciones SINCO

**Idea.** Aplicar la rúbrica de 001 (E0/E1/E2, `physical_bottleneck`) directamente a cada función del catálogo SINCO, con el título, la descripción y los ejemplos como contexto, y agregar por grupo. No usa O*NET ni el crosswalk.

**Definición operativa.** `e_f` = mapa(E-clase de la función f). `E_g` = media de `e_f` sobre las funciones del grupo g (sec. 3.6). Reporta `share_E2`, `share_any`, `E_g_inferior`, `E_g_superior`.

**Compatibilidad con 001.** Respeta 4.1 (concepto: propiedad técnica), 4.3 (escala, mapa, campos) y 4.6. **Se aparta de** 4.2 (unidad: tarea O*NET -> O*NET-SOC -> SINCO; aquí es función SINCO -> grupo SINCO), 4.4 (no hay core/supplemental, ni pesos de importancia O*NET) y 4.5 (no aplica el crosswalk). Además `docs/rubric.md` dice "Se anota cada tarea de O*NET"; extenderla a funciones SINCO requiere decisión registrada (regla 2). Propuesta: una enmienda a 001 §4.2 y §4.4 que declare A como ruta alternativa con unidad "función SINCO", sin tocar 4.3.

**Texto usado.** Funciones (3,542, unidad anotada); contexto: título, descripción, ejemplos (sec. 3.1). Residuales: NA (sec. 3.3). Erratas: sec. 3.2.

**Unidad de anotación y agregación.** Anotación por función, enviada por lotes de un grupo (todas sus funciones en un mismo mensaje, con `function_id = sinco_code + orden`). Riesgo de anclaje entre funciones del mismo mensaje; se mide con una ablación de una función por llamada en una submuestra (sec. 6.5). Agregación: sec. 3.6.

**Quién anota y trazabilidad.** Subagentes de Claude Code según la decisión del usuario para el piloto (sin API, modelo `claude-sonnet-5-5 (subagente Claude Code)`; temperatura no controlable), o API si el humano lo decide después. 3 corridas independientes con orden propio de grupos y de funciones. Cada corrida con los campos de la sec. 3.5. Requeriría un esquema nuevo (`SincoFunctionAnnotation`, claves `sinco_code`, `orden`) y un módulo análogo a `subagent.py`; es código nuevo, fuera de esta propuesta.

**Salida.** E0/E1/E2 + `physical_bottleneck` + `confidence` + `rationale`; mapa a 0/0.5/1 de 001.

**Costo estimado** (supuestos **[NO VERIFICADO]**: función ≈ 20 palabras ≈ 35 tokens; descripción ≈ 120 palabras ≈ 170 tokens; título ≈ 12; ejemplos ≈ 3.48 × 6 = 21; prompt fijo ≈ 600 tokens; salida por función ≈ 70 tokens):
- Ítems por corrida: 3,542 funciones; 457 grupos.
- Entrada por corrida, un grupo por llamada: funciones 3,542 × 35 = 123,970; contexto 457 × (12 + 170 + 21) = 92,771; prompt 457 × 600 = 274,200; total = 490,941 ≈ **0.49 M tokens** en 457 llamadas.
- Salida por corrida: 3,542 × 70 = 247,940 ≈ **0.25 M tokens**.
- 3 corridas: ≈ 1.47 M tokens de entrada, 0.74 M de salida, 1,371 llamadas.
- Variante con 10 grupos por llamada: 46 llamadas por corrida; entrada = 123,970 + 92,771 + 46 × 600 = 244,341 por corrida (≈ 0.73 M en 3 corridas); salida igual.
- Piloto de A sugerido: 40 grupos estratificados × 7.75 funciones ≈ 310 funciones; entrada ≈ 40 × (491k / 457) ≈ 43 k tokens por corrida; trivial.
- Residuales (sensibilidad): 33 descripciones ≈ 33 × (12 + 170 + 600) ≈ 26 k tokens por corrida.
- Ablación de una función por llamada, submuestra de 300 funciones: 300 × (600 + 35 + 203) ≈ 251 k tokens de entrada, 21 k de salida.
- **Dependencias nuevas:** ninguna de paquetes (pydantic y pyarrow ya están). Sí: esquema/módulo nuevo y la decisión de modelo, vía, fecha de corte y presupuesto (008 §7 "requiere decisión").

**Ventajas.** Independiente de O*NET y del crosswalk sin validar; texto nativo y mexicano; barata respecto de anotar todo O*NET; auditable (rationale por función); misma rúbrica ya probada en piloto.

**Límites.** Funciones genéricas y pocas por grupo; sin ponderación de importancia; heterogeneidad intra-grupo; 33 residuales NA; sin acceso a lo que se hace en la práctica.

**Cómo se validaría.** Sec. 6 completa; énfasis en muestra humana de funciones y en la ablación de contexto.

### Método B - Puntuación semántica por embeddings y transferencia por vecinos más cercanos

**Idea.** Representar cada función SINCO (y cada tarea O*NET anotada) como un vector, y asignar a la función SINCO la exposición de las tareas O*NET anotadas más parecidas (kNN). Evita el crosswalk SINCO -> O*NET a nivel de ocupación: la transferencia es de tarea a función, por similitud de contenido.

**Definición operativa.** Conjunto de referencia R: tareas O*NET con `exposure_class` anotada con la rúbrica 001. Para la función f: `e_f = sum_j(K(s_j) · e_j) / sum_j K(s_j)` sobre los k vecinos en R, con s_j la similitud coseno y K un núcleo monótono. Se reporta además la similitud máxima `s_max` y la clase modal ponderada. `E_g` por la sec. 3.6.

**Por qué el piloto no basta.** Solo hay 40 tareas anotadas (40 de 1,016 ocupaciones). Con 40 vecinos posibles, kNN es inviable. Se necesita ampliar R. Propuesta: R de 2,000 tareas O*NET *core*, estratificadas por grupo mayor SOC (cifra **PROVISIONAL**: a calibrar con validación cruzada dejando uno fuera; el piloto de 40 es semilla y se incluye). Alternativa: R = todas las tareas O*NET (≈ 19,265 si el número de 31.0 fuera igual al de 27.2 de Eloundou, **[NO VERIFICADO]**); coincide con el insumo de la ruta O*NET y de C.

**Compatibilidad con 001.** Respeta 4.1 y la escala de 4.3 en la capa de R. Se aparta de: 4.2 (unidad), 4.4 y 4.5 (no hay E_o ni crosswalk). Introduce un elemento que 001 no contempla: una **medida derivada de similitud** (promedio ponderado de clases de vecinos), no una clase asignada por un anotador a la función. Requiere enmienda de 001 §4.2-4.5 por la misma razón que A, más una declaración explícita de que el puntaje es un estimador por transferencia (no una anotación). Las variantes "similitud con 338 capacidades de IA" al estilo AI-OCI se descartan como medida principal: exigen elaborar y fechar un catálogo de capacidades y producen un puntaje continuo sin anclaje en E0/E1/E2.

**Texto usado.** Funciones (3,542) y, como segundo vector, descripción (490) para residuales (sensibilidad). Sin ejemplos ni excluye en el vector principal (el excluye añadiría ruido de otros grupos).

**Unidad y agregación.** Función -> `e_f` -> `E_g` (sec. 3.6). Funciones con `s_max` bajo se marcan `fuera_de_soporte` (umbral a fijar por validación cruzada, sin valor propuesto) y se excluyen de `E_g` con reporte de cobertura.

**Quién anota y trazabilidad.** El anotador de R es el LLM (subagentes o API, regla 4 como en A). La puntuación SINCO la hace un modelo de embeddings multilingüe (español-inglés), versión fijada, semilla fija. Qué modelo concreto: **[NO VERIFICADO]**, no lo evalué; no recomiendo uno. Búsqueda exacta con numpy basta para ~6,000 vectores; no hace falta una biblioteca de índices.

**Salida.** `e_f` en [0, 1] (promedio de clases 0/0.5/1) y clase modal; mapeo a 001 por la misma tabla.

**Costo estimado** (mismos supuestos de A; tarea O*NET en inglés ≈ 45 tokens + título 10 = 55):
- Anotación de R = 2,000 tareas en lotes de 40 (como el piloto): 50 llamadas por corrida; entrada = 2,000 × 55 + 50 × 600 = 140,000 por corrida; salida = 2,000 × 70 = 140,000. Tres corridas: ≈ **0.42 M de entrada, 0.42 M de salida, 150 llamadas**.
- Si R = todas (19,265): 482 llamadas por corrida (19,265 / 40); entrada = 19,265 × 55 + 482 × 600 = 1,059,575 + 289,200 = 1,348,775 ≈ 1.35 M por corrida; salida = 1.35 M. Tres corridas: ≈ **4.05 M de entrada y 4.05 M de salida**.
- Embeddings (cómputo local): 3,542 × 35 + 490 × 170 + 2,000 × 55 = 123,970 + 83,300 + 110,000 ≈ 0.32 M tokens, minutos de CPU **[NO VERIFICADO]**; sin costo de API si el modelo es local.
- **Dependencias nuevas que requieren aprobación:** un paquete y un modelo de embeddings (por ejemplo una biblioteca de transformers; peso de descarga y licencia **[NO VERIFICADO]**), no incluidos en el stack aprobado (pandas, pyarrow, pydantic, streamlit, pytest). Si se usara una API de embeddings, choca con la decisión del usuario de no usar API. Esquema para R y para los vecinos.

**Ventajas.** Barato una vez anotado R; no usa el crosswalk a nivel ocupación; permite medir `s_max` como señal de cobertura del soporte; reproducible y determinista dado el modelo.

**Límites.** No es independiente del anotador: hereda sus errores (R lo anota el mismo LLM con la misma rúbrica), así que su concordancia con A **no** es validación independiente. Depende de la calidad de los embeddings entre español e inglés. Una función genérica puede acercarse a tareas de ocupaciones sin relación. Es el método que más se aparta de 001 y el único con una dependencia nueva de software.

**Cómo se validaría.** Validación cruzada dejando uno fuera en R (kappa ponderado y error absoluto medio entre `e_j` real y predicho a partir de los demás); concordancia con A; muestra humana (sec. 6).

### Método C - Híbrido: transferencia O*NET por crosswalk top-2 contrastada con la señal del texto SINCO

**Idea.** Calcular `E_O(g)` por la ruta ya construida (E_o de las O*NET del top-2 del grupo, módulo `src/score/exposicion.py`) y `E_A(g)` (Método A, o B si A no existe), y combinarlos con una regla explícita para las discrepancias. La señal del texto SINCO sirve para ajustar y detectar errores del crosswalk, no para promediar sin control.

**Definición operativa.** `Delta_g = E_A(g) - E_O(g)`. Umbrales PROVISIONALES, sin base externa; se recalibran con la muestra humana (sec. 6.3) antes de usarse:
1. **Concordancia** `|Delta| <= 0.25` (medio escalón de clase): `E_C = (w_A · E_A + w_O · E_O) / (w_A + w_O)` con pesos inversamente proporcionales a la varianza de remuestreo de cada ruta; si la varianza no es estimable, pesos iguales. Etiqueta `concordante`.
2. **Discrepancia moderada** `0.25 < |Delta| <= 0.50`: `E_C = E_A` (texto mexicano, mientras el crosswalk esté `sin_validar`); el intervalo cubre ambos valores; etiqueta `discrepancia_moderada`; entra a revisión humana por muestreo.
3. **Discrepancia grande** `|Delta| > 0.50`: `E_C = NA` con `motivo_na = "discrepancia_sin_resolver"` hasta que un revisor humano lea la descripción, las funciones y los pares O*NET y registre la resolución (tercer evaluador). No se promedia por decreto.
4. **Sin crosswalk usable** (`sin_coincidencia` o `cobertura_insuficiente` del módulo): `E_C = E_A`, etiqueta `solo_texto_sinco`. **Sin funciones** (residual): `E_C = NA` salvo que exista `E_O` con crosswalk de confianza alta, caso en que `solo_onet`, marcado; propuesta por defecto NA.
Se reportan siempre las tres cifras (`E_A`, `E_O`, `E_C`) y la etiqueta, para que el lector vea el origen.

**Compatibilidad con 001.** Respeta 4.1-4.6 en la rama O*NET; la rama A tiene los apartamientos de A (4.2 y 4.4). 4.5 se conserva tal cual para `E_O`. La regla de combinación y los umbrales son **nuevos**; requieren decisión registrada (regla 7) y enmienda de 001 para declarar `E_C` como medida combinada con su etiqueta.

**Texto usado.** El de A (funciones, descripción, ejemplos) más el texto de las tareas O*NET en la rama O*NET.

**Quién anota.** A y la anotación completa de O*NET (insumo de la ruta existente): ambas con LLM (subagentes/API); revisión humana de discrepancias. Trazabilidad: regla 4 en cada corrida; además hash del crosswalk y `match_status`.

**Salida.** `E_C` en [0, 1] con etiqueta de origen; clase por umbrales de 001 solo si se decide (001 no define cortes de clase para grupos).

**Costo estimado.**
- Rama A: sec. 4-A (≈ 1.47 M entrada y 0.74 M salida en 3 corridas, un grupo por llamada).
- Rama O*NET: anotación completa de tareas O*NET, 3 corridas: ≈ 4.05 M entrada y 4.05 M salida (con 19,265 tareas; el total real del proyecto y la fracción *core* son **[NO VERIFICADO]**; si solo se anotaran *core*, bajaría en proporción desconocida). Esta rama es el costo pendiente de 008 §7 y ya forma parte del plan aprobado.
- Total C: ≈ 4.05 + 1.47 = **5.52 M entrada** y 4.05 + 0.74 = **4.79 M salida**; ≈ 1,371 + 1,446 = 2,817 llamadas (482 × 3 = 1,446 por lotes de 40).
- Revisión humana de discrepancias: número desconocido hasta observar `Delta`.
- **Dependencias nuevas:** ninguna de paquetes. Sí: decisión sobre umbrales de combinación y rediseño de la salida de `exposicion_sinco` (hoy sin `E_A`).

**Ventajas.** Usa la ruta O*NET (con importancia y tareas centrales) y la señal local; la discrepancia es un instrumento de diagnóstico del crosswalk top-2, hoy el eslabón más débil.

**Límites.** Es la ruta más cara; la regla de combinación es arbitraria hasta calibrarla; el ajuste puede esconder el error del crosswalk bajo una media. Comparte el anotador LLM con A y B. Si la regla 2 devuelve `E_A`, C degenera en A para los casos difíciles.

**Cómo se validaría.** Sec. 6; adicionalmente: porcentaje de grupos por etiqueta, y si la muestra humana prefiere A, O*NET o el promedio en los casos discrepantes (acuerdo de la regla con el árbitro humano).

## 5. Tabla comparativa

| Criterio | A: LLM directo sobre funciones SINCO | B: embeddings + kNN | C: híbrido con crosswalk |
|---|---|---|---|
| Supuesto central | La rúbrica 001 es aplicable a funciones genéricas de SINCO | Funciones y tareas O*NET parecidas tienen exposición parecida | La ruta O*NET y la ruta SINCO se corrigen mutuamente |
| Insumos | 3,542 funciones, 490 descripciones, 1,642 ejemplos | Funciones SINCO + conjunto R de tareas O*NET anotadas (piloto de 40 insuficiente) | A + anotación completa O*NET + crosswalk top-2 |
| Depende del crosswalk sin validar | No | No (a nivel ocupación); sí del embedding entre idiomas | Sí, en una rama; la otra lo contrasta |
| Unidad | Función SINCO | Función SINCO | Grupo (E_A, E_O) |
| Escala | E0/E1/E2 -> 0/0.5/1 | Promedio ponderado de clases (derivado) | Combina ambas con etiqueta de origen |
| Apartamiento de 001 | 4.2, 4.4, 4.5 y `rubric.md` | 4.2-4.5, medida derivada | 4.5 intacto; regla nueva de combinación |
| Costo en tokens (3 corridas) | ≈ 1.47 M entrada, 0.74 M salida | R=2,000: ≈ 0.42 M / 0.42 M; R=todas: ≈ 4.05 M / 4.05 M; más embeddings locales | ≈ 5.52 M / 4.79 M |
| Dependencias nuevas | Esquema y módulo; sin paquetes | Paquete y modelo de embeddings | Sin paquetes; reglas nuevas |
| Residuales sin funciones (33) | NA | NA | NA (por defecto) |
| Independencia del anotador LLM | No | No (hereda el anotador de R) | No |
| Riesgo principal | Funciones demasiado genéricas | Embeddings multilingües y soporte insuficiente de R | Combinación arbitraria; costo |
| Validez esperada | Media-alta en contenido; sin verificar | Media-baja en contenido; buena para contraste | Media-alta si el crosswalk mejora; si no, reduce a A |
| Complejidad de implementación | Baja-media | Media | Alta |

La fila "validez esperada" es un juicio mío, no un resultado; ninguna cifra respalda hoy el orden.

## 6. Diseño de validación común

### 6.1 Acuerdo entre corridas (interna)
- Por ítem: kappa de Cohen ponderado (cuadrático) por pares de corridas y alfa de Krippendorff ordinal entre las 3 corridas; acuerdo exacto como descriptivo (referencia: 0.90-0.95 en el piloto O*NET, que es otro texto y 40 ítems, **no** una expectativa para SINCO). Como orden de magnitud externo, Eloundou reporta acuerdo humano-GPT-4 de 65.6 % a 82.1 % según la medida (Tabla 2, p. 8), con una definición de acuerdo que no queda explicada para las medidas ponderadas; tampoco es expectativa para SINCO.
- Por grupo: CCI de `E_g` entre corridas y rango min-max. Con 3 corridas, la varianza entre corridas se estima mal; se reporta como tal.
- Cambio de modelo, de orden y de versión de prompt: tratados como factores de sensibilidad, no como corridas repetidas.

### 6.2 Convergencia entre métodos
Spearman y kappa ponderado de `E_g` entre A, B y `E_O` (ruta O*NET), por terciles y por división; gráfico de Bland-Altman. Advertencia explícita: A, B y C comparten anotador LLM y rúbrica, por lo que su acuerdo no demuestra validez, solo coherencia. N:1 del crosswalk produce grupos SINCO con el mismo `E_O`; los intervalos y correlaciones que involucren `E_O` deben usar el número efectivo de ocupaciones O*NET distintas.

### 6.3 Muestra humana de referencia (el único contraste independiente del LLM)
- **Funciones:** 300 funciones (≈ 8.5 % de 3,542; propuesta, no calculada con potencia formal; el error estándar del kappa con 3 categorías y n = 300 sería del orden de 0.04-0.05, estimación aproximada **[NO VERIFICADO]**), estratificadas por división y por clase LLM (para no dejar vacíos E2), doble revisión independiente con la rúbrica v1, ciega a la etiqueta del LLM. Se reportan kappa ponderado entre revisores, consenso adjudicado por un tercero y kappa ponderado (LLM, consenso) con IC por bootstrap.
- **Grupos:** 49 grupos (≈ 10 % de 490, igual que la proporción de 003) con calificación holística de `E_g` en tres niveles por dos revisores a partir de la descripción y las funciones, para contrastar el nivel de grupo y el efecto de la agregación.
- Quién revisa, con qué guía y cuántas horas: **requiere decisión** (el mismo vacío que 003 §5.4). Eloundou señala que sus anotadores no eran ocupacionalmente diversos y que etiquetas de calidad exigen personas con conocimiento de las ocupaciones (§3.4.1, p. 9): criterio útil para elegir revisores.

### 6.4 Referencias externas
- **Probabilidad de automatización de Frey-Osborne** (trasladada a SINCO por el emparejamiento de 005): solo **comparación convergente imperfecta**. Mide automatización de ocupaciones completas, no exposición técnica de tareas; no se fija signo esperado ni se usa como criterio de aprobación. **Evidencia añadida:** Eloundou (p. 20, Tabla 9 en p. 21) reporta que, condicional a las demás medidas, la medida de automatización de Frey-Osborne correlaciona **negativamente** con su exposición a LLM, y lo atribuye a la baja exposición de tareas físicas; por tanto un signo negativo o nulo no sería una anomalía. Aviso de circularidad: C y `E_O` comparten crosswalk con ese traslado, así que su correlación con Frey-Osborne no es independiente; A y B sí lo son respecto del crosswalk. No aparecen como "validación" en el artículo.
- **Puntajes OIT por CIUO-08** (Gmyrek, Berg, Bescond 2023): su uso exige un puente SINCO -> CIUO-08 que no existe en el PDF ni en las tablas. El Método B de 003 (mapeo semiautomático) está aprobado solo en principio y no se implementa hasta que el humano lo pida. Hasta entonces: **no hay validación contra OIT**. Si se construye, hay que reconocer que el puente es un nuevo eslabón con error propio. Cifras y metodología de WP 96: **[NO VERIFICADO]**.
- **AIOE/Webb/Eloundou:** Eloundou (p. 20) encuentra asociación positiva con Webb (software y, con menor significancia, IA), con SML de Brynjolfsson y con tareas cognitivas rutinarias, y "for the most part" ninguna correlación con el AIOE de Felten et al. (2018); atribuye la diferencia a que AIOE puntúa por habilidades de la ocupación y no agrega desde tareas. Los puntajes por ocupación de Eloundou: el README del repositorio `github.com/openai/GPTs-are-GPTs` (WebFetch, 2026-10-19; resumen de herramienta, no copia literal) menciona `occ_level.csv` con calificaciones de GPT-4 y de humanos, licencia MIT en la barra lateral; **no confirma** que existan etiquetas por tarea. Comparabilidad y pasaje a SINCO por crosswalk siguen siendo **[NO VERIFICADO]**; cualquier uso pasa por el mismo problema de crosswalk.

### 6.5 Sensibilidad (pruebas planeadas)
1. Mapa inferior y superior (001 §4.3).
2. Contexto: solo función; con descripción; con descripción y ejemplos; con excluye (A).
3. Lote por grupo frente a una función por llamada (anclaje), submuestra de 300 funciones.
4. Idioma del prompt (rúbrica en español frente a inglés) en una submuestra, y el texto SINCO traducido al inglés frente al original **[NO VERIFICADO que haya traducción disponible]**.
5. Exclusión de funciones fusionadas (2281) y de grupos con `pocas_funciones`.
6. Tratamiento de residuales (NA frente a imputación marcada).
7. Orden de funciones y grupos, tres semillas.
8. En C: umbrales de discrepancia 0.20, 0.25, 0.30 (valores solo para ver sensibilidad).
9. Control negativo: `physical_bottleneck = true` debe asociarse con menor `E_g`; si no, el anotador está mal calibrado. Grupos de contraste (esperados alta y baja exposición) elegidos por el humano **antes** de ver resultados; no los fijo yo. Referencia: Eloundou lista 34 ocupaciones sin ninguna tarea expuesta (Tabla 11, apéndice D, p. 31), casi todas de oficios manuales; sirve como ejemplo de control negativo, no como lista a fijar.

### 6.6 Incertidumbre e intervalos
- Capas: (i) variación entre corridas (min-max y alfa); (ii) composición de funciones: remuestreo de funciones dentro del grupo (bootstrap, B por fijar); como las funciones son la lista completa y no una muestra aleatoria de una población, esto es un **intervalo de sensibilidad**, no un intervalo de confianza de muestreo; con ~8 funciones es grueso; (iii) crosswalk (en C): rango mínimo-máximo de las O*NET emparejadas (ya implementado por el módulo en `E_sinco_min/max`); (iv) entre métodos.
- Un intervalo combinado se calcula por remuestreo jerárquico: corrida -> función -> (crosswalk). Detalle numérico de B y de la propagación al nivel superior: **requiere decisión** (continúa el vacío de la decisión de diseño estadístico de 001 §10.10, aún sin redactar).

### 6.7 Reglas de reporte
- Toda cifra procede de un script en `src/` y de `data/processed/` (reglas 1 y 6); este documento no contiene resultados.
- Etiqueta `PROVISIONAL, SIN VALIDAR` hasta cerrar muestra humana y acuerdo entre corridas; `sin_validar` para cualquier valor que dependa del crosswalk top-2; `imputado`, `pocas_funciones`, `fuera_de_soporte`, `discrepancia_*` según corresponda.
- Se nombra "exposición técnica potencial según el contenido de las funciones descritas en SINCO 2019" (o "tareas O*NET" según la ruta). Prohibido llamarla riesgo de pérdida de empleo (001 §4.6); los escenarios de pérdida van aparte.
- Se reporta cobertura: grupos con medida / 490; 33 residuales NA.
- Asociaciones con salario, educación o informalidad: descriptivas (001 §8).

## 7. Recomendación (pendiente de revisión humana)

1. **Piloto de A primero** (40 grupos estratificados, 3 corridas, ≈ 43 k tokens de entrada por corrida según la cuenta de la sec. 4-A) y, en paralelo, la muestra humana de funciones (300) con doble revisión. Razones: es independiente del eslabón más débil (crosswalk `sin_validar`); usa el texto mexicano en su idioma; reutiliza la rúbrica y la infraestructura de subagentes; es la más barata de las tres rutas con medición propia; y deja el artefacto más auditable (rationale por función).
2. **C como contraste, no como medida principal inicial.** Su valor no es el promedio sino la discrepancia: cuando exista anotación completa de O*NET (pendiente de 008 §7), `Delta` mide qué tanto el crosswalk top-2 desvía la medida. Adoptar `E_C` como cifra principal solo si la muestra humana respalda la regla de combinación.
3. **B al final y opcional**, como contraste de bajo costo cuando R exista, no como medida principal: introduce la única dependencia de software nueva, es el que más se aparta de 001 y su acuerdo con A no es independiente. Valdría la pena si el humano quiere una señal que no pase por razonamiento de LLM sobre las funciones.
4. Antes de cualquier corrida, la decisión humana de **fecha de corte de capacidades, modelo/vía y presupuesto** (008 §7). Mientras esté "requiere decisión", ni el CLI de anotación ni este diseño pueden ejecutarse con proveedor real.

## 8. Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Anotar solo la descripción (1 ítem por grupo) | Una sola clase por grupo, sin variabilidad ni IC por composición; sirve para los 33 residuales solo como sensibilidad |
| Similitud con un catálogo de capacidades de IA (estilo AI-OCI) como medida principal | Requiere construir y fechar el catálogo; sin anclaje en E0/E1/E2; no verificado el detalle del método |
| Puntaje continuo del anotador | Descartado en 001 §4.3 (reproducibilidad) |
| Imputar residuales con la media del subgrupo en el caso base | 003 §4 no imputa por defecto; contamina intervalos |
| Aplicar las erratas a las tablas | Decisión de metodología pendiente; impacto marginal (1 grupo cada uno) |

## 9. Preguntas abiertas para el humano

1. ¿Se acepta A como ruta alternativa con enmienda a 001 §4.2 y §4.4 y a la regla de `docs/rubric.md` ("se anota cada tarea de O*NET")? ¿O el plan principal sigue siendo la ruta O*NET y A es solo contraste? **Nota (2026-10-19):** el orquestador reporta que el usuario escribió "Aprobar E1 y E2", que se lee como aprobación de las enmiendas E-1 y E-2 de 011 §5 (no de las categorías E1/E2 de la rúbrica; ambigüedad por confirmar). Si se confirma, E-1 establece la ruta S (función SINCO, que es este Método A) como alternativa a la ruta O y esta pregunta queda resuelta en ese punto. Siguen pendientes la enmienda a `docs/rubric.md` (E-6) y a 001 §4.4 (E-4). No se aplicó ningún cambio a 001, `rubric.md` ni `glossary.md`.
2. ¿Fecha de corte de capacidades, modelo y vía (subagentes u otra) y presupuesto para la corrida completa? (008 §7: requiere decisión.)
3. ¿Quién revisa la muestra humana (300 funciones, 49 grupos) y con qué guía? ¿Hay presupuesto de horas?
4. ¿Se aprueba el umbral provisional de `pocas_funciones` (< 3) y los umbrales de discrepancia de C (0.25 y 0.50)? No tengo base empírica; propongo calibrarlos con la muestra humana.
5. ¿Se acepta tratar los 33 residuales como NA? ¿Se quiere la sensibilidad con imputación marcada?
6. ¿Se aprueba que `Excluye` no entre al prompt principal, y que los ítems afectados por erratas (5115, 9111) se omitan?
7. ¿Se autoriza un paquete y modelo de embeddings (Método B)? Si sí, ¿cuál, y se acepta el costo de ampliar R? Si el tamaño de R es 2,000 o todas las tareas.
8. ¿Fuente de empleo para ponderar subgrupo, grupo principal y división (ENOE u otra)? Sin ella, los niveles superiores quedan como descriptivos no ponderados.
9. ¿Se autoriza construir el puente SINCO -> CIUO-08 (003, Método B) para validar contra OIT? Mientras no, no hay validación OIT.
10. ¿Alguien puede abrir 005, 008 y 009 y confirmar que mi lectura de ellos (sec. 0) es correcta? Y confirmar con el parquet: longitud real de las funciones, distribución de funciones por grupo y número total de tareas O*NET 31.0, que alimentan el costo.
11. (Nueva) ¿Alguien puede mirar en el PDF de Eloundou el glifo de la tercera medida (E1 + E2) y decirnos si es gamma o zeta? Mientras tanto se nombra por definición.

## 10. Riesgos de esta propuesta

1. Los supuestos de tokens (35 por función, 170 por descripción, 600 por prompt, 70 por salida) no están medidos; el costo real puede variar. Debe recalcularse con una medición sobre los datos antes de aprobar presupuesto.
2. Confundir coherencia entre métodos con validez: los tres usan el mismo anotador.
3. Funciones genéricas pueden producir exposición uniformemente intermedia (E1) y comprimir el rango entre grupos; se revisa con la distribución de `E_g` y con el control negativo.
4. Umbrales de C sin base: pueden inducir un falso consenso.
5. Datos de la literatura de segunda mano (Felten, Webb, AI-OCI, WP 96): marcados; no citar en el artículo sin lectura de la fuente primaria.
6. Que se lea E1/E2 del proyecto como las E1/E2 de Eloundou (sec. 2.1).

## 11. Fuentes consultadas (2026-10-19)

- Eloundou, Manning, Mishkin, Rock (2023), arXiv:2303.10130v5. PDF local `data/raw/Founts/` registrado en `data/raw/manifest.json` como `eloundou_2023_v5_pdf` (sha256 que empieza `af3edd4e`); texto completo leído en la extracción con `pdftotext` del orquestador. Origen: https://arxiv.org/abs/2303.10130 (resumen) y versión HTML https://arxiv.org/html/2303.10130 (lectura previa parcial, hasta ~100,000 de 125,671 caracteres).
- Repositorio de Eloundou et al.: https://github.com/openai/GPTs-are-GPTs (WebFetch, resumen de herramienta).
- Gmyrek, Berg, Bescond (2023), OIT WP 96: https://www.ilo.org/publications/generative-ai-and-jobs-global-analysis-potential-effects-job-quantity-and (solo cabecera y conclusión).
- OIT WP 140 (actualización): https://www.ilo.org/node/706766 (resumen del método).
- Felten, Raj, Seamans (2021), método vía fuente secundaria: https://sites.bu.edu/tpri/2021/06/02/occupational-industry-and-geographic-exposure-to-artificial-intelligence-a-novel-dataset-and-its-potential-uses (solo apareció en resultados de búsqueda; no abierta).
- Webb (2020), vía Brookings y ficha NBER de resultados de búsqueda: https://www.brookings.edu/articles/what-jobs-are-affected-by-ai/ y https://conference.nber.org/conf_papers/f123534/f123534.pdf (no abiertos).
- Awuah-Gyasi y Estrada (2025), AI-OCI: https://ojs.aaai.org/index.php/AIES/article/view/36545 (solo resumen devuelto por la búsqueda; el PDF no fue legible).
- Dominski y Lee (2025). https://arxiv.org/html/2507.08244 (resumen y comienzo).
- Hihn et al. (2025), embeddings para clasificación ocupacional alemana: https://arxiv.org/abs/2509.04942 (solo resumen; relevancia indirecta para B).
- Frey y Osborne (2013), Gmyrek et al. (2024), Ceballos y Guadarrama (2025): ver 001 §9 (no se reconsultaron).
- Archivos del proyecto leídos: ver sec. 0.
