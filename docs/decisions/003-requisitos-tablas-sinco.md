# 003 - Requisitos metodológicos de las tablas SINCO 2019 y estrategia de crosswalk SINCO -> CIUO-08

> **ESTADO: APROBADA POR EL USUARIO (2026-10-19)** (ver "Registro de aprobación" y "Registro 2"; sin solicitud a INEGI; Método B / SINCO -> ISCO-08 autorizado solo en principio). Son requisitos, no código (regla 7 de CLAUDE.md). Depende de la decisión 001, ya aprobada.

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de todas las fuentes: 2026-10-19
- Coordinación: agente de datos (conversión del PDF `data/raw/sinco_2019.pdf` a tablas relacionales).

## Registro de aprobación

Cita textual del usuario (2026-10-19): "Aprobado 004, 001 y 003. La solicitud de la tabla no la necesitamos ya estan las tablas del catálogo".

**Lo que se aprueba:** los requisitos de las secciones 1 a 3 (unidad de análisis a grupo unitario de 4 dígitos, campos requeridos del PDF y criterios de calidad de las tablas) y el diseño de validación descrito.

**Respuesta específica del usuario sobre INEGI:** "La solicitud de la tabla no la necesitamos, ya están las tablas del catálogo". La pregunta de esta decisión sobre pedir a INEGI la tabla SINCO-CIUO-08 (y SINCO 2011) queda **resuelta como NO necesaria por decisión del usuario**. La recomendación 1 de §4 y la pregunta 3 de §5 quedan sin efecto; no se envía solicitud.

**Matiz factual (según los reportes del agente de datos, no verificado por mí directamente):** las tablas del catálogo SINCO **no contienen correspondencia con CIUO-08, SCIAN ni O*NET**; contienen jerarquía, descripciones, ocupaciones ejemplo, funciones e incluye/excluye (`docs/diccionario_datos_sinco.md`). Consecuencias:
- El **Método A** (embeddings directos SINCO -> O*NET, decisión 005) es el que se apoya en las tablas del catálogo como insumo.
- El **Método B** (restricción por el puente ISCO-08 -> SOC 2010) requiere el eslabón SINCO -> ISCO-08, que no tiene insumo propio. Ver el Registro 2 para su autorización en principio.
- La opción 5 de §4 (puente vía SINCO 2011) pierde su vía de obtención por INEGI; no hay otra fuente consultada.

## Registro 2 (2026-10-19): aprobación de pendientes

Cita textual del usuario, en respuesta al reporte del agente de métodos: "Si, aprobar pendientes incluyendo uvicorn."

Interpretación registrada (sin ampliar): el "Si" confirma que la aprobación se extiende a las propuestas concretas de esta decisión para sus preguntas abiertas, incluida la construcción de SINCO -> ISCO-08 por mapeo semiautomático con validación humana. Cada pregunta de §5 queda con su estado (APROBADA con el valor propuesto o "requiere decisión"); ver §5. No se inventan valores donde el documento no recomienda uno.

**Método B / SINCO -> ISCO-08: autorizado solo en principio.**
- Aprobado en principio: el mapeo semiautomático (opción 2 de §4) con **doble revisión humana** (003 §4 y 005 §8.1), con validación humana obligatoria de las parejas propuestas y kappa de Cohen sobre {exacto, parcial, incorrecto} en una submuestra con doble revisión.
- **No se implementa hasta que el usuario lo pida explícitamente.** El alcance implementable sigue siendo el Método A de 005 (R.4 y R.7).
- Siguen sin valor y requieren decisión cuando se pida implementarlo: quién valida y con qué guía, texto CIUO-08 en español con licencia utilizable, y uso de LLM para reordenar candidatos.

## 0. Insumos leídos y límites de esta decisión

Leídos: `docs/decisions/001-definicion-exposicion.md`, `docs/issues/datos-2026-10-19-crosswalk-sinco-isco08-onet-bloqueado.md`, `CLAUDE.md`, `data/raw/manifest.json` (PDF SINCO sha256 `6a8a80d6...f5f6`; O*NET 31.0; BLS ISCO-08 -> SOC 2010).
No existían (al redactar) `docs/sinco_pdf_exploracion.md` ni `docs/data_dictionary.md`. **Los requisitos de la sección 2 se redactaron sin haber visto el contenido del PDF ni el parquet**: no pude abrir el PDF (sin herramienta de render/extracción) ni `sinco.parquet`. Todo lo que diga qué contiene el PDF es [NO VERIFICADO] y debe contrastarse con la exploración del agente de datos.

### Discrepancia de conteos (actualizada 2026-10-19)
El encargo indicaba que el catálogo parseado tiene **490 grupos unitarios**. Una búsqueda web (2026-10-19) que resumía una presentación del SNIEG/CESNIDS reportaba, para SINCO 2019: 9 divisiones, 53 grupos principales, 156 subgrupos y **468 grupos unitarios**, y para SINCO 2011: 9, 52, 163 y **490**. Es un resumen de buscador; el PDF de la presentación no se pudo leer (cifrado/binario).

**Actualización (según el orquestador; no verificado por mí en el PDF):** ahora hay cuatro cifras en circulación: **468** (que el orquestador atribuye a SINCO 2011), **481** y **489** (ambas del manuscrito de Ceballos y Guadarrama; ver abajo) y **490** (SINCO 2019 según el PDF de INEGI). Esto **invierte la atribución** del resumen de buscador que cité antes (468 para 2019, 490 para 2011), que por tanto queda superado y no debe usarse. Con ello la discrepancia entre 490 (parquet) y el PDF 2019 parece resuelta a favor de 490, **pendiente de que el agente de datos lo confirme contando niveles en el PDF**. Mientras tanto, este documento usa "N grupos unitarios" sin fijar el número cuando la distinción importa.

**Cifras del manuscrito de Ceballos y Guadarrama (según el orquestador):** la introducción dice que adaptan Frey y Osborne (2017) "a las 481 ocupaciones disponibles en el catálogo mexicano" y la sección 3 dice "El catálogo del SINCO se conforma de 489 ocupaciones" en nueve categorías; es una **inconsistencia interna 481 frente a 489**. El PDF cita a INEGI (2019) y no dice qué versión de SINCO usa. Ninguna de las dos cifras coincide con 468 ni con 490: qué unidad cuentan (¿grupos unitarios con exclusiones, ocupaciones del catálogo?) **[NO VERIFICADO]**. No se usan para fijar el número de grupos del proyecto.

## 1. (a) Unidad de análisis SINCO

### Pregunta
¿A qué nivel de SINCO se estima y reporta la exposición?

### Alternativas
| Alternativa | Ventaja | Problema |
|---|---|---|
| A. Grupo unitario (4 dígitos) | Es el nivel más fino con título en el catálogo; comparable en granularidad con CIUO-08 a 4 dígitos (puente natural y referencia de validación OIT); suficiente para microdatos ENOE si éstos codifican a 4 dígitos [NO VERIFICADO] | Heterogeneidad interna: cada grupo unitario agrupa varias ocupaciones reales |
| B. Subgrupo (3 dígitos) | Menos ruido de crosswalk, menos celdas vacías | Pérdida de resolución; mezcla ocupaciones muy distintas |
| C. Ocupación individual (títulos) | Máxima resolución | El catálogo no tiene títulos individuales de ocupación (según el encargo); solo existirían como "ocupaciones ejemplo" dentro de descripciones, si el PDF las trae [NO VERIFICADO] |

### Decisión propuesta
Unidad de análisis y de reporte principal: **grupo unitario de 4 dígitos**. Razones: (1) es el nivel más bajo con identificador y título oficial; (2) permite el puente a CIUO-08 a 4 dígitos, donde existen referencias externas; (3) permite agregar hacia arriba (subgrupo, grupo principal, división) por empleo. Las ocupaciones ejemplo, si existen, se usan como **evidencia de matching y de interpretación**, no como unidades de estimación. Los niveles superiores se reportan como agregados ponderados por empleo, nunca como promedios simples de códigos. Se debe reportar la heterogeneidad interna como incertidumbre (rango entre O*NET mapeadas, ver 001 §4.5), no ocultarla.

Riesgo: unidades con muy pocas O*NET mapeadas o con crosswalk débil tendrán intervalos amplios; se marcan con `crosswalk_confidence` y se permite reportar a 3 dígitos como respaldo.

## 2. (b) Campos del PDF que requiere la metodología

Todo "si existe" depende de verificación en el PDF. Prioridad: **E** esencial, **D** deseable.

| Campo (por nivel y código) | Prioridad | Uso |
|---|---|---|
| Código, nivel, título, código padre (ya en parquet) | E | Jerarquía, agregación, llaves |
| Descripción del grupo (texto de la ficha) | E | Matching semántico al crosswalk; contexto para anotar y para revisores |
| Funciones / tareas del grupo, si se listan | E | Cuando haya funciones SINCO, comparar con tareas O*NET para validar el crosswalk (similitud tarea-tarea) y detectar 1:N mal asignados. No sustituyen las tareas O*NET como insumo de anotación (001) |
| "Incluye" / ocupaciones ejemplo | E | Casi todo el matching a nivel de título pasa por aquí; mejora recuperación en 1:N |
| "Excluye" / notas de límite, con código destino si lo hay | E | Reglas de rechazo de candidatos del mapeo; define fronteras entre grupos |
| Correspondencia con CIUO-08 (columna o anexo), si existe | E | Eliminaría o reduciría el bloqueo del issue. El agente de datos reporta que **no** existe en el PDF; se pide confirmar buscando también anexos, notas al pie y texto de "comparabilidad" |
| Correspondencia con SINCO 2011 (tabla de equivalencias), si existe | D | Puente alterno: documentos o literatura que relacionen SINCO 2011 con CIUO-08 [NO VERIFICADO que existan]; también necesaria para series y para el conflicto de conteos |
| Página del PDF de cada registro y bloque de texto original | E | Trazabilidad (ver (c)) |
| Texto OCR/extracción crudo y bandera de calidad | D | Auditar errores de parseo |

Para anotación: la anotación de tareas se hace sobre tareas O*NET (001), así que los campos SINCO no entran al prompt de anotación en la medida principal. Pueden entrar en una variante (contexto mexicano) solo con decisión aparte.

## 3. (c) Criterios de calidad y validación de las tablas

Criterios mínimos que deben cumplirse y comprobarse con pruebas (pytest) antes de dar por buena la fase; si fallan, issue en `docs/issues/` y detenerse (regla 5).

1. **Cobertura de niveles**: conteo por nivel (división, grupo principal, subgrupo, grupo unitario) igual al declarado por el propio PDF/INEGI; resolver la discrepancia de conteos (ver sección 0). Sin códigos duplicados ni faltantes en la secuencia esperada.
2. **Integridad referencial**: todo padre existe y es del nivel inmediato superior; el código de 4 dígitos es consistente con el prefijo de su padre; cada hijo tiene exactamente un padre.
3. **Cobertura de contenido**: por tabla de campos de (b), porcentaje de grupos unitarios con descripción, funciones, incluye/excluye y ocupaciones ejemplo no vacíos. Umbral propuesto: 100 % para descripción; lo demás se reporta sin umbral y se investigan los vacíos (pueden ser reales, no error). Umbrales sujetos a revisión humana.
4. **Trazabilidad**: cada registro con `source_pdf_sha256` (el del manifest), página (inicio y fin), y método de extracción con versión. Las tablas derivadas se regeneran de forma determinista desde el PDF a partir de un script.
5. **Verificación independiente de una muestra**: revisión humana de una muestra aleatoria estratificada por división (tamaño a fijar; propuesta inicial: 5 % de grupos unitarios, mínimo 3 por división) comparando texto de tabla contra imagen de página. Se reporta la tasa de error y su intervalo (Wilson) [tamaño de muestra [NO VERIFICADO] como suficiente; es propuesta].
6. **Calidad de texto**: control de codificación (acentos, ñ), guiones de corte de línea, encabezados/pies de página colados, listas mal fusionadas. Pruebas automáticas de patrones sospechosos.
7. **Esquema**: tablas y tipos validados con pydantic/pyarrow; llaves primarias únicas; sin escritura en `data/raw/`.
8. **Sin cifras manuales**: cualquier conteo reportado en el artículo debe salir de `data/processed/` (regla 6).

## 4. (d) Crosswalk SINCO -> CIUO-08

### Pregunta
Dado que no hay tabla oficial SINCO 2019 -> CIUO-08 en el PDF y no se encontró otra publicada por INEGI/SNIEG (issue del agente de datos; mi búsqueda del 2026-10-19 tampoco la encontró, pero no fue exhaustiva), ¿cómo se construye el eslabón?

### Hechos consultados
- Búsqueda web 2026-10-19: no apareció una tabla oficial SINCO 2019 - CIUO-08; sí un método para Argentina (CNO -> CIUO-08) de Chávez Molina, Bernasconi y Rodríguez de la Fuente (2020), que ilustra el enfoque de mapeo por reglas y sintaxis, no consultado en detalle. https://www.aacademica.org/joserodriguez/74
- Precedente mexicano O*NET -> SINCO: Ceballos Mina y Guadarrama Gómez (2025), *Desarrollo y Sociedad* 100, DOI 10.13043/DYS.100.1. **Actualización (2026-10-19):** el usuario agregó a `data/raw` el manuscrito PDF (id `ceballos_guadarrama_2025_pdf`, sha256 `669e3c4b7ced7a2d1f428ccc28b26c07dd65e001e2af9c500c7be8ecc5510baa`, "Brechas salariales y automatización.docx.pdf"), que leyó el orquestador (no yo). **Verificado por el orquestador:** la frase sobre el emparejamiento existe textualmente: "se adaptaron los cálculos elaborados por Frey y Osborne (2017), correspondientes a ocupaciones registradas en la encuesta O*NET, emparejándolos con las ocupaciones inscritas en el SINCO. En los casos en que no se identificaron coincidencias directas entre los catálogos, se asignó la probabilidad de una ocupación similar o la media del subgrupo al que pertenecía el empleo". Pero el artículo **no describe cómo se hizo el emparejamiento** (ni manual ni automático, ni criterios, ni cobertura, ni cuántas ocupaciones por imputación, ni el crosswalk usado); la hipótesis de que era "manual" no está respaldada por el texto. Asume que las probabilidades de EE. UU. aplican a México (cita Cebreros et al. 2020 y Varela y Tavares 2023) y reconoce la limitación. Datos: ENOE 3T 2024; Oaxaca-Blinder con corrección de sesgo de selección. Es relevante como contraste de reglas: su imputación "ocupación similar / media del subgrupo" para casos sin coincidencia es una alternativa a comparar con las reglas 1:N y N:1 de esta decisión, que no imputan sino que conservan el conjunto y reportan mínimo/máximo (ver 001 §4.5). **No se modifica ninguna decisión propuesta por este precedente.** Aclaración de alcance: el artículo mide probabilidad de automatización (Frey-Osborne) y su relación con diferencias salariales, **no exposición a IA**. **Siguen [NO VERIFICADO]:** versión de SINCO usada, método exacto de emparejamiento (directo vía SOC/CIUO o por texto), cobertura (directa frente a imputada), y si la versión de la revista coincide con el manuscrito. Pendiente: nada que leer sobre el método en el manuscrito; si se quiere saber cómo emparejaron, hay que preguntar a los autores o buscar material suplementario.
- Otros estudios mexicanos que aplican Frey-Osborne a SINCO, solo por resultado de búsqueda y no leídos: Cabrero Mendoza y Guajardo Mendoza (CLAD, 2022), https://revista.clad.org/ryd/article/view/lucha-contra-desempleo-tecnologico-analisis-casos-en-mexico ; Minian y Martínez Monroy (2018), https://www.probdes.iiec.unam.mx/index.php/pde/article/download/64001/62384?inline=1 . Posibles precedentes de crosswalk O*NET/SOC -> SINCO a revisar.
- La presentación SNIEG/CESNIDS (no legible por mí) describe el proceso de actualización de SINCO 2019. https://snieg.mx/Documentos/Demografico/sesiones/doc_22019/1_presentacion_sinco_cesnids.pdf
- No verifiqué si INEGI publica la correspondencia en otro producto (p. ej., en su micrositio de clasificaciones o en documentos de la ENOE). [NO VERIFICADO]. Era la primera cosa que debía confirmarse con INEGI; el usuario decidió no solicitarla (ver Registro de aprobación).

### Alternativas
| # | Opción | Ventaja | Riesgo |
|---|---|---|---|
| 1 | Solicitar tabla a INEGI (atencion.usuarios@inegi.org.mx, ya propuesta en el issue) **[DESCARTADA por el usuario, 2026-10-19: no se solicita]** | Fuente oficial, defendible | Tiempo; puede no existir; puede ser parcial |
| 2 | Mapeo semiautomático a nivel de grupo unitario (SINCO) vs unidad CIUO-08: candidatos por similitud de texto (título + descripción + incluye/ocupaciones ejemplo vs títulos y definiciones CIUO-08), luego validación humana obligatoria **[APROBADA en principio, Registro 2; no se implementa hasta que el usuario lo pida]** | Barato, auditable, reproducible, escalable (centenas de unidades) | Calidad depende del texto; sesgo de modelos de similitud; el humano valida muchas parejas |
| 3 | Mapeo manual completo por expertos | Mayor calidad esperada | Costoso; poco reproducible; requiere experto en clasificaciones |
| 4 | Saltarse CIUO-08: SINCO -> SOC/O*NET directo por texto (es el Método A de 005) | Una sola cadena | Pierde el ancla oficial BLS ISCO->SOC y las referencias OIT por CIUO; validación más difícil |
| 5 | Puente vía SINCO 2011 si existe correspondencia SINCO 2011 -> CIUO-08 | Reusa trabajo previo | Existencia [NO VERIFICADA]; añade un salto 2011 -> 2019 y más 1:N; sin vía de obtención tras descartar la solicitud a INEGI |

### Recomendación original (estado tras los registros)
Original: seguir **1 y 2 en paralelo**: enviar la solicitud a INEGI (y a la vez preguntar por SINCO 2011) y construir el mapeo semiautomático (2) con **validación humana obligatoria**, donde el resultado de INEGI, si llega, se usa como estándar de oro para medir la calidad del mapeo semiautomático y reemplazarlo. No usar la opción 4 como principal; sí como control de sensibilidad si hay recursos.
Actualización (2026-10-19): la parte 1 queda descartada por el usuario. La parte 2 queda aprobada en principio (Registro 2), sin implementarse hasta que el usuario lo pida. Sin tabla de INEGI no hay estándar de oro externo para el mapeo; la validación depende de la muestra de oro con revisores. Por la elección del usuario de apoyarse en las tablas del catálogo, el Método A de 005 (la opción 4) es el que se implementa primero; eso lo marca el propio usuario y no lo decido aquí.

Diseño del mapeo semiautomático (descripción, no implementación):
1. **Generación de candidatos**: para cada grupo unitario SINCO, top-k (k propuesto 5, a ajustar) unidades CIUO-08 por similitud textual en español (el texto CIUO-08 en español de la OIT sería la fuente; [NO VERIFICADO] que esté disponible y su licencia). Se puede usar un LLM para reordenar candidatos, siempre registrando modelo, prompt, fecha y run_id (regla 4).
2. **Reglas estructurales como restricciones**: prioridad al encaje de grupo principal/gran grupo (la estructura de grandes grupos de CIUO-08 es la que se espera ver reflejada, aunque SINCO difiere en su lógica de agrupación [NO VERIFICADO punto por punto]); los candidatos fuera del gran grupo esperado se marcan para revisión, no se descartan automáticamente.
3. **Validación humana**: al menos un revisor por pareja propuesta; doble revisión independiente en una submuestra para medir acuerdo (kappa de Cohen sobre {exacto, parcial, incorrecto}). Los desacuerdos se resuelven por un tercero y se registran.
4. **Tipos de correspondencia** (campo `crosswalk_type`): 1:1, 1:N (un SINCO abarca varias CIUO), N:1 (varios SINCO caen en una CIUO), M:N. Atributo adicional `match_quality` ({exacto, parcial, amplio}) y `crosswalk_confidence`.
5. **Reglas de resolución de 1:N y N:1** (consistentes con 001 §4.5):
   - SINCO 1:N CIUO: se conservan todas las CIUO válidas como conjunto; el puntaje se agrega entre ellas con pesos explícitos (uniformes en el caso base; sensibilidad con pesos de empleo, p. ej. ENOE o empleo de EE. UU.), y se reporta mínimo y máximo.
   - SINCO N:1 CIUO: cada SINCO hereda el valor de la CIUO sin dividir; se marca la repetición para no inflar la muestra efectiva al calcular intervalos o correlaciones (los grupos SINCO que comparten CIUO no son independientes).
   - Parejas con `match_quality` = amplio: entran con peso menor o solo en la sensibilidad (peso a fijar por humanos).
   - Contraste con precedente (Ceballos Mina y Guadarrama Gómez, 2025; su texto dice que asignan "la probabilidad de una ocupación similar o la media del subgrupo" cuando no hay coincidencia directa, sin dar detalle): imputar la media del subgrupo cuando falta coincidencia directa. Aquí no se imputa en el caso base; si se quisiera como sensibilidad, debe marcarse como imputado y excluirse del cálculo de intervalos de confianza de unidades con coincidencia propia. Es una opción para la revisión humana, no una decisión.
6. **Eslabón posterior** CIUO-08 -> SOC 2010 (BLS, ya en `data/raw/`) -> O*NET-SOC: es 1:N y N:1 también; la acumulación de ambigüedades de dos eslabones debe propagarse (remuestreo jerárquico, 002 pendiente). Falta verificar que O*NET 31.0 use una taxonomía SOC que se relacione con SOC 2010 de forma directa; el issue menciona "O*NET-SOC 2019" y no lo he verificado. [NO VERIFICADO]

### Diseño de validación del crosswalk
- **Estándar de oro parcial**: (i) la tabla de INEGI si llega (descartada su solicitud el 2026-10-19; ya no aplica salvo que el usuario la reabra); (ii) una submuestra anotada doblemente por expertos (propuesta: ~10 % de grupos unitarios, estratificada por gran grupo CIUO esperado y por tipo 1:1/1:N/N:1).
- **Métricas**: precisión y recall del conjunto de candidatos del mapeo semiautomático contra la submuestra; proporción de aciertos en top-1 y top-k; kappa entre revisores; proporción por `match_quality`.
- **Coherencia aguas abajo**: comprobar que las unidades SINCO mapeadas a una misma CIUO tengan exposiciones coherentes; revisar casos atípicos donde el rango entre O*NET mapeadas sea grande.
- **Sensibilidad de resultados**: re-estimar la exposición por SINCO bajo mapeos alternativos (solo exactos; exactos más parciales; con pesos de empleo) y reportar cambios de rango (correlación de Spearman entre versiones, número de unidades que cambian de cuartil).
- **Incertidumbre del crosswalk en intervalos**: remuestrear parejas del crosswalk con probabilidad según `match_quality` (diseño detallado en 002).
- **Referencia externa**: los puntajes OIT por CIUO-08 (Gmyrek et al., 2023; no consultados, ver 001) solo sirven si el eslabón SINCO -> CIUO es confiable; no usar un mismo crosswalk para construir y para validar sin reconocer la circularidad. Si se usa el mismo mapeo SINCO -> CIUO en ambos lados, la validación solo evalúa la cadena CIUO -> SOC -> O*NET y la anotación, no el eslabón SINCO.

### Riesgos
1. Mapeo sesgado por vocabulario: SINCO describe ocupaciones mexicanas con términos locales; el modelo de similitud puede fallar con regionalismos.
2. Fatiga/inconsistencia de revisores humanos; mitigar con guía de criterios escrita y doble revisión de una submuestra.
3. Errores de crosswalk se confunden con ruido de anotación; separar fuentes de incertidumbre en los intervalos.
4. Dependencia de un LLM para generar candidatos: reproducibilidad (fijar versión, guardar salidas).
5. La tabla de INEGI, si llegara, podría ser a otra granularidad o a otra revisión de la CIUO (hoy no se solicita).
6. Coste de oportunidad: el bloqueo retrasa fases posteriores; el mapeo semiautomático requiere decisión humana de aprobar el método, y ésta es esa decisión.

## 5. (e) Preguntas abiertas para revisión humana (estado tras el Registro 2)

1. ¿Se confirma el grupo unitario de 4 dígitos como unidad principal? ¿Reportar a 3 dígitos como respaldo? **APROBADA** (valor propuesto en §1): grupo unitario de 4 dígitos; 3 dígitos como respaldo para unidades con crosswalk débil.
2. Discrepancia de conteos (468 / 481 / 489 / 490): ¿cuál es la cifra correcta según el PDF 2019? **Parcialmente atendida:** según el orquestador, el PDF de INEGI SINCO 2019 reporta 490 y 468 corresponde a SINCO 2011 (ver §0); 481 y 489 son del manuscrito de Ceballos y Guadarrama, con inconsistencia interna y sin versión de SINCO. **Requiere confirmación:** el agente de datos debe contar niveles en el PDF 2019.
3. ~~Solicitud a INEGI~~ **RESUELTA por el usuario: no es necesaria.**
4. ¿Se aprueba el mapeo semiautomático con validación humana (opción 2)? **APROBADA en principio** (Registro 2), no se implementa hasta que el usuario lo pida. **Requiere decisión:** quién valida (personas con conocimiento de clasificaciones) y la guía de criterios; 003 no los nombra.
5. Tamaño de la submuestra doble-revisada (propuesta 10 %) y de la de verificación de tablas (propuesta 5 %, mínimo 3 por división). **APROBADA** con esos valores propuestos.
6. ¿Se permite usar un LLM para reordenar candidatos del crosswalk? **Requiere decisión:** §4 lo permite en principio "registrando modelo, prompt, fecha y run_id" (regla 4), pero 005 (R.2) no aprueba ningún LLM ni API y recomienda no activarlo por defecto; no hay modelo concreto que aprobar.
7. ¿Pesos de parejas "amplias" y pesos 1:N? **APROBADA en lo propuesto:** uniformes en el caso base; ponderación por empleo (ENOE o EE. UU.) solo como sensibilidad; parejas "amplias" con peso menor o solo en sensibilidad. **Requiere decisión:** el peso numérico de las parejas "amplias" (§4: "a fijar por humanos") y la fuente de empleo.
8. Datos faltantes del PDF: ¿el agente de datos confirma qué campos de la sección 2 existen? **Tarea pendiente:** ya existen `docs/sinco_pdf_exploracion.md` y `docs/diccionario_datos_sinco.md`; falta cotejarlos con la sección 2.
9. ¿La taxonomía O*NET-SOC 31.0 se enlaza con SOC 2010 de manera directa? **Resuelta en lo operativo por la ingesta del agente de datos (005 R.7):** se usa el puente O*NET 2019 -> 2010 del O*NET Center (1164 filas) y de ahí SOC 2010. Qué hacer con las multiplicidades y casos fuera del puente: ver 005 R.7. No verifiqué los Parquet.
10. ¿Está el texto de CIUO-08 en español disponible y utilizable (licencia)? **Requiere decisión:** sin recomendación ni verificación.
11. ¿Alguien lee el texto completo de Ceballos Mina y Guadarrama Gómez (2025)? **Atendida en parte:** el orquestador leyó el manuscrito (ver §4); el artículo no describe el método de emparejamiento. Queda abierta la comparación con la versión de la revista y preguntar a los autores por el método, si se desea.
12. **P-B:** ¿qué se hace con el Método B (SINCO -> ISCO-08)? **APROBADA en principio** la vía semiautomática con doble revisión humana (Registro 2); **no se implementa hasta que el usuario lo pida explícitamente.**

## 6. Fuentes consultadas (2026-10-19)

- Resultado de búsqueda web sobre SINCO 2019 y CIUO-08 (resumen del buscador; cifras de niveles 468/490 de la presentación SNIEG, con atribución a año **superada** por el orquestador, ver §0): https://snieg.mx/Documentos/Demografico/sesiones/doc_22019/1_presentacion_sinco_cesnids.pdf (intento de lectura directa: PDF cifrado/binario, no legible; solo se usó el resumen del buscador).
- Documento INEGI SINCO 2019 (aparece en resultados; no leído por mí; el orquestador reporta que dice 490): https://operativos.inegi.org.mx/capacitaciones/ocupo/img\MATERIAL DE APOYO\Sistema Nacional de Clasificación de Ocupaciones, 2019 SINCO.pdf
- Chávez Molina, Bernasconi, Rodríguez de la Fuente (2020), crosswalk CNO -> CIUO-08 (Argentina): https://www.aacademica.org/joserodriguez/74 (solo resultado de búsqueda).
- Ceballos Mina, O. E. y Guadarrama Gómez, H. (2025). La automatización del empleo en México y sus efectos sobre las disparidades salariales. *Desarrollo y Sociedad*, 100. DOI 10.13043/DYS.100.1. https://revistas.uniandes.edu.co/index.php/dys/article/view/11083 (metadatos y resumen leídos); PDF de la revista https://revistas.uniandes.edu.co/index.php/dys/article/view/11083/10931 (no legible con mis herramientas). Manuscrito PDF en `data/raw` (id `ceballos_guadarrama_2025_pdf`, sha256 `669e3c4b7ced7a2d1f428ccc28b26c07dd65e001e2af9c500c7be8ecc5510baa`), leído por el orquestador, no por mí.
- Cabrero Mendoza y Guajardo Mendoza (2022), CLAD; Minian y Martínez Monroy (2018), *Problemas del Desarrollo*: URLs en la sección 4 (solo resultados de búsqueda; no leídos).
- Archivos del proyecto: `docs/decisions/001-definicion-exposicion.md`, `docs/issues/datos-2026-10-19-crosswalk-sinco-isco08-onet-bloqueado.md`, `data/raw/manifest.json`, `CLAUDE.md`.
