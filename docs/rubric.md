# Rúbrica de anotación (versión 2; decisiones 001, 006 y 015)

Se anota cada tarea de O*NET (ruta O) o cada función SINCO (ruta S); en la ruta S, "tarea" se lee como "función SINCO". Esta rúbrica mide **exposición** (propiedad técnica de la tarea). No mide adopción, rentabilidad, regulación ni pérdida de empleo.

## Concepto
Exposición = grado en que un sistema de IA (modelos de lenguaje y software o herramientas construidas sobre ellos, con las capacidades documentadas en la fecha de anotación) podría ejecutar la tarea, o reducir sustancialmente el esfuerzo humano para ejecutarla, manteniendo calidad comparable. Es neutral respecto de si la IA sustituye o complementa.

## Campos por tarea
1. `exposure_class` (ordinal):
   - `E0` sin exposición: la IA actual no reduce el esfuerzo de forma material.
   - `E1` exposición con apoyo: la IA reduce sustancialmente el esfuerzo, pero un humano ejecuta, supervisa o valida el resultado.
   - `E2` exposición directa: la IA (con herramientas razonables disponibles) puede completar la tarea.
2. `physical_bottleneck` (booleano): la tarea exige presencia física o destreza manual como componente central. Se registra aparte; un cero por motivo físico no equivale a "la IA no es capaz" en sentido cognitivo.
3. `confidence`: alta, media o baja según la ambigüedad de la tarea.
4. `rationale`: texto breve para auditoría.
5. `eloundou_class` (ordinal EL0/EL1/EL2/EL3): campo independiente de `exposure_class`, anotado sobre la misma unidad. No equivale a `exposure_class`; no se convierte una escala en otra por regla. Se clasifican los dos campos de manera independiente y no se corrige uno con base en el otro.

No se admiten puntajes continuos libres del anotador.

## Clasificación `eloundou_class`
Fuente: Eloundou, Manning, Mishkin y Rock (2023), arXiv:2303.10130v5, apéndice A.1, pp. 24-26 (paginación según el conteo de saltos de página del texto extraído, a cotejar con el PDF). El texto en inglés es el normativo y se transcribe literalmente; **si la traducción difiere, prevalece el inglés**. Un prompt en español sería otra `prompt_version`. Dentro del texto literal, "E0/E1/E2/E3" son las etiquetas de Eloundou y corresponden a EL0/EL1/EL2/EL3 de este proyecto; **no** son las E0/E1/E2 de `exposure_class`.

**Contexto para el anotador (A.1, p. 24).**
- "Consider the most powerful OpenAI large language model (LLM) This model can complete many tasks that can be formulated as having text input and text output where the context for the input can be captured in 2000 words. The model also cannot draw up-to-date facts (those from <1 year ago) unless they are captured in the input."
- "Assume you are a worker with an average level of expertise in your role trying to complete the given task. You have access to the LLM as well as any other existing software or computer hardware tools mentioned in the task. You also have access to any commonly available technical tools accessible via a laptop (e.g. a microphone, speakers, etc.). You do not have access to any other physical tools or materials."
- "Please label the given task according to the taxonomy below."

**EL0, sin exposición (A.1, pp. 24-25).** "Label tasks E0 if direct access to the LLM through an interface like ChatGPT or the OpenAI playground cannot reduce the time it takes to complete this task with equivalent quality by half or more. If a task requires a high degree of human interaction (for example, in person demonstrations) then it should be classified as E0."

**EL1, exposición directa (A.1, p. 25).** "Label tasks E1 if direct access to the LLM through an interface like ChatGPT or the OpenAI playground alone can reduce the time it takes to complete the task with equivalent quality by at least half. This includes tasks that can be reduced to: - Writing and transforming text and code according to complex instructions, - Providing edits to existing text or code following specifications, - Writing code that can help perform a task that used to be done by hand, - Translating text between languages, - Summarizing medium-length documents, - Providing feedback on documents, - Answering questions about a document, or - Generating questions a user might want to ask about a document."

**EL2, exposición mediante aplicaciones basadas en LLM (A.1, p. 25).** "Label tasks E2 if having access to the LLM alone may not reduce the time it takes to complete the task by at least half, but it is easy to imagine additional software that could be developed on top of the LLM that would reduce the time it takes to complete the task by half. This software may include capabilities such as: - Summarizing documents longer than 2000 words and answering questions about those documents - Retrieving up-to-date facts from the Internet and using those facts in combination with the LLM capabilities - Searching over an organization's existing knowledge, data, or documents and retreiving information" [sic: "retreiving" en el original].

**EL3, exposición dadas capacidades de imagen (A.1, p. 25).** "Suppose you had access to both the LLM and a system that could view, caption, and create images. This system cannot take video media as inputs. This system cannot accurately retrieve very detailed information from image inputs, such as measurements of dimensions within an image. Label tasks as E3 if there is a significant reduction in the time it takes to complete the task given access to a LLM and these image capabilities: - Reading text from PDFs, - Scanning images, or - Creating or editing digital images according to instructions."

**Traducción de apoyo (del proyecto; no normativa).** E0: el acceso directo al LLM mediante una interfaz como ChatGPT no puede reducir a la mitad o más el tiempo de la tarea con calidad equivalente; si exige un alto grado de interacción humana, E0. E1: el acceso directo al LLM por sí solo reduce al menos a la mitad el tiempo con calidad equivalente (escribir y transformar texto o código, editar, escribir código que ayude a una tarea manual, traducir, resumir documentos de extensión media, dar retroalimentación, responder o generar preguntas sobre un documento). E2: el LLM solo puede no alcanzar la mitad, pero es fácil imaginar software construido sobre él que sí (resumir documentos de más de 2000 palabras, recuperar hechos actualizados de Internet, buscar en datos u documentos de una organización). E3: reducción significativa del tiempo con un LLM y capacidades de imagen (leer texto de PDF, escanear imágenes, crear o editar imágenes digitales).

**Ejemplos del apéndice.** Los cinco ejemplos de software construido sobre el LLM (A.1, p. 25) y los cinco ejemplos de anotación (A.1, pp. 25-26) no se transcriben aquí; el prompt de anotación los copia completos del PDF registrado en `data/raw/manifest.json` (id `eloundou_2023_v5_pdf`).

**Definiciones del cuerpo (§3.3, pp. 6-7).** "Calidad equivalente": un tercero, típicamente el receptor del producto, no notaría ni le importaría la ayuda del LLM (nota a, p. 7). Umbral: 50 % de reducción de tiempo. EL3 se funde con EL2 en las medidas ("we combine E2 and E3 for all analyses", nota b, p. 7); se guarda la etiqueta cruda.

**Notas de aplicación.** (1) El preámbulo describe un LLM de 2023; la versión literal permite comparar con Eloundou; actualizarlo es otra `prompt_version`. (2) La rúbrica se diseñó para tareas y DWA de O*NET; aplicarla a una función SINCO es un cambio de unidad cuyo efecto no está verificado.

## Mapa numérico (fijado en configuración, no en código)
Medida principal (`exposure_class`): E0 = 0, E1 = 0.5, E2 = 1.
Sensibilidad: límite inferior (E0 = E1 = 0, E2 = 1) y límite superior (E0 = 0, E1 = E2 = 1).
Medidas de comparación (`eloundou_class`, con EL3 contado dentro de EL2): `alfa_S` = EL1; `beta_S` = EL1 + 0.5·EL2; `cota_sup_S` = EL1 + EL2.

## Agregación (resumen; detalle en la decisión 001, sección 4.4)
Por ocupación O*NET-SOC: promedio de los puntajes de las tareas centrales con pesos iguales. Variante: incluir tareas suplementarias y ponderar por importancia/frecuencia/relevancia de O*NET. Ruta S: media de pesos iguales sobre todas las funciones del grupo. Se reportan además `share_E2` y `share_any`.

## Trazabilidad
Cada corrida registra `prompt_version`, modelo, fecha y `run_id`, además de versión de O*NET, versión de traducción y semilla/temperatura.
