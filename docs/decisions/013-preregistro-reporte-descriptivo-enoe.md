# 013 - Pre-registro (BORRADOR) del reporte descriptivo por estratos con la ENOE

> **ESTADO: BORRADOR, PENDIENTE DE REVISIÓN HUMANA (2026-10-19). NO ESTÁ FIRMADO.** Es una propuesta de plan de análisis. No descarga ni consulta ningún microdato de la ENOE, no autoriza dependencias, gasto ni modelo, y no modifica 001, `docs/rubric.md` ni `docs/glossary.md`. Hasta que un humano lo firme (sección 16) y se cumplan las tres condiciones de la sección 2, **no se descarga nada**. Todo valor marcado PROVISIONAL o "propuesta" es una opción para que decida el humano, no una decisión.

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de las fuentes web: 2026-10-19
- Origen: decisión 012, Registro 1 (el usuario eligió el reporte descriptivo por estratos, autorizó usar `enoeR` y dispuso que no se descargue hasta cumplir las condiciones). Decisión 012 §8.1 propuso este pre-registro con el número 013.

## 0. Qué se verificó y qué no (leer primero)

- **Leído:** decisiones 001 (con las enmiendas aplicadas), 011 y 012; `CLAUDE.md`.
- **Consultado en la web (2026-10-19, resúmenes de herramienta, no copias literales):** la página de GitHub de `enoeR`; un resultado de búsqueda sobre la nota de clasificaciones del 3T 2021 de la ENOE Nueva Edición; resultados de búsqueda sobre la definición de informalidad de INEGI. **Los PDF de INEGI no pudieron abrirse con mi herramienta.**
- **Reportado por el orquestador (README de `enoeR` leído por él):** ediciones y tablas disponibles; licencia MIT en el README y NOASSERTION en la API de GitHub; el orquestador no ha descargado nada.
- **No consulté ni descargué** ningún microdato, tabulado, cuestionario ni diccionario de variables de la ENOE. **Todos los nombres de variables de la ENOE que aparecen abajo son [NO VERIFICADO]**; se usan solo como descripción del contenido que habría que localizar en el diccionario de datos de INEGI.
- No leí 005, 008 ni 009; no inspeccioné `data/processed/` ni `data/raw/manifest.json`.

## 1. Pregunta y propósito

**Pregunta.** ¿Cómo se distribuye la exposición técnica a IA (la medida congelada de este proyecto) entre las personas ocupadas de México, y cómo difiere esa distribución entre estratos de contexto (formal/informal, región, sexo, edad, educación, tamaño del establecimiento, sector, nivel de ingresos como descriptor)?

**Propósito.**
- **Descriptivo.** Describe la distribución de una medida fija sobre una población ponderada. No estima efectos.
- **No causal.** No se afirma que la informalidad, la región o el ingreso causen o sean causados por la exposición.
- **No calibra la exposición.** La ENOE solo aporta la ponderación (factor de expansión) y los estratos; ningún parámetro de la exposición se ajusta con datos de la ENOE (012 §4, §8.5). B3 queda desaconsejado y B2 diferido (012, Registro 1).
- **Lectura obligatoria de las diferencias entre estratos.** Como la exposición técnica es constante dentro de un grupo SINCO (012 §2, punto 5 en desacuerdo), toda diferencia de exposición media entre estratos es **composición ocupacional** (en qué grupos SINCO trabajan las personas de cada estrato). El reporte debe decirlo y cuantificarlo (sección 8.4); no puede interpretarse como diferencia de exposición "dentro de la ocupación".

## 2. Condiciones previas a cualquier descarga (compuertas)

No se descarga ningún dato de la ENOE hasta que se cumplan las tres, en este orden de verificación:

| # | Compuerta | Qué la satisface | Quién |
|---|---|---|---|
| G1 | Existe una **exposición congelada** | El artefacto de la sección 3 existe en `data/processed/`, con hashes y `run_id` registrados | Pipeline + humano |
| G2 | **Pre-registro firmado** | Este documento pasa de BORRADOR a FIRMADO con fecha y firma humana (sección 16), con las decisiones de la sección 15 resueltas | Humano |
| G3 | El humano **define informalidad, estratos y trimestres** | Secciones 5 y 6 con valores fijos, no propuestos | Humano |

Además (condiciones prácticas, no autorizaciones): R y `enoeR` instalados y fijados (sección 12), y una regla de almacenamiento que impida publicar microdatos (sección 12). El orquestador debe confirmar por escrito que no se descargó nada antes de la firma.

**Estado hoy (2026-10-19):** G1 no se cumple (la corrida completa de anotación no existe: 011 §8, fases 2-4, y las decisiones de modelo, fecha de corte y muestra humana siguen pendientes). G2 no se cumple (este borrador). G3 no se cumple. B1 "avanza" (012 Registro 1) pero aún no produce posteriores.

## 3. La exposición que se congela

El reporte usa **una versión fija de la exposición, decidida antes de ver la ENOE**. La congelación consiste en un artefacto con los siguientes campos, todos fijados y con hash:

| Campo | Contenido |
|---|---|
| Versión del catálogo | `sinco_fuente.sha256` (011 §4.e) y versión SINCO 2019 |
| Rutas | **Ruta S** (función SINCO -> grupo, sin crosswalk) como ruta principal de este reporte (propuesta; decide el humano), y **ruta O** (tarea O*NET -> top-2 -> SINCO) como contraste, siempre etiquetada `sin_validar` mientras no exista la muestra de oro |
| Medida principal | `E_g` de 001 (`exposure_class`, mapa 0 / 0.5 / 1) |
| Medidas de comparación | `alfa_S` (EL1), `beta_S` (EL1 + 0.5·EL2), `cota_sup_S` (EL1 + EL2), con EL3 fundida en EL2 (001 §4.3, puntos 5 y E-3) |
| Variantes de sensibilidad | Mapas inferior y superior de 001 §4.3; `share_E2`, `share_any` |
| Anotación | `prompt_version` (propuesto: `ann-v2-sinco-el`; no existe aún), `prompt_sha256`, modelo (hoy Sonnet 5.5 por subagentes, 011 §4.e), fecha de cada corrida, fecha de corte de capacidades, `run_id` de cada una de las R corridas |
| Matching (ruta O) | Hash de la tabla de candidatos top-2 con sus puntajes y el estado `sin_validar`/validado |
| Incertidumbre de medición | Si existe: posterior de B1 (semilla, hash de los sorteos, versión de priors y de código). Si no: las R corridas crudas (la incertidumbre se simula remuestreando entre corridas, sección 9) |
| Tratamiento de NA | Residuales sin funciones (33 grupos) = NA sin imputación (011 §4.a); lista de grupos con `pocas_funciones` y su umbral PROVISIONAL |
| Config | Hash de la configuración de mapas y umbrales (`src/score/config.toml` o la que corresponda) |

**Variante congelada.** El humano elige antes de firmar cuál es la "versión de registro": (i) media de corridas, (ii) posterior de B1 sin muestra humana (solo consistencia), (iii) posterior de B1 con muestra humana. Cada una se rotula con lo que es (012 §5, B1). **Propuesta:** (iii) si existe; si no, (i) con intervalos entre corridas, y decirlo en el reporte.

**Regla.** La ENOE no puede modificar ningún campo de esta tabla (012 §8.1, punto 4). Si se halla un error de la exposición después de ver la ENOE, se registra como desviación (sección 14) y el reporte se repite con la versión nueva, mostrando ambas.

## 4. Datos de la ENOE: ediciones, trimestres y versión de SINCO

### 4.1 Ediciones disponibles según `enoeR` (reporte del orquestador y página de GitHub)
- ENOE 2005T1-2020T1.
- 2020T2: **no disponible** (ETOE telefónica, otra encuesta).
- ENOE-N (Nueva Edición) 2020T3-2022T4.
- ENOE 2023T1 en adelante.
- Tablas: `sdem` (sociodemográfica), `coe1t`, `coe2t` (cuestionarios de ocupación y empleo), `hog`, `viv`.
- Comparabilidad entre ENOE, ENOE-N y la ENOE desde 2023T1 (cambios de cuestionario, de marco o de factores): **[NO VERIFICADO]**; es un riesgo para cualquier serie que cruce 2022T4 -> 2023T1.

### 4.2 Versión de SINCO por trimestre [NO VERIFICADO] y qué hacer
- **Lo que sé (segunda mano):** un resultado de búsqueda sobre la nota de clasificaciones del 3T 2021 de la ENOE-N indica que desde ese trimestre se incorpora el SINCO 2019 (URL en la sección 19; el PDF no pudo abrirse). La decisión 012 §4.8 recogía lo mismo desde otro resumen.
- **Lo que no sé:** qué clasificador usan los trimestres previos (se presume SINCO 2011 hasta 2T 2021; no verificado), si la ENOE desde 2023T1 mantiene SINCO 2019, y a cuántos dígitos viene el código en cada edición (se necesitan 4 para coincidir con el grupo unitario).
- **Regla propuesta:** el reporte usa **solo trimestres cuya versión de SINCO sea 2019, verificada en el documento de clasificaciones de INEGI y en el diccionario de variables antes de firmar**. No se usa el puente 2011 -> 2019: el anexo de equivalencia fue descartado (issue `docs/issues/datos-2026-10-19-sinco-anexo-equivalencia-descartado.md`; su intento exploratorio dejó 57 filas sin anclar y bloques ambiguos, según 012 §4.8). Si el humano quiere ampliar a trimestres con SINCO 2011, requiere una decisión nueva sobre el puente y queda fuera de este plan.
- **Cómo se une a SINCO 2019:** unión exacta por código de 4 dígitos de la ocupación principal de la persona ocupada con la clave del grupo unitario del catálogo del proyecto. Se reporta, por trimestre y por estrato: porcentaje ponderado de ocupados con (a) código válido y presente en el catálogo con medida, (b) código válido pero grupo residual o sin funciones (NA), (c) código inexistente en el catálogo, (d) código "no especificado" o ausente. Ninguna imputación en el caso base. Si los códigos de la ENOE vienen a menos de 4 dígitos, el reporte se limita al nivel que permita el código, con una regla de agregación fijada antes de descargar (decisión humana).
- **Qué hacer si algún trimestre candidato resulta ser SINCO 2011:** se excluye del análisis; no se mezcla ni se traduce. Se registra en el reporte qué trimestres se excluyeron y por qué.

### 4.3 Trimestres candidatos (propuesta para decidir)
Dado que desde 2021T3 se presume SINCO 2019 y que `enoeR` ofrece ENOE-N hasta 2022T4 y ENOE desde 2023T1:

| Opción | Periodo principal (A) | Periodo de réplica (B) | Comentario |
|---|---|---|---|
| 1 (propuesta) | 2022T1-2022T4 (ENOE-N) | 2024T1-2024T4 (ENOE) | Año completo cada uno (evita estacionalidad). Brecha de 2023 completa entre A y B (ver 4.4). Cruza el cambio de edición ENOE-N -> ENOE. Requiere verificar que 2022T1-T2 sean SINCO 2019 (el 3T 2021 es el primero según la nota; 2022 sería posterior) |
| 2 | 2024T1-2024T4 (ENOE) | Sin réplica | La más simple; no hay cambio de edición dentro del reporte. El manuscrito de Ceballos y Guadarrama usa ENOE 3T 2024 (reporte del orquestador), lo que permite un contraste contextual (no una validación) |
| 3 | 2021T3-2022T4 (ENOE-N) | 2024T1 en adelante (ENOE) | Más trimestres en A; el 2021T3 es el primer trimestre en que se presume SINCO 2019 y puede tener problemas de transición |
| 4 | Un solo trimestre de referencia (p. ej. 2024T3) | Otro trimestre del mismo trimestre calendario un año después | Evita estacionalidad con mínimo costo; pierde precisión |

El número y la elección de trimestres son **decisión humana** (sección 15). Los trimestres más recientes disponibles al firmar (el 2026T3 aún no existiría a la fecha de este borrador) se evalúan al firmar.

### 4.4 Panel rotatorio y brecha entre periodos
Según un resumen del catálogo de INEGI (012 §8.2, no verificado contra la metodología vigente), cada vivienda se visita cinco trimestres consecutivos. Si es así, dos trimestres no comparten viviendas cuando los separan al menos cinco trimestres de calendario (por ejemplo, 2022T4 y 2024T1: hay cuatro trimestres intermedios, 2023T1-T4). Con la opción 1, A (2022T1-T4) y B (2024T1-T4) no compartirían viviendas. **Hay que verificar el esquema de visitas** en la metodología de INEGI antes de firmar, y confirmar si `enoeR` o las tablas permiten identificar la vivienda para comprobarlo. Esta es una precisión de la frase "al menos cinco trimestres" de 012 §8.2.

## 5. Unidad, población y ponderación

- **Unidad de análisis:** persona ocupada, con su **ocupación principal**. No se analizan segundas ocupaciones. (Variable de ocupación principal y filtro de ocupados: **[NO VERIFICADO]**; se fijan con el diccionario de INEGI antes de firmar.)
- **Población de referencia:** personas ocupadas de la edad mínima que defina el humano (la ENOE trata a la población de 15 años o más; verificar). El reporte declara el filtro exacto (condición de actividad, edad mínima, entrevista completa) con los nombres de variable reales del diccionario. Esos filtros se fijan antes de descargar.
- **Ponderación:** factor de expansión de la persona (trimestral) del diseño de la ENOE. Nombre y definición exactos de la variable: **[NO VERIFICADO]**. Todas las estadísticas puntuales son ponderadas.
- **Varios trimestres:** el reporte principal se calcula **por trimestre** y se combina en un periodo con una regla fijada antes de descargar. Si se combinan trimestres en una sola estimación, el factor se reescala (p. ej. dividir entre el número de trimestres); la regla de INEGI para combinar trimestres es **[NO VERIFICADO]** y se verifica antes de firmar. Como trimestres adyacentes comparten viviendas (panel), los intervalos no pueden tratar los trimestres como muestras independientes (sección 9).
- **Datos faltantes:** no se imputan ocupación, edad, sexo ni estrato. Las personas con dato faltante en el estrato se reportan en una categoría "no especificado" (o se excluyen en esa tabulación, con el porcentaje excluido declarado).

## 6. Estratos propuestos (a decidir por el humano)

Cada estrato es una variable categórica fijada antes de descargar. Las variables y categorías reales de la ENOE son **[NO VERIFICADO]**; abajo se describe la intención.

| # | Estrato | Propuesta | Qué hay que decidir / verificar |
|---|---|---|---|
| 1 | Formal / informal | Dos o tres categorías según la definición oficial de INEGI. INEGI sigue el marco de la OIT con la matriz de Hussmanns: **sector informal** (15ª CIET, 1993) y **empleo informal** (17ª CIET, 2003); texto literal **[NO VERIFICADO]** (012 §9; resultados de búsqueda de esta fecha coinciden, sin abrir los PDF). Propuesta: reportar (a) empleo informal (total, incluye informal en el sector formal y trabajo no remunerado/subordinado sin protección) frente a formal, y como estrato fino, (b) empleo informal en el sector informal frente a empleo informal fuera de él frente a formal | Cuál definición pre-registrar; variable(s) de INEGI que la identifican (hay que localizarlas en el diccionario); si la variable existe en todas las ediciones y trimestres elegidos |
| 2 | Región | Entidad federativa (32) y/o una agrupación regional fijada de antemano (no elegida tras ver resultados). Posible estrato urbano/rural si existe la variable | Agrupación regional; si se reporta por entidad, con la regla de supresión de la sección 7 |
| 3 | Sexo | Hombre / mujer (como lo codifica la encuesta) | Ninguna adicional |
| 4 | Edad | Rangos fijados de antemano. Propuesta: 15-24, 25-34, 35-44, 45-54, 55-64, 65 o más | Rangos finales; edad mínima de la población |
| 5 | Nivel educativo | Categorías agregadas de escolaridad (p. ej. hasta primaria, secundaria, media superior, superior) | Variable y categorías de la ENOE; agrupación |
| 6 | Tamaño del establecimiento | Si existe en la ENOE, las categorías de tamaño de la unidad económica de la ocupación principal | **Existencia de la variable [NO VERIFICADO]**; si no existe, el estrato se omite y se declara |
| 7 | Sector de actividad | Sector agregado (primario / secundario / terciario) o la agrupación del sistema de clasificación de actividades que use la encuesta (SCIAN en la ENOE-N según la nota consultada, no verificado) | Nivel de agregación; variable |
| 8 | Nivel de ingresos | **Descriptor, no resultado.** Cuantiles (p. ej. cuartiles) del ingreso mensual o por hora de las personas ocupadas con ingreso declarado, definidos en la población de referencia del periodo A y **congelados** (los puntos de corte no se recalculan en B). Se reporta el porcentaje de ocupados sin ingreso declarado | Ingreso mensual o por hora; deflactor para comparar periodos (no se deflacta sin decisión); tratamiento de no respuesta, ingresos cero y valores extremos; qué variable |

**Cruces.** Se reportan estratos simples y, como máximo, los cruces **fijados aquí**: informalidad x sexo, informalidad x región (agrupada), informalidad x nivel educativo. Cualquier otro cruce es exploratorio y se etiqueta así. Esta lista limita las comparaciones múltiples (sección 10).

## 7. Estadísticos y umbrales

Para cada estrato `s`, trimestre o periodo `q`, medida de exposición `m` (principal: `E_g`; comparación: `alfa_S`, `beta_S`, `cota_sup_S`) y ruta `r` (S, O):

1. **Distribución:** histograma ponderado de la medida en bins fijos (propuesta: 10 bins de ancho 0.1 en [0, 1]); y la distribución ponderada por **división** SINCO (9 divisiones) para mostrar la composición.
2. **Media ponderada** de la medida, con el factor de expansión.
3. **Cuantiles ponderados:** mediana, p10, p25, p75, p90 (definición del cuantil ponderado fijada y documentada en el script; propuesta: función de distribución empírica ponderada, tipo inverso de la ecdf, sin interpolación).
4. **Proporción de ocupados con exposición alta** bajo umbrales **fijados de antemano**. Propuesta (a decidir): umbrales absolutos 0.25, 0.50 y 0.75 para `E_g`, y el tercil superior de la distribución ponderada de `E_g` en la población de referencia del periodo A (corte congelado). No se elige el umbral tras ver los resultados. Para `alfa_S`, el porcentaje del empleo con `alfa_S` = 0 se rotula "exposición directa nula" y no se presenta como análogo de la "cobertura cero" de Anthropic (011 §4.c.1, §4.d).
5. **Cobertura:** porcentaje ponderado de ocupados con medida disponible (sección 4.2), por estrato; y porcentaje en grupos `pocas_funciones` y en grupos con `crosswalk_confidence` baja (ruta O).
6. **Descomposición composicional** (sección 8.4) para las diferencias entre estratos.

**Supresión de celdas.** No se reporta una estimación si la celda tiene menos de `n_min` observaciones muestrales sin ponderar (propuesta PROVISIONAL: 30) o si el coeficiente de variación estimado supera un umbral (propuesta PROVISIONAL: 30 %); se marca como no publicable. Ambos valores los fija el humano antes de descargar.

Todas las cifras salen de scripts en `src/` (regla 1) y solo las cifras presentes en `data/processed/` pueden citarse en el artículo (regla 6).

## 8. Diseño del análisis

### 8.1 Qué se compara
- Entre estratos, dentro de un periodo.
- Entre las rutas S y O, para cada estrato (la diferencia entre rutas es un diagnóstico del crosswalk, 011 §4.a).
- Entre periodos A y B (si hay réplica), solo para comprobar que el patrón descriptivo no depende del periodo; no para estimar cambios.

### 8.2 Sin pruebas de hipótesis como criterio
El reporte es descriptivo: se publican estimaciones con intervalos, no valores p ni "significancia". Si el humano quiere hipótesis direccionales (H1, H2 de 012 §5, B3), deben listarse en la sección 15 antes de firmar, con su regla de decisión; de lo contrario no se prueban.

### 8.3 Control negativo y chequeo de sanidad (antes de interpretar)
Se verifica, con grupos de contraste elegidos por el humano antes de ver resultados (011 §4.g.6), que la exposición media sea menor donde `physical_bottleneck` domina. Un fallo se trata como problema de medición (no se reajusta con la ENOE).

### 8.4 Descomposición composicional (decisión del humano)
Para entender cuánto de la diferencia entre dos estratos viene de qué divisiones/grupos SINCO ocupan: (a) estandarización directa por división SINCO (qué diferencia quedaría si ambos estratos tuvieran la misma distribución por división) y (b) lo mismo por grupo unitario. Es descriptivo y no usa parámetros estimados de exposición. Si el humano prefiere otra descomposición, la fija antes de firmar.

## 9. Incertidumbre: diseño muestral y matching

Se reportan **tres** intervalos por estimación, para no mezclar fuentes:
- **I-diseño:** incertidumbre por el diseño muestral de la ENOE, con la exposición fija (la media de corridas o la media posterior).
- **I-medición:** incertidumbre de la exposición (corridas del anotador, posterior de B1, y matching en la ruta O), con los pesos fijos.
- **I-total:** ambas combinadas.

### 9.1 Incertidumbre de diseño
- La ENOE es un diseño probabilístico, bietápico, estratificado y por conglomerados (resumen del catálogo de INEGI; detalles **[NO VERIFICADO]**). Las variables de estrato de diseño, unidad primaria de muestreo y factor de expansión que permiten estimar varianzas deben localizarse en el diccionario de INEGI antes de firmar; si no están en las tablas descargadas, el reporte solo puede publicar intervalos aproximados y debe decirlo.
- Método propuesto: remuestreo por conglomerados (bootstrap por unidad primaria de muestreo dentro de estrato, con réplicas de pesos) o linealización; la elección y el número de réplicas son PROVISIONALES, a decidir. El stack aprobado (`requirements.txt`) no incluye un paquete de encuestas; implementarlo con numpy/pandas es una decisión de implementación que no se toma aquí. Si se usa un paquete nuevo, requiere aprobación.
- Trimestres adyacentes comparten viviendas, de modo que las estimaciones de trimestres consecutivos son dependientes; los intervalos de un periodo con varios trimestres deben estimarse con réplicas que respeten la pertenencia a la vivienda (o a la unidad primaria), no suponiendo independencia entre trimestres. Detalle **[NO VERIFICADO]**.

### 9.2 Incertidumbre de medición, propagada por simulación
Para `b = 1..B` (B PROVISIONAL, propuesta 1,000; a decidir):
1. **Exposición por grupo:** se extrae un vector de `E_g^(b)` para todos los grupos SINCO. Si existe B1: un sorteo del posterior (conjunto de sorteos congelado en la sección 3). Si no: se elige al azar, por grupo, una de las R corridas (o se remuestrean las funciones del grupo, que es un intervalo de **sensibilidad** y no de muestreo, 011 §4.g.7). El procedimiento se declara en el reporte con su nombre exacto.
2. **Matching (solo ruta O):** para cada grupo SINCO, se extrae cuál de sus candidatos top-2 es "el correcto" con probabilidades tomadas de la **tabla de candidatos** congelada: (i) si existe el modelo de B1.b calibrado con la muestra de oro, con esas probabilidades; (ii) si no, con probabilidades uniformes entre los candidatos, y se declara explícitamente que es un supuesto sin validar. `E_o^(b)` se recalcula con el candidato extraído. La ruta S no tiene esta etapa.
3. **Diseño:** se aplica una réplica de pesos del esquema de 9.1 (la misma réplica para todas las medidas en esa iteración).
4. Con `E_g^(b)` y los pesos de la réplica `b` se calculan todos los estadísticos de la sección 7.

Los intervalos se obtienen de los percentiles de las `B` réplicas (nivel de cobertura a decidir, p. ej. 90 % u 80 %, 012 §5). I-medición se obtiene con pesos fijos; I-diseño con exposición fija; I-total con ambos. Se reporta la **descomposición de la varianza** entre fuentes.

### 9.3 Qué NO se promete
- Los intervalos de I-medición con 3 corridas y ~8 funciones por grupo serán anchos; es un resultado, no un defecto (012 §7).
- Sin muestra humana, I-medición mide consistencia del anotador y no su exactitud (012 §5). Sin muestra de oro del matching, la parte del matching se basa en un supuesto uniforme.
- El error diferencial del matching (012 §4.7) no se corrige con esta simulación; se examina comparando S y O por estrato, y reportando la cobertura de `match_quality` por estrato.

## 10. Cómo se evita el uso doble de los datos

- **Congelar antes de ver.** G1-G3 (sección 2): la exposición, los estratos, los umbrales, las reglas de supresión, el método de intervalos y la lista de cruces quedan fijados y fechados antes de la descarga. La ENOE no modifica ningún parámetro de la exposición.
- **Partición temporal con brecha.** El periodo A es el reporte principal; el periodo B (si el humano lo aprueba) repite exactamente el plan sin cambios y se reportan ambos lado a lado (012 §8.2-§8.4). La brecha de la sección 4.4 evita viviendas compartidas. Riesgo: cambios reales entre periodos y el cambio de edición ENOE-N -> ENOE (4.1).
- **Qué se permite mirar antes de computar estadísticos:** solo controles de integridad (número de filas, tipos, hash, rango de valores, porcentaje de códigos de ocupación presentes en el catálogo), registrados en un log. Ningún cálculo de exposición por estrato antes de la firma del plan de ejecución.
- **Una sola vuelta.** No hay segunda ronda de recalibración. Si algo se modifica tras ver resultados, es una desviación (sección 14), no una corrección silenciosa.
- **Comparaciones múltiples.** El número de estratos, cruces, medidas y umbrales queda limitado por este documento; todo lo demás es exploratorio y se rotula así. No se informa solo lo que "salió".

## 11. Prohibiciones

1. Cambiar `E_g`, `alfa_S`, `beta_S`, `cota_sup_S`, los mapas, pesos, etiquetas, prompts o el matching por cualquier motivo basado en la ENOE.
2. Calibrar cualquier parámetro contra salario, ingreso, horas, formalidad o empleo (B3).
3. Parámetros de exposición distintos por formal/informal.
4. Elegir periodo, estratos, umbrales, definición de informalidad, supresión de celdas o método de intervalo después de ver resultados.
5. Excluir ocupaciones o personas "que se ven raras" sin una regla previa; los casos raros se auditan como problemas de medición.
6. Reportar solo uno de los periodos, rutas o medidas por conveniencia.
7. Usar la ENOE para decidir cuál ruta (S u O) es la correcta.
8. Descargar o consultar microdatos antes de cumplir las compuertas G1-G3.
9. Usar la exposición como "riesgo de pérdida de empleo", "riesgo de desplazamiento", probabilidad de automatización o predicción de empleo (001 §4.6).
10. Interpretar una diferencia entre estratos como diferencia de exposición dentro de la misma ocupación (sección 1).
11. Publicar microdatos de la ENOE en el repositorio público.
12. Imputar ocupaciones faltantes o inexistentes en el catálogo en el caso base.
13. Estimar efectos de la exposición sobre salarios o formalidad (regresiones causales o de "efecto"). Si se quieren asociaciones descriptivas con ingreso, deben listarse y fijarse en la sección 15, y se rotulan descriptivas (001 §8).

## 12. Etiquetado y reproducibilidad

### 12.1 Etiquetado obligatorio en tablas, figuras y texto
- La medida se llama **"exposición técnica a IA"** (001 §4.1); nunca riesgo, amenaza, pérdida o desplazamiento de empleo.
- **Mientras el matching no esté validado**, toda cifra de la ruta O lleva `sin_validar`. **Mientras no exista muestra humana**, toda cifra de exposición lleva "sin validar" (B1 sin humana mide consistencia).
- Se declara en cada tabla: ruta (S/O), medida, versión de la exposición congelada (hash), periodo, edición de la ENOE, estrato, tamaño de muestra sin ponderar, y si la celda cumple la regla de supresión.
- Se declara que las diferencias entre estratos son **composición ocupacional** de una medida constante por grupo SINCO.
- Se declara que la exposición es del contenido descrito del grupo SINCO (funciones del catálogo), no del puesto individual, y que no mide adopción, acceso a tecnología ni formalidad.

### 12.2 `enoeR`: versión, commit, descargas, hashes
- **Herramienta autorizada para descargar:** https://github.com/DiegoSReco/enoeR (rama `master`; la página mostraba 14 commits al consultar; paquete en desarrollo). **Antes de descargar:** (a) fijar el **commit** y la versión de `DESCRIPTION` (no visibles en la consulta); (b) registrar versión de R, sistema operativo y `sessionInfo()`; (c) guardar el hash del código de la función de descarga usado.
- **Licencia:** MIT según el README; NOASSERTION según la API de GitHub (reporte del orquestador). Es un paquete propio del usuario: el humano confirma la licencia del repositorio antes de depender de él; no se redistribuye código de terceros por esta vía.
- **Funciones:** el README documenta `enoe_load` (un trimestre) y marca `enoe_list` (varios trimestres) como "In Progress"; `enoe_codebook()` está planeada, no implementada. Se recomienda descargar trimestre por trimestre con `enoe_load` salvo que el humano valide `enoe_list`.
- **Verificación independiente:** antes de firmar, descargar (con autorización, tras las compuertas) un trimestre y comparar su estructura contra el diccionario de datos de INEGI; registrar el resultado. Si el paquete falla o cambia, se registra como desviación.
- **Fechas y hashes:** cada archivo descargado se registra en `data/raw/manifest.json` con sha256, fecha y hora de descarga, URL de origen de INEGI (según reporte de `enoeR`), edición, trimestre, tabla y commit de `enoeR` (regla 3: `data/raw/` es inmutable). Quien ejecute el registro debe hacerlo por script; este agente no escribe en `data/`.
- **R como herramienta externa:** el stack del proyecto es Python (CLAUDE.md). R y `enoeR` se usan solo para descargar los CSV; todo el procesamiento ocurre en Python (`src/`). El humano decide si acepta R como herramienta externa (012 §9, §13 punto 12).

### 12.3 Política de datos de la ENOE
- **No se publican microdatos de la ENOE en el repositorio público** (política indicada por el orquestador; la decisión 007 declara el repositorio público con datos publicados, de modo que los microdatos de la ENOE son una excepción explícita). Hay que impedirlo por configuración (regla de ignorado de git para la ruta de los CSV, o almacenamiento fuera del repositorio) **antes** de descargar. La regla concreta y el cambio en `.gitignore` los hace un humano o el agente de datos, no este agente.
- **Se publican solo agregados** (tablas por estrato) que cumplan la regla de supresión de la sección 7, en `data/processed/`.
- **Términos de uso de INEGI para la redistribución de microdatos:** **[NO VERIFICADO]**; no consulté los términos. Se verifican antes de descargar y de publicar cualquier tabulado derivado.
- **Dónde viven los CSV originales:** `data/raw/` (inmutable) con la regla de ignorado de git; si el humano prefiere almacenamiento externo, se registran allí hash y ruta en `manifest.json`.

### 12.4 Reproducibilidad del cómputo
- Semillas fijas y registradas para el remuestreo (sección 9); versión de Python y de librerías (`requirements.txt`).
- Cada cifra publicada tiene un script en `src/` y un archivo en `data/processed/`, con hash del insumo de exposición y de la tabla de la ENOE (regla 1 y regla 6).
- Pruebas (`pytest`) para: unión por código SINCO, cobertura, cuantiles ponderados, y que la simulación con pesos iguales y exposición constante reproduzca la media conocida. (Diseño de pruebas, sin implementarlas aquí.)

## 13. Alternativas consideradas

| Alternativa | Veredicto |
|---|---|
| A. Dos rondas con recalibración de parámetros por formal/informal (propuesta original del usuario) | No adoptada (012 §4, §12) |
| B. Reporte descriptivo por estratos con exposición congelada, un periodo | **Base de este borrador** |
| C. B + réplica en un periodo separado por una brecha | **Propuesta** como robustez (opcional; decide el humano) |
| D. B + capa B2 de aplicabilidad al contexto | Diferida (012, Registro 1) |
| E. Regresiones de ingreso sobre exposición | Prohibida como calibración; asociaciones descriptivas solo si el humano las lista (sección 11, punto 13) |
| F. Unir con SINCO 2011 mediante el anexo de equivalencia | Descartada (issue de equivalencia 2011-2019) |
| G. Usar tabulados publicados por INEGI en vez de microdatos | Posible para una parte de los estratos; no permite estimar la distribución de la exposición sin microdatos; no explorada |

## 14. Desviaciones del plan

Toda desviación se anota en un registro con fecha, motivo, qué se había visto antes de decidir y qué se cambió (012 §8.5, punto 8). Las desviaciones se reportan en el artículo. Aquí se listarán las desviaciones que ocurran después de la firma (hoy: ninguna).

## 15. Decisiones humanas pendientes (lista para firmar)

| # | Decisión | Opciones / propuesta |
|---|---|---|
| H1 | ¿Se aprueba el reporte con este plan y propósito (descriptivo, no causal, no calibra)? | Sí / no / con cambios |
| H2 | Versión de registro de la exposición congelada | (i) media de corridas; (ii) posterior B1 sin muestra humana; (iii) posterior B1 con muestra humana (propuesta si existe) |
| H3 | Ruta principal del reporte | Ruta S (propuesta) con O como contraste `sin_validar` |
| H4 | Definición de informalidad a pre-registrar | Empleo informal total; sector informal; desglose de la matriz de Hussmanns (propuesta (a) y (b) de la sección 6); variable de INEGI |
| H5 | Edición(es) y trimestres | Opciones 1 a 4 de la sección 4.3 u otra; verificación de la versión SINCO por trimestre |
| H6 | ¿Réplica en periodo B con brecha? | Sí (opción 1 o 3) / no (opción 2) |
| H7 | Estratos finales y categorías | Sección 6; en particular tamaño del establecimiento si existe; ingreso: mensual o por hora y cuantiles |
| H8 | Cruces permitidos | informalidad x sexo, informalidad x región, informalidad x educación (propuesta) |
| H9 | Umbrales de exposición alta | 0.25, 0.50, 0.75 absolutos y tercil superior congelado (propuesta) |
| H10 | Regla de supresión de celdas | `n_min` (propuesta 30) y CV máximo (propuesta 30 %) |
| H11 | Método de intervalos de diseño y número de réplicas `B` | Bootstrap por conglomerados vs. linealización; `B` (propuesta 1,000); nivel (80 % o 90 %) |
| H12 | Descomposición composicional | Estandarización directa por división y por grupo (propuesta) u otra |
| H13 | Hipótesis direccionales (H1, H2 de 012) y asociaciones descriptivas con ingreso | Listar o no |
| H14 | Aceptar R y `enoeR` como herramienta externa solo de descarga; fijar commit; confirmar licencia | Sí / no |
| H15 | Dónde se guardan los CSV de la ENOE y el cambio de configuración de git que impide publicarlos | `data/raw/` con regla de ignorado vs. almacenamiento externo; quién hace el cambio |
| H16 | Verificación de términos de uso de INEGI para tabulados derivados | Pendiente |
| H17 | Tratamiento de códigos de ocupación a menos de 4 dígitos, residuales y no especificados | Regla de agregación; sin imputación (propuesta) |
| H18 | Fecha de firma y quién firma | Humano |

## 16. Firma (vacía)

- Estado: **BORRADOR, NO FIRMADO**.
- Fecha de firma: ______ ; Firmado por: ______ ; Hash de la exposición congelada: ______ ; Commit de `enoeR`: ______ ; Decisiones H1-H18 resueltas: ______.
- Este agente no aprueba ni firma su propio documento.

## 17. Riesgos

1. **Falsa lectura causal o de "riesgo":** mitigada con etiquetado y prohibiciones (11, 12.1).
2. **Composición presentada como efecto dentro de la ocupación:** mitigada con la descomposición (8.4) y el texto obligatorio.
3. **Versión de SINCO incorrecta en algún trimestre:** unir códigos de 2011 con el catálogo 2019 produciría un cruce falso. Mitigación: verificar la versión por trimestre y excluir (4.2).
4. **Error diferencial del matching** correlacionado con informalidad (012 §4.7): puede fabricar o esconder diferencias en la ruta O. Mitigación: ruta S principal, comparación S-O por estrato, cobertura de `match_quality`.
5. **Exposición sin validar:** sin muestra humana ni muestra de oro, las cifras son provisionales (etiqueta).
6. **Herramienta de descarga en desarrollo** (`enoeR`): errores o cambios silenciosos. Mitigación: commit fijado, hashes, verificación contra el diccionario de INEGI (12.2).
7. **Cambio de edición ENOE-N -> ENOE** y cambios reales entre periodos: pueden confundir la réplica. Mitigación: declararlo; no interpretar A frente a B como cambio.
8. **Variables inexistentes** (tamaño del establecimiento, SINCO a 4 dígitos, variables de diseño muestral): obligan a recortar el plan. Mitigación: verificación previa al firmar.
9. **Ingreso mal medido:** no respuesta, redondeo y valores extremos. Mitigación: es descriptor, no resultado; reglas de tratamiento fijadas.
10. **Publicación accidental de microdatos** en un repositorio público (decisión 007). Mitigación: regla de ignorado antes de descargar (12.3).
11. **Derechos y términos de INEGI** no verificados.
12. **Dependencia circular con la muestra humana y la corrida completa:** G1 puede tardar; el calendario no es controlado por este plan.
13. **Pocas funciones por grupo** y shrinkage de B1 aplanando diferencias (012 riesgo 2): se reporta con y sin pooling si hay B1.
14. **Datos de segunda mano:** todo lo de INEGI en este documento viene de resúmenes de buscador; los PDF no se abrieron.

## 18. Lista de [NO VERIFICADO]

- Versión de SINCO por trimestre (2019 desde 2021T3 según un resumen; nada sobre 2023 en adelante) y número de dígitos del código.
- Comparabilidad de ENOE, ENOE-N y ENOE 2023T1+.
- Esquema de visitas del panel (cinco trimestres) y cómo identificar la vivienda.
- Nombres y definiciones exactas de variables: ocupación principal, factor de expansión, estrato de diseño, unidad primaria de muestreo, condición de ocupación, informalidad, tamaño del establecimiento, ingresos, escolaridad, sector.
- Regla de INEGI para combinar trimestres y para estimar varianzas.
- Texto literal de la definición de informalidad de INEGI.
- Existencia de tamaño del establecimiento en la ENOE.
- Términos de uso/redistribución de los microdatos de INEGI.
- Versión, commit y licencia efectiva de `enoeR`; comportamiento de `enoe_load` y `enoe_list`; instalación de R en este equipo.
- Contenido de 005, 008 y 009; existencia de la muestra de oro del matching.
- Que la cita del usuario relayada por el orquestador sea textual.

## 19. Fuentes consultadas (2026-10-19)

- `enoeR`, repositorio del usuario: https://github.com/DiegoSReco/enoeR (WebFetch, resumen de herramienta; ediciones, tablas, funciones, estado "In Progress", MIT en el README; versión y commit no visibles). README leído además por el orquestador (reporte).
- INEGI, nota de clasificaciones del 3T 2021 de la ENOE Nueva Edición (SINCO 2019 desde ese trimestre; solo resumen de resultado de búsqueda, **no abierto**): https://inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_nota_clasificaciones_trim3_2021.pdf
- INEGI, clasificaciones de la ENOE (no abierto): https://inegi.org.mx/contenidos/programas/enoe/15ymas/doc/clasificaciones_enoe_123.pdf
- Informalidad (resultados de búsqueda, no abiertos): presentación de INEGI en la CEPAL https://www.cepal.org/sites/default/files/presentations/20190404_16._heredia-inegi.pdf ; Negrete, INEGI/WIEGO https://wiego.org/wp-content/uploads/2019/09/Negrete-Measurement-Issues.pdf ; ficha del Banco Mundial (variable armonizada de sector informal, otra fuente) https://microdata.worldbank.org/catalog/7720/variable/MX2009H_TUE_PPAL
- Diseño muestral de la ENOE (resumen del catálogo de INEGI, vía 012): https://www.inegi.org.mx/rnm/index.php/catalog/1105
- Gelman y Loken, forking paths (vía 012): https://forrt.org/glossary/english/garden_of_forking_paths/
- Documentos del proyecto: `CLAUDE.md`; `docs/decisions/001-definicion-exposicion.md` (con enmiendas aplicadas), `011-metodo-tipo-anthropic-eloundou-sinco.md`, `012-calibracion-bayesiana-enoe.md`; issue `docs/issues/datos-2026-10-19-sinco-anexo-equivalencia-descartado.md` (citado por 012; no releído en esta tarea).
