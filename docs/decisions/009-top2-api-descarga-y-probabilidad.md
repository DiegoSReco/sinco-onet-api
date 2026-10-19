# 009 - Emparejamiento top-2, descarga de datos en la API, probabilidad de automatización visible y método de exposición

> **ESTADO: APROBADA por el usuario en lo dicho (sección 2 y registro de la sección 4.3); PENDIENTE DE REVISIÓN HUMANA en lo demás (secciones 3, 5 a 8).** Autor: agente de métodos. Fecha: 2026-10-19. Este documento registra decisiones; no implementa ni calcula cifras (reglas 1 y 7 de CLAUDE.md).

## 1. Pregunta

¿Cómo cambian el emparejamiento (005), la API (004) y el desarrollo del método de exposición (001) a partir de las instrucciones del usuario del 2026-10-19: usar solo los 2 primeros embeddings, permitir descargar el dataset con sus matches, mostrar y descargar la probabilidad de automatización (Frey-Osborne), dejar el deployment pendiente y crear el archivo del método de exposición?

## 2. Lo que el usuario dijo (APROBADO)

Cita textual del usuario (2026-10-19, transmitida por el coordinador): "dejemos pendientes el deployment. Continua con lo siguientes pasos. Antes solo utiliza los embeddings más altos (2 primeros). En la api agrega la opción para descarga el data set ya sea filtrado o completo. Ya con sus respectivos matches. Continua con la asignación de probabilidad, De igual forma que se observe en la API y pueda descargarse. Agregue en data/raw en artículo de Owen pero no menciona nada de la asgignacio nde probabilidad. Continua con el método de exposición y crea el file de python donde lo desarrollarás."

Registro (sin ampliar):
- **(a) El deployment queda pendiente.** Se refiere al despliegue/hosting público (004: opciones D, E o B+E; 007). No revierte la elección de la opción B de 004 ni el repositorio ya publicado (007). Interpretación del agente de métodos: no se despliega ninguna instancia pública hasta nueva orden.
- **(b) Emparejamiento top-2.** `k_top = 2`: los **dos** O*NET-SOC con mayor similitud por grupo SINCO **sustituyen** al conjunto candidato S definido por umbrales en 005 §5.4 (S = rango <= 5 y similitud >= sim_top1 - delta). **Interpretación del orquestador, a confirmar por el usuario:** top-2 **por modelo**, con **bge-m3 como principal y multilingual-e5-large como alterno** (005 §5.3).
- **(c) La API gana descarga y visibilidad de la probabilidad** (sección 4).
- **(d) Se crea `src/score/exposicion.py`** como lugar de desarrollo del método de exposición (001, aprobada), sin correr sobre datos reales mientras solo exista el piloto (008).
- **(e) Pendientes** (sección 6).
- **Artículo de Owen (Ceballos y Guadarrama):** el usuario lo agregó a `data/raw` y se registró en `data/raw/manifest.json`. Lo verificado y lo no verificado está en 001 §3.5, 003 §0 y §4 y 005 §2. Dato del usuario: el artículo "no menciona nada de la asignación de probabilidad" (se interpreta como el método de emparejamiento; la lectura del orquestador coincide: ver 005 §2).

## 3. Emparejamiento top-2: efectos sobre 005 (propuesto; pendiente de revisión humana lo no dicho)

Lo que cambia por la instrucción:
- El conjunto de candidatos por grupo SINCO es exactamente **2 O*NET-SOC por modelo** (el de mayor y el de segunda mayor similitud). `n_candidatos <= 2`. Si dos candidatos colapsan al mismo SOC 2010 (005 §5.6), se cuentan una vez y `n_candidatos` puede ser 1.
- `margin = sim_top1 - sim_top2` sigue definido y sigue siendo la bandera de confianza; `rango` es 1 o 2.
- La recuperación puede seguir calculando k = 10 internamente (005 §5.4) para diagnóstico, pero **solo los 2 primeros se usan** en el crosswalk, en la agregación de `p_FO` y en la API. Esta es mi lectura de "solo utiliza los embeddings más altos"; a confirmar.
- Agregación de `p_FO` por SINCO (005 §5.7): media ponderada por similitud sobre los (<= 2) candidatos como cifra principal; `p_FO_mean` (uniforme), `p_FO_min`, `p_FO_max`, `p_FO_top1` siguen. Con 2 candidatos min/max acotan la ambigüedad entre el mejor y el segundo. Cada candidato puede a su vez mapear a varios SOC 2010 por el puente (25 casos en la ingesta, según 005 R.7): esa multiplicidad se propaga como en 005 §5.7.

Lo que **requiere decisión** (no dicho por el usuario ni fijado en 005 para top-2):
1. Si el peso entre los 2 candidatos es **softmax con tau** (005 §5.6) o **uniforme**; tau seguiría sin calibrar.
2. Qué pasa con la regla de **`sin_coincidencia`** (005 §5.6: sim_top1 bajo un umbral -> NA): con top-2 siempre hay 2 candidatos; ¿se conserva el umbral para dejar `NA`? 005 no lo recomienda con top-2.
3. Si la **muestra de oro** (005 §8.1: pooled de top-5 de varios métodos) se arma con los top-2 de cada modelo o con más candidatos; y las métricas (precision@1, @3, @5, MRR) cambian de sentido con top-2 (p. ej. precision@2).
4. Si la variante alternativa (e5) entra en la API y en la agregación o solo en la comparación.

Efecto en el crosswalk (004): las columnas opcionales del Método A1 (`modelo`, `rango`, `similitud`, `margen`, `similitud_alt`, `rango_alt`, `modelo_alt`, `baja_confianza`, `match_status`) siguen pendientes de confirmación (004, Registro 4); con top-2, `rango` toma los valores 1 y 2.

## 4. API: descarga del dataset y probabilidad de automatización (modifica 004 en un punto)

Lo dicho por el usuario (APROBADO): la API debe permitir **descargar el dataset completo o filtrado, con sus respectivos matches**; y debe **mostrar y permitir descargar la probabilidad de automatización (Frey-Osborne)** por SINCO.

### 4.1 Regla de 004 que se reemplaza
004 establecía (Contrato del crosswalk, Endpoints y Riesgo 2) que ningún endpoint devuelve scores, exposición ni probabilidades, con lista blanca y prueba automática. **Esa regla queda reemplazada por:**
- **La API sirve y permite descargar la "probabilidad de automatización (Frey-Osborne)"**, que debe:
  - rotularse exactamente así (005 R.1b), nunca como "exposición" ni "riesgo de pérdida de empleo";
  - marcarse **NO validada** (005 R.4, R.7);
  - leerse de `sinco_probabilidad_fo.parquet` **si existe**; si no existe, el endpoint responde un estado vacío explícito, no un error;
  - ir acompañada de `match_status`, `n_candidatos`, `margin` y la cobertura (005 §8.4).
- **Sigue prohibido servir exposición** (`E_o`, `share_E2`, `share_any`, `exposure_class` o cualquier derivado de la anotación) por la API, y las valoraciones de `tareas_onet_ratings` siguen fuera de los endpoints de scores según 004.
- La lista blanca y la prueba automática de 004 (Riesgo 2) deben actualizarse para permitir exactamente las columnas de la probabilidad rotulada y seguir fallando ante cualquier columna de exposición. **La actualización de esas pruebas es trabajo del implementador y requiere revisión.**
- Registro en 004: Registro 5.

### 4.2 Descarga
- Descarga del dataset **completo o filtrado** (por división, grupo, código, etc.), con sus matches (candidatos top-2, similitud, rango, margen, banderas) y la probabilidad (4.1). Solo lectura (GET); sin escritura en `data/raw` ni `data/processed`.
- Formato (CSV, Parquet, JSON), límites de tamaño y filtros concretos: **no los fijó el usuario; requiere decisión** (el implementador puede proponer CSV y Parquet; no está aprobado).
- Las descargas deben incluir los **avisos** pertinentes: resultados del emparejamiento NO validados; atribución a O*NET (CC BY 4.0, USDOL/ETA) y a INEGI; para la probabilidad, la fuente Frey y Osborne (2013; versión de revista 2017).

### 4.3 Licencia de Frey-Osborne: advertencia, decisión del usuario y riesgo aceptado
Versión inicial de esta sección (superada): se dejaba como decisión humana pendiente si se publicaban las probabilidades, porque el repositorio público no contenía tablas de Frey-Osborne.

- **Advertencia dada al usuario (por el orquestador, transmitida por el coordinador):** la licencia de redistribución del PDF y de las tablas de Frey-Osborne **no está declarada** y publicarlas es **difícil de revertir**.
- **Decisión del usuario (cita textual):** "Cambia esa regla y usa probabilidades en el repo".
- **Registro (sin ampliar):** el usuario decidió, con la advertencia en mano, que la API sirva y descargue la probabilidad (4.1) y que se publiquen en el repositorio las **tablas derivadas de SINCO** con probabilidades (ver 007: `sinco_probabilidad_fo.parquet` y `match_cobertura.json`). **La licencia de Frey-Osborne queda como "riesgo aceptado por el usuario", no como resuelta.** El alcance exacto de lo publicado (qué tablas) está en 007; la interpretación del orquestador sobre que el PDF y la tabla cruda de 702 filas por SOC **no** se publican está **pendiente de confirmación del usuario**.
- **Riesgo residual:** licencia sin declarar; los autores u Oxford Martin podrían objetar; lo publicado puede quedar en cachés y forks aunque se retire; una instancia pública de la API serviría esas probabilidades.
- **Mitigación mínima propuesta (pendiente de revisión humana):** (i) nota de atribución y cita completa de Frey y Osborne (2013; versión de revista 2017) en el README y en las descargas; (ii) compromiso de retirar los datos derivados de Frey-Osborne si el titular de derechos lo solicita; (iii) rótulo permanente "NO validada" y "probabilidad de automatización (Frey-Osborne)".
- Descargar el dataset con texto de SINCO y de O*NET: la redistribución de INEGI no está revisada (007 §4.2); O*NET exige atribución en cada descarga.
- La función de descarga amplía la superficie de exposición de datos en una API pública: refuerza que el **deployment** siga pendiente (2(a)).

## 5. Método de exposición: `src/score/exposicion.py`

- Se crea `src/score/exposicion.py` como lugar de desarrollo del método de **exposición** definido en 001 (aprobada): `exposure_class` E0/E1/E2 -> `e_t` (0, 0.5, 1) -> `E_o` (promedio de tareas centrales con pesos iguales) -> SINCO vía crosswalk (001 §4.3 a §4.5). La rúbrica y el glosario están en versión 1 (006).
- **Sin correr sobre datos reales mientras solo exista el piloto** (008: 40 tareas, subagentes, resultados NO finales). Pruebas con datos sintéticos están permitidas; ninguna cifra del piloto se agrega a exposición (008 §2.7) ni entra al artículo (regla 6).
- Toda cifra de exposición debe salir de un script en `src/` (regla 1) y registrarse en `data/processed/` (regla 6). Los parámetros (mapa 0/0.5/1, variantes, pesos) van en configuración, no en código (001 §4.3).
- La exposición por SINCO usa el crosswalk top-2 (3); las reglas de agregación 1:N y N:1 de 001 §4.5 aplican con a lo sumo 2 O*NET por grupo.

## 6. Pendientes (requieren decisión)

1. **Agregación entre corridas de anotación** (3 corridas del piloto, 008): provisional; falta fijar si se promedian los `e_t`, se toma la moda de `exposure_class` o se usa otra regla, y cómo se reporta el desacuerdo. Hasta decidirlo, cualquier regla en `exposicion.py` es provisional y debe marcarse así.
2. **Umbral de cobertura para `E_SINCO`:** qué proporción mínima de tareas anotadas (o de ocupaciones O*NET con exposición disponible) exige un grupo SINCO para reportar `E_SINCO` en vez de `NA`. Sin recomendación en 001; sin valor.
3. Los puntos de la sección 3 (pesos entre los 2 candidatos, `sin_coincidencia`, muestra de oro con top-2, papel de e5).
4. Formato y límites de la descarga (4.2) y actualización de la lista blanca de la API (4.1).
5. **Confirmar con el usuario** qué tablas de Frey-Osborne se publican (la interpretación del orquestador: tablas derivadas de SINCO sí; PDF y tabla cruda por SOC no). La licencia queda como riesgo aceptado (4.3), no resuelta.
6. Confirmar la interpretación del orquestador del top-2 (por modelo; bge-m3 principal, e5 alterno).
7. Heredados: corrida completa de anotación (008 §7), tareas sin tipo core/supplemental, revisores y umbral de kappa, hosting público (004).

## 7. Riesgos

1. **Top-2 reduce la cobertura de la ambigüedad:** descartar candidatos 3 a 5 puede ocultar el SOC correcto cuando el texto SINCO es amplio; se pierde parte de la información de 005 §5.4. Mitigación: conservar k = 10 para diagnóstico y validar con la muestra de oro.
2. **Con 2 candidatos, min/max y el margen son más fáciles de leer pero menos informativos;** un solo candidato dominante con segundo irrelevante puede sesgar la media ponderada si el peso es uniforme.
3. **Mostrar la probabilidad en la API puede confundirse con exposición.** Mitigación: rotulado fijo, aviso NO validada, separación visual, y exposición no servida.
4. **Licencia de Frey-Osborne sin declarar:** riesgo aceptado por el usuario (4.3); difícil de revertir (cachés, forks, historial de Git); posible objeción de los autores u Oxford Martin.
5. **Resultados NO validados** disponibles para descarga pueden usarse como definitivos. Mitigación: rótulo en cada archivo y respuesta.
6. **Exponer resultados derivados de los 2 primeros** sin la muestra de oro puede inducir lecturas de calidad no medida.
7. **Cambio de contrato de la API sin actualizar pruebas** (4.1): riesgo de fuga de columnas de exposición.
8. **Estadísticas derivadas de F-O (`match_cobertura.json`) y tablas derivadas** permiten, en principio, reconstruir parte de la información de la tabla cruda; "derivado" no equivale a "libre de la licencia". No se evaluó cuánto se puede reconstruir.

## 8. Fuentes

Sin fuentes externas nuevas. Se basa en las decisiones 001, 004, 005, 006, 007 y 008 y en las citas del usuario transmitidas por el coordinador. Lo dicho sobre `src/score/exposicion.py`, `sinco_probabilidad_fo.parquet`, `match_cobertura.json` y el manifest viene del coordinador; no lo verifiqué.
