# 005 - Emparejamiento SINCO 2019 -> SOC/O*NET con embeddings, para asignar probabilidades de Frey y Osborne

> **ESTADO: APROBADA POR EL USUARIO (2026-10-19), implementación autorizada** en el alcance de las secciones R.1 a R.8 (aprobación global en R.7; aprobación de pendientes en R.8). Lo que R.7 y R.8 marcan como "requiere decisión" sigue pendiente de revisión humana. Depende de 001 y 003, aprobadas el 2026-10-19 (ver R.6 y R.8). El número 004 lo usa el agente de datos (despliegue de la API; aprobada, opción A). El número 006 contiene los cambios propuestos a la rúbrica y el glosario.
> Nota histórica: al redactarse (propuesta del agente de métodos) no se había instalado nada, ejecutado ningún modelo ni calculado ninguna cifra (reglas 1 y 7 de CLAUDE.md). Esa situación se mantiene hasta que se implemente.

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de todas las fuentes: 2026-10-19

## R. Registro de aprobación

Cita textual del usuario (2026-10-19): "Apruebo. Recuerda las tablas relaciones es para utilizarlas construye el método de embeddingss en R o python para asignar la probabilidad. Es verdad no estamos explorando probabilidad si no exposición pero en esta etapa tendremos ese score y despues lo compararemos con exposición."

### R.1 Lo que SÍ se desprende de la respuesta
(a) **Se aprueba construir el método de emparejamiento con embeddings** (SINCO 2019 -> O*NET-SOC -> probabilidad), en R o Python a elección del implementador. CLAUDE.md fija Python tras la ingesta; el insumo de datos ya está en R en `src/ingest/` con intercambio por Parquet (decisión 002). Lo razonable es Python para embeddings, leyendo los Parquet.
(b) **Resuelve la pregunta P1.** Las probabilidades de Frey y Osborne se usarán en esta etapa como score/variable comparativa, para compararlas después con la exposición del proyecto (decisión 001). Deben nombrarse siempre "probabilidad de automatización (Frey-Osborne)"; nunca "exposición" ni "riesgo de pérdida de empleo". (Esto armoniza la etiqueta de §8.4, que decía "probabilidad de computarización ... trasladada a SINCO 2019"; se conserva esa descripción larga en el metadato y se usa la etiqueta corta aquí indicada en tablas y texto.) La exposición sigue siendo el resultado principal.
(c) **Las tablas relacionales de SINCO se usan como insumo** (según mi lectura de "las tablas relaciones es para utilizarlas": las tablas Parquet relacionales de SINCO descritas en `docs/diccionario_datos_sinco.md`: `sinco`, `sinco_descripcion`, `sinco_ocupaciones_ejemplo`, `sinco_funciones`, `sinco_incluye_excluye`, y las de O*NET). Ver ambigüedad A1 abajo.

### R.2 Dependencias nuevas aprobadas por esa respuesta (lista cerrada)
Solo las que 005 §10 listó para embeddings y que se consideran cubiertas por el "Apruebo":
1. `sentence-transformers` o `FlagEmbedding` (uno de los dos, a elección del implementador), con sus dependencias transitivas (`torch`, `transformers`).
2. `scikit-learn`.
3. `scipy`.
4. Descarga de los pesos de los modelos candidatos de §5.3 (BAAI/bge-m3, intfloat/multilingual-e5-large) desde Hugging Face, fijando revisión (commit) exacta.

Quedan **fuera** (no aprobadas): APIs de pago (embeddings o LLM), rerank con LLM (P13), `statsmodels`, `faiss`, cualquier otro paquete. Cualquier adición exige nueva decisión. Descargas de datos nuevos (tabla FO, crosswalk O*NET 2010<->2019, texto ISCO-08) siguen requiriendo hash en `data/raw/manifest.json` (regla 3) y no están autorizadas por la respuesta (ver R.3). (La tabla FO y el puente O*NET 2019 -> 2010 ya se ingestaron por el agente de datos; ver R.7. El texto ISCO-08 no.) (`uvicorn` fue aprobado en 004, Registro 2; no es una dependencia de este método.)

**Registro obligatorio por corrida (regla 4):** `run_id`, modelo (nombre), revisión/commit del modelo, fecha, `text_template_version`, `seed`, normalización, truncamiento, versiones de librerías y dispositivo/dtype, y hash de la matriz de vectores (§4.3). Sin estos campos la corrida no es válida. Los parámetros (k, delta, tau, umbrales, B) viven en un archivo de configuración versionado, no en el código.

### R.3 Lo que NO quedó resuelto por la primera respuesta y estaba PENDIENTE DE REVISIÓN HUMANA
(Estado original. Las respuestas posteriores cubren varios de estos puntos; ver R.7 y R.8 para el estado vigente de cada uno.)
- P6: A como método principal vs ambos (A y B). Ver R.6 sobre el efecto de no solicitar la tabla a INEGI.
- P9: tamaño y composición de la muestra de oro, revisores, umbral de kappa; y el nivel de los umbrales (cosenos, delta, tau, margen), que dependen de la muestra de oro.
- P2: lectura de la metodología de Ceballos y Guadarrama (2025).
- P4: obtención y versión SOC de la tabla de Frey-Osborne en formato de datos. Sin ella no hay probabilidad que asignar.
- P5: crosswalk O*NET-SOC 2019 -> 2010 (archivo y versión).
- P7: texto ISCO-08 en español y licencia.
- P10: ponderación (softmax / uniforme / empleo de EE. UU.).
- P11: residuales (NA vs imputación marcada).
- P12: conciliar 490 / 468 / 489 grupos.
- P13: LLM como reranker (no aprobado).
- Embeddings por API (no aprobados; ver R.2).
- La resolución de P8 es parcial: se aprueban modelos locales y dependencias de R.2; no APIs.
- (P3, solicitud a INEGI, ya no está pendiente: resuelta por el usuario; ver R.6.)

### R.4 Alcance mínimo implementable sin esas respuestas
1. **Solo Método A** (§5), variante A1 (español contra inglés), como primer paso. Se implementa **la recuperación** SINCO -> O*NET-SOC (matriz de similitud, top-k, margen, banderas, `match_status`), que no requiere la tabla FO ni el puente 2019 -> 2010.
2. Modelos: BGE-M3 y multilingual-e5-large, ambos locales, comparados; elección definitiva tras la muestra de oro.
3. Parámetros (k = 10, delta, tau, umbrales de baja confianza) en **configuración**, con valores iniciales marcados "provisional, sin calibrar".
4. **Todos los resultados se marcan `validado = FALSE` / "NO validado"** y así deben rotularse en cualquier salida, hasta pasar la muestra de oro (§8). No se publican cifras del artículo con ellos (regla 6).
5. La asignación de `p_FO` (§5.7) queda **condicionada** a P4 y P5: el código puede dejarse listo, pero no se ejecuta hasta que existan la tabla FO y el puente, ambos con hash en el manifest. Si no se consiguen, se escribe un issue en `docs/issues/` y se detiene esa parte (regla 5). (Condición cumplida por la ingesta descrita en R.7; la asignación de `p_FO` puede ejecutarse, marcada NO validada.)
6. **Método B queda bloqueado** por la falta del eslabón SINCO -> ISCO-08 (issue de datos; 003). No se implementa. (R.8: autorizado solo en principio; sigue sin implementarse hasta que el usuario lo pida explícitamente.)
7. El emparejamiento puede escribir `data/processed/crosswalk.parquet` con el esquema de 004 (fuente declarada, `estado_validacion = sin_validar`, `run_id`), sin columnas de score.
8. Las salidas conservan candidatos, similitudes y rangos (§4.2); nada se descarta en silencio.

### R.5 Ambigüedades detectadas
- A1: "las tablas relaciones" podría referirse a las tablas relacionales de SINCO (mi lectura), o también a las de O*NET o a una tabla de correspondencia (BLS ISCO-08 -> SOC). Esta última solo sería usable en B (bloqueado) o como control posterior (§5.5).
- A2: "R o python": no se fija; se propone Python por CLAUDE.md. El implementador debe registrar la elección.
- A3: "tendremos ese score": se interpreta como probabilidad de Frey-Osborne asignada por emparejamiento; no se interpreta como autorización para usarla como exposición ni para sustituir la definición de 001.
- A4: "Apruebo" no se extiende a APIs de pago, a la muestra de oro ni a las demás preguntas abiertas. (Matizado por R.7 y R.8.)

### R.6 Actualización (2026-10-19): aprobación de 001, 003 y 004; solicitud a INEGI
Cita textual del usuario: "Aprobado 004, 001 y 003. La solicitud de la tabla no la necesitamos ya estan las tablas del catálogo".
- **001, 003 y 004 quedan aprobadas.** 005 ya no depende de decisiones pendientes. Modificar `docs/rubric.md` y `docs/glossary.md` requería decisión posterior (regla 2): ver R.8 y la decisión 006.
- **P3 resuelta por el usuario: no se solicita la tabla SOC-SINCO / SINCO-CIUO-08 a INEGI** (ni la equivalencia 2011-2019 por esa vía). Se anula la posibilidad de que esa tabla sustituya a B1 o sirva de estándar de oro (§12, P3 original).
- **Efecto sobre B:** las tablas del catálogo SINCO (según los reportes del agente de datos) no contienen correspondencia con CIUO-08, SCIAN ni O*NET. El Método A se apoya directamente en ellas. El Método B sigue sin el eslabón SINCO -> ISCO-08 y ahora tampoco hay vía oficial prevista para obtenerlo; solo quedaría el mapeo semiautomático B1 con validación humana (§6.1; 003 §4 opción 2). Ver R.8 para su autorización en principio.
- Sin tabla de INEGI, la calidad del emparejamiento se mide únicamente con la muestra de oro humana (§8): su tamaño y revisores (P9) se vuelven más críticos.

### R.7 Aprobación global ("aprobar todo") y estado vigente de las preguntas abiertas

Cita textual del usuario (2026-10-19): "aprobar todo".

**Interpretación registrada (sin ampliar):** el usuario aprueba las recomendaciones y valores por defecto propuestos en esta decisión (005) para las preguntas abiertas que seguían pendientes, junto con los asentamientos ya registrados de 001, 003 y 004, y autoriza proceder a implementar el Método A. No se interpreta como aprobación de nada que 005 no recomiende de forma concreta (esos puntos se marcan "requiere decisión") ni de dependencias distintas de R.2. (La extensión a 001/003/004 y a `rubric.md`/`glossary.md` se registra en R.8.)

**Hechos nuevos de datos** (reportados por el agente de datos; no verifiqué los Parquet directamente; fuente: `docs/issues/datos-2026-10-19-frey-osborne-puente-discrepancias.md`, que sí leí):
- Se ingestaron `data/processed/frey_osborne_probabilidades.parquet` (702 filas) y `data/processed/puente_onet_soc2019_soc2010.parquet` (1164 filas; 1110 códigos O*NET-SOC 2010 y 1012 códigos 2019 distintos; es 1:N / N:1).
- Por la vía puente (O*NET 2019 -> O*NET 2010 -> SOC 2010 -> Frey-Osborne), 811 de las 1016 ocupaciones O*NET 31.0 alcanzan al menos una probabilidad: 786 con un único SOC 2010 y 25 con más de uno (24 con probabilidades distintas). Las 205 restantes quedan sin probabilidad por esa vía; el issue solo documenta la causa de 4 (ver abajo), no de las otras 201.
- 4 ocupaciones O*NET 31.0 no están en el puente (posteriores a la taxonomía 2019 del crosswalk): 15-1299.04, 15-1299.05, 15-1299.06 y 15-1299.07.
- 17 de los 702 códigos de Frey-Osborne no aparecen como SOC 2010 en el puente (29-1060, 29-1111, 25-3999, 25-1000, 29-9799, 39-4831, 15-1179, 15-1799, 29-2037, 13-1078, 29-2799, 49-9799, 31-9799, 15-1150, 47-4799, 45-2090, 51-9399); parecen códigos agregados/heredados; no se corrigieron. (El propio issue anota, sin corregir, que 29-1111 Registered Nurses es 29-1141 en SOC 2010.)
- La extracción del apéndice del PDF empareja rangos y códigos por orden (el `-layout` pierde la alineación), con verificaciones por página y contra valores conocidos del paper; el PDF no declara licencia. 70 filas tienen etiqueta de entrenamiento (33 con 0, 37 con 1).

**Preguntas abiertas cubiertas por la aprobación y valor aprobado** (tal como lo recomienda esta decisión):

| Pregunta | Estado | Valor aprobado |
|---|---|---|
| P1 | Resuelta (R.1b) | Variable comparativa; etiqueta "probabilidad de automatización (Frey-Osborne)" |
| P3 | Resuelta (R.6) | No se solicita tabla a INEGI |
| P4 | Resuelta por la ingesta | Tabla FO en `data/processed/frey_osborne_probabilidades.parquet` (702 filas). Salvedades de calidad: ver "Requiere decisión" (verificación de la transcripción por muestra) |
| P5 | Resuelta por la ingesta | Puente O*NET 2019 -> 2010 en `data/processed/puente_onet_soc2019_soc2010.parquet` (1164 filas, `2010_to_2019_Crosswalk.csv` del O*NET Center según el issue) |
| P6 | Cubierta en lo recomendado | Método A como principal; B como contraste parcial solo si se implementa (ver R.8) |
| P8 | Cubierta | Modelos locales BGE-M3 y multilingual-e5-large comparados en la muestra de oro, uno elegido por precision@1 y @5 con criterios fijados antes; dependencias de R.2; sin APIs |
| P9 (parte) | Cubierta en lo recomendado | Piloto de 50-60 grupos y muestra principal n = 200; doble revisión independiente de los 200 (alternativa económica: 50 % más tercer revisor); estratificación de §8.1; mitad calibración y mitad prueba; kappa de Cohen y ponderado con umbral **fijado antes de ver los datos** (ver "Requiere decisión" sobre el número) |
| P10 | Cubierta | Ponderación de candidatos por softmax de similitud con tau calibrado (cifra principal `p_FO_w`); uniforme (`p_FO_mean`), min, max y top-1 siempre reportados; ponderación por empleo de EE. UU. solo como sensibilidad y solo si se consigue una fuente verificada |
| P11 | Cubierta | Caso base: `NA` con `match_status = sin_coincidencia`; imputación por media ponderada de hermanos del subgrupo solo como sensibilidad, marcada `imputado = TRUE` y fuera de intervalos y correlaciones |
| P13 | Cubierta | LLM como reranker no se activa por defecto; no se usa en la primera implementación |
| Reglas de reporte (§8.4) | Cubiertas | Etiqueta corta, cobertura, `match_status`, rango min-max, `baja_confianza`, cifras solo de `data/processed/` |
| Multiplicidad del puente O*NET 2019 -> 2010 (25 ocupaciones con más de un SOC 2010, 24 con probabilidades distintas) | Cubierta por §5.7 | El conjunto de SOC 2010 se propaga con pesos uniformes y se reporta (`p_FO_min`, `p_FO_max`, `n_candidatos`); luego se agrega a SINCO por similitud. Esta regla es la que 005 fija; ver "Requiere decisión" si el usuario prefiere otra |
| Ocupaciones O*NET nuevas sin equivalente en el puente (4 casos de 15-1299.xx) y sin probabilidad por la vía puente (resto de las 205) | Cubierta por §5.7 | Quedan sin `p_FO`, se cuentan y se reportan; nada se imputa en silencio |

**Requiere decisión (005 no tiene recomendación concreta; sigue pendiente de revisión humana):**
1. **Los 17 códigos de Frey-Osborne fuera del puente.** 005 no fija regla para códigos del lado FO sin equivalente en el puente (§5.7 solo cubre ocupaciones O*NET nuevas). Opciones a decidir: dejarlos sin enlace (default conservador, que es lo que ocurre sin acción), proponer correspondencias manuales con validación humana (p. ej. 29-1111 -> 29-1141, que el issue señala pero no corrige), o agrupar por código padre. No se decide aquí.
2. **Licencia del PDF de Frey-Osborne.** El PDF no declara licencia (issue). 005 no la trata. Requiere decisión sobre si la tabla puede redistribuirse en salidas públicas (dashboard, artículo, API) o solo usarse internamente con cita.
3. **Verificación de la extracción del apéndice.** El emparejamiento rango-código por orden está verificado por el agente de datos con comprobaciones por página y seis valores del paper; 005 §9 riesgo 6 pide verificar la transcripción contra el PDF "con muestra" sin fijar su tamaño. Requiere decisión: tamaño de la muestra y quién la revisa.
4. **Número del umbral de kappa** y **quiénes son los revisores** (P9). 005 solo dice que se fija antes de ver los datos y cita la convención 0.6-0.8 (no verificada contra fuente); no recomienda un valor.
5. **Método B (P6, P7, y P-B de 003).** B depende de SINCO -> ISCO-08 (inexistente, no se pedirá a INEGI) y de texto ISCO-08 en español con licencia (P7, sin recomendación). Estado actualizado en R.8: autorizado en principio, no se implementa hasta que el usuario lo pida; P7 sigue requiriendo decisión.
6. **P2** (lectura de Ceballos y Guadarrama 2025): es una tarea humana, sin recomendación ejecutable. Sigue abierta.
7. **P12** (490 / 468 / 489 grupos): 005 no tiene valor recomendado; depende de que el agente de datos cuente en el PDF. Sigue abierta y debe resolverse antes de fijar el tamaño de la muestra de oro.
8. **Valores numéricos iniciales** de delta, tau, umbrales de baja confianza y B (bootstrap): 005 solo da B = 1000 "a decidir" y k = 10 como inicial; el resto se calibra con la muestra de oro. Se implementan en configuración como "provisional, sin calibrar".
9. **Dependencias fuera de R.2** (p. ej. `statsmodels`, APIs): siguen no aprobadas. (Kappa, ICC y bootstrap pueden calcularse con scikit-learn y scipy.)

**Efecto sobre el alcance de R.4:** queda autorizada la implementación del Método A, ahora incluyendo la asignación de `p_FO` (la condición de R.4.5 se cumple), con todos los resultados marcados NO validados hasta pasar la muestra de oro. B sigue sin implementarse.

### R.8 Aprobación de pendientes (2026-10-19)

Cita textual del usuario, en respuesta al reporte del agente de métodos: "Si, aprobar pendientes incluyendo uvicorn."

**Interpretación registrada (sin ampliar):** el "Si" confirma la extensión de la aprobación a las propuestas concretas de 001, 003 y 004 para sus preguntas abiertas, incluidas las dos que el agente de métodos señaló como no cubiertas. El estado de cada pregunta quedó registrado en cada decisión (001 §10, 003 §5, 004 "Preguntas abiertas"). Lo que no tiene recomendación concreta sigue "requiere decisión"; no se inventan valores.
- **`docs/rubric.md` y `docs/glossary.md`:** la aprobación de 001 más esta respuesta constituyen la decisión registrada de la regla 2. El texto exacto está en `docs/decisions/006-cambios-rubrica-glosario.md` (aprobada en principio, pendiente de aplicar). 005 no modifica esos archivos.
- **Método B / SINCO -> ISCO-08:** autorizado **solo en principio**, con diseño de doble revisión humana (003 §4 y 005 §8.1). **No se implementa hasta que el usuario lo pida explícitamente.** Sigue requiriendo decisión: P7 (texto ISCO-08 en español y licencia), revisores y guía, y uso de LLM. El alcance implementable sigue siendo el Método A (R.4, R.7).
- **uvicorn:** aprobado en 004 (Registro 2). No afecta a este método. No aprueba FastAPI/starlette.
- **Siguen como "requiere decisión"** (el usuario no dio valor y 005 no lo recomienda): los 17 códigos de Frey-Osborne fuera del puente, licencia del PDF de Frey-Osborne, tamaño y revisor de la verificación de la extracción, número del umbral de kappa y revisores, P7, P2, P12, valores numéricos iniciales (delta, tau, umbrales, B) y dependencias fuera de R.2.

---

## 0. Alcance, insumos y límites

Leídos: `CLAUDE.md`, `docs/decisions/001`, `docs/decisions/003`, `docs/diccionario_datos_sinco.md`, el issue `docs/issues/datos-2026-10-19-crosswalk-sinco-isco08-onet-bloqueado.md` y `data/raw/manifest.json` (SINCO 2019 PDF; O*NET 31.0 texto; BLS ISCO-08 -> SOC 2010, versión 2012).

No pude abrir los Parquet (no tengo herramienta para ello en esta sesión). Lo que digo de su contenido proviene solo del diccionario de datos y del encargo (p. ej. `onet_ocupaciones` con 1016 filas). Tampoco pude listar `docs/issues/`; leí el único issue que conocía por nombre (cita en 003). Si hay otros issues, no los vi. (Posteriormente leí el issue de Frey-Osborne y el puente; ver R.7.)

Aclaración de alcance, importante (decisión 001): la probabilidad de Frey y Osborne es una medida de **probabilidad de computarización/automatización de la ocupación completa**, no la **exposición a IA** que este proyecto define sobre tareas. Esta decisión propone cómo *trasladar* esa probabilidad a SINCO 2019 mediante emparejamiento; su uso sería (i) referencia de validación convergente de la exposición, o (ii) variable comparativa. No es el resultado principal. (P1 resuelta por el usuario: variable comparativa; ver sección R.)

## 1. Pregunta

¿Cómo asignar a cada grupo unitario SINCO 2019 (490 según el parquet; ver discrepancia 468/490/489 en 003 §0, sin resolver aquí) una probabilidad de Frey y Osborne, pasando por O*NET/SOC, con emparejamiento basado en embeddings, de forma reproducible, auditable y con incertidumbre explícita?

## 2. Hipótesis sobre Ceballos y Guadarrama (2025): estado de verificación

El usuario cree que el artículo hace el emparejamiento "manualmente". **[NO VERIFICADO]**.

Intentos (2026-10-19):
- PDF https://revistas.uniandes.edu.co/index.php/dys/article/view/11083/10931: la herramienta devolvió solo encabezado de la revista; sin texto.
- HTML https://revistas.uniandes.edu.co/index.php/dys/article/view/11083/11419: igual, solo encabezado.
- Página del artículo https://revistas.uniandes.edu.co/index.php/dys/article/view/11083: resumen (ENOE 2024, Oaxaca-Blinder, efectos negativos sobre salarios) y referencias que mencionan SINCO 2019; **no** describe el método de emparejamiento. (El resumen devuelto por la herramienta no es lectura directa de las referencias; no lo uso para afirmar nada más.)
- Una búsqueda web con sus términos no devolvió el artículo ni nada sobre su emparejamiento.

Por tanto no sé si el emparejamiento es manual, por tabla de correspondencia o por texto; tampoco su versión de SINCO, el año de Frey-Osborne ni su cobertura. La cita "ocupación similar o media del subgrupo" sigue **sin confirmar**. Acción pendiente: que una persona lea la sección metodológica.

**Hallazgo colateral útil (otro artículo, no Ceballos).** Minian y Martínez Monroy (2018, *Problemas del Desarrollo*, https://www.probdes.iiec.unam.mx/index.php/pde/article/download/64001/62384?inline=1), según el resumen que produjo la herramienta de lectura (no verifiqué el texto directamente, y el fragmento citado debe contrastarse con el original), emplean "la tabla de comparación SOC-SINCO proporcionada por el INEGI (2012)", con SINCO 2011; la tabla usa SOC a 5 dígitos y Frey-Osborne a 6; ponderan las probabilidades con empleo de EE. UU. (BLS 2016) o promedio simple, y reportan resultados similares con ambos y entre 5 y 6 dígitos. Implicaciones: (a) existe, o existió, una tabla de INEGI SOC-SINCO (2011), lo que **matiza el issue de datos** (que busca SINCO 2019 -> CIUO-08) y debería consultarse a INEGI [**actualización 2026-10-19: el usuario decidió no solicitarla; ver R.6**]; (b) sería SINCO 2011, no 2019, y el anexo de equivalencia 2011-2019 quedó fuera de alcance (diccionario de datos); (c) hay precedente mexicano de promedio simple vs ponderado por empleo de EE. UU.
Cabrero Mendoza y Guajardo Mendoza (CLAD, 2022) aplican el método adaptado a SINCO según un resultado de búsqueda; **no leído**.

## 3. Datos y términos de referencia

### 3.1 Lado SINCO (diccionario de datos)
Por grupo unitario: `sinco.titulo` y `sinco_descripcion.titulo_ampliado`, `descripcion` (490/490), `sinco_ocupaciones_ejemplo` (472/490), `sinco_funciones` (457/490; los 33 restantes son residuales), `sinco_incluye_excluye` (398 con "excluye", 22 con "incluye"). Los "excluye" nombran grupos vecinos: útiles como **texto negativo** o como pista de frontera, no como texto a embeber en el perfil.

### 3.2 Lado O*NET / SOC
- `onet_ocupaciones` (1016 filas con descripción) y `tareas_onet_en`. O*NET 31.0 usa la taxonomía O*NET-SOC 2019, basada en SOC 2018; la búsqueda del 2026-10-19 sobre O*NET 25.1 indica 1016 títulos de los cuales 923 son ocupaciones con datos (https://www.onetcenter.org/taxonomy.html vía resultado de búsqueda; no confirmé que 31.0 conserve esas cifras). Si el 1016 de `onet_ocupaciones` incluye los títulos sin datos de tareas, esas filas no tendrán tareas: **[NO VERIFICADO]**, comprobar con el parquet.
- O*NET publica servicios de conversión entre la taxonomía 2010 y la 2019 (https://www.onetcenter.org/taxonomy.html, resultado de búsqueda). No localicé ni leí el archivo de crosswalk 2010 <-> 2019 (el informe https://onetcenter.org/reports/Taxonomy2019.html no trae las cifras de 1:1/divisiones/fusiones en la parte leída). **[NO VERIFICADO por mí]**: el archivo, su forma y proporción de cambios. (El agente de datos ya lo ingestó como `2010_to_2019_Crosswalk.csv`; ver R.7.)
- BLS ISCO-08 -> SOC 2010 (2012), ya en `data/raw/`. No he abierto el XLS: **[NO VERIFICADO]** si incluye títulos ISCO en inglés y qué columnas tiene.

### 3.3 Frey y Osborne
- Fuente primaria: "The Future of Employment" (2013), Oxford Martin School. https://www.oxfordmartin.ox.ac.uk/publications/the-future-of-employment y PDF https://oms-www.files.svdcdn.com/production/downloads/academic/The_Future_of_Employment.pdf (redirección desde el enlace de oxfordmartin). La herramienta devolvió el PDF como binario ilegible; **no pude ver el apéndice con la tabla de probabilidades ni confirmar** la versión de SOC (que suponen 6 dígitos y, según mi recuerdo, SOC 2010 con 702 ocupaciones) ni el formato de la tabla. **[NO VERIFICADO por mí]**. (El agente de datos extrajo el apéndice; ver R.7.)
- Verificado por búsqueda (no por el documento): 702 ocupaciones; clasificador de procesos gaussianos; entrenamiento con 70 ocupaciones etiquetadas a mano en un taller por economistas e investigadores de aprendizaje automático (fuente: https://arxiv.org/pdf/1706.06906, resultado de búsqueda; y nota de la ONS https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/articles/theprobabilityofautomationinengland/latest).
- **La tabla en formato de datos** (CSV/XLSX) no la localicé. Candidatos: transcribir el apéndice del PDF por script (OCR/extracción) o buscar un repositorio de réplica; ambos requieren verificación y manifest (regla 3). (Resuelto: transcripción por script por el agente de datos; ver R.7.)
- Puente de versiones. FO está (a confirmar) en SOC 2010; O*NET 31.0 está en O*NET-SOC 2019 (SOC 2018). Necesita el puente 2019 -> 2010 (1:N y N:1). El método B termina directamente en SOC 2010 (vía BLS) y evita ese puente; el método A lo necesita (ver §5).
- Nivel: FO está a SOC detallado (6 dígitos, a confirmar); O*NET-SOC añade sufijo `.NN`. Colapsar `.NN` a SOC de 6 dígitos al unir.

## 4. Principios comunes a ambos métodos

1. **Cosenos no son probabilidades**. Los umbrales absolutos de similitud dependen del modelo y del texto; se calibrarán contra la muestra de oro (§8) y se fijarán en configuración, no en código. Hasta calibrar, solo se proponen reglas relativas (rango, margen entre top-1 y top-2).
2. **Nada se descarta en silencio**. Todo emparejamiento conserva candidatos, similitudes, rangos y banderas.
3. **Registro de corrida de embeddings** (regla 4 adaptada): `run_id`, `embedding_model` (nombre y revisión/commit exacto del repositorio del modelo o versión de la API), `model_date`, `text_template_version` (análogo a `prompt_version`), `normalization` (L2), `max_length/truncamiento`, versiones de librerías, dispositivo/dtype, `seed` (para muestreos y bootstrap; el cálculo de embeddings es en principio determinista, pero con GPU/dtype puede variar a nivel numérico, **[NO VERIFICADO]**; se guarda un hash de la matriz). Si se usa LLM para rerank: además `prompt_version`, modelo, fecha, temperatura.
4. **Hash y versión de los insumos**: SINCO PDF, O*NET 31.0, BLS xls, tabla FO (cuando exista), crosswalk O*NET 2010-2019.
5. **Plantillas de texto** versionadas, con el mismo orden de campos en ambos lados.

## 5. Método A - Recuperación directa SINCO -> O*NET-SOC, sin pasar por ISCO

### 5.1 Qué se embebe
- **SINCO (consulta)**, un documento por grupo unitario: `titulo_ampliado` + `descripcion` + hasta N `ocupaciones_ejemplo` (todas, son cortas) + `funciones` (variante A+F). Variante "título solo" y variante "con funciones" para sensibilidad. Los `excluye` no entran en el documento principal. Si se supera el límite de tokens del modelo, truncar por campo con prioridad: título, ocupaciones ejemplo, descripción, funciones (y registrar truncamiento). Para modelos de 512 tokens (p. ej. multilingual-e5-large, verificado) el truncamiento será común en funciones; para BGE-M3 (8192, verificado) no.
- **O*NET (documento)**: título + `descripcion` de `onet_ocupaciones` (+ títulos alternativos si están en el zip de O*NET 31.0: **[NO VERIFICADO]**, comprobar) y variante "+ tareas core" (concatenar o promediar embeddings de tareas; el promedio de embeddings de tareas es otra opción; se prueba en sensibilidad). Se usa la tabla `tareas_onet_en` como insumo, **sin** depender de la traducción de la fase translate.
- **Diagnóstico de tareas inexistentes en México**: para cada función SINCO, la similitud máxima con tareas del O*NET candidato (`cobertura_funciones` = fracción de funciones SINCO con alguna tarea O*NET sobre un umbral calibrado) y, a la inversa, fracción de tareas core O*NET sin función SINCO cercana. Es una bandera de calidad, no entra al cálculo.

### 5.2 Multilingüe
| Variante | Descripción | Ventaja | Riesgo |
|---|---|---|---|
| A1 (propuesta base) | SINCO en español original contra O*NET en inglés original, con modelo multilingüe | Sin traducción, sin ruido de traducción; barato | La calidad cruzada es menor que la monolingüe; regionalismos |
| A2 | SINCO traducido al inglés (LLM, corrida registrada) contra O*NET en inglés | Comparación monolingüe | Doble costo; la traducción introduce sesgo; reproducibilidad (modelo y fecha) |
| A3 | O*NET traducido al español (ya hay traducción de tareas en el pipeline) contra SINCO en español | Reaprovecha la fase translate | La traducción de descripciones de ocupación quizá no existe; depende de la fase translate |
Propuesta: A1 como base y A2 como sensibilidad sobre una muestra o el total (costo bajo: 490 documentos). A3 solo si la traducción ya existe y se versiona. Se mide el efecto del idioma con el acuerdo entre variantes (§9).

### 5.3 Modelos candidatos (solo lo verificado)
- **BAAI/bge-m3** (https://huggingface.co/BAAI/bge-m3, consultado 2026-10-19): más de 100 idiomas, 1024 dimensiones, 8192 tokens, licencia MIT, modos denso, disperso y multivector. Referencia a la cifra de MIRACL: solo por fuentes secundarias de la búsqueda, no la cito.
- **intfloat/multilingual-e5-large** (https://huggingface.co/intfloat/multilingual-e5-large, consultado 2026-10-19): ~100 idiomas (inicializado desde xlm-roberta-large), 1024 dimensiones, 512 tokens, MIT; exige prefijo `query: ` / `passage: ` (el modelo lo requiere por entrenamiento; para similitud simétrica, `query: ` en ambos lados según la ficha). Aviso de la ficha: puede degradarse en idiomas de pocos recursos (el español no es un caso bajo recursos, pero no lo medí).
- Otros (embeddings de pago por API, modelos tipo `paraphrase-multilingual`, GTE, etc.): **[NO VERIFICADO]**, no consulté sus fichas, licencias ni precios. Antecedentes en búsqueda (solo resúmenes, no leídos): TitleMatch (arXiv 2510.01470) usa GTE-small con vecino más cercano sobre títulos O*NET; el informe "Related 2024" de O*NET usa SBERT sobre tareas y DWA (https://www.onetcenter.org/dl_files/Related_2024.pdf; PDF ilegible para la herramienta; dato solo del resumen de búsqueda); ESCO usó un BERT afinado más validación experta para mapear O*NET a ESCO (https://esco.ec.europa.eu/, resumen de búsqueda).
- Propuesta: comparar BGE-M3 y multilingual-e5-large en la muestra de oro y elegir uno por criterios preestablecidos (precision@1, @5); el otro queda como sensibilidad.

### 5.4 Similitud, top-k y umbrales
- Coseno sobre vectores L2-normalizados; matriz 490 x 1016 por fuerza bruta (no se requiere índice vectorial).
- Top-k: k = 10 para recuperación; conjunto de candidatos S = {j : rango <= 5 y sim_j >= sim_top1 - delta}, con delta calibrado (valor inicial sugerido a ajustar en la muestra de oro, no fijado aquí).
- Margen: `margin = sim_top1 - sim_top2`. Casos con margen bajo o sim_top1 bajo (cuantiles calibrados) -> bandera `baja_confianza`.
- Diagnóstico de consistencia de gran grupo SOC (2 dígitos) esperado a partir de la división SINCO: **solo bandera**, no restricción (la estructura SINCO difiere de SOC; 003 §4).
- Rerank opcional con LLM (mismo registro de corrida): solo para candidatos del top-5; salida categórica {exacto, parcial, incorrecto} + justificación; se compara con la muestra de oro antes de adoptarlo. **No se activa por defecto.**

### 5.5 Combinación con la tabla ISCO-08 -> SOC 2010
No se usa como restricción. Se usa **después**, como control: para cada emparejamiento A, ver si el SOC 2010 final es alcanzable desde alguna ISCO con un SINCO plausible; solo es posible tras construir SINCO -> ISCO (003). Hasta entonces, no aplica.

### 5.6 Reglas de cardinalidad
- **1:N (SINCO -> varios O*NET-SOC)**: se conserva S con pesos `w_j = softmax(sim_j / tau)` normalizados dentro de S (tau calibrado; alternativa uniforme). Dos O*NET-SOC con el mismo SOC 2010 se colapsan antes de ponderar.
- **N:1 (varios SINCO al mismo SOC)**: cada uno hereda el valor; se marca `n_sinco_mismo_soc` para tratar la dependencia en intervalos y correlaciones (clusters).
- **Residuales / sin coincidencia** (los 33 grupos sin funciones son residuales): si `sim_top1` está bajo el umbral, el grupo queda **sin valor** (`NA`, `match_status = sin_coincidencia`). Como sensibilidad, imputación marcada (`imputado = TRUE`) con la media ponderada de los hermanos del subgrupo con coincidencia propia; nunca entra en intervalos ni en correlaciones de validación. (Esto es lo más cercano a la regla "ocupación similar / media del subgrupo" que atribuye el usuario a Ceballos, aún **no verificada**.)

### 5.7 Enlace de probabilidades FO
`O*NET-SOC 2019` -> (puente O*NET 2019 -> 2010) -> `SOC 2010 6 dígitos` -> `p_FO`. Reglas del puente: 1:N (un O*NET 2019 puede corresponder a varios 2010) y N:1; se propaga como conjunto con pesos uniformes y se reporta. Las ocupaciones O*NET 2019 nuevas, sin equivalente 2010, quedan sin p_FO (se cuentan y se reportan).
- Agregación a SINCO: **media ponderada por similitud** como cifra principal (`p_FO_w`); además `p_FO_mean` (uniforme), `p_FO_min`, `p_FO_max`, `p_FO_top1`. Mínimo y máximo acotan la ambigüedad. Se reporta `n_candidatos`, `margin`, `match_status`.
- Alternativa de ponderar por empleo de EE. UU. (como Minian y Martínez Monroy, según la herramienta): requiere una fuente de empleo por SOC (p. ej. OEWS de BLS), **[NO VERIFICADO]**; se deja como sensibilidad, a decidir por el humano.

## 6. Método B - Recuperación restringida por el puente ISCO-08 -> SOC 2010

### 6.1 Prerrequisito (bloqueo)
B necesita un eslabón SINCO 2019 -> ISCO-08 que **no existe** (issue; 003). [Actualización 2026-10-19: el usuario decidió no solicitar la tabla a INEGI y las tablas del catálogo no traen esa correspondencia; ver R.6. B autorizado solo en principio, sin implementar hasta que el usuario lo pida; ver R.8.] Por eso B tiene dos etapas de emparejamiento, ambas con validación humana:

- **B1: SINCO -> ISCO-08** por similitud de texto (003 §4, opción 2): documento SINCO como en A; documento ISCO-08 = título + definición. **[NO VERIFICADO]** si dispongo de texto ISCO-08 en español (OIT) con licencia utilizable; sí hay en inglés al menos títulos si el XLS BLS los trae (no abierto). Alternativa si solo hay inglés: es el mismo problema multilingüe de §5.2. Validación humana obligatoria (003).
- **B2: ISCO-08 -> SOC 2010** con la tabla BLS (en `data/raw/`). Para un ISCO con varios SOC (1:N), los candidatos son el conjunto SOC del puente.
- **B3: desambiguación**: embeddings **solo para elegir/ponderar dentro del conjunto del puente**: similitud entre el documento SINCO y el documento O*NET/SOC de cada SOC 2010 candidato (con el mismo texto de §5.1; SOC 2010 se representa con la ocupación O*NET-SOC cuyo código colapsa a ese SOC, y la descripción de O*NET 31.0; si hay varias, promedio de sus vectores o el mejor). Aquí hay una sutileza: el texto de O*NET 31.0 describe O*NET-SOC 2019, no 2010 (diferencias de título/definición a verificar; los datos 2010 archivados están en O*NET 25.0 y no se ingestaron).
- **B4: rerank opcional** con LLM sobre los candidatos de B3, mismas reglas de registro.

### 6.2 Combinación con el puente
Restricción estructural **fuerte**: solo SOC alcanzables desde los ISCO vinculados al SINCO. Se relaja con una variante "B-laxa": si el mejor candidato de A está fuera del conjunto del puente y su similitud supera por margen calibrado al mejor candidato del puente, se marca `discrepancia_puente` y se envía a revisión (no cambia el valor automáticamente).

### 6.3 Reglas de cardinalidad
- SINCO 1:N ISCO: unión de conjuntos SOC, cada SOC con peso combinado (peso ISCO por similitud B1 x peso de desambiguación B3); se colapsa por SOC.
- ISCO 1:N SOC: pesos por similitud (B3), no uniformes, con uniforme como sensibilidad.
- N:1: igual que A.
- Sin coincidencia en B1 (similitud baja o sin ISCO plausible) -> `sin_coincidencia`, mismas reglas de imputación marcada que A.
- Ventaja: B termina en SOC 2010 sin el puente O*NET 2019 -> 2010 para p_FO.

### 6.4 Enlace de probabilidades FO
`SOC 2010` -> `p_FO` directo (si la tabla FO está en SOC 2010, **[NO VERIFICADO]**). Agregación como en §5.7 (`p_FO_w`, `p_FO_mean`, min, max).

## 7. Comparación A vs B

| Aspecto | A (directa) | B (restringida por puente) |
|---|---|---|
| Dependencias de datos nuevas | Tabla FO; puente O*NET 2019 -> 2010 | Tabla FO; texto ISCO-08 (y su licencia); eslabón SINCO -> ISCO |
| Etapas de error | Una de recuperación + puente 2019->2010 | SINCO->ISCO + ISCO->SOC (BLS, 1:N) + desambiguación |
| Bloqueos | Ninguno estructural (salvo tabla FO) | SINCO->ISCO no existe (issue); depende de validación humana |
| Ancla externa | Ninguna oficial; calidad solo por muestra de oro | Ancla oficial BLS ISCO->SOC; referencias OIT por CIUO utilizables (con cautela de circularidad) |
| Multilingüe | Un salto cruzado es/en | Dos saltos posibles (es->ISCO, texto->SOC) |
| Ruido de alineación con FO | Puente de versión O*NET 2019 -> SOC 2010 | Directo a SOC 2010 |
| Cobertura de O*NET | Cubre las 1016 con descripción; puede elegir O*NET sin datos de tareas | Limitada a los SOC del puente |
| Interpretabilidad | Alta (ranking + similitud) | Alta (restricción explícita), pero cadena más larga |
| Costo de cómputo | Bajo (490 x 1016) | Bajo; costo humano mayor (valida B1) |
| Riesgo principal | Recupera ocupación textualmente parecida pero de otro oficio | Errores heredados de B1; puente BLS 2012 desactualizado |
| Uso previsto | Línea base y chequeo de B | Línea alternativa independiente |

Propuesta: ejecutar ambos y reportar el acuerdo. Si solo hay capacidad para uno, A (sin bloqueos) como principal y B como contraste parcial en una submuestra, **a decidir por el humano**. (Estado: A como principal aprobado; B autorizado en principio, sin implementar; ver R.7 y R.8.)

## 8. Diseño de validación

### 8.1 Muestra de oro
- **Población**: grupos unitarios SINCO (490 o el número que se concilie).
- **Tamaño**: piloto de 50-60 para afinar la guía y estimar kappa; muestra principal n = 200 (propuesta; con precisión estimada de ±7 puntos para proporciones cercanas a 0.5 sin corrección por población finita, aproximación `1.96*sqrt(.25/200)` ~ 0.069; la corrección por población finita la reduce). Es un compromiso entre costo y precisión; **no es una cifra validada**.
- **Estratificación** (asignación proporcional con mínimos): división SINCO (9); margen de A en terciles; tipo de caso (A y B coinciden / discrepan / sin coincidencia); presencia/ausencia de funciones y ocupaciones ejemplo; residuales vs específicos. Sobremuestrear discrepancias (donde hay más información) con ponderación inversa en las estimaciones globales.
- **Protocolo ciego**: cada revisor ve el SINCO (texto completo) y un conjunto pooled de candidatos (top-5 de A1, A2, B y modelos alternativos, más 2 distractores aleatorios), en orden aleatorio, sin etiqueta de método ni similitud; puede además proponer un SOC fuera de la lista ("ninguno / otro"). Pooled-recall tiene sesgo hacia lo que los métodos recuperan; el campo "otro SOC" lo mitiga parcialmente.
- **Etiquetas**: por pareja {exacto, parcial, incorrecto}; por SINCO, el conjunto aceptable de SOC y un "mejor SOC".
- **Doble revisión independiente** de toda la muestra de 200 (no solo el 10 % de 003; alternativa económica: doble revisión del 50 % más un tercer revisor para desacuerdos). Dos o más revisores con conocimiento de clasificaciones (003 P4), guía escrita.
- **Acuerdo**: kappa de Cohen sobre {exacto, parcial, incorrecto} y kappa ponderado (ordinal); además acuerdo en el "mejor SOC" (proporción y kappa a nivel de SOC detallado, y de grupo amplio). Intervalos por bootstrap. Umbral de "aceptable" (convención común: 0.6-0.8 sustancial; **es una convención, no una norma**; **[NO VERIFICADO]** contra la fuente): fijar antes de ver los datos. Si kappa < umbral, reformular guía y repetir el piloto. Desacuerdos: resolver por tercero y registrar.
- Los revisores y la muestra no se usan para afinar tau/delta y evaluar con las mismas parejas: dividir en calibración (p. ej. 50 %) y prueba (50 %) o validación cruzada por estratos.

### 8.2 Métricas
- precision@1, precision@k (k=3,5), MRR, y precision sobre el **conjunto aceptable**; recall del conjunto aceptable en top-k (con la salvedad del pooling); cobertura (`proporción con valor`).
- Calidad por estrato (división; margen), con intervalos de Wilson para proporciones.
- **Acuerdo A vs B**: coincidencia exacta de top-1 SOC; coincidencia a nivel de grupo amplio SOC; Jaccard de conjuntos candidatos; para `p_FO`: ICC o Spearman, diferencia absoluta media, y proporción de grupos con |Delta p| > 0.2 (umbral ilustrativo, a ajustar), gráfica Bland-Altman. Todo por script en `src/` (regla 1).
- **Efecto de traducción**: acuerdo A1 vs A2 con las mismas métricas.
- **Evaluación aguas abajo**: error en `p_FO` respecto de `p_FO` calculado con el "mejor SOC" de oro (MAE, sesgo).

### 8.3 Sensibilidad de la probabilidad final al método
Re-calcular `p_FO` variando: modelo (BGE-M3, e5), texto (título / +descripción / +funciones), idioma (A1/A2), k, delta, tau, agregación (ponderada, media, top-1, min, max), puente de versión (colapsado vs ponderado), método (A, B). Reportar: correlación de rango entre versiones, número de grupos que cambian de cuartil (ideas ya en 003), y descomposición de varianza entre factores (p. ej. ANOVA de factores sobre `p_FO`). **Intervalo de incertidumbre del emparejamiento**: muestrear (con semilla registrada) el emparejamiento por grupo desde la distribución softmax de candidatos y recomputar `p_FO` (B = 1000 como valor inicial; **a decidir**); el intervalo resultante recoge la ambigüedad del emparejamiento, no la incertidumbre de FO misma (que tiene la suya, no consultada).

### 8.4 Reglas de reporte
- Siempre nombrar `p_FO` como "probabilidad de automatización (Frey-Osborne)" (decisión del usuario, sección R); en metadatos puede ampliarse a "probabilidad de computarización de Frey y Osborne (2013) trasladada a SINCO 2019 mediante emparejamiento [método, versión]". Nunca "exposición a IA" ni "riesgo de pérdida de empleo".
- Reportar siempre la cobertura, la proporción por `match_status`, el rango min-max y los casos `baja_confianza`.
- No mostrar un solo número de método sin la comparación con el otro método y con la muestra de oro.
- Cifras del artículo solo desde `data/processed/` (regla 6).
- Correlaciones con la exposición propia se reportan con cluster por SOC compartido (N:1) y se aclara que el mismo emparejamiento alimenta ambos lados si así ocurre (ver riesgos).

## 9. Riesgos

1. **Circularidad.** (a) Si el mismo emparejamiento SINCO -> O*NET alimenta tanto la exposición propia (por tareas O*NET) como `p_FO`, la correlación entre ambas está inflada por construcción: comparten el puente y el error de emparejamiento; solo evalúa la anotación, no el emparejamiento (003 hace la misma observación para OIT). Mitigación: usar B (independiente de A) para el lado de la validación, o reportar la correlación con ambos. (b) FO etiquetó con juicio humano y entrenó con descriptores de O*NET (la parte de variables de O*NET es mi recuerdo, **[NO VERIFICADO]**): si la exposición propia también se basa en O*NET, hay dependencia de insumo. (c) El mismo LLM que anota podría rerankear: sesgos compartidos.
2. **Sesgo de traducción y de vocabulario.** Embeddings cruzados es/en pueden fallar en regionalismos y oficios con nombres locales; A2 introduce el sesgo del traductor. Mitigación: A1 vs A2 y muestra de oro.
3. **Tareas O*NET que no existen en México.** Un emparejamiento correcto en título puede ocultar un contenido de trabajo distinto (más manual, otras herramientas). La probabilidad de FO es de EE. UU., 2013. Mitigación: bandera `cobertura_funciones`; reporte de que es transferencia.
4. **Granularidad desigual.** Un grupo SINCO puede ser más amplio o más estrecho que varios SOC: agregación media oculta heterogeneidad; se reporta min-max.
5. **Puente de versiones** O*NET 2019 -> SOC 2010 (A) y BLS 2012 (B): desactualizaciones, y suposiciones en ocupaciones nuevas.
6. **Dependencia de la tabla FO**: si no se localiza o no se transcribe bien, el proyecto no puede avanzar en esta línea. Verificar transcripción contra el PDF con muestra.
7. **Efecto del residual**: los grupos residuales (33 sin funciones) casan con "All Other"; esas ocupaciones pueden carecer de datos O*NET.
8. **Muestra de oro con sesgo de pooling** y revisores con conocimiento heterogéneo; kappa puede ser bajo en ocupaciones ambiguas.
9. **Interpretación pública** de `p_FO`: se confunde con la exposición; reglas de reporte arriba.
10. **Reproducibilidad de modelos**: las versiones de modelos de HF/API cambian; fijar revisión y guardar vectores y hashes.
11. **Hipótesis sobre Ceballos**: si su emparejamiento resultara ser manual o por tabla INEGI, la comparación con su resultado es una validación adicional (no lograda; ver §2); no se da por supuesto.
12. **(Nuevo, R.7)** 17 códigos de FO fuera del puente, 205 ocupaciones O*NET sin probabilidad por la vía puente, y licencia del PDF de FO sin declarar: ver "Requiere decisión" en R.7.

## 10. Costos y dependencias (no se instala nada sin aprobación)

Estado tras la aprobación (sección R.2): quedan aprobadas solo las dependencias de embeddings listadas allí. El resto de este apartado conserva el análisis original.

Paquetes que se necesitarían y que **no están en el stack de CLAUDE.md**:
- `sentence-transformers` o `FlagEmbedding` (+ `torch`, `transformers`) para los modelos locales. Peso y requisitos de la descarga de pesos de los modelos: **[NO VERIFICADO]** (no consulté tamaño de archivos); ejecución en CPU es viable para ~1500 documentos, pero no medí tiempos.
- `scikit-learn` / `scipy` / `statsmodels` para kappa, ICC, bootstrap (verificar si ya se usan; `numpy` ya sería dependencia de pandas). (Aprobados: scikit-learn y scipy; `statsmodels` no.)
- Opcional: cliente de API de embeddings y LLM (costos **[NO VERIFICADO]**, requiere clave y política de datos; el contenido SINCO/O*NET es público, no hay datos personales). (No aprobado.)
- `faiss` no necesario por el tamaño.
- Descarga de pesos desde Hugging Face requiere acceso a red; las fuentes de datos necesarias (tabla FO, crosswalk O*NET 2010/2019, texto ISCO-08) también son descargas nuevas con hash en `data/raw/manifest.json`.
- Costo humano: dos revisores x ~200 parejas (más piloto) es el costo dominante.
- El agente de datos usa R (src/ingest/*.R); si el emparejamiento se implementa en Python, hay mezcla de entornos: definir interfaz Parquet entre ambos.

## 11. Fuentes consultadas (2026-10-19)

- Frey y Osborne (2013), página: https://www.oxfordmartin.ox.ac.uk/publications/the-future-of-employment; PDF: https://oms-www.files.svdcdn.com/production/downloads/academic/The_Future_of_Employment.pdf (descargado, ilegible con mis herramientas; apéndice no leído por mí; extraído por el agente de datos).
- Entrenamiento con 70 ocupaciones etiquetadas a mano: https://arxiv.org/pdf/1706.06906 y https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/articles/theprobabilityofautomationinengland/latest (solo resultados de búsqueda).
- Ceballos Mina y Guadarrama Gómez (2025): https://revistas.uniandes.edu.co/index.php/dys/article/view/11083 (resumen); PDF .../11083/10931 y HTML .../11083/11419 (sin texto legible).
- Minian y Martínez Monroy (2018): https://www.probdes.iiec.unam.mx/index.php/pde/article/download/64001/62384?inline=1 (vía resumen de la herramienta, no lectura directa).
- Cabrero Mendoza y Guajardo Mendoza (2022): https://revista.clad.org/ryd/article/view/lucha-contra-desempleo-tecnologico-analisis-casos-en-mexico (solo resultado de búsqueda).
- O*NET-SOC taxonomía: https://www.onetcenter.org/taxonomy.html (solo resultado de búsqueda); informe https://onetcenter.org/reports/Taxonomy2019.html (sin cifras de crosswalk en lo leído).
- BGE-M3: https://huggingface.co/BAAI/bge-m3 ; multilingual-e5-large: https://huggingface.co/intfloat/multilingual-e5-large (leídos).
- Antecedentes de matching con embeddings (solo resúmenes de búsqueda, no leídos): https://arxiv.org/pdf/2510.01470 ; https://www.onetcenter.org/dl_files/Related_2024.pdf ; https://esco.ec.europa.eu/ (mapeo O*NET-ESCO).
- Archivos del proyecto: CLAUDE.md, decisiones 001 y 003, diccionario de datos, issues de crosswalk y de Frey-Osborne/puente (`docs/issues/datos-2026-10-19-frey-osborne-puente-discrepancias.md`, leído), manifest.

## 12. Preguntas abiertas para la revisión humana

(Estado vigente en R.7 y R.8.)

P1. **[RESUELTA por el usuario, 2026-10-19; ver sección R.1b]** Rol de Frey-Osborne: variable/score comparativa, a comparar después con la exposición; etiqueta "probabilidad de automatización (Frey-Osborne)". (Texto original: ¿se usa como referencia de validación convergente de la exposición propia, como variable comparativa, o no se usa? Es una medida de automatización (001), no de exposición; si se publica junto a la exposición, ¿bajo qué etiqueta y con qué advertencias?)
P2. ¿Alguien puede leer la metodología de Ceballos y Guadarrama (2025) y confirmar versión de SINCO, año de FO, tipo de emparejamiento y cobertura? Hoy: [NO VERIFICADO]. **Sigue abierta (requiere decisión/tarea humana, R.7).**
P3. **[RESUELTA por el usuario, 2026-10-19; ver R.6: no se solicita a INEGI]** (Texto original: ¿Se solicita a INEGI la tabla SOC-SINCO (que Minian y Martínez Monroy citan para SINCO 2011) y la equivalencia 2011-2019? Cambia el diseño: podría sustituir a B1 o servir de oro.) Efecto: B1 no puede sustituirse por esa tabla; B sigue sin el eslabón SINCO -> ISCO-08 (ver R.8).
P4. **[RESUELTA por la ingesta del agente de datos, 2026-10-19; ver R.7]** Tabla FO en `data/processed/frey_osborne_probabilidades.parquet` (702 filas). Quedan salvedades en R.7 (verificación por muestra, licencia, 17 códigos fuera del puente). (Texto original: ¿De dónde se obtiene la tabla FO en formato de datos y se confirma su versión SOC?)
P5. **[RESUELTA por la ingesta del agente de datos, 2026-10-19; ver R.7]** Puente en `data/processed/puente_onet_soc2019_soc2010.parquet` (1164 filas). (Texto original: ¿Se localiza y aprueba el crosswalk O*NET-SOC 2019 -> 2010 de O*NET?)
P6. ¿A como principal y B como contraste, o ambos con igual peso? ¿Se aprueba que B dependa de B1 (SINCO->ISCO) con validación humana? **APROBADA:** A como principal; B autorizado solo en principio con doble revisión humana (003 §4, 005 §8.1), sin implementar hasta que el usuario lo pida (R.8).
P7. ¿Hay texto ISCO-08 en español con licencia utilizable? [NO VERIFICADO]. **Requiere decisión (R.7, R.8).**
P8. ¿Se aprueban BGE-M3 y multilingual-e5-large como candidatos, y la instalación de dependencias (§10)? ¿Se admiten embeddings por API? (Aprobada por R.2 y R.7: modelos locales y dependencias de R.2; APIs no.)
P9. Tamaño y composición de la muestra de oro (n=200, doble revisión completa vs 50 %), quiénes revisan y umbral de kappa. (Cubierta en lo recomendado: n=200 con piloto, doble revisión completa, umbral fijado de antemano; el número del umbral y los revisores requieren decisión, R.7.)
P10. Ponderación de candidatos: ¿softmax por similitud, uniforme o por empleo de EE. UU. (fuente no verificada)? ¿Pesos por empleo de México no disponibles a nivel sub-SINCO? (Aprobada: softmax; uniforme y empleo EE. UU. como sensibilidad.)
P11. Tratamiento de residuales y sin coincidencia: ¿dejar NA o imputar con media del subgrupo (marcado)? (Aprobada: NA en caso base; imputación marcada solo como sensibilidad.)
P12. Conciliar el número de grupos unitarios (490 / 468 / 489) antes de fijar la muestra. **Sigue abierta (R.7).**
P13. ¿Se usa un LLM como reranker? Si sí, ¿con registro completo (regla 4) y evaluación previa en la muestra de oro? (Aprobada la recomendación: no se activa por defecto.)

## 13. Lista de [NO VERIFICADO] explícitos

- Método de emparejamiento y cobertura de Ceballos y Guadarrama (2025); la cita "ocupación similar o media del subgrupo"; que sea manual.
- Contenido del apéndice de Frey y Osborne (tabla, versión SOC, formato) **por mí**; que use SOC 2010 (el issue del agente de datos indica que 17 códigos no están en el puente como SOC 2010).
- Entrenamiento de FO con variables de O*NET (recuerdo propio).
- Archivo de crosswalk O*NET-SOC 2010 <-> 2019 y proporciones de cambios, **por mí** (el agente de datos reporta 1164 filas); cifras 1016/923 para la versión 31.0.
- Columnas del XLS BLS y si incluye títulos ISCO.
- Texto ISCO-08 en español y licencia; títulos alternativos de O*NET en el zip de 31.0.
- Detalles de Minian y Martínez Monroy más allá del resumen de la herramienta; Cabrero y Guajardo (2022) no leído.
- Cifras de rendimiento de BGE-M3/e5; modelos de pago y sus precios; tiempos de cómputo; determinismo numérico entre dispositivos.
- Umbrales de kappa como convención; valores iniciales de delta, tau, B (a calibrar).
- Fuente de empleo por SOC para ponderar (OEWS).
- Que las tablas del catálogo SINCO no contengan correspondencia con CIUO-08, SCIAN ni O*NET: lo afirman los reportes del agente de datos; no lo verifiqué directamente.
- Cifras de R.7 (702, 1164, 811, 786, 25, 24, 17, 4): tomadas del reporte del coordinador y del issue de datos; no abrí los Parquet.
