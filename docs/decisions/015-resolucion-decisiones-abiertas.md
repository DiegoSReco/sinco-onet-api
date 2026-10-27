# 015 - Resolución de las decisiones abiertas (001 a 014), enmiendas E-4 a E-7, corrida completa de anotación (ruta S) y despliegue

> **ESTADO: APROBADA POR EL USUARIO en lo que sigue, por su instrucción "Aprobar todas las decisiones abiertas" (2026-10-19, ver "Registro de aprobación"). Esta decisión PREVALECE sobre los estados "pendiente" de 001 a 014 en lo que resuelve.** Salvo las excepciones de la sección 1.2 (hechos externos que no se resuelven por decreto) y las que la sección 7 lista como no decretables. Los valores marcados origen **C** (criterio conservador fijado aquí) o **P** (provisional ya documentado) quedan además **pendientes de revisión humana en su valor concreto**: una aprobación en bloque aprueba el mecanismo de adopción, no puede haber visto valores que nacen en este documento.

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de las fuentes web: 2026-10-19
- Esta decisión **no modifica** `docs/rubric.md` ni `docs/glossary.md` (regla 2). Entrega el texto final de E-6 y E-7 (sección 2) para que el orquestador lo aplique; la regla 2 queda satisfecha por esta decisión registrada. Tampoco escribe en `data/`, `src/` ni `paper/`.

## Registro de aprobación

Cita textual del usuario, tal como la recibí del orquestador (2026-10-19): "Resolver corrida completa. Aprobar todas las decisiones abiertas. Mejora UX en API. Quiero mostrar una forma mas amigable la conexión SINCO y O*NET. Despues de aprobar esto manten abierta la API y comienza con el despliegue. Utiliza el repositorio para el despliegue."

- **Procedencia:** yo no recibí el mensaje directamente del usuario; el orquestador lo cita como textual. Un mensaje de un agente no es consentimiento: el humano debe cotejar la cita en la conversación. Si no coincide, esta decisión pasa a "pendiente de revisión humana" completa.
- **Alcance de "aprobar todas" (lectura mía, sin ampliar):** se adopta, para cada pregunta abierta o "requiere decisión" de 001 a 014, (a) la recomendación explícita del documento si existe, (b) el valor provisional ya documentado si solo existe ese, (c) si no hay ninguno, la opción más conservadora y reversible, dicho aquí con razones. No aprueba hechos externos (1.2), no firma el pre-registro 013 (7.1), no autoriza cifras en el artículo (regla 6) ni valida nada.
- **"Mejora UX en API" y "forma más amigable la conexión SINCO y O*NET":** instrucciones de implementación. No son decisiones metodológicas; no las especifico. Restricción que sí registro: la presentación amigable del emparejamiento conserva los rótulos obligatorios (no validado, `fuente`, `estado_validacion`, 004) y no sirve exposición (4.3).

## Qué se leyó y qué no

**Leído completo:** `CLAUDE.md` (en contexto), 001, 003 (`003-requisitos-tablas-sinco.md`), 004 (el archivo se llama `004-api-despliegue.md`), 006, 007 (`007-repositorio-publico.md`), 008 (`008-piloto-anotacion.md`), 010, 011, 012, 013, 014; `docs/rubric.md` y `docs/glossary.md` (versión 1); `src/score/config.toml`, `src/score/README.md`, `src/annotate/config.toml`, `src/calibrate/config.toml`, `src/calibrate/README.md`, `src/match/revision_manual_config.toml`; el issue `docs/issues/emparejamiento-2026-10-19-parametros-provisionales-y-sin-coincidencia.md`.

**No pude abrir (mi herramienta no lista directorios; probé varios nombres y no existen con ellos):** 002, 005, 009 y el resto de `docs/issues/` (incluidos el issue de la muestra de oro y los `score-2026-10-19-*`). Todo lo que digo de ellos proviene de lo que citan los demás documentos y del encargo del orquestador y queda **[NO VERIFICADO]**: en particular, el umbral kappa 0.60 de la muestra de oro, los umbrales de cobertura 0.5/0.95 (estos sí aparecen en `src/score/config.toml`, verificado) y los hiperparámetros de B1 (verificados en `src/calibrate/config.toml`). No inspeccioné `data/processed/` ni `data/raw/manifest.json`.

## 1. Tabla maestra de resolución

Leyenda de **origen**: **R** = recomendación explícita del documento; **P** = valor provisional ya documentado en un documento, issue o config (se adopta como provisional revisable); **C** = criterio conservador y reversible fijado aquí (con razón). **Rev.** = reversible sin rehacer cómputo costoso (S) o con rehacer cómputo (N). Si una pregunta ya estaba APROBADA en el propio documento, no se repite.

### 1.1 Preguntas resueltas

| ID | Doc | Pregunta | Valor adoptado | Origen | Rev. |
|---|---|---|---|---|---|
| M1 | 001 P3 | Fecha de corte de capacidades (corrida completa) | Fecha de cada corrida (se registra por lote; ver 3.8). Misma regla del piloto | P (008 §2.6; 011 §4.e) | S |
| M2 | 001 P3 / 008 §7.1 | Modelo y vía del anotador (corrida completa) | `claude-sonnet-5-5 (subagente Claude Code)`, sin API, sin clave, sin gasto de dinero; 3 corridas | P (008 §2; 010 §4-A) | S |
| M3 | 001 P6 / 010 P8 / 011 P6 | Fuente de empleo para pesos del crosswalk y niveles superiores | Pesos de crosswalk uniformes (ya aprobado). Niveles superiores: promedio no ponderado rotulado "descriptivo, no ponderado por empleo" hasta firmar 013; luego ENOE por 013. No se elige OEWS ni otra fuente de EE. UU. | C (010 §3.6; 013) | S |
| M4 | 001 P7 | Ajuste por brecha digital/informalidad como medida secundaria | **No hay medida ajustada.** Solo el reporte descriptivo por estratos de 013. B2 queda diferido | P (012 Registro 1) | S |
| M5 | 001 P8 | Puntajes OIT como referencia "principal" | **No.** Son una referencia convergente más; no hay validación OIT mientras no exista el puente SINCO-CIUO-08 (003 Método B, no implementado) | C (001 no la recomienda) | S |
| M6 | 001 P10 | Diseño estadístico (acuerdo, intervalos, remuestreo) | El de la sección 3.9 de esta decisión, que consolida 010 §6, 011 §4.g, 012 B1 y 013 §9. No se abre un archivo nuevo para el diseño | R (010/011/012) | S |
| M7 | 003 P2 | Conteo de grupos unitarios | 490, el documentado en `docs/diccionario_datos_sinco.md` y usado por 010 | P | S |
| M8 | 003 P4 / P12 | Mapeo semiautomático SINCO -> CIUO-08 | Sigue "autorizado en principio, no se implementa" (003 Registro 2). Quién valida y con qué guía: no aplica hasta que el usuario lo pida | R (003) | S |
| M9 | 003 P6 | LLM para reordenar candidatos de crosswalk | **No** (005 R.2 no aprueba ningún LLM ni API) | C | S |
| M10 | 003 P7 | Peso numérico de parejas "amplias" | No aplica hasta Método B. Si se implementa: fuera del caso base, solo sensibilidad | C | S |
| M11 | 003 P10 | Texto de CIUO-08 en español y licencia | Sin uso; sin verificación. Se retoma solo si se pide Método B | C | S |
| M12 | 004 P5 | Texto exacto de atribución | El de la sección 4.5 | R (004: atribuir a O*NET e INEGI) + consulta de fuente | S |
| M13 | 004 P6 | Hosting público, autenticación, CORS, costos | Sección 4: sitio estático en GitHub Pages; todo solo lectura; sin autenticación; sin costo; contenedor preparado, no ejecutado | C | S |
| M14 | 004 P7 / Reg. 4 | Columnas opcionales del crosswalk (Método A1) y `opentelemetry-api` transitiva | **Aprobadas** ambas. Condición: la lista blanca y la prueba de fuga deben tratar `similitud`, `margen`, `rango`, `baja_confianza` como medidas de emparejamiento, no como scores de exposición | P (004 Reg. 4) | S |
| M15 | 004 P8 / Reg. 5 | Formato, límites y filtros de descargas | Archivos pregenerados CSV y Parquet estáticos en el sitio (sin límites dinámicos). Para la API: los límites ya implementados, que el implementador documenta. No invento cifras. Detalle de 009 §4.2 no leído | C | S |
| M16 | 005/issue | delta, tau, umbrales baja_confianza / sin_coincidencia, k | Los de la tabla del issue de emparejamiento (bge-m3: delta 0.04, tau 0.05; e5: 0.02/0.02; cuantiles 0.10 y 0.05; k = 10, rango máx. 5). Provisionales, sin calibrar | P (issue) | S |
| M17 | 005/issue | Modelo principal del emparejamiento | `bge-m3` provisional | P (issue) | S |
| M18 | 005/009 | k_top del emparejamiento | 2 (top-2) | P (001 §4.5; 010; src/score) | S |
| M19 | 005 (R.7) | Umbral kappa de la muestra de oro | 0.60, provisional revisable. **Valor tomado del encargo del orquestador; no pude abrir el issue** | P [NO VERIFICADO] | S |
| M20 | 007 P1 | Licencia de la documentación y de los datos publicados | Código: MIT (ya decidido). Documentación y datos derivados: **sin licencia añadida** (todos los derechos reservados por omisión) con las atribuciones de terceros obligatorias; abrir una licencia después es posible, retirarla no | C | S |
| M21 | 007 P3 | PDF de F-O y tabla cruda de 702 filas | **No se publican** (interpretación del orquestador, adoptada). Solo tablas derivadas de SINCO | C | S (si no se publicó) |
| M22 | 007 P4 | Mitigación mínima de la licencia de F-O | Adoptada: atribución y cita completa en README, sitio y descargas; compromiso de retirar a petición del titular; rótulo permanente "probabilidad de automatización (Frey-Osborne)", NO validada | R (007 §2.2) | S |
| M23 | 007 P5 | Enlaces de `docs/decisions` a `docs/issues` no publicado | `docs/issues/` no se publica; el README lo dice (nota de que los issues viven en el repositorio local) | C | S |
| M24 | 007 P8 | Publicar `CLAUDE.md` | No. El README resume las reglas que los documentos citan por número | R (007) | S |
| M25 | 008 §7.2 | Traducción frente a inglés (corrida completa) | Ruta S: **español original de SINCO**, sin traducción. Ruta O (diferida): inglés original; la traducción sigue sin resolver | C | S |
| M26 | 008 §7.3 | 418 tareas O*NET sin tipo core/supplemental | Fuera de la medida principal (001 §4.4 usa core); entran solo en la variante `E_o_todas`. Sin imputar. Aplica a la ruta O (diferida) | P (`src/score/config.toml`) | S |
| M27 | 008 §7.4 | Umbral de "acuerdo aceptable" entre corridas | Kappa ponderado cuadrático >= 0.60 por campo como condición para usar el campo en cifras principales; por debajo se reporta con rótulo "consistencia insuficiente". Alfa de Krippendorff ordinal: se reporta, sin umbral | P (M19) / C | S |
| M28 | 008 §7.5 | Contradicción API / sin API | Prevalece **sin API** (confirmado por el encargo del orquestador: "sin API ni clave") | R (008 §3) | N si luego se usa API |
| M29 | 008 §7.7 / 010 P3 / 011 P7 | Referencia humana: quiénes, cuántas | 300 funciones + 49 grupos; el usuario como revisor 1; segundo revisor opcional (3.10) | C | S |
| M30 | 010 P1 | Ruta S como plan principal | Sí (E-1 aprobada). La ruta O es contraste diferido | R (011) | S |
| M31 | 010 P4 | Umbral `pocas_funciones` (< 3) | 3, provisional | P (010 §3.6) | S |
| M32 | 010 P4 | Umbrales de discrepancia del Método C (0.25 y 0.50) | 0.25 y 0.50, provisionales; **solo operan si se activa C (requiere ruta O)**; 010 §6.5 prevé sensibilidad 0.20/0.25/0.30 | P (010 §4-C) | S |
| M33 | 010 P5 | 33 residuales | `E = NA`, `motivo_na = "residual_sin_funciones"`, sin imputar. No se ejecuta la sensibilidad con imputación | R (010 §3.3) | S |
| M34 | 010 P6 | `Excluye` y erratas en el prompt | `Excluye` fuera del prompt; ejemplos de 5115 fuera del contexto; función fusionada de 2281 anotada y marcada `item_fusionado` | R (010 §3.1-3.2) | S |
| M35 | 010 P7 | Embeddings como Método B de exposición | **No se autoriza** (dependencia nueva; no es medición independiente). El uso de embeddings del emparejamiento (`src/match`) no cambia | C | S |
| M36 | 010 P9 / 011 | Puente SINCO -> CIUO-08 para validar con OIT | No. Sin validación OIT | C | S |
| M37 | 011 P3 | Etiquetas por tarea de Eloundou públicas | Comparación a nivel ocupación con `occ_level.csv` si existe y su licencia lo permite; no hay réplica tarea a tarea garantizada. Existencia de etiquetas por tarea: **[NO VERIFICADO]** | R (011 §4.g.3) | S |
| M38 | 011 P4 | Segundo modelo anotador | No (sin API) | C | S |
| M39 | 011 P5 | Preámbulo literal de 2023 o actualizado | Literal de 2023 en `ann-s-v1`. Una variante actualizada sería otro prompt y otra decisión; no se corre ahora | R (011 §4.e) | S |
| M40 | 011 §4.e | Calibración con 60 funciones | No se separa conjunto de calibración: cualquier ajuste del prompt crea una `prompt_version` nueva y la muestra humana está congelada antes (3.5, 3.10) | C | S |
| M41 | 011 §4.g.3 | Prueba de contaminación entre campos (un campo por llamada) | Ablación opcional en 300 funciones, después de aceptar la corrida; no es condición de aceptación | R (011/010) | S |
| M42 | 012 P3 | Partición de la ENOE | Temporal con brecha (la que 012 recomienda), sujeta a 013 | R (012 §8.2) | S |
| M43 | 012 P6 | Dependencia bayesiana | **No.** Gibbs conjugado propio en numpy (ya implementado en `src/calibrate`). Jerarquía y modelo ordinal con efecto de función quedan sin implementar | R (012 §9, opción 1) | S |
| M44 | 012 P8 | Hipótesis direccionales | **Ninguna pre-registrada.** Solo el control negativo `physical_bottleneck` (011 §4.g.6) con grupos de contraste que elige el usuario antes de ver resultados. El usuario puede añadir hipótesis antes de firmar 013 | C (012 las dejó "a fijar por el humano") | S |
| M45 | 012 P12 / 013 H14 | R y `enoeR` como herramienta externa | Aceptado solo para descargar, con commit fijado, y solo después de las compuertas G1-G3 | R (012 Registro 1) | S |
| M46 | 013 H1 | Plan y propósito del reporte | Descriptivo, no causal, no calibra | R (013) | S |
| M47 | 013 H2 | Versión de registro de la exposición congelada | (iii) posterior de B1 con muestra humana si existe; si no, (i) media de corridas con intervalos entre corridas, y se dice | R (013 §3) | S |
| M48 | 013 H3 | Ruta principal | Ruta S; ruta O como contraste `sin_validar` si existe | R | S |
| M49 | 013 H4 | Definición de informalidad | Propuesta (a) empleo informal frente a formal y (b) desglose de la matriz de Hussmanns. **La variable de INEGI y el texto literal siguen sin verificar** | R, con verificación pendiente | S |
| M50 | 013 H5 / H6 | Edición, trimestres y réplica | Opción 1 (A = 2022T1-T4, B = 2024T1-T4). **Condición:** verificar SINCO 2019 en 2022T1-T2 y el esquema de panel; si falla cualquiera, opción 2 (2024T1-T4 sin réplica) | R (013 §4.3) / C | S |
| M51 | 013 H7 | Estratos | Los de 013 §6; tamaño del establecimiento solo si la variable existe | R | S |
| M52 | 013 H8 | Cruces | informalidad x sexo, x región agrupada, x educación | R | S |
| M53 | 013 H9 | Umbrales de exposición alta | 0.25, 0.50, 0.75 absolutos y tercil superior congelado | R | S |
| M54 | 013 H10 | Supresión de celdas | `n_min` = 30; CV máximo 30 % | R (PROVISIONAL en 013) | S |
| M55 | 013 H11 | Intervalos de diseño | Bootstrap por conglomerados; B = 1,000; nivel 90 % (igual que `src/calibrate/config.toml`) | R (PROVISIONAL en 013) | S |
| M56 | 013 H12 | Descomposición | Estandarización directa por división y por grupo | R | S |
| M57 | 013 H13 | Asociaciones descriptivas con ingreso | No se listan; solo el ingreso como descriptor de estrato | C | S |
| M58 | 013 H15 | Dónde viven los CSV de la ENOE | `data/raw/` con regla de ignorado de git antes de descargar; la regla la aplica el agente de datos o el usuario, no yo | R (013 §12.3) | S |
| M59 | 013 H17 | Códigos a menos de 4 dígitos, residuales, no especificados | Sin imputación; categorías separadas en el reporte de cobertura | R | S |
| M60 | 014 B5.1 | Circularidad por revisión manual | La muestra de oro (255 grupos) y el matching automático evalúan; la revisión manual solo corrige. Los grupos corregidos dentro de la muestra de oro se marcan `corregido_manual` y no se usan para calibrar y evaluar a la vez | R (014) | S |
| M61 | 014 B5.2 | Revisor ciego | Ideal: ocultar similitudes y aleatorizar candidatos. Si la exportación ya mostró rangos, se declara el sesgo de anclaje y la tasa ACEPTAR_RANGO1 no se presenta como precisión del modelo. **Cómo se exportó: [NO VERIFICADO]** | C | S |
| M62 | 014 B5.3 | Criterio de NINGUNO | Juicio del revisor, con comentario obligatorio; se listan aparte; ante duda, buscar en O*NET antes de marcar | R (014) / encargo | S |
| M63 | 014 B5.4 | DUDA | Se ignora (queda el automático con su bandera) y se lista | R (014) | S |
| M64 | 014 B5.5 | Un revisor o dos | Un revisor con etiqueta `revision_manual_1_revisor`; segundo revisor sobre submuestra solo si el usuario lo consigue | R (014) | S |
| M65 | 014 B5.6 | Grupos `ok` | Muestreo del 5 % de los grupos `ok`, en ciego y mezclados, para estimar su tasa de error. Con 407 grupos `ok` (490 - 83, cifras de 014 no recalculadas) son unos 21 grupos; el intervalo de Wilson será ancho (con cero errores en 21, el límite superior al 95 % ronda 15 %; cálculo ilustrativo, el script lo recalcula) | R (encargo) | S |
| M66 | 014 B5.7 | Versionado | La revisión manual se versiona con sha256 y fecha en `match_corridas`; ubicación `data/processed/revision_manual/` (no en `data/raw/`) | R (014) / C | S |
| M67 | 014 B5.8 | Propagación al matching | Los pares manuales no tienen error cero: los intervalos conservan la incertidumbre de emparejamiento (min-max), y se usa la tasa de error de la submuestra doble si existe | R (014) | S |
| M68 | 014 B5.9 | Grupos NINGUNO en agregados | Se excluyen con cobertura reportada; sin imputación | C | S |
| M69 | 014 B5.10 | Probabilidades ya publicadas | No sobrescribir: versión nueva con etiqueta de corrida; se mantienen ambas | R (014) | S |
| M70 | 014 B5.11 | Pares manuales y salida alternativa (e5) | Solo modelo principal (`aplica_a_modelo = "principal"`) | P (config) | S |
| M71 | 014 B5.12 | Umbral absoluto de `sin_coincidencia` | Se propone después de la revisión; hoy sigue el cuantil | P | S |
| M72 | 014 B.3 | Evaluación | Siempre "automático" frente a "automático + manual" | R (014) / encargo | S |
| M73 | 014 A.5 | Experimentos de diagnóstico del emparejamiento | Autorizados en principio, sin dependencias nuevas: (ii) texto mínimo, (iii) tareas O*NET en el lado inglés, (iv) igualar truncamiento, (v) análisis por división, control recall@10. **No** autorizados: (i) traducción automática y (vi) reranqueo con modelo o LLM (dependencia o API). Comparaciones pareadas con corrección por comparaciones múltiples | R (014) / C | S |
| M74 | 001 P9 | Referencias a completar (AIOE, Webb, Arntz, etc.) | No es decisión: tarea humana; sigue abierta (sección 6) | n/a | n/a |

### 1.2 Excepciones: hechos externos que NO se resuelven por decreto

| Tema | Estado | Qué se hace mientras tanto | Responsable |
|---|---|---|---|
| Términos de redistribución de INEGI | **Verificación pendiente.** Evidencia parcial de esta fecha (resumen de herramienta de https://www.inegi.org.mx/inegi/terminos.html): la sección "Del libre uso" permite copiar, distribuir, difundir, adaptar, reordenar, extraer y explotar la información, sin alterar ni suprimir sus metadatos, con crédito a INEGI como autor, mención de la fuente ("Fuente: INEGI, nombre del producto"), aviso al usuario final de transformaciones y sin aparentar postura oficial. La sección leída no menciona microdatos. No es lectura jurídica primaria | Se publican las tablas del catálogo SINCO con la atribución y el aviso de transformación de 4.5. **Los microdatos de la ENOE no se publican** (013 §12.3) y no se descarga nada antes de verificar sus términos (013 H16) | Usuario |
| Licencia de Frey-Osborne | **Riesgo aceptado por el usuario, no resuelto** (007 §2.2) | Mitigación M22; no se publican PDF ni tabla cruda | Usuario (titular de derechos: Frey y Osborne / Oxford Martin) |
| Símbolo griego de la tercera medida de Eloundou | **Verificación pendiente** (glifo ilegible en el texto extraído; el README del repositorio de Eloundou dice "gamma") | Se nombra `cota_sup_S` por su definición (E-3, E-8) | Quien abra `eloundou_2023_v5_pdf` y mire el glifo (el usuario) |
| Verificación humana de cifras citadas | **Pendiente** (cifras de Ceballos y Guadarrama, páginas de Eloundou, 47 %, etc.) | Ninguna cifra de literatura se cita en el artículo sin cotejo; las cifras propias salen de `data/processed/` (regla 6) | Usuario o revisor humano |

## 2. Enmiendas E-4, E-5, E-6 y E-7 (011 §5): APROBADAS

Con el Registro 4 de 011 ya estaban aprobadas E-1, E-2, E-3 y E-8. Esta decisión aprueba E-4 a E-7 con el texto exacto de abajo. **Quién aplica qué:** el orquestador aplica E-6 y E-7 (archivos protegidos, regla 2); un implementador aplica E-5 en el esquema; E-4 se inserta en 001 §4.4 (edición de 001 por el agente de métodos o el orquestador, a instrucción del usuario).

### E-4. Se añade al final de 001 §4.4

> **Ruta S:** media de pesos iguales sobre todas las funciones del grupo (SINCO no distingue core/supplemental). **Ruta O, variante:** core con peso 2 y supplemental con peso 1, normalizados a suma 1 por ocupación (Eloundou et al. 2023, p. 8, notas 6-7); Eloundou usa pesos iguales en varias de sus figuras y tablas, de modo que la variante debe declararse en cada resultado.

### E-5. Se añade al final de 001 §7 (esquema)

> **Campos añadidos (E-5):** `eloundou_class` (EL0/EL1/EL2/EL3; etiqueta cruda, EL3 se funde en EL2 solo en las medidas), `sinco_code`, `orden`, `route` (S/O). Regla: en la ruta S, un registro por (`run_id`, `sinco_code`, `orden`); en la ruta O, un registro por (`run_id`, `task_id`). En la ruta S los campos `onet_soc`, `task_id`, `task_text_en`, `task_text_es` y `task_type` son nulos; en la ruta O lo son `sinco_code` y `orden`.

**E-5b (adición de esta decisión, necesaria para el protocolo de 3.7; no estaba en 011).** Se añade a 001 §7: `function_text_es` (texto original de la función SINCO, ruta S), `prompt_sha256`, `batch_id` (lote), `attempt` (número de intento del lote), `capability_cutoff` (fecha de corte = fecha del lote), `temperature_requested`, `temperature_controlled` (booleano; falso en subagentes) y `temperature_note`, `item_fusionado` (booleano, para 2281), `source_sha256` (`sinco_fuente.sha256`). El implementador del esquema puede pedir ajustes de nombre; no de contenido.

### E-6. Texto final de `docs/rubric.md` (versión 2)

Sustituye el archivo completo. Cambios respecto de la versión 1: encabezado; primera línea (ruta S y ruta O); campo 5 `eloundou_class`; sección de Eloundou con el texto literal; mapas `*_S`; una línea de agregación de la ruta S (derivada de E-4); trazabilidad. Todo lo demás es idéntico a la versión 1.

~~~~markdown
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
~~~~

### E-7. Texto final de `docs/glossary.md` (versión 2)

Sustituye el archivo completo. Se añaden los términos de E-7; se **omiten** "cobertura de uso externa" y "mezcla de tareas de usuarios de Claude.ai en México" porque el usuario descartó la capa de uso observado (011 Registro 3; 011 dejaba la omisión al humano). Se añade "Función (SINCO)" por consistencia con E-1 (adición de esta decisión).

~~~~markdown
# Glosario (versión 2; decisiones 001, 005, 006 y 015)

- Exposición: grado en que un sistema de IA podría ejecutar una tarea, o reducir sustancialmente el esfuerzo humano para ejecutarla, con calidad comparable. Es una propiedad técnica de la tarea; no implica adopción ni pérdida de empleo.
- Exposición teórica: exposición medida por anotación del contenido de tareas o funciones, sin datos de uso observado. Es la única capa que reporta este proyecto.
- Exposición de una ocupación (`E_o`): promedio de los puntajes de exposición de sus tareas centrales (E0 = 0, E1 = 0.5, E2 = 1), con pesos iguales como medida principal.
- `share_E2`: proporción de tareas de una ocupación con `exposure_class` E2. `share_any`: proporción con E1 o E2. Son las lecturas de "fracción de tareas".
- `exposure_class`: clase ordinal de la tarea (E0 sin exposición, E1 exposición con apoyo, E2 exposición directa).
- `eloundou_class`: clase ordinal EL0/EL1/EL2/EL3 según la rúbrica literal de Eloundou et al. (2023), apéndice A.1. Es un campo independiente de `exposure_class`; no se convierte una escala en otra por regla. EL3 (capacidades de imagen) se anota por separado y se funde con EL2 en las medidas.
- `alfa_S`: medida de comparación con Eloundou = proporción de EL1. `beta_S`: EL1 + 0.5·EL2. `cota_sup_S`: EL1 + EL2 (EL3 dentro de EL2); es la tercera medida de Eloundou y el nombre de su símbolo griego no está verificado.
- Ruta S: medición con la función SINCO como unidad (tabla `sinco_funciones`) y agregación al grupo unitario, sin crosswalk. Ruta O: medición con la tarea O*NET como unidad, agregación a O*NET-SOC y traslado a SINCO por emparejamiento. Todo resultado lleva la etiqueta de su ruta.
- Función (SINCO): ítem de la lista de funciones de un grupo unitario del catálogo SINCO 2019; unidad de anotación de la ruta S.
- `physical_bottleneck`: indicador de que la tarea exige presencia física o destreza manual como componente central.
- Pérdida de empleo: fenómeno distinto de la exposición. Los escenarios de pérdida se reportan aparte y con supuestos explícitos; no se derivan mecánicamente de la exposición.
- Probabilidad de automatización (Frey-Osborne): probabilidad de computarización de una ocupación completa de EE. UU. (Frey y Osborne, 2013), trasladada a SINCO 2019 mediante emparejamiento. No es exposición ni riesgo de pérdida de empleo; se usa como variable comparativa. Los resultados del emparejamiento se rotulan NO validados hasta pasar la muestra de oro.
- SINCO: Sistema Nacional de Clasificación de Ocupaciones 2019 (INEGI).
- Grupo unitario (SINCO): nivel de 4 dígitos, unidad principal de análisis y reporte.
- CIUO-08: Clasificación Internacional Uniforme de Ocupaciones 2008 (ISCO-08).
- O*NET-SOC: clasificación de ocupaciones de O*NET.
- Crosswalk: correspondencia entre clasificaciones; puede ser 1:1, 1:N, N:1 o M:N. Se conserva el tipo de relación y la incertidumbre.
~~~~

## 3. Corrida completa de anotación (008 §7, 010, 011): resolución operativa

### 3.1 Alcance y ruta primaria

- **Corrida completa primaria = ruta S**: función SINCO -> grupo unitario, sin crosswalk. Universo (conteos documentados, no recalculados por mí): 490 grupos; **3,542 funciones en 457 grupos** (7.75 por grupo); **33 grupos sin funciones -> `E = NA`, `motivo_na = "residual_sin_funciones"`, sin imputar** (M33).
- Contexto por función: título del grupo, descripción y ocupaciones ejemplo (sin los de 5115 por errata). `Excluye` y `Incluye` no entran al prompt principal. La función fusionada de 2281 se anota como un ítem y se marca `item_fusionado`; sensibilidad: excluirla.
- Texto en **español original**; las rúbricas van como en 3.5.

### 3.2 Ruta O: DIFERIDA como contraste (fuera de esta corrida)

- **Costo (011 §4.f, supuestos de tokens NO medidos, con 19,265 tareas de O*NET 27.2 como cota; el total de 31.0 del proyecto es [NO VERIFICADO]):** ruta S ≈ 0.79 M tokens de entrada y 0.83 M de salida en 138 llamadas con lotes de 10 grupos; ruta O ≈ 4.62 M de entrada y 4.51 M de salida en 1,446 llamadas (lotes de 40 tareas). La ruta O cuesta del orden de 5.9 veces la entrada, 5.4 veces la salida y 10.5 veces las llamadas de la S, contra una cuota de sesión de cifra desconocida.
- **Razones para diferir:** (1) la cuota de subagentes es el límite real y no está medida; (2) el producto de la ruta O depende del crosswalk `sin_validar`, de modo que no mejora la medida principal hoy; (3) hay problemas abiertos que no se resuelven por decreto: 418 tareas sin tipo, traducción frente a inglés, tamaño real del universo; (4) el valor de la ruta O es diagnóstico (discrepancia `E_A - E_O`, Método C), útil solo cuando S esté aceptada.
- **Cuándo se reabre:** decisión nueva del usuario, tras la aceptación de la corrida S (3.9), con medición real de tokens y cuota. Reversible: no se pierde nada (el piloto O de 40 tareas, `ann-v1`, sigue siendo `PILOTO, NO RESULTADO`).

### 3.3 Campos por función

`exposure_class` (E0/E1/E2, 001), `eloundou_class` (EL0/EL1/EL2/EL3, E-2), `physical_bottleneck` (booleano), `confidence` (alta/media/baja), `rationale` (texto de máximo 25 palabras, para limitar tokens de salida; valor C). Esquema: 001 §7 con E-5 y E-5b. Los dos campos de clase se piden de manera independiente (riesgo de contaminación: 011 riesgo 2; ablación opcional, M41).

### 3.4 Anotador y corridas

- Subagentes de Claude Code, `claude-sonnet-5-5 (subagente Claude Code)`, **sin API, sin clave, sin gasto de dinero** (M2, M28). Temperatura no controlable: se registra `temperature_requested = null`, `temperature_controlled = false`, `temperature_note = "no controlable en subagentes; valor por defecto de la sesión"` (como en 008). No se promete reproducibilidad exacta.
- **3 corridas independientes:** cada lote de cada corrida lo hace un subagente **nuevo** que recibe el contenido del lote **dentro del mensaje** y no recibe rutas a otras corridas. Se le indica no usar herramientas ni leer archivos. La independencia la garantiza el orquestador, no una barrera técnica, y así se declara.
- Orden propio por corrida: semilla `seed_base + k` (`seed_base = 20261019`, `k = 1, 2, 3`, de `src/annotate/config.toml`); se baraja el orden de grupos y el de funciones dentro del grupo, y los lotes salen de partir esa lista. Los lotes difieren entre corridas (reduce el anclaje compartido).

### 3.5 Prompt `ann-s-v1`

- Nueva `prompt_version = "ann-s-v1"` (sustituye al nombre provisional `ann-v2-sinco-el` de 011/013; `ann-v1` no se modifica). Se guarda el archivo del prompt con su `prompt_sha256` en el registro de cada lote.
- Contenido, en este orden: (a) tarea y formato de salida, en español; (b) la rúbrica de 001/`docs/rubric.md` v2 (`exposure_class`, `physical_bottleneck`, `confidence`), en español como está; (c) la rúbrica de Eloundou **en inglés literal** (E-6), con los cinco ejemplos de software y los cinco ejemplos de anotación copiados completos del PDF `eloundou_2023_v5_pdf`; (d) una línea fuera del texto literal que dice que E0/E1/E2/E3 del bloque (c) se devuelven como EL0/EL1/EL2/EL3 y no son las clases del bloque (b); (e) la instrucción de clasificar ambos campos de manera independiente; (f) el contexto de cada grupo y sus funciones en español original, con `function_id = sinco_code + orden`.
- El preámbulo de 2023 se mantiene literal (M39). Que el anotador sea un modelo de otra empresa que el que nombra el preámbulo es una desviación que se registra, no se corrige.
- **Inmutabilidad:** una vez registrada cualquier corrida con `ann-s-v1`, no se edita. Cualquier cambio de texto es `ann-s-v2` y obliga a repetir las corridas afectadas. No se cambia el prompt a mitad de una corrida.

### 3.6 Lotes

- **N = 10 grupos por lote, con tope de 120 funciones** (un lote se cierra al llegar a 10 grupos o a 120 funciones). Esto da del orden de **46 a 50 lotes por corrida** (el número exacto lo calcula el script) y de 138 a 150 invocaciones en 3 corridas.
- **Razones (C, con base en 010 §4-A y 011 §4.f):** (a) con un grupo por llamada el prompt fijo (probablemente de miles de tokens, 011 §4.f advierte que 1,000 se queda corto) se paga 457 veces por corrida; con 10 grupos, 46 veces; (b) más de 12 grupos por lote aumenta el anclaje entre grupos y el riesgo de que una respuesta salga incompleta; (c) 10 grupos son unas 78 funciones y unos 6,000 a 8,000 tokens de salida, manejable; (d) un lote rechazado se reintenta barato. El anclaje entre grupos del mismo lote se mide con la ablación de M41 y se mitiga porque los lotes difieren entre corridas. Reversible: cambiar N en otra corrida es un factor de sensibilidad.

### 3.7 Protocolo reanudable

Rutas (propuesta; el implementador puede ajustar nombres, no la lógica): `data/processed/annotations/sinco_s/<run_id>/` con `entrada/lote_NNN.json`, `salida/lote_NNN.json`, `intentos/lote_NNN_aK.txt` (respuesta cruda de cada intento, nunca se borra), `estado.json` y `run_meta.json`.

1. **`run_id`:** `s-completa-<fecha>-rK` (no debe empezar por `piloto`, `dryrun` ni `dry-run`, que `src/score` trata como piloto).
2. **Preparación:** un script genera todos los `entrada/lote_NNN.json` de una corrida a partir de las tablas, con semilla y `sinco_fuente.sha256`, y escribe el hash de cada entrada. Hasta aquí no se invoca ningún subagente.
3. **Checkpoint por lote:** `estado.json` guarda, por lote, `pendiente | en_curso | ok | invalido | fallido`, intentos, sha256 de entrada y salida, modelo, fecha y hora. Se escribe después de cada lote.
4. **Validación del lote** (por script, no a mano): JSON bien formado; exactamente los `function_id` del lote, sin faltantes ni sobrantes ni repetidos; `exposure_class` en {E0, E1, E2}; `eloundou_class` en {EL0, EL1, EL2, EL3}; `physical_bottleneck` booleano; `confidence` en {alta, media, baja}; `rationale` no vacío. Un lote es válido solo si todas sus funciones lo son (no se acepta un lote a medias).
5. **Reintento:** un lote inválido se reintenta con un subagente nuevo y la misma entrada, **hasta 2 reintentos** (3 intentos en total; coincide con `max_reintentos_formato = 2` de la config). Una interrupción por cuota o error de herramienta no cuenta como intento inválido. Si el tercer intento falla, el lote queda `fallido`, se escribe un issue en `docs/issues/` (regla 5) y la corrida se detiene hasta decisión humana.
6. **Importación:** cuando todos los lotes de una corrida están `ok`, un script los une en `run_<run_id>.parquet` con el esquema de 001 §7 + E-5/E-5b, valida de nuevo y escribe el registro de la corrida. Fila fuera de esquema -> issue y detenerse.
7. **Puntos de pausa:** (a) al alcanzar un límite de uso de la sesión, no se lanzan más subagentes y se deja `estado.json` consistente; se informa al usuario y se reanuda cuando haya cuota; no se pasa a API; (b) después de los primeros 10 lotes de la corrida 1, si más del 10 % salió inválido en el primer intento, pausa para revisar el prompt (cambio = `ann-s-v2`, 3.5); (c) tras completar la corrida 1 y validarla (cobertura 100 %); (d) tras completar la corrida 3, antes de calcular acuerdo.
8. **Orden de ejecución:** **por corridas completas** (corrida 1 entera, luego 2, luego 3), de modo que en cualquier pausa existan corridas completas y la independencia no dependa de intercalar. Dentro de una corrida, hasta 4 lotes en paralelo (valor C para cuidar la cuota; el usuario puede bajarlo).
9. **Reanudación:** se lee `estado.json`; los lotes `ok` no se repiten; los `en_curso` pasan a `pendiente`.
10. **Fecha y modelo:** `run_date` = fecha de inicio de la corrida; `capability_cutoff` y `model` = valores de cada lote. Si una corrida abarca más de 7 días calendario, se etiqueta `corrida_multidia` y se reporta el rango de fechas (umbral C). Las 3 corridas pueden tener fechas distintas; se reporta.
11. **Presupuesto:** cuota de subagentes de la sesión; sin API y sin gasto de dinero. Estimación de invocaciones: 138 a 150 más reintentos, más 12 del piloto; tokens según 011 §4.f, sin medir. Se recalcula con medición real al preparar el primer lote.

### 3.8 Compuertas previas y orden de las fases

| Paso | Qué | Condición |
|---|---|---|
| 0 | Aplicar E-6 y E-7; implementar E-5; construir el generador de prompt y de lotes y su validador | Esta decisión |
| 1 | **Congelar la muestra humana** (3.10) con semilla, antes de ver ninguna etiqueta | Paso 0 |
| 2 | **Piloto de la ruta S (G0):** 40 grupos estratificados por división (semilla 20261019), **fuera de la muestra humana**, 3 corridas, `ann-s-v1`. Se rotula `PILOTO, NO RESULTADO`. Pasa si: 100 % de lotes válidos tras reintentos; rechazos en el primer intento <= 10 %; ningún campo con más de 80 % de las funciones en una sola clase (valor C, alerta de colapso de rango); tabla cruzada `exposure_class x eloundou_class` revisada | Paso 1 |
| 3 | Corrida completa: 3 corridas con `ann-s-v1` congelado, por corridas completas | G0 pasada |
| 4 | Acuerdo entre corridas, B1 sin referencia, control negativo, reporte de cobertura | Corridas 1 a 3 |
| 5 | Importar la muestra humana, B1 con referencia, medidas por grupo con rótulo actualizado | Revisión del usuario |

G0 es una elección conservadora mía: el usuario puede **renunciar a ella con instrucción explícita** (reversible); el riesgo es que un defecto del prompt obligue a repetir las 3 corridas. Si G0 revela un defecto, se crea `ann-s-v2` y G0 se repite.

### 3.9 Criterios de aceptación de la corrida completa

| Criterio | Umbral | Origen | Si falla |
|---|---|---|---|
| Cobertura | 100 % de los 457 grupos con funciones y de las 3,542 funciones, en cada una de las 3 corridas; los 33 residuales con `NA` y motivo | R/C | Corrida no aceptada; completar lotes |
| Lotes fallidos definitivos | 0 | C | Issue y detenerse |
| Rechazos en el primer intento | <= 10 % de los lotes (alerta, no impide aceptar) | C | Revisar prompt (`ann-s-v2`) |
| Acuerdo entre corridas, por campo | Kappa de Cohen ponderado cuadrático por pares >= 0.60, para `exposure_class` y para `eloundou_class` (con EL3 fundida en EL2 y, aparte, con las 4 clases crudas); alfa de Krippendorff ordinal entre las 3 corridas, solo reporte; acuerdo exacto descriptivo | P (M27) | El campo se reporta con "consistencia insuficiente" y no se usa en cifras principales |
| Por grupo | Rango min-max y CCI de `E_g` entre corridas (reporte; con 3 corridas la varianza se estima mal y así se dice) | R (010 §6.1) | n/a |
| B1 sin referencia humana | Convergencia R-hat <= 1.05 y ESS >= 100 (config de `src/calibrate`); **se etiqueta consistencia entre corridas, NO exactitud**; corridas del mismo LLM no son independientes | P | Advertencia en el resumen |
| Control negativo | `physical_bottleneck = true` asociado con menor `E_g` y menor `alfa_S`, con grupos de contraste elegidos por el usuario antes de ver resultados | R (011 §4.g.6) | Problema de medición: se investiga, no se reajusta |
| Rango | Distribución de `E_g` y tabla cruzada de las dos rúbricas publicadas | R | n/a |

**Qué NO prueba la aceptación:** que la medida sea válida. Solo la muestra humana es independiente del LLM (010 §6.3).

**Estadística de incertidumbre (M6):** entre corridas (min-max, alfa); composición de funciones por bootstrap dentro del grupo, que es un **intervalo de sensibilidad, no de muestreo** (las funciones son la lista completa); crosswalk solo en la ruta O (rango de las O*NET emparejadas); intervalo bayesiano de B1 al 90 %; para ENOE, I-diseño, I-medición e I-total (013 §9).

### 3.10 Muestra humana de referencia

- **300 funciones.** Congelada **antes** de ver etiquetas del LLM y por tanto no estratificada por la clase del LLM (resuelve la tensión entre 010 §6.3, que estratifica por clase LLM, y 011 §4.e, que la congela antes). Estratificación por división SINCO, asignación proporcional al número de funciones y mínimo 15 por división (valor C), semilla registrada, hash de la lista. Si tras las corridas la muestra contiene menos de 30 funciones EL2 (valor C), se añade una segunda muestra estratificada por clase con sus probabilidades de inclusión registradas, rotulada aparte; B1 modela la inclusión.
- **49 grupos** con calificación holística de `E_g` en tres niveles (descripción + funciones), de los 457 con funciones, estratificados por división con mínimo 3 por división, semilla registrada. Independiente de las 300 funciones (el diseño anidado ahorraría lectura pero agrupa la muestra; no se adopta).
- **Revisor 1: el usuario.** Segundo revisor solo si el usuario lo consigue, sobre una submuestra de 100 funciones (un tercio; valor C) y los 49 grupos si es posible. **Si no hay segundo revisor, se usa un solo revisor y se etiqueta `revision_humana_1_revisor`**: no hay kappa humano-humano ni adjudicación, y el revisor es también autor del diseño (no es independiente del proyecto).
- **Guía** (a redactar por el implementador o el agente de documentación en el archivo que el usuario indique): el revisor ve exactamente el contexto que vio el anotador y la misma rúbrica (001 y Eloundou literal), **no ve ninguna etiqueta del LLM**, en orden aleatorio; registra los cuatro campos y un comentario opcional; anota el tiempo por juicio para estimar horas (se desconoce hoy); no consulta las corridas hasta terminar. Clasificar ambos campos de manera independiente.
- Horas: **desconocidas** [NO VERIFICADO]; 300 funciones + 49 grupos = 349 juicios con un revisor. El usuario puede acortar, y se reporta el tamaño efectivo.
- Con la muestra importada: matrices de confusión humano-LLM por campo, kappa ponderado (LLM, humano) con IC bootstrap por grupo, B1 con referencia (`--unidad modelo`, no `corrida`, para recuperar el sesgo común del LLM, `src/calibrate/README.md`).

### 3.11 Qué se reporta y cómo se rotula

- Rótulo obligatorio en toda tabla, figura y texto: **"exposición teórica SINCO, sin_validar"** (que se corresponde con `"PROVISIONAL, SIN VALIDAR"` de las configuraciones). Tras importar la muestra humana de un revisor: "exposición teórica SINCO; contrastada con 1 revisor humano; no es validación independiente". Nunca "riesgo", "amenaza", "pérdida" ni "desplazamiento de empleo" (001 §4.6).
- Medidas: `E_g` (principal), `alfa_S`, `beta_S`, `cota_sup_S` (comparación, nunca comparar niveles absolutos con Eloundou: se comparan rangos y concordancia ordinal), `share_E2`, `share_any`, mapas inferior y superior, `physical_bottleneck` por grupo, y el mínimo y máximo entre corridas.
- Cobertura: grupos con medida / 490; 33 residuales NA; grupos `pocas_funciones` (< 3).
- Ninguna cifra entra al artículo sin un script en `src/` y un archivo en `data/processed/` (reglas 1 y 6). Esta decisión no contiene resultados.
- Esta corrida es lo que habilita la compuerta G1 de 013 (exposición congelada), no la firma.

## 4. Despliegue (004, 007)

### 4.1 Instrucción del usuario

Registro: el usuario pide **mantener abierta la API local** y **comenzar el despliegue usando el repositorio** https://github.com/DiegoSReco/sinco-onet-api. Mantener la API local abierta es una tarea de operación (proceso `uvicorn` en el equipo), no una decisión metodológica; la API FastAPI sigue siendo la fuente local y de desarrollo.

### 4.2 Despliegue 1 (primario): sitio estático en GitHub Pages desde el repositorio

- **Qué:** la misma interfaz, leyendo JSON/CSV/Parquet **pregenerados** por un script de exportación que parte de las tablas del repositorio (script nuevo, en `src/`, lo escribe el implementador; no es parte de esta decisión).
- **Cómo:** GitHub Actions con flujo propio. Según la documentación de GitHub consultada (2026-10-19, https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), el flujo usa `actions/configure-pages`, `actions/upload-pages-artifact` y `actions/deploy-pages` (versiones de la página: `@v5`, `@v4`, `@v4`; el implementador las verifica al escribir el flujo), permisos `pages: write` e `id-token: write`, entorno `github-pages`, y el artefacto debe ser un tar gzip sin enlaces simbólicos ni duros, de menos de 10 GB.
- **Límites** (https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits, 2026-10-19): sitio de hasta 1 GB, límite blando de 100 GB de ancho de banda al mes, 10 builds por hora que no aplica a flujos propios, tiempo de espera de 10 minutos; usos prohibidos: sitios comerciales, transacciones sensibles. Un sitio informativo de lectura no los toca. Los datos del repositorio público ya caben en < 1 GB [NO VERIFICADO].
- **Acción del usuario necesaria:** en la configuración del repositorio, fijar la fuente de Pages en "GitHub Actions". No requiere cuenta nueva.
- **Por qué es reversible y barato:** sin servidor, sin costo, se desactiva desde la configuración. Lo ya publicado puede persistir en cachés (riesgo 4.6).

### 4.3 Qué NO publica el sitio

Se publica lo que la API local ya sirve por 004: catálogo SINCO, catálogo O*NET, emparejamiento rotulado "no validado" con `fuente` y `estado_validacion`, y la probabilidad de automatización (Frey-Osborne) rotulada y no validada (004 Registro 5). **No se publican medidas de exposición** (`E_g`, `E_o`, `alfa_S`, etc.) en esta fase (004 las prohíbe; la prohibición se levanta solo con decisión nueva, después de la muestra humana). Tampoco microdatos de la ENOE, ni PDF de F-O ni su tabla cruda, ni `oro_*` ni anotaciones del piloto. Todo es solo lectura: sin autenticación, sin escritura, sin formularios.

### 4.4 Despliegue 2 (preparado, no ejecutado): contenedor FastAPI en Render o similar

- Se prepara `Dockerfile` y `render.yaml` (la especificación de Blueprint consultada, https://render.com/docs/blueprint-spec, 2026-10-19: servicio `type: web`, `runtime: docker`, `plan: free`, 0.1 CPU y 512 MB de RAM; la cuenta del proveedor de Git debe tener acceso al repositorio).
- **No se ejecuta**: requiere que el usuario conecte su cuenta. Comportamiento del plan gratuito (suspensión por inactividad, límites) **[NO VERIFICADO]**.
- Solo GET, sin autenticación y sin escritura; CORS restringido al origen del sitio de Pages (C). Servidor: `uvicorn` (aprobado); `gunicorn` sigue no aprobado. El `Dockerfile` no debe copiar `data/raw/` ni secretos (007 lo dejó sin probar).

### 4.5 Dependencias y atribución

- Aprobados: `uvicorn`, `fastapi`, `starlette`, `httpx` (solo pruebas). **Aprobadas ahora:** la ampliación de columnas opcionales del crosswalk (Método A1) y `opentelemetry-api` como dependencia transitiva (004 Registro 4, M14). El implementador fija versiones y las registra.
- **Texto de atribución exacto.** Debe aparecer en cada página del sitio, en el README y en las descargas.
  - **O*NET** (texto de https://www.onetcenter.org/license_db.html, consultado 2026-10-19; el sitio exige indicar la versión y marca registrada): "This page includes information from the O*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA). Used under the CC BY 4.0 license. O*NET® is a trademark of USDOL/ETA." Como el proyecto modifica y combina esta información: "[NOMBRE A CONFIRMAR POR EL USUARIO; por defecto DiegoSReco] has modified all or some of this information. USDOL/ETA has not approved, endorsed, or tested these modifications." En descargas de archivos, "This page" se sustituye por "This product" [la variante exacta no se verificó en la fuente]. La versión es 31.0 según el manifiesto del proyecto. Un archivo con la lista de cambios (o un contacto) acompaña las descargas.
  - **SINCO / INEGI** (términos de uso de INEGI, resumen de herramienta, 2026-10-19): "Fuente: INEGI, Sistema Nacional de Clasificación de Ocupaciones, SINCO 2019." Aviso de transformación: "Las tablas fueron extraídas del PDF oficial y reordenadas por este proyecto. Este uso no representa una postura oficial del INEGI."
  - **Frey-Osborne** (DOI y paginación vistos en los resultados de búsqueda de https://www.oxfordmartin.ox.ac.uk/publications/view/2279, 2026-10-19): "Probabilidad de automatización (Frey-Osborne): Frey, C. B. y Osborne, M. A. (2017). The future of employment: How susceptible are jobs to computerisation? Technological Forecasting and Social Change, 114, 254-280. https://doi.org/10.1016/j.techfore.2016.08.019. Versión de trabajo: Oxford Martin School, 2013. Probabilidades de ocupaciones de EE. UU. trasladadas a SINCO 2019 por un emparejamiento propio de este proyecto, NO validado. No es exposición a IA ni riesgo de pérdida de empleo. Los datos se retirarán si el titular de los derechos lo solicita."
- **Marca explícita:** los datos publicados incluyen las probabilidades derivadas (riesgo aceptado por el usuario, licencia sin declarar, 007 §2.2); **el sitio estático las expondrá públicamente**, con rótulo permanente.

### 4.6 Riesgos del despliegue

1. Publicar es difícil de revertir (cachés, forks, historial); aplica a las probabilidades de F-O.
2. Los términos de INEGI tienen verificación humana pendiente (1.2).
3. Una presentación "amigable" del vínculo SINCO-O*NET puede leerse como correspondencia oficial: el rótulo "no validado" y la fuente deben ser visibles, no solo en la ficha.
4. El sitio y el README deben decir qué es exposición teórica y qué no: nada de lenguaje de pérdida de empleo.
5. Los archivos pregenerados pueden quedar desfasados de la API local; el flujo los regenera en cada despliegue.
6. Costo de Render y comportamiento del plan gratuito no verificados.

## 5. Revisión manual del emparejamiento (014): política aprobada

Con las respuestas conservadoras de M60 a M73:

1. `NINGUNO` = juicio del revisor, con comentario obligatorio; se listan aparte.
2. `DUDA` se ignora (queda el automático con su bandera) y se lista.
3. Un solo revisor, con etiqueta explícita `revision_manual_1_revisor`; no se llama validado.
4. Muestreo del 5 % de los grupos `ok`, en ciego y mezclados, para estimar su tasa de error.
5. La revisión manual se versiona con sha256 y fecha; el archivo previo no se sobrescribe; la corrida queda en `match_corridas`.
6. Evaluación siempre "automático" frente a "automático + manual"; la evaluación de precisión usa la muestra de oro, no los grupos corregidos.
7. La revisión corrige el modelo principal; no es la validación del método.

## 6. Preguntas que esta decisión deja a verificación externa (no son decisiones)

Ver la lista final de la sección 8.

## 7. Qué NO se decreta aquí y razones

1. **Firma del pre-registro 013 y descarga de la ENOE (compuertas G1-G3).** El usuario mismo puso estas compuertas (012 Registro 1). Firmar exige antes verificar variables, versión de SINCO por trimestre y el esquema de panel, que son hechos externos aún sin verificar; H4, H5 y H7 dependen de ellos, y H16 y H18 son humanas. M46 a M59 fijan valores, **no firman**. Hasta la firma no se descarga nada.
2. **Validez de la medida.** Aprobar no valida: sin la muestra humana, toda cifra es consistencia entre corridas (B1) y se rotula "sin_validar".
3. **Disponibilidad del tiempo del usuario como revisor.** La muestra humana (300 + 49) y la revisión manual de 83 grupos no se pueden decretar; dependen de horas que no conozco.
4. **Activar la ruta O.** Cuesta una cuota que no está medida y depende del crosswalk sin validar; se decide con datos de cuota.
5. **Publicar medidas de exposición.** Lo prohíbe 004 y no hay validación; se decide después de la muestra humana.
6. **Hipótesis direccionales para la validación de constructo.** 012 las dejó "a fijar por el humano antes de ver los datos"; fijarlas por decreto las vuelve inválidas como prueba previa.
7. **Los hechos externos de 1.2.**
8. **Procedencia de la aprobación.** Mi capacidad de registrar una aprobación depende de una cita relayada; el humano debe cotejarla.

## 8. Lista final: pendientes reales que siguen requiriendo al usuario o a verificación externa

1. **INEGI:** leer los términos de uso vigentes (incluido el tratamiento de microdatos de la ENOE) y confirmar la redistribución de las tablas del catálogo SINCO ya publicadas. Responsable: usuario. Bloquea: descarga de la ENOE (013 H16).
2. **Frey-Osborne:** el riesgo de licencia sigue aceptado y no resuelto; si el titular objeta, retirar. Responsable: usuario.
3. **Glifo de la tercera medida de Eloundou** (¿gamma?): mirar el PDF `eloundou_2023_v5_pdf`. Responsable: usuario. Hasta entonces `cota_sup_S`.
4. **Cotejo de cifras citadas** (Ceballos y Guadarrama, páginas de Eloundou, cifras de OIT y de otras fuentes de segunda mano) antes del artículo; y completar las referencias de 001 §10.9. Responsable: usuario o revisor humano.
5. **Muestra humana:** revisar 300 funciones y 49 grupos (revisor 1) y, si se consigue, un segundo revisor; además la revisión manual de 83 grupos del emparejamiento, el muestreo del 5 % de los `ok` y la muestra de oro (255 grupos) con revisores. Responsable: usuario.
6. **Pre-registro 013:** verificar variables de la ENOE, versión de SINCO por trimestre y esquema de panel; resolver H4, H5, H7, H14-H16 y H18; firmar. Responsable: usuario. Sin esto no se descarga.
7. **Acciones de cuenta:** activar GitHub Pages con "GitHub Actions" como fuente; confirmar el nombre que irá en la atribución de O*NET; conectar Render solo si se quiere el despliegue 2. Responsable: usuario.
8. **Documentos que no pude abrir:** 002, 005, 009 y los issues de la muestra de oro y de score; confirmar que el kappa 0.60 y mi lectura de ellos son correctas. Responsable: quien tenga acceso (usuario u orquestador).

## 9. Fuentes consultadas (2026-10-19)

- Archivos del proyecto listados en "Qué se leyó y qué no".
- O*NET Center, licencia de la base de datos (texto de atribución, CC BY 4.0, versión, marca): https://www.onetcenter.org/license_db.html (WebFetch, resumen de herramienta).
- INEGI, términos de uso (sección "Del libre uso de la información"): https://www.inegi.org.mx/inegi/terminos.html (WebFetch, resumen de herramienta; no es lectura jurídica primaria).
- GitHub Docs, flujos propios de Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages (WebFetch, resumen).
- GitHub Docs, límites de Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits (WebFetch, resumen).
- Render, especificación de Blueprint (`render.yaml`): https://render.com/docs/blueprint-spec (WebFetch, resumen).
- Frey y Osborne (2017), referencia de revista, volumen, páginas y DOI: resultado de búsqueda con la página https://www.oxfordmartin.ox.ac.uk/publications/view/2279 (2026-10-19; la ficha no se abrió, solo el resultado de búsqueda).
- Las fuentes de las demás decisiones se citan en 001, 003, 010-014 y no se reconsultaron.

## 10. Lista de [NO VERIFICADO]

- Que la cita del usuario transmitida por el orquestador sea textual.
- Contenido de 002, 005, 009 y de los issues no leídos; el kappa 0.60 de la muestra de oro; que 3,542 funciones, 457 y 33 coincidan con `data/processed/` (cifras de los diccionarios, vía 010).
- Tokens por lote y cuota de sesión de los subagentes (supuestos de 011 §4.f); tamaño del universo O*NET 31.0.
- Horas de revisión humana.
- Cómo se exportó la tabla de revisión manual (si el revisor vio similitudes).
- Ediciones/trimestres con SINCO 2019 en la ENOE, variables de la ENOE y esquema de panel (013 §18).
- Términos de INEGI sobre microdatos; licencia efectiva de `enoeR`.
- Glifo de la tercera medida de Eloundou.
- Comportamiento del plan gratuito de Render; versiones actuales de las acciones de GitHub; que el sitio quepa en < 1 GB.
- La variante "This product" del texto de atribución de O*NET para descargas.
