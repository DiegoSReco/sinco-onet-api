# 001 - Definición operativa de exposición a IA para SINCO 2019

> **ESTADO: APROBADA POR EL USUARIO (2026-10-19)** (ver "Registro de aprobación" y "Registro 2"). La modificación de `docs/rubric.md` y `docs/glossary.md` quedó autorizada por el Registro 2 y se redacta en la decisión 006 (texto pendiente de aplicar; este documento no los modifica).

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de todas las fuentes: 2026-10-19

## Registro de aprobación

Cita textual del usuario (2026-10-19): "Aprobado 004, 001 y 003. La solicitud de la tabla no la necesitamos ya estan las tablas del catálogo".

**Lo que la aprobación SÍ habilita** (tal cual el documento, sin cambios): la definición operativa de exposición de la sección 4 como base del proyecto, es decir: concepto de exposición como propiedad técnica de la tarea (4.1); unidad tarea O*NET -> O*NET-SOC -> SINCO 2019 (4.2); escala por tarea `exposure_class` E0/E1/E2 con `physical_bottleneck`, `confidence` y `rationale` (4.3); mapa principal E0 = 0, E1 = 0.5, E2 = 1 con variantes de límite inferior y superior (4.3); agregación a O*NET-SOC con tareas centrales y pesos iguales, más `share_E2` y `share_any` (4.4); reglas de agregación a SINCO para 1:1, 1:N y N:1/M:N (4.5); separación de exposición y pérdida de empleo (4.6); y los campos del esquema de la sección 7 como base de implementación. Con ello queda autorizado diseñar e implementar el esquema de anotación y los scripts que dependan de esta definición, sujeto a las demás reglas de CLAUDE.md.

**Lo que NO se desprendía de esa primera aprobación:** modificar `docs/rubric.md` y `docs/glossary.md`, las preguntas abiertas no respondidas y los elementos **[NO VERIFICADO]** (que siguen sin verificar). Ver el Registro 2 para lo que cambió después.

## Registro 2 (2026-10-19): aprobación de pendientes

Cita textual del usuario, en respuesta al reporte del agente de métodos: "Si, aprobar pendientes incluyendo uvicorn."

Interpretación registrada (sin ampliar): el "Si" confirma que la aprobación se extiende a las propuestas concretas de esta decisión para sus preguntas abiertas, incluida la modificación de `docs/rubric.md` y `docs/glossary.md`.
- **Regla 2 de CLAUDE.md:** la aprobación de 001 más esta respuesta constituyen la decisión registrada que la regla exige para modificar `docs/rubric.md` y `docs/glossary.md`. El texto exacto propuesto está en `docs/decisions/006-cambios-rubrica-glosario.md` (estado: aprobada en principio, pendiente de aplicar). Este documento no modifica esos archivos.
- Cada pregunta abierta de la sección 10 queda registrada con su estado: APROBADA con el valor propuesto en el documento, o "requiere decisión" cuando el documento no contiene recomendación concreta (no se inventan valores). Ver la sección 10.
- Los **[NO VERIFICADO]** siguen sin verificar; la aprobación no los verifica.
- Esta decisión sigue distinguiendo exposición de la probabilidad de automatización de Frey-Osborne; el uso de esta última como variable comparativa se rige por 005 (sección R).

## 1. Pregunta

¿Qué significa operativamente "exposición a IA" de una ocupación SINCO 2019, medida a partir de tareas de O*NET traducidas al español, de modo que sea reproducible, separable de "pérdida de empleo" y validable?

## 2. Contexto

- El proyecto estima exposición, no pérdida de empleo. Los escenarios de pérdida van aparte y con supuestos explícitos (CLAUDE.md).
- El borrador `docs/rubric.md` puntúa cada tarea de 0 a 1 (0 = requiere presencia física/destreza manual; 0.5 = la IA apoya y el humano ejecuta o valida; 1 = la IA ejecuta la tarea completa) y registra confianza alta/media/baja. El borrador `docs/glossary.md` define exposición como "fracción de tareas de una ocupación que un sistema de IA puede ejecutar".
- Observación sobre los borradores (no se modifican aquí): (a) el glosario habla de una *fracción de tareas* (conteo binario), mientras la rúbrica produce un puntaje gradual; hay que elegir una sola definición; (b) la rúbrica ancla el 0 en un motivo (físico) y el 0.5 en otro (apoyo con validación humana), por lo que mezcla dos ejes (capacidad técnica y rol humano). Cualquier cambio requiere una decisión posterior registrada (ver decisión 006).
- Cadena de datos prevista: tareas O*NET (inglés) -> traducción -> anotación -> agregación a O*NET-SOC -> crosswalk -> SINCO 2019.

## 3. Resumen de literatura

Solo se resume lo que se consultó el 2026-10-19 (resúmenes/páginas de resultados, no siempre el texto completo). Lo no verificado está marcado **[NO VERIFICADO]**.

### 3.1 Frey y Osborne (2013)
- Qué mide: probabilidad de "computarización" de 702 ocupaciones detalladas de EE. UU., estimada con un clasificador de procesos gaussianos; concluyen que alrededor de 47 % del empleo total de EE. UU. está "en riesgo"; salarios y escolaridad se relacionan negativamente con esa probabilidad. (Oxford Martin School, página de la publicación; búsqueda web.)
- Unidad: la ocupación completa, no la tarea. Es una medida de *automatización/sustitución* (riesgo), no de exposición neutral.
- Limitaciones señaladas en fuente consultada: la crítica de Arntz, Gregory y Zierahn (OCDE, 2018) sostiene que el enfoque supone que se automatizan ocupaciones enteras y no tareas, y reporta ~9 % para EE. UU. Esto se obtuvo de un artículo periodístico en español (El Economista, Argentina) vía búsqueda; **[NO VERIFICADO]** contra el documento de la OCDE.
- Discrepancias a resolver antes de citar: la página de Oxford Martin indica fecha 1 de septiembre de 2013; otra fuente de la búsqueda, 17 de septiembre de 2013. Tampoco se verificó el procedimiento de etiquetado de entrenamiento ni los "cuellos de botella" de ingeniería (**[NO VERIFICADO]**: no aparecen en la página consultada). No se verificó la versión publicada en revista.

### 3.2 Felten, Raj y Seamans (AIOE)
- Qué mide: el *AI Occupational Exposure* (AIOE), medida de exposición ocupacional a IA; derivan además una exposición industrial (AIIE) y geográfica por condado (AIGE). Publicado en *Strategic Management Journal* 42(12): 2195-2217, diciembre de 2021 (registro de Princeton y búsqueda web).
- Del resumen consultado no se obtuvo el método detallado. De memoria, se construye cruzando aplicaciones de IA (p. ej., datos de EFF) con habilidades/capacidades de O*NET: **[NO VERIFICADO]**, confirmar en el texto.
- Limitación relevante (a confirmar): es una medida ocupacional agregada, sin granularidad de tarea y sin distinguir sustitución de complementariedad **[NO VERIFICADO]**.
- Nota: un intento de recuperar el artículo en arXiv devolvió un documento distinto (el identificador era erróneo); no se usó.

### 3.3 Eloundou, Manning, Mishkin y Rock (2023), "GPTs are GPTs"
- Qué mide: alineación de ocupaciones y tareas con las capacidades de los LLM, usando una rúbrica que combina anotación humana y clasificación con GPT-4; distingue LLM solo frente a software impulsado por LLM. Cifras del resumen (arXiv 2303.10130): ~80 % de la fuerza laboral de EE. UU. podría tener al menos 10 % de sus tareas afectadas; ~19 % al menos 50 % de sus tareas; ~15 % de las tareas podrían hacerse significativamente más rápido con igual calidad con acceso a un LLM, y 47-56 % si se incluye software/herramientas.
- La definición formal de "exposición" no aparece en el resumen consultado. De memoria, la rúbrica usa categorías E0 (sin exposición), E1 (exposición directa: el LLM reduce ≥ 50 % el tiempo de la tarea), E2 (exposición con herramientas adicionales) y las agregaciones alfa (E1), beta (E1 + 0.5·E2) y gamma (E1 + E2): **[NO VERIFICADO]**, confirmar en el texto completo antes de adoptar nombres o umbrales.
- Es el antecedente metodológico más cercano a este proyecto (tarea -> ocupación, anotación con LLM + humanos). Limitación: el criterio es "reducción de tiempo con igual calidad", que no implica adopción ni sustitución.

### 3.4 Webb (2020)
- Qué mide: exposición por traslape textual entre descripciones de tareas O*NET y textos de patentes (software, robots industriales, IA). Con tecnologías previas, mayor exposición se asoció con caídas de empleo y salario; para IA, las ocupaciones de salario alto y no rutinarias aparecen más expuestas. Webb advierte que la medida no predice si el efecto será positivo o negativo. (SSRN 3482150, nov. 2019; resúmenes secundarios.)
- Limitación: depende de que el texto de patentes refleje capacidad real; es retrospectivo respecto de patentes. Detalles de método **[NO VERIFICADO]** más allá del resumen. Este documento se cita como "Webb (2020)" por la convención del encargo; la ficha consultada es el borrador SSRN de 2019, confirmar la referencia final.

### 3.5 América Latina
- Gmyrek, Winkler y Garganta (Banco Mundial, Policy Research WP 10863, julio 2024), "Buffer or Bottleneck?": exposición a IA generativa en empleo de América Latina con encuestas armonizadas de hogares; ajustan por brecha digital; el resumen reporta que los empleos de mayor educación, formales, mejor remunerados y urbanos muestran mayor exposición, y que cerca de la mitad de los empleos con potencial de aumento están limitados por falta de uso de tecnologías digitales. Se consultó solo el resumen; no se verificó si incluye México por separado.
- Gmyrek, Berg y Bescond (OIT, WP 96, agosto 2023), puntajes por ocupación CIUO-08 a 4 dígitos, accesibles en un repositorio del Banco Mundial. **No se consultaron sus cifras ni su metodología**; son una referencia externa candidata de validación (ver sección 8) y un puente natural CIUO-08 -> SINCO.
- Ceballos Mina y Guadarrama Gómez (2025), "La automatización del empleo en México y sus efectos sobre las disparidades salariales", *Desarrollo y Sociedad* núm. 100, DOI 10.13043/DYS.100.1 (metadatos y resumen verificados en la página del artículo, 2026-10-19). Según ese resumen: usan la ENOE 2024 y una descomposición Oaxaca-Blinder con corrección por sesgo de selección; encuentran efectos negativos de la automatización sobre los sueldos, sobre todo para trabajadores menos calificados. **Mide probabilidad/riesgo de automatización (adaptación de Frey y Osborne), no exposición a IA**, y su variable de resultado es salarial. Según la cita aportada por el usuario (no verificada), adaptan las probabilidades de Frey-Osborne a SINCO emparejando ocupaciones O*NET con las del SINCO y, sin coincidencia directa, asignan la de una ocupación similar o la media del subgrupo. **[NO VERIFICADO]**: el texto completo (PDF) no pudo leerse (la herramienta devolvió el PDF sin texto legible y no hay lector instalado), por lo que no se confirmaron las citas textuales, la versión de SINCO (2011 o 2019), el año de Frey-Osborne que citan (el usuario indica 2017), el detalle del emparejamiento ni su cobertura. Nota de autoría: el encargo mencionaba solo a Owen Eli Ceballos; la página lista también a Humberto Guadarrama Gómez (ambos UAM-Azcapotzalco). Uso en este proyecto: antecedente mexicano de crosswalk O*NET -> SINCO (ver 003) y referencia contextual; no sustituye la definición de exposición propuesta aquí.
- Otros estudios mexicanos hallados en una búsqueda web (2026-10-19), solo por resultado de búsqueda y **no leídos**: Cabrero Mendoza y Guajardo Mendoza (CLAD, 2022), Frey-Osborne aplicado a SINCO; Minian y Martínez Monroy (*Problemas del Desarrollo*, 2018). URLs en sección 9. Son candidatos a revisar como precedentes de crosswalk a SINCO.
- No se encontró ni se consultó literatura específica sobre SINCO 2019 con exposición a IA. Pendiente de búsqueda.

## 4. Definición operativa propuesta

### 4.1 Concepto
**Exposición** = grado en que un sistema de IA (modelos de lenguaje y software/herramientas construidas sobre ellos, con capacidades actuales documentadas en la fecha de anotación) podría ejecutar una tarea, o reducir sustancialmente el esfuerzo humano para ejecutarla, manteniendo calidad comparable. Es una propiedad técnica de la *tarea*. **No** implica adopción, rentabilidad, regulación, ni destrucción de empleo. Es neutral respecto a si la IA sustituye o complementa.

### 4.2 Unidad de análisis
Tarea O*NET -> ocupación O*NET-SOC -> ocupación SINCO 2019 (a 4 dígitos, o el nivel en que el crosswalk lo permita; decisión abierta, ver sección 10).

### 4.3 Escala de anotación por tarea
Se propone separar los ejes que el borrador mezcla. Cada anotación incluye:

1. `exposure_class` (ordinal, 3 categorías):
   - `E0` sin exposición: la IA actual no reduce el esfuerzo de forma material.
   - `E1` exposición con apoyo: la IA reduce sustancialmente el esfuerzo, pero un humano ejecuta, supervisa o valida el resultado.
   - `E2` exposición directa: la IA (con herramientas razonables disponibles) puede completar la tarea.
2. `physical_bottleneck` (booleano): la tarea exige presencia física o destreza manual como componente central. Se registra aparte para que el cero físico no se confunda con "la IA no es capaz" en el sentido cognitivo, y para poder reportar variantes con/sin software.
3. `confidence` (alta/media/baja) según ambigüedad de la tarea (heredado de la rúbrica).
4. `rationale` breve (texto), para auditoría.

Mapa numérico a puntaje de tarea `e_t` en [0, 1], parametrizado y fijado en configuración, no en código: **E0 = 0, E1 = 0.5, E2 = 1** como medida principal (coincide con los anclajes 0 / 0.5 / 1 del borrador). Variantes de sensibilidad: "límite inferior" (E0 = E1 = 0, E2 = 1) y "límite superior" (E0 = 0, E1 = E2 = 1). La relación con el estilo alfa/beta/gamma de Eloundou et al. es conceptual; no se afirma equivalencia.

Se descartan puntajes continuos libres (p. ej., 0.37) del anotador: son poco reproducibles entre corridas. Las categorías facilitan medidas de acuerdo (kappa ponderado, alfa de Krippendorff ordinal).

### 4.4 Agregación a ocupación O*NET-SOC
`E_o = sum_t(w_t * e_t) / sum_t(w_t)`.
- Ponderación principal: pesos iguales entre tareas **centrales** (core) de O*NET. Las tareas suplementarias se excluyen de la medida principal y se incluyen en una variante.
- Variante: ponderar por importancia/relevancia/frecuencia de tarea de O*NET, si están disponibles para cada tarea **[NO VERIFICADO]**: confirmar los campos disponibles en la versión de O*NET que se ingeste (se debe registrar versión y hash en `data/raw/manifest.json`).
- Se reportan además: `share_E2` (proporción de tareas con E2) y `share_any` (E1 o E2), para conectar con la lectura "fracción de tareas" del glosario.

### 4.5 Agregación a SINCO 2019 vía crosswalk
Cadena propuesta: O*NET-SOC -> SOC -> CIUO-08 -> SINCO 2019. Existencia y forma de los archivos de correspondencia (INEGI, BLS, OIT) **no fue verificada** en esta consulta. (Ver 003 y 005: el enlace SINCO -> O*NET se hace por el Método A de 005, directo, sin pasar por CIUO-08.)
- Correspondencia 1:1: se hereda `E_o`.
- Correspondencia 1:N (un SINCO con varias O*NET): el conjunto de tareas de SINCO es la unión de tareas de las O*NET mapeadas (sin deduplicar ocupaciones, con deduplicación textual opcional) y se promedia con pesos de crosswalk; si no hay pesos, pesos uniformes entre ocupaciones O*NET, y como sensibilidad ponderar por empleo de EE. UU. Se reportan además mínimo y máximo de `E_o` entre las ocupaciones mapeadas como cota de la ambigüedad del crosswalk.
- Correspondencia N:1 o M:N (una O*NET alimenta varios SINCO): se asigna la misma `E_o` a cada SINCO destino, sin dividir, y se marca la fila con `crosswalk_type`.
- Cada fila SINCO conserva `n_onet_mapped`, `crosswalk_type` y `crosswalk_confidence` para no ocultar la incertidumbre.
- El diseño estadístico detallado (acuerdo entre corridas, intervalos, remuestreo sobre tareas y sobre el crosswalk) se desarrolla en una decisión separada (002, por escribir).

### 4.6 Exposición frente a automatización y complementariedad
- El resultado principal es **exposición**. `E1` captura complementariedad potencial; `E2` captura sustitución técnica potencial de la tarea, no del puesto.
- Se prohíbe llamar a E_o "riesgo de pérdida de empleo". Las ocupaciones con exposición alta pueden ver aumento de productividad, cambio de tareas o nada, según la adopción (Webb advierte que la exposición no indica dirección).
- Escenarios de pérdida: etapa posterior, aparte, con supuestos explícitos (adopción, elasticidad, reasignación de tareas), nunca derivados mecánicamente de `E_o`.

### 4.7 Ponderaciones por empleo
- La exposición por ocupación es independiente del empleo. Para agregados (por sector, región, sexo) se ponderará con microdatos de INEGI (se prevé la ENOE; **no consultada** aquí), usando el factor de expansión. Las cifras agregadas se calculan por script en `src/` (regla 1).

### 4.8 Trazabilidad
Cada corrida registra `prompt_version`, modelo, fecha y `run_id` (regla 4), además de versión de O*NET, versión de traducción y semilla/temperatura.

## 5. Alternativas consideradas

| Alternativa | Ventaja | Por qué no es la principal |
|---|---|---|
| A. Probabilidad de computarización por ocupación (Frey-Osborne) | Simple, conocida | Unidad ocupación completa; mide automatización; entrenamiento con etiquetas pequeñas; crítica por ignorar la heterogeneidad de tareas |
| B. Cruce de habilidades O*NET con aplicaciones de IA (AIOE) | Replicable, sin anotación por tarea | Sin granularidad de tarea; no capta IA generativa actual **[a confirmar]**; no distingue complementariedad |
| C. Traslape textual con patentes (Webb) | Medida independiente de juicio | Depende de patentes y de coincidencia léxica; difícil con tareas traducidas |
| D. Anotación por tarea con LLM + humanos (Eloundou) **[propuesta]** | Granular, auditable, actualizable, comparable | Sensible a prompt/modelo; requiere medir consistencia y validar |
| E. Puntaje continuo 0-1 libre | Más resolución aparente | Baja reproducibilidad entre corridas |
| F. Binario (fracción de tareas ejecutables) | Coincide con el glosario | Pierde la complementariedad; muy sensible al umbral |
| G. Tomar puntajes de OIT por CIUO-08 y mapear a SINCO | Barato, ya existe | No es propio, no controla la anotación; mejor como validación externa |

## 6. Riesgos y limitaciones específicos para México

1. **Transferibilidad de tareas O*NET**: describen ocupaciones de EE. UU.; el contenido real del trabajo en México (más manual, menos digitalizado, otras herramientas) difiere. La exposición medida es *técnica*, no del puesto mexicano concreto. Mitigación: nombrar la medida "exposición potencial según contenido de tareas O*NET" y evitar generalizar.
2. **Informalidad**: gran parte del empleo en México es informal (cifra no verificada aquí; consultar ENOE/INEGI antes de citar). La literatura regional reporta que el empleo formal y urbano aparece más expuesto y que la brecha digital frena el aprovechamiento (Gmyrek et al., 2024, solo resumen). La exposición técnica sobrestima el impacto efectivo en ocupaciones con baja adopción digital.
3. **Crosswalk O*NET-SOC -> SINCO**: SINCO 2019 y CIUO-08 no son 1:1 con SOC; las ocupaciones mexicanas con descripciones amplias agrupan tareas distintas. Riesgo de ruido y de heterogeneidad intra-ocupación. No se verificó la existencia de una tabla oficial SINCO-CIUO; hay que localizar y registrar la fuente.
4. **Traducción**: errores o cambios de matiz al traducir tareas alteran la anotación. Mitigación: anotar sobre inglés original y español en una submuestra, y reportar discrepancia.
5. **Dependencia del modelo y de la fecha**: la capacidad de la IA cambia; el puntaje está fechado. Reportar `model`, fecha y `prompt_version`.
6. **Sesgo del anotador LLM**: puede sobre-calificar tareas cognitivas y subestimar contexto físico y social. Mitigación: `physical_bottleneck`, submuestra humana, validación externa.
7. **Interpretación pública**: riesgo de que "exposición" se lea como "desempleo". Mitigación: lenguaje en glosario y en el artículo; escenarios aparte.

## 7. Implicaciones para el esquema de anotación (pydantic, a implementar tras aprobación)

Campos mínimos por registro: `run_id`, `prompt_version`, `model`, `run_date`, `onet_soc`, `task_id`, `task_text_en`, `task_text_es`, `exposure_class` (E0/E1/E2), `physical_bottleneck`, `confidence`, `rationale`, `task_type` (core/supplemental). Validaciones: clases en el conjunto permitido; un registro por (`run_id`, `task_id`). Si un entregable no cumple el esquema, se escribe un issue en `docs/issues/` y se detiene el proceso (regla 5). El esquema no se implementa aquí.

## 8. Implicaciones para la validación (a detallar en decisión posterior)

- Convergente: correlación de rango (Spearman) de `E_o` con AIOE, con Webb y con Frey-Osborne (esta última como medida de automatización, se espera correlación imperfecta) a nivel de ocupación mapeada; y con los puntajes de OIT por CIUO-08 (Gmyrek et al. 2023). Requiere crosswalk y por lo tanto hereda su ruido.
- Interna: acuerdo entre corridas (kappa ponderado / alfa de Krippendorff ordinal), por modelo, por temperatura y por versión de prompt.
- Humana: submuestra anotada por personas, estratificada por ocupación y por confianza, con acuerdo humano-LLM.
- Sensibilidad: mapas numéricos alternativos (límite inferior/superior), pesos por importancia, tratamiento del crosswalk.
- Regla de reporte: las asociaciones con salario o educación se presentan como descriptivas.

## 9. Fuentes consultadas (2026-10-19)

- Eloundou, Manning, Mishkin, Rock (2023). GPTs are GPTs. https://arxiv.org/abs/2303.10130 (solo resumen).
- Frey y Osborne (2013). The Future of Employment. https://www.oxfordmartin.ox.ac.uk/publications/the-future-of-employment (página de la publicación; resumen). Resultados de búsqueda adicionales: https://www.oxfordmartin.ox.ac.uk/downloads/academic/The_Future_of_Employment.pdf/?t=230123x2 (no abierto).
- Crítica de Arntz, Gregory, Zierahn vía nota periodística: https://eleconomista.com.ar/economia/el-mito-desempleo-tecnologico-n5828 (solo resultado de búsqueda; secundaria).
- Felten, Raj, Seamans (2021), SMJ 42(12): 2195-2217. https://collaborate.princeton.edu/en/publications/occupational-industry-and-geographic-exposure-to-artificial-intel/ (registro bibliográfico; método no consultado).
- Webb (2019/2020). https://papers.ssrn.com/abstract=3482150 (ficha SSRN, vía resultado de búsqueda; resúmenes secundarios en getAbstract).
- Gmyrek, Winkler, Garganta (2024). https://webapps.ilo.org/static/english/intserv/working-papers/wp121/index.html (resultado de búsqueda; resumen) y repositorio https://reproducibility.worldbank.org/catalog/168 (no abierto).
- Gmyrek, Berg, Bescond (2023), OIT WP 96: ver https://www.ilo.org/media/583436/download (resultado de búsqueda, no abierto).
- Ceballos Mina, O. E. y Guadarrama Gómez, H. (2025). La automatización del empleo en México y sus efectos sobre las disparidades salariales. *Desarrollo y Sociedad*, 100. DOI 10.13043/DYS.100.1. Página: https://revistas.uniandes.edu.co/index.php/dys/article/view/11083 (metadatos y resumen leídos); PDF: https://revistas.uniandes.edu.co/index.php/dys/article/view/11083/10931 (descargado, no legible con las herramientas disponibles; texto completo **no leído**).
- Cabrero Mendoza y Guajardo Mendoza (2022), CLAD: https://revista.clad.org/ryd/article/view/lucha-contra-desempleo-tecnologico-analisis-casos-en-mexico (solo resultado de búsqueda; no leído).
- Minian y Martínez Monroy (2018), *Problemas del Desarrollo*: https://www.probdes.iiec.unam.mx/index.php/pde/article/download/64001/62384?inline=1 (solo resultado de búsqueda; no leído).

Nota de verificación: el intento de abrir https://arxiv.org/abs/2106.12040 (supuesto AIOE) devolvió un artículo no relacionado; no se usó.

## 10. Preguntas abiertas para la revisión humana (estado tras el Registro 2)

1. ¿Se aprueba separar `exposure_class` (E0/E1/E2) de `physical_bottleneck`, y modificar `rubric.md` y `glossary.md`? **APROBADA** (valor propuesto: separar los ejes). El texto exacto está en la decisión 006, pendiente de aplicar.
2. ¿El mapa E0/E1/E2 -> 0/0.5/1 es aceptable como medida principal, o se prefiere "fracción de tareas E2"? **APROBADA** (valor propuesto en 4.3): mapa 0 / 0.5 / 1 como medida principal; `share_E2` y `share_any` se reportan además.
3. ¿Qué sistema de IA define la frontera (LLM solos, LLM con herramientas, IA general)? ¿Con qué fecha de corte de capacidades? **APROBADA en lo que el documento propone** (4.1): modelos de lenguaje y software/herramientas construidas sobre ellos, con capacidades documentadas en la fecha de anotación (la fecha se registra por corrida). **Requiere decisión:** la fecha de corte concreta y la versión del modelo anotador; 001 no las fija.
4. ¿Solo tareas centrales, o también suplementarias? ¿Se acepta ponderar por importancia como variante? **APROBADA** (4.4): medida principal con tareas centrales y pesos iguales; suplementarias e importancia/frecuencia/relevancia como variantes.
5. ¿Nivel de agregación SINCO? ¿Qué fuente oficial de crosswalk? **APROBADA en lo propuesto:** grupo unitario de 4 dígitos (003 §1). Fuente de crosswalk: el usuario decidió no solicitar tabla a INEGI; el enlace SINCO -> O*NET se hace por el Método A de 005 con las tablas del catálogo. Una fuente oficial de crosswalk **no existe** y no se inventa.
6. ¿Pesos del crosswalk 1:N: uniformes, por empleo de EE. UU. o por empleo en México (ENOE)? **APROBADA** (4.5): pesos de crosswalk si existen; si no, uniformes; ponderación por empleo de EE. UU. como sensibilidad. La fuente de empleo (OEWS u otra) **requiere decisión** (no verificada); la ENOE como ponderación solo para agregados (4.7).
7. ¿Se incluye un ajuste por brecha digital/informalidad como medida secundaria, o solo como escenario? **Requiere decisión:** 001 no tiene recomendación concreta (solo menciona el riesgo).
8. ¿Se usan los puntajes de OIT/Banco Mundial como referencia externa principal de validación? **APROBADA en parte:** se usan como una de las referencias convergentes (sección 8, junto con AIOE, Webb y Frey-Osborne). **Requiere decisión:** si son la referencia "principal" (001 no lo recomienda) y la consulta de sus cifras y metodología, que no se hizo.
9. Referencias a completar. **Tarea humana, sin valor que aprobar;** sigue abierta.
10. Decisión 002 (diseño estadístico: acuerdo entre corridas, intervalos, remuestreo) por redactar. **Requiere decisión:** 001 no contiene un diseño concreto más allá de kappa ponderado / alfa de Krippendorff ordinal y la sensibilidad de la sección 8. (Nota: el número 002 lo usó el agente de datos para la decisión de stack; este diseño necesitará otro número.)
