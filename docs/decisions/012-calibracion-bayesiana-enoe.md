# 012 - Calibración bayesiana con la ENOE en dos rondas: opinión crítica y diseño alternativo

> **ESTADO: PENDIENTE DE REVISIÓN HUMANA, CON UN REGISTRO DE DECISIONES DEL USUARIO (2026-10-19; ver "Registro 1").** Es una propuesta y una opinión metodológica. No se implementa nada, no se descarga ni se consulta ningún microdato de la ENOE (instrucción explícita del usuario, que el Registro 1 mantiene hasta que se cumplan tres condiciones), no modifica 001, `docs/rubric.md` ni `docs/glossary.md` (regla 2), no autoriza dependencias, gasto ni modelo. Lo que contradiga 001 aprobada se señala como tal y exigiría una decisión posterior.

- Fecha: 2026-10-19
- Autor: agente de métodos
- Fecha de consulta de las fuentes web: 2026-10-19
- Pedido del usuario (cita textual): "1. Descartar exposicion empirica porque no tenemos acceso a datos de Mexico. De la exposición con el marco de Eloundou me quedan dudas por el mercado laboral en mexico. Pensaba en un enfoque bayesiano para calibrar esos parámetros. El objetivo cuando ya se tenga el matcheo (más preciso) es cruzar con los datos de la ENOE (aun no descargues nada de datos de ENOE). Lo que podría hacer en dos rondas. Podemos hacer la asignación de esa exposición, aplicarla a los datos de la ENOE, dividir por formales e informales y recalibrar esos parámetros de exposicion. El agente Metodo puede opinar sobre esta propuesta."

## Registro 1 (2026-10-19): decisiones del usuario sobre esta propuesta

**Cita textual del usuario, tal como me la transmitió el orquestador (mensaje del usuario, 2026-10-19):** "Avanza con el B1 por el momento. Reporte descriptivo por strato. Para enoe puedes usar el paquete que estoy creando para realizar descargas temporales en R. https://github.com/DiegoSReco/enoeR. Aprobar E-1,E-2, E-3 y E-8".

**Procedencia.** Yo no recibí el mensaje directamente; el orquestador lo cita como textual. El humano puede cotejarlo en la conversación.

**Qué se registra (lectura mía, sin ampliar):**
1. **Se avanza con B1 por ahora** (modelo bayesiano de error de medición tipo Dawid-Skene, sin ENOE; sección 5). "Avanza" no autoriza por sí solo lo que B1 necesita y 012 dejó como "requiere decisión": la muestra humana (quién, guía, horas), la elección entre Gibbs en numpy y un paquete bayesiano (PyMC, Stan, NumPyro; dependencia nueva), el modelo/vía y la fecha de corte de la corrida completa, ni el matching top-2 validado. Esas decisiones siguen pendientes (sección 9). Sin muestra humana B1 mide consistencia, no exactitud (sección 5).
2. **El análisis con ENOE será un REPORTE DESCRIPTIVO POR ESTRATOS** ("strato" se lee como "estratos"): la alternativa simple recomendada en la sección 10 (una ronda descriptiva con exposición congelada y estratos de contexto). Consecuencias: **B3 (calibración contra salarios o formalidad) queda desaconsejado** (ya lo estaba) y no se persigue; **B2 (exposición ajustada por contexto) queda DIFERIDO**: el usuario no lo pidió; solo se activaría con una decisión nueva (001 §10.7 sigue "requiere decisión"). La alternativa A de la sección 12 (recalibrar en dos rondas) no se adopta. El plan del reporte está en el borrador `013-preregistro-reporte-descriptivo-enoe.md` (pendiente de revisión humana).
3. **Se autoriza usar el paquete `enoeR`** (https://github.com/DiegoSReco/enoeR, repositorio público del usuario, rama `master`) para las descargas temporales de la ENOE, **pero NO se descarga nada hasta que se cumplan las tres condiciones siguientes**: (a) exista una **exposición congelada** (versión, hashes y `run_id` registrados); (b) esté **firmado el pre-registro** (decisión 013, hoy borrador); (c) el **humano defina informalidad, estratos y trimestres**. El orquestador informa que no ha descargado nada.
4. **E-1, E-2, E-3 y E-8 aprobadas** (decisión 011, Registro 4) y aplicadas a 001. E-4 a E-7 siguen pendientes. Esto cumple en parte el punto 11 de la sección 13 (confirmación de E-1 y E-2); la ruta S y `eloundou_class`, de los que depende B1, quedan definidos en 001 §4.2-§4.3, aunque `rubric.md` y el esquema (E-5, E-6) siguen sin actualizar.

**Hechos sobre `enoeR` verificados por el orquestador (README leído) y por mí (página de GitHub, WebFetch, 2026-10-19; resumen de herramienta):** descarga microdatos de la ENOE directamente de INEGI en CSV; ediciones: ENOE 2005T1-2020T1, 2020T2 no disponible (ETOE telefónica), ENOE-N 2020T3-2022T4, ENOE 2023T1 en adelante; tablas `sdem`, `coe1t`, `coe2t`, `hog`, `viv`; funciones `enoe_load` (un trimestre) y `enoe_list` (varios trimestres; marcada "In Progress" en el README); `enoe_codebook()` planeada, no implementada. Licencia: MIT en el README; la API de GitHub reporta NOASSERTION (según el orquestador); la página muestra un archivo LICENSE cuyo texto no vi. Versión del paquete y commit: **no visibles** (la página muestra "14 Commits"); hay que fijarlos antes de descargar (013). El paquete está en desarrollo.

**Qué NO cambia este registro:** no hay descarga ni consulta de microdatos; los resúmenes de INEGI de esta decisión siguen siendo de segunda mano; las preguntas abiertas de la sección 13 no listadas arriba siguen abiertas.

## 0. Qué se verificó y qué no (leer primero)

**Leído directamente (archivos del proyecto):** `CLAUDE.md`; decisiones 001, 003, 010 y 011 (esta última completa, incluida la rúbrica literal de Eloundou en §5, E-2, ya verificada contra el PDF en la revisión de 011); `docs/rubric.md` y `docs/glossary.md` (versión 1); `src/score/README.md`; `src/annotate/README.md`; `requirements.txt`; el issue `datos-2026-10-19-sinco-anexo-equivalencia-descartado.md`.

**No pude leer:** las decisiones 005 y 009 (probé `005-emparejamiento-sinco-onet.md` y `009-modulo-exposicion.md` y no existen con esos nombres; mi herramienta no lista directorios). Lo que sé de ellas viene de lo que citan 001, 003, 010, 011 y los README (005 = Método A de emparejamiento SINCO -> O*NET por embeddings, resultado `sin_validar`, muestra de oro; 009 = módulo de exposición con crosswalk top-2). Todo detalle de su contenido es **[NO VERIFICADO]**. Tampoco inspeccioné `data/processed/*.parquet` ni `data/raw/manifest.json`.

**Consultas web de esta decisión (2026-10-19), todas resúmenes de herramienta, no copias literales:** versión de SINCO en la ENOE; definición de informalidad de INEGI; diseño muestral de la ENOE; ENDUTIH; Dawid y Skene (1979); Gelman y Loken (garden of forking paths). **Los PDF de INEGI que intenté abrir (`nota_nvas_clasificaciones.pdf`, `clasificaciones_enoe_123.pdf`, `Informalidad_FINAL.pdf`) devolvieron binario ilegible para mi herramienta**; lo que digo de ellos viene solo de los resúmenes del buscador y queda marcado.

**No consulté ni descargué ningún microdato, tabulado ni cuestionario de la ENOE.** Qué variables trae la ENOE (tamaño de establecimiento, uso de computadora en el trabajo, código SINCO a cuántos dígitos, formalidad) es **[NO VERIFICADO]** en todo este documento; lo trato como supuesto a confirmar antes de cualquier diseño final.

## 1. Pregunta

El usuario descarta la capa de uso observado (U0 de 011 §4.c.3) por falta de datos de México y propone: (i) un enfoque bayesiano para calibrar los parámetros de la exposición tipo Eloundou, dudosos para el mercado laboral mexicano; (ii) cuando el matching sea más preciso, cruzar con la ENOE en dos rondas: asignar la exposición, aplicarla a la ENOE, dividir por formales e informales y recalibrar los parámetros de exposición. ¿Es defendible? ¿Qué se puede calibrar, contra qué, y con qué protocolo?

## 2. Dónde estoy de acuerdo y dónde no (resumen de la postura)

**De acuerdo**
1. Descartar la capa de uso observado: no hay dato mexicano verificado (011 §4.c.2) y sintetizarlo está prohibido.
2. Las dudas sobre transferir el marco de Eloundou a México son legítimas y están en la propia fuente: Eloundou declara que su foco en EE. UU. limita la generalización por organización industrial, infraestructura, regulación, "linguistic diversity" y contexto cultural, y que sus datos de empleo cubren sobre todo economía formal (011 §2.2, pp. 6 y 23 del PDF según la paginación de 011).
3. Un marco bayesiano es una buena herramienta para **propagar incertidumbre** (ruido del anotador, ruido del matching) hacia las cifras agregadas. Hoy 001/010 solo prevén min-max, bootstrap de sensibilidad y kappa; no hay un modelo de error.
4. La ENOE es la fuente natural para **ponderar** y **describir contexto** (001 §4.7; 011 §4.d). Cruzar la exposición con ella es el paso correcto.
5. Hacerlo en etapas y con la exposición ya congelada antes de mirar la ENOE: de acuerdo en el espíritu; abajo lo rediseño para que sea realmente confirmatorio.

**En desacuerdo**
1. **No hay observable contra el cual calibrar un parámetro de exposición técnica con la ENOE.** La exposición (001 §4.1) es una propiedad de la tarea; la ENOE observa personas, sus ocupaciones, ingresos, formalidad y horas. Para que un resultado laboral informe un parámetro técnico se necesita un supuesto causal (que la exposición explica ese resultado), que es justo lo que 001 prohíbe asumir (§4.1, §4.6, §8).
2. **Recalibrar por separado para formales e informales borra la diferencia que se quiere estudiar** y la vuelve tautológica (sección 4.4).
3. **Dos rondas sobre los mismos datos** sin partición ni plan congelado son un caso de "garden of forking paths" (sección 5).
4. **La mayoría de las dudas del usuario no son parámetros calibrables**; son problemas de alcance (aplicabilidad) que se resuelven declarándolos y midiéndolos aparte, no ajustándolos contra empleo (sección 3).
5. Hay un punto estructural que cambia la pregunta: **la exposición vive a nivel de grupo SINCO, así que dentro de un mismo grupo un trabajador formal y uno informal tienen exactamente la misma exposición técnica.** Cualquier diferencia formal/informal en exposición promedio es **composición ocupacional** (en qué grupos SINCO trabajan). Una diferencia dentro del grupo solo puede venir de supuestos de contexto (capa B2), nunca de la medición técnica.

## 3. Diagnóstico: qué supuestos del marco pueden no sostenerse en México y de qué tipo son

Clasificación: **(a)** parámetro calibrable (existe un observable que lo informa), **(b)** problema de medición (ruido o sesgo del anotador o del matching; se estima con muestra humana y réplicas), **(c)** problema de definición/alcance (aplicabilidad; no se arregla calibrando contra empleo; se declara, se mide aparte o se acota la afirmación). "Conv." = convención de la definición.

| # | Supuesto o rasgo del marco | Dónde aparece | Tipo | Qué hacer |
|---|---|---|---|---|
| 1 | Trabajador con laptop, software y acceso a un LLM; "no tiene otras herramientas físicas" | Preámbulo de la rúbrica, A.1 p. 24 (011 E-2) | **(c)**; parcialmente **(a)** vía B2 | Es parte de la definición de EL1/EL2; no se calibra. Se mide el contexto por separado (B2) con priors informados |
| 2 | Informalidad: Eloundou cubre sobre todo economía formal | 011 §2.2 | **(c)** | La exposición técnica no depende de la formalidad (mismo grupo, misma exposición). La formalidad entra como estrato de reporte y como covariable de B2 |
| 3 | Estructura de tareas distinta de O*NET (ruta O) | 001 §6.1 | **(b)** por matching incorrecto; **(c)** por diferencias reales de contenido | (b): modelo de error del matching con muestra de oro. (c): ruta S (texto mexicano) como contraste, y declarar la heterogeneidad intra-grupo |
| 4 | Idioma/traducción: rúbrica inglesa, tareas O*NET en inglés, SINCO en español | 010 §3.7, 011 §4.h | **(b)** | Efecto de idioma sobre el anotador estimable con ablación y revisores bilingües (B1) |
| 5 | Tamaño de empresas: E2 supone que "es fácil imaginar software adicional" (inversión complementaria); Eloundou fija 0.5 por "additional investment" (011 §2.2) | A.1 p. 25; p. 8 | **(c)** y convención en el 0.5 | El 0.5 es una convención; su relevancia por tamaño de empresa es un parámetro de contexto (B2) con prior, no de la medición técnica |
| 6 | Ocupaciones SINCO más genéricas (7.75 funciones por grupo frente a ~18.96 tareas por ocupación en O*NET 27.2, 010 §3.7) | 010/011 | **(b)** (ruido: acuerdo bajo en funciones vagas) y **(c)** (el grupo agrupa ocupaciones distintas) | (b): dificultad por función y shrinkage en B1. (c): no se arregla; se reporta |
| 7 | Umbral de 50 % de reducción de tiempo con calidad equivalente | Eloundou p. 7-8, "somewhat arbitrary" | **Conv.** (c) | No calibrable. Sensibilidad (p. ej. rúbrica con otro umbral = otro prompt) |
| 8 | LLM de referencia de 2023 (2,000 palabras, sin hechos recientes) frente a anotador de 2026 | A.1 p. 24; 011 §4.e | **(c)** | Preámbulo literal vs actualizado como dos prompts; no se calibra |
| 9 | Rúbrica diseñada para tareas O*NET aplicada a funciones SINCO (cambio de unidad) | 011 E-2 nota 2 | **(b)** y **(c)** | Tabla cruzada de rúbricas y muestra humana; el efecto del cambio de unidad solo se mide con humanos |
| 10 | Anotador que conoce el trabajo sobre todo desde texto en inglés y contextos más digitalizados | 010 §3.7 | **(b)** | Matriz de confusión del anotador frente a revisores mexicanos (B1) |
| 11 | Regulación y supervisión humana (fuente de desacuerdo en Eloundou) | §3.4 | **(c)** | No se calibra; límite declarado |
| 12 | Pesos de tareas (core 2:1 frente a iguales; funciones SINCO iguales) | 011 E-4 | **Conv.**; débilmente **(a)** | Sensibilidad; calibración opcional contra juicio holístico humano, con la salvedad de la sección 4.6 |
| 13 | Umbral de cobertura/confianza del matching (`umbral_onet_sinco`, PROVISIONAL en `src/score/config.toml`) | `src/score/README.md` | **(a)** contra la muestra de oro del matching | Se calibra con la muestra de oro, no con la ENOE |

**Conclusión del diagnóstico.** De las 13 filas, los parámetros que un dato puede informar son los de **medición** (4, 6b, 9, 10, 13) y se informan con **muestras humanas y réplicas**, no con la ENOE. Las filas de **alcance** (1, 2, 5, 7, 8, 11) no tienen observable de empleo que las identifique; lo honesto es nombrarlas y, si se quiere una cifra, producirla como una capa separada con priors explícitos (B2). Las **convenciones** (7, 12 parcial, el 0.5) no se calibran: se reportan como ejes de sensibilidad.

## 4. Evaluación crítica de "asignar exposición, aplicarla a la ENOE, dividir formal/informal y recalibrar"

### 4.1 ¿Contra qué observable se calibraría un parámetro de exposición técnica?

Candidatos y por qué ninguno sirve como objetivo de calibración:
- **Salario o ingreso por ocupación (ENOE):** correlaciona con escolaridad, sector, urbanidad y tamaño de empresa. Ajustar la exposición para que explique salarios convierte la medida en un predictor de salarios. Eloundou y Anthropic reportan asociaciones (Anthropic: el cuartil superior gana 47 % más, 011 §2.1) y las tratan como descripción; 001 §8 manda lo mismo.
- **Formalidad:** es una característica del vínculo laboral y de la unidad económica, no de la tarea. Un parámetro "calibrado" a la formalidad absorbería informalidad.
- **Adopción de IA:** la ENOE no la mide hasta donde sé **[NO VERIFICADO]**; y aun si existiera, adopción no es exposición (001 §4.1).
- **Cambios de empleo:** fuera del alcance (escenarios aparte, 001 §4.6); además la ENOE es corte transversal con panel corto (el diseño tiene cinco visitas en cinco trimestres, según el resumen del catálogo de INEGI), insuficiente para identificar efectos de una tecnología que apenas se adopta.

**No existe un observable que sea a la vez independiente de otros determinantes y relacionado con la exposición técnica por construcción.** Calibrar contra cualquiera de los anteriores sería ajustar un parámetro técnico a un resultado que tiene muchas otras causas.

### 4.2 Circularidad y endogeneidad

Si se ajusta un parámetro (por ejemplo el 0.5, o el peso de tareas) para maximizar el ajuste con salarios o formalidad, la exposición resultante "explica" salarios y formalidad por construcción. Después cualquier análisis de la relación exposición-salario (la tabla que el artículo querría mostrar) es circular. Esto contradice 001 §4.1 (propiedad técnica, neutral entre sustitución y complementariedad) y 001 §8 (asociaciones solo descriptivas) **si la calibración es contra resultados laborales**. Contra insumos de contexto (variables de acceso, tamaño) no contradice 001, pero entonces ya no es "exposición" sino la capa B2 con otro nombre (sección 6).

### 4.3 Identificación: qué es identificable con la ENOE y qué no

La exposición de un trabajador es `E_g(i)`, función del grupo SINCO `g(i)` del trabajador `i`. La ENOE aporta, por grupo, la distribución de covariables y el factor de expansión. Los parámetros del generador de `E_g` (clases latentes de funciones, sesgos del anotador, mapa 0/0.5/1) no entran en ninguna ecuación de la ENOE salvo a través de un modelo de resultados `Y_i = f(E_g(i), X_i) + e_i`. Ese modelo no identifica los parámetros de `E_g` sin supuestos fuertes: `E_g` es constante dentro de `g`, está confundida con todo lo que varía entre ocupaciones, y la ENOE no trae variación exógena.

| Parámetro | ¿Identificable con la ENOE? | Qué lo informa en cambio |
|---|---|---|
| Sesgo/ruido del anotador (confusión entre E0/E1/E2) | No | Muestra humana de referencia y réplicas (B1) |
| Mapa 0/0.5/1 (el 0.5) | No; es una definición | Sensibilidad; convención de Eloundou |
| Pesos de tareas/funciones | No (salvo supuesto causal) | Sensibilidad; opcionalmente juicio holístico humano |
| Umbral del matching | No | Muestra de oro del matching |
| Peso de aplicabilidad por celda de contexto (acceso, formalidad, tamaño) | **Parcialmente y solo si** existe un observable de acceso/uso digital por celda en la ENOE u otra encuesta **[NO VERIFICADO]**; de lo contrario, el posterior es prácticamente el prior | Priors informados (literatura, expertos); ENDUTIH solo si cruza por variables compatibles **[NO VERIFICADO: los resultados de búsqueda no mostraron ocupación como variable de cruce]** |
| Composición ocupacional por formalidad, región, sexo | Sí (es dato) | La ENOE directamente, con factor de expansión |

### 4.4 La recalibración por grupo (formal/informal) borra la diferencia

Si se estima un conjunto de parámetros `θ_formal` y `θ_informal` para que la exposición "se ajuste" dentro de cada grupo, la diferencia de exposición entre grupos pasa a depender de cuánto se permite variar `θ` entre grupos, es decir, del modelo y no de los datos. Dos casos:
- Si la calibración empuja ambos grupos hacia un mismo objetivo, la diferencia se achata.
- Si se calibra cada grupo contra su propia distribución de resultados, la diferencia queda definida por los resultados y no por las tareas: tautología.

Además, como la exposición técnica es constante dentro de `g`, **la única diferencia formal/informal que existe sin supuestos es composicional** y se mide con una descomposición simple entre ocupaciones (efecto "entre grupos"). Si se quisiera una diferencia **dentro** del grupo, hace falta un supuesto explícito de contexto (B2) y esa diferencia es una hipótesis, no un hallazgo.

### 4.5 Dos rondas con los mismos datos: sobreajuste y "forking paths"

Si la ronda 2 usa decisiones tomadas después de ver los resultados de la ronda 1 con los mismos datos, la inferencia de la ronda 2 condiciona implícitamente en muchas comparaciones no reportadas; Gelman y Loken describen ese problema aun sin mala fe (resumen consultado en FORRT; DOI 10.1511/2014.111.460). La ENOE es una muestra grande, así que casi cualquier diferencia será "significativa": la ronda 2 encontrará algo y no habrá criterio externo para distinguirlo de ruido. Se necesita congelar (sección 7).

### 4.6 Pesos "calibrados" contra juicio humano holístico: una salvedad

Se podría ajustar un peso (p. ej. core vs supplemental, o `w` del EL2) para maximizar el acuerdo con calificaciones holísticas de 49 grupos por revisores (010 §6.3). Con ~49 grupos, tres categorías y un peso libre, el riesgo de sobreajuste es alto y el humano es otro juicio, no verdad. Se admite solo como análisis de sensibilidad, nunca como valor de registro.

### 4.7 Ruido del matching sin validar como error de medición en la variable cruzada

Mientras el crosswalk esté `sin_validar`, `E_o` llevada a SINCO tiene error de matching. Dos consecuencias para cualquier cruce con la ENOE:
1. **Atenuación:** si el error es clásico (independiente de lo que se cruza), las asociaciones con salario, formalidad o escolaridad se atenúan hacia cero.
2. **Error diferencial (peor):** los grupos peor emparejados probablemente son los de oficios con poca contraparte en O*NET (manuales, de servicios personales, muchos informales) o los residuales/genéricos. Si el error de matching correlaciona con formalidad, **fabrica o esconde diferencias formal/informal**. No lo puedo afirmar con datos (no tengo la muestra de oro); es el riesgo estructural a descartar antes de cruzar.
Mitigación: no cruzar con la ENOE hasta tener la muestra de oro y el modelo de error del matching (B1.b); incluir `match_quality`/`cobertura_onet` como estrato de reporte; reportar siempre la ruta S (sin crosswalk) y la ruta O por separado.

### 4.8 Versión de SINCO en la ENOE

Según el resumen del buscador (no verificado contra el documento, cuyo PDF no pude leer), el documento de clasificaciones de la ENOE (edición 2023) indica que a partir del tercer trimestre de 2021 la encuesta usa el SINCO 2019. **Si es así**, solo los trimestres desde 3T 2021 son directamente compatibles con el catálogo de este proyecto; los anteriores usarían SINCO 2011 y requerirían una equivalencia 2011-2019, cuyo anexo fue descartado por ahora (issue `datos-2026-10-19-sinco-anexo-equivalencia-descartado`; su intento exploratorio dejó 57 filas sin anclar y bloques ambiguos). Recomendación: restringir el análisis a trimestres con SINCO 2019 y no intentar el puente 2011-2019 en esta fase. Además, el resumen mencionó una encuesta distinta, "ENOE N" (ENOEN), con documento de diseño muestral de 2021: cuál es la fuente vigente para este proyecto es **[NO VERIFICADO]** y debe decidirlo el humano al elegir los datos. A cuántos dígitos viene el código en la ENOE (si 4, para coincidir con el grupo unitario): **[NO VERIFICADO]**. *(Actualización 2026-10-19: una búsqueda adicional devolvió, como resumen de herramienta, que la nota de clasificaciones del 3T 2021 de la ENOE Nueva Edición dice que desde ese trimestre se incorpora el SINCO 2019: https://inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_nota_clasificaciones_trim3_2021.pdf , no abierto por mí. Sigue siendo segunda mano y no cubre trimestres posteriores a 2022.)*

## 5. Diseño propuesto por niveles

Idea rectora: **calibrar la medición contra referencias humanas; modelar el contexto como una capa separada y con priors; y usar la ENOE para ponderar y describir, no para ajustar la exposición.** *(Registro 1: se avanza con B1; el análisis con ENOE es el reporte descriptivo por estratos; B2 diferido; B3 desaconsejado.)*

### Nivel B1. Modelo bayesiano de error de medición (no usa la ENOE) [AVANZA, Registro 1]

**Objetivo.** Pasar de "una etiqueta del LLM por función" a una distribución posterior de la clase verdadera de cada función, y de ahí a una distribución posterior de `E_g`, `alfa_S`, `beta_S` y `cota_sup_S`.

**Estimando.** Se define como la media de la clase verdadera sobre las funciones listadas del grupo (cantidad de población finita: las funciones son la lista completa, 010 §6.6), no un parámetro de superpoblación. Así la incertidumbre es de **medición**, no de muestreo de funciones.

**Modelo generativo (esquema).**
- Índices: función `f` en grupo `g`, subgrupo `s(g)`, división `d(g)`; anotador `k` (corrida del LLM `r=1..R`, y revisores humanos `h=1..H`).
- Clase verdadera latente: `z_f ∈ {0,1,2}` (EL0, EL1, EL2 con EL3 fundida; análogo con `exposure_class` de 001 para el campo propio).
- Prior jerárquico: `z_f ~ Categórica(π_g)`, `π_g ~ Dirichlet(α_d)`, `α_d ~` hiperprior por división (parcial pooling). Para grupos con 1-2 funciones el prior estabiliza; **se reporta también la estimación sin pooling** porque el shrinkage comprime diferencias entre grupos.
- Verosimilitud (versión Dawid-Skene): `y_{f,k} | z_f=c ~ Categórica(Θ_k[c,·])`, con `Θ_k[c,·] ~ Dirichlet(β_k)`; Dawid y Skene (1979) es la referencia original de estimar tasas de error de observadores sin verdad conocida (Applied Statistics 28(1): 20-28, DOI 10.2307/2346806, vía registro RePEc).
- Versión ordinal (más parsimoniosa con 3 categorías): `u_f ~ N(μ_g, σ²)`, `y_{f,k}` por umbrales `τ_k` específicos del anotador, con desplazamiento `δ_k` (sesgo) y escala; reduce parámetros frente a una matriz 3x3 por anotador.
- **Corrección esencial (dependencia entre corridas).** Las R corridas del mismo modelo y prompt **no son anotadores independientes**: comparten el sesgo del modelo. Si se modelan como independientes dado `z_f` (supuesto clásico de Dawid-Skene), el posterior será falsamente preciso. Se añade un efecto de función compartido por todas las corridas (`b_f`: dificultad/ambigüedad y sesgo sistemático del LLM en esa función) y un efecto de corrida. **La verdad `z_f` solo se identifica separadamente del sesgo común del LLM mediante la muestra humana.** Sin muestra humana, B1 solo mide consistencia (varianza entre corridas), no exactitud.
- Muestra humana (010 §6.3: 300 funciones, doble revisión ciega, adjudicación): los revisores entran como anotadores con sus propias `Θ_h`; la adjudicación como un anotador más, no como verdad. Con la muestra estratificada por clase del LLM (para no dejar vacía EL2) hay que ajustar por el diseño de muestreo (el muestreo depende de la etiqueta del LLM: no es ignorable salvo que el modelo condicione en ella; se modela la inclusión o se ponderan las funciones).
- Ruta O (si se mantiene): igual por tarea, y encima el **modelo de error del matching** (B1.b).

**B1.b. Error de matching como parte del modelo.** Para cada par (grupo SINCO `g`, ocupación O*NET `j`) del top-2, `c_{gj} ∈ {correcto, parcial, incorrecto}` con `P(c_{gj} | s_{gj}, rango, tipo)` por regresión logística ordinal bayesiana ajustada con la **muestra de oro** (la doble revisión de ~10 % de grupos, 003 §5.5; regenerada con top-2). Luego `E_O(g)` se calcula como mezcla sobre qué pares son correctos, en vez de min-max. Esto convierte el umbral de confianza (hoy PROVISIONAL) en una curva de precisión calibrada. **[NO VERIFICADO]** qué columnas de puntaje exporta realmente el matching de 005.

**Parámetros que B1 calibra:** `Θ_k` o `(τ_k, δ_k)` por anotador, efectos de corrida y de función, hiperparámetros por división, efecto de idioma (si hay ablación), curva de calidad del matching.

**Qué reporta B1:** posterior de `E_g` (media, intervalo creíble al 90 % u 80 %, a fijar), probabilidad posterior de pertenecer a cada tercil, posterior de la tabla cruzada `exposure_class` x `eloundou_class`, matrices de confusión humano-LLM con intervalos, comparación posterior de rutas S y O (`Delta_g`), y chequeos predictivos (abajo).

### Nivel B2. Capa de aplicabilidad al contexto: "exposición ajustada por contexto" [DIFERIDO, Registro 1]

**Qué es.** Una cantidad **distinta y nombrada distinta** de la exposición técnica: "exposición ajustada por contexto (acceso potencial)". **No la reemplaza.** La exposición técnica sigue siendo la medida principal de 001.

**Por qué se justifica.** Atiende las filas 1, 2 y 5 del diagnóstico: el preámbulo de Eloundou supone laptop, software y LLM; en una microempresa o en la informalidad esas condiciones pueden no darse. Es también la respuesta a 001 §10.7 (¿ajuste por brecha digital/informalidad como medida secundaria o solo escenario?), que está **"requiere decisión"** y que esta propuesta no resuelve.

**Forma propuesta (esquema).** Celdas de contexto `c` = (formalidad x tamaño de unidad económica x ámbito urbano/rural, a confirmar con las variables disponibles **[NO VERIFICADO]**).
- Composición del grupo: `ω_{g,c}` = proporción del empleo del grupo `g` en la celda `c`, de la ENOE con factor de expansión (dato, con incertidumbre de diseño).
- Parámetros de aplicabilidad: `a_c ∈ [0,1]` con prior informado `Beta(m_c κ, (1-m_c) κ)` donde `m_c` y `κ` se fijan por elicitación de expertos o literatura. Opcionalmente un peso distinto para el componente complementario: `beta_c = EL1 + w_c · EL2`, con `w_c` ≤ el 0.5 convencional (tamaño pequeño menos inversión complementaria posible).
- `E_g^ctx = Σ_c ω_{g,c} · a_c · E_g`. (Alternativa sin multiplicar: reportar `E_g` por celda de contexto sin parámetros; ver recomendación.)
- Jerarquía: `a_c` compartiendo información entre celdas parecidas.

**Qué se calibra y contra qué.** Solo si existe un observable de **acceso o capacidad de uso** por celda (variables de uso de computadora, internet o equipo en el trabajo; **[NO VERIFICADO] que la ENOE las traiga**; ENDUTIH mide uso de internet y computadora por persona, y su desglose por ocupación **no apareció en los resultados**, así que la unión con SINCO es [NO VERIFICADO]). Sin observable, el posterior es el prior: se reporta como **análisis de escenario con priors explícitos y no como calibración**. Es mejor decirlo así que simular un aprendizaje que no ocurre.

**Reglas.** (i) `a_c` mide capacidad de acceso, **no adopción**; mezclar ambos contradiría 001 §4.1. (ii) Nunca se calibra contra salario, formalidad como resultado ni empleo. (iii) Requiere una decisión nueva y, si se aprueba, una enmienda del glosario (regla 2) para el término nuevo.

### Nivel B3. Calibración directa contra resultados de la ENOE (salarios, formalidad) [DESACONSEJADO]

**Evaluación: se desaconseja como calibración.** Argumentos: sección 4 (sin observable, circularidad, endogeneidad, confusión, contradice 001 §4.1 y §8). 

**Lo que sí se permite con la ENOE (y no es calibración):**
- **Asociaciones descriptivas** de `E_g` con escolaridad, salario y formalidad, con factor de expansión y diseño complejo, y con la incertidumbre de B1 propagada (regresión sobre sorteos del posterior de `E_g`, que corrige la atenuación por error de medición que de otro modo sesgaría los coeficientes hacia cero). Se rotulan descriptivas (001 §8).
- **Hipótesis direccionales fijadas antes de ver la ENOE**, usadas como prueba de validez de constructo con aprobación o rechazo, no para ajustar parámetros. Ejemplos de hipótesis (a fijar por el humano, no por mí): H1, `E_g` asociada positivamente con escolaridad promedio del grupo; H2, `E_g` menor donde `physical_bottleneck` domina (ya es el control negativo de 011 §4.g.6). Si fallan, se investiga la medición (rutas S y O, anotador, matching), no se reajusta.
- **Nota de contexto, sin conclusión:** el manuscrito de Ceballos y Guadarrama (según el reporte del orquestador, no verificado por mí) halla probabilidad de automatización media de 58 % para formales y 80 % para informales con Frey-Osborne; la literatura regional que reporté en 001 §3.5 (solo resumen) dice que el empleo formal y urbano aparece más expuesto a IA generativa. Si ambas son ciertas, la diferencia de signo entre automatización y exposición a IA generativa es esperable por construcción (tareas manuales rutinarias frente a tareas cognitivas), y es una razón más para no calibrar una medida contra la otra ni contra resultados.

### Cuadro: qué hace cada nivel

| Nivel | Qué se estima | Contra qué | Usa ENOE | Cambia la exposición técnica |
|---|---|---|---|---|
| B1 | Error de anotación y de matching; posterior de `E_g` | Corridas múltiples, muestra humana, muestra de oro del matching | No | No (la mide con incertidumbre; reemplaza el min-max) |
| B1.b | Calidad del matching por par | Muestra de oro | No | Afecta `E_O` |
| B2 | `a_c` y composición `ω_{g,c}` | Priors; datos de acceso solo si existen; `ω` de la ENOE | Sí, solo como contexto y composición | No; produce otra cantidad |
| B3 | Asociaciones y pruebas direccionales | Resultados de la ENOE | Sí | **No**; prohibido recalibrar |

## 6. Parámetros candidatos: cuáles se calibran y cuáles son convenciones

| Parámetro | Valor actual | Tipo | Cómo se trata |
|---|---|---|---|
| Peso del EL2 en la medida intermedia (el 0.5) | 0.5 (Eloundou; E1 + 0.5·E2) | Convención de la definición | Eje de sensibilidad `w ∈ [0,1]` (alfa en 0, beta en 0.5, cota superior en 1); curva `E_g(w)`. No se estima |
| Mapa E0/E1/E2 de 001 (0 / 0.5 / 1) | fijado en config | Convención | Límites inferior y superior ya previstos (001 §4.3) |
| Umbral de 50 % de tiempo | Eloundou | Convención (c) | Solo sensibilidad vía otro prompt |
| Sesgo del anotador (confusión, `δ_k`, `τ_k`) | sin modelo | Calibrable | B1 con muestra humana |
| Varianza entre corridas / dificultad por función | sin modelo | Calibrable | B1 con 3+ corridas |
| Efecto de idioma del prompt/texto | sin medir | Calibrable | B1 con ablación de idioma y revisores bilingües |
| Pesos de tareas (core 2:1, iguales, tiempo) | iguales en S | Convención; sensibilidad | Opcional contra juicio holístico, solo sensibilidad (4.6) |
| Umbral de confianza/cobertura del matching | `umbral_onet_sinco` PROVISIONAL | Calibrable | B1.b con muestra de oro |
| Pesos 1:N del crosswalk (uniformes) | uniformes | Convención con sensibilidad | B1.b da probabilidades por par; los pesos de empleo EE. UU./México solo sensibilidad |
| Umbral `pocas_funciones` (< 3) | PROVISIONAL | Convención que se vuelve parámetro de regularización | Lo absorbe el pooling de B1 |
| Aplicabilidad `a_c`, peso `w_c` por contexto | sin definir | Prior; calibrable solo con observable de acceso | B2, escenario (diferido) |
| Preámbulo (2023 vs actual) | literal de 2023 | Convención (c) | Dos prompts |

## 7. Qué se reporta

- **Posteriores y intervalos creíbles** de `E_g`, `alfa_S`, `beta_S`, `cota_sup_S` por grupo; para niveles superiores, la media ponderada por empleo calculada **por sorteo del posterior**, de modo que el intervalo combine incertidumbre de medición con la de diseño de la ENOE. Con ~8 funciones por grupo y 3 corridas, intervalos anchos son un resultado, no un defecto.
- **Chequeos predictivos:** (i) *prior predictive* para verificar que los priors no implican exposiciones absurdas; (ii) *posterior predictive* de la distribución de etiquetas por corrida y por anotador (¿el modelo reproduce el desacuerdo observado?); (iii) chequeo de que las funciones con alta varianza entre corridas se concentran donde el modelo dice que hay ambigüedad; (iv) validación cruzada sobre la muestra humana (dejar fuera revisores o funciones) con log densidad predictiva; (v) cobertura empírica de los intervalos sobre funciones humanas retenidas.
- **Sensibilidad de priors** (al menos dos niveles de informatividad) y comparación con el resultado no bayesiano (media simple de corridas), para mostrar cuánto cambia el modelo.
- Diagnósticos de muestreo (R-hat, ESS, divergencias) si se usa MCMC; si se usa Gibbs conjugado propio, trazas y semillas.
- Todo con etiqueta `PROVISIONAL, SIN VALIDAR` hasta cerrar la muestra humana, como en 010 §6.7; ninguna cifra sin script en `src/` (regla 1).

## 8. Protocolo de dos rondas rediseñado

*(Registro 1: el usuario eligió el reporte descriptivo por estratos; este protocolo de dos rondas se conserva como registro de lo analizado. Lo que aplica al reporte descriptivo —congelar, pre-registrar, partición, prohibiciones— se retoma en el borrador 013. La ronda 2 con actualización de parámetros de B2 no se persigue mientras B2 esté diferido.)*

Principio: la ronda 2 debe ser **confirmatoria** y estar atada a un plan escrito antes de mirar la ENOE.

### 8.1 Antes de tocar la ENOE (ronda 0, congelado)
1. Congelar la exposición de registro: versión del catálogo (sha256), rutas S y O, prompt(s) y `prompt_sha256`, `run_id`, mapas, posteriors de B1 (semilla, versión del modelo y de los priors), todo con hash en un artefacto registrado.
2. Registrar en `docs/decisions/` (propuesta: decisión 013, "pre-registro del cruce con la ENOE") el plan de análisis: estimandos, definiciones (formalidad según INEGI, ver 9), exclusiones permitidas, hipótesis direccionales, reglas de decisión, forma de partición y criterio de validación de B2. Se firma con fecha **antes de descargar** microdatos.
3. Fijar la regla de partición de manera determinista antes de descargar (sección 8.2).
4. Los parámetros de B1/B1.b ya están estimados sin la ENOE; **la ENOE no puede modificarlos**.

### 8.2 Partición de los datos
La ENOE es un panel rotatorio: cinco paneles, cada vivienda permanece cinco trimestres y cada trimestre se reemplaza un quinto (resumen del catálogo de INEGI; no verificado contra la metodología vigente). Particionar por trimestres adyacentes filtraría información (80 % de la muestra se repite). Opciones:
- **Partición temporal con brecha:** ronda 1 en un año y ronda 2 en otro separado por al menos cinco trimestres (sin viviendas compartidas, por el esquema anterior). Ventaja: sin solapamiento de viviendas. Riesgo: cambios reales entre periodos (recuperación postpandemia, adopción de herramientas de IA generativa) que confundirían la comparación; ambos periodos deben ser SINCO 2019 (desde 3T 2021 si se confirma, 4.8). *(Precisión en 013: si una vivienda se visita en cinco trimestres consecutivos, dos trimestres no comparten viviendas cuando los separan al menos cinco trimestres de calendario, es decir, cuatro trimestres intermedios; "al menos cinco trimestres" de esta viñeta debe leerse así y está sujeto a la verificación del esquema de panel.)*
- **Partición por conglomerados** (unidades primarias de muestreo asignadas al azar a cada mitad dentro de cada estrato): mantiene el periodo, pero exige tratar cada mitad como submuestra con su propio diseño y reescalar los factores de expansión; complejidad **[NO VERIFICADO]**.
Recomendación: partición temporal con brecha, por simplicidad, declarando el riesgo de cambio temporal. La decisión es del humano.

### 8.3 Ronda 1 (exploratoria y descriptiva, partición A)
Permitido:
- Distribución de `E_g` (y sus posteriors) ponderada por factor de expansión: global, por formal/informal, por región, sexo, tamaño de unidad, grupo de edad. Descomposición composicional entre grupos SINCO.
- Cobertura: cuántas personas ocupadas caen en grupos con medida, con residuales NA, por `match_quality` y por ruta.
- Las asociaciones descriptivas de B3 y las pruebas direccionales.
- Ajuste de **B2** con priors y datos de contexto si existe un observable (8.4).
- Diagnóstico de calidad: códigos SINCO de la ENOE no presentes en el catálogo, porcentaje de ocupados sin código válido.
No permitido en la ronda 1: modificar `E_g`, etiquetas, prompts, matching, mapas ni pesos con base en lo que se ve.

### 8.4 Ronda 2 (confirmatoria, partición B)
Permitido:
- Repetir exactamente el plan de la ronda 1 sobre la partición B, sin cambios, y reportar ambos resultados lado a lado.
- **Solo** actualizar los parámetros de contexto de B2 (`a_c`, `w_c`), con un criterio de validación fuera de muestra fijado de antemano: mejora en densidad predictiva logarítmica esperada (ELPD) sobre la partición B frente al modelo con solo el prior, con regla de aceptación (p. ej. mejora mayor que dos errores estándar; umbral **PROVISIONAL**, a fijar por el humano). Si no se cumple, se conservan los priors y se reporta que los datos no informaron.
- El observable de validación de B2 tiene que existir y estar nombrado en el pre-registro; si no existe, la ronda 2 es solo la réplica del plan de la ronda 1.

### 8.5 Qué NO se permite en ninguna ronda
1. Cambiar la exposición técnica (`E_g`, `alfa_S`, `beta_S`, `cota_sup_S`) por algún motivo basado en la ENOE.
2. Calibrar cualquier parámetro contra salario, ingreso, horas, formalidad como resultado, o empleo.
3. Parámetros distintos por formal/informal en la exposición técnica (la técnica es una; el contexto es B2).
4. Elegir la partición, el periodo, las exclusiones o la definición de informalidad después de ver resultados.
5. Excluir ocupaciones "que se ven raras" sin regla previa; en su lugar, se examinan como casos de auditoría de medición.
6. Reportar solo la ronda en que algo "salió".
7. Usar la ENOE para decidir cuál de las rutas (S u O) es la correcta.
8. Cualquier desviación se registra en `docs/decisions/` con fecha, motivo y qué se vio antes de decidir.

## 9. Dependencias del plan

| Dependencia | Estado |
|---|---|
| Matching más preciso: muestra de oro, regenerarla con top-2, validar | No existe; 005 no pude leerlo; 003 prevé ~10 % de grupos con doble revisión; quién revisa y con qué guía "requiere decisión" |
| Corrida completa de anotación | Modelo/vía, fecha de corte, presupuesto o cuota: "requiere decisión" (001 §10.3, 008 §7 según 010) |
| Muestra humana de funciones (300) y 49 grupos | Revisores, guía y horas: "requiere decisión" |
| Versión de SINCO en la ENOE | Según un resumen de buscador, SINCO 2019 desde 3T 2021 (ver 4.8, actualización); **[NO VERIFICADO]** contra INEGI (PDF ilegible para mi herramienta) |
| Fuente de datos de la ENOE y decisión ENOE vs ENOEN | Registro 1: se usará `enoeR`, que cubre ENOE y ENOE-N; **qué ediciones y trimestres usar sigue siendo decisión del humano** (013). Ceballos y Guadarrama usan ENOE 3T 2024, según el reporte del orquestador |
| Definición oficial de informalidad de INEGI | Según el buscador, INEGI sigue el marco de la OIT con la matriz de Hussmanns (empleo informal en el sector informal, empleo informal fuera del sector informal, empleo formal), basado en la 15ª CIET (1993, sector informal) y la 17ª CIET (2003, empleo informal). **Texto literal [NO VERIFICADO]**; hay que leer la metodología de la ENOE antes de pre-registrar la variable |
| Variables de contexto en la ENOE (tamaño de establecimiento, tipo de unidad, uso de computadora) | **[NO VERIFICADO]** |
| Diseño complejo de la ENOE (estratos, conglomerados, factor de expansión) | Diseño probabilístico, bietápico, estratificado y por conglomerados según el resumen del catálogo de INEGI; detalles de varianza y de combinación de trimestres **[NO VERIFICADO]** |
| Paquetes bayesianos | El stack aprobado (CLAUDE.md, `requirements.txt`) tiene numpy 2.5.4 y pandas; **no tiene scipy, PyMC, Stan ni NumPyro**. Opción 1 (sin dependencias nuevas): implementación propia en numpy de un muestreador de Gibbs para Dawid-Skene con priors Dirichlet (condicionalmente conjugado) y EM; alcanza para B1 con matrices de confusión, no para el modelo ordinal jerárquico con efectos de función. Opción 2 (requiere aprobación): PyMC, Stan (CmdStan/cmdstanpy) o NumPyro para B1 completo y B2; la instalación en este equipo Windows (compilador, versión de Python) **[NO VERIFICADO]**. La Stan User's Guide incluye modelos de codificación de datos con el modelo de Dawid y Skene (resultado de búsqueda, no leído) |
| R para `enoeR` (Registro 1) | El stack de CLAUDE.md es Python; `enoeR` requiere R. Instalar R y el paquete en este equipo es una herramienta externa nueva para la descarga: versión de R y estado de la instalación **[NO VERIFICADO]**; la decisión de aceptarla como herramienta externa (no como dependencia del código en `src/`) es del humano (013) |
| Costo computacional | B1 con 3,542 funciones y 4-5 anotadores (3+ corridas + revisores) es pequeño; tiempo de muestreo por estimar **[NO VERIFICADO]**, no medido. B2 es pequeño (celdas por grupo). El costo dominante es humano (revisores) y de anotación, no computacional |

## 10. Recomendación y plan por fases (pendiente de revisión humana)

**Recomendación.** (1) Aceptar el enfoque bayesiano **como modelo de error de medición (B1)**, no como calibración contra el mercado laboral. (2) Tratar las dudas de transferibilidad como **alcance**, reportando una capa B2 separada, con priors explícitos y nombre distinto, o más simplemente un reporte descriptivo de la exposición técnica por estrato de contexto sin parámetros. (3) Usar la ENOE para **ponderar y describir**, con exposición congelada, plan pre-registrado y ronda 2 confirmatoria. (4) Desaconsejar B3 como calibración. *(Registro 1: el usuario adoptó (1), el reporte descriptivo por estratos de (2) y (4); B2 diferido.)*

**Mi alternativa más sencilla y más defendible a "dos rondas de recalibración":** una ronda descriptiva con exposición congelada, estratificada por contexto (formal/informal, tamaño, región) y con descomposición composicional, más una réplica en la partición B. Con esto se responde "¿cómo cambia la exposición entre trabajadores formales e informales?" sin ningún parámetro nuevo y sin riesgo de circularidad. B2 se activa solo si el humano decide que necesita una cifra de aplicabilidad.

| Fase | Entregable | Depende de |
|---|---|---|
| F0 | Decisiones del humano sobre esta propuesta (B1, B2, B3, protocolo, partición) | Revisión humana (parcialmente hecha: Registro 1) |
| F1 | Matching más preciso y muestra de oro con top-2 | 005, revisores |
| F2 | Piloto de anotación de la ruta S (011 §8) con 3 corridas y registro completo | Enmiendas E-1/E-2 (aprobadas, Registro 4 de 011); E-5 y E-6 pendientes; fecha de corte, modelo/vía |
| F3 | Muestra humana de funciones y 49 grupos | Revisores y guía |
| F4 | B1 en versión sin dependencias nuevas (Gibbs conjugado) y, si se aprueba, B1 completo con paquete bayesiano | F2, F3; aprobación de dependencia |
| F5 | Pre-registro 013 y congelado de exposición, antes de descargar la ENOE | F4; decisión de datos (versión SINCO, ediciones de la ENOE, definición de informalidad, estratos, trimestres) |
| F6 | Reporte descriptivo por estratos (ronda 1) | F5, descarga autorizada |
| F7 | Réplica en la partición B (opcional, según 013); B2 solo si hay observable y una decisión nueva | F6 |

## 11. Riesgos de esta propuesta

1. **Falsa precisión de B1:** si se modelan las corridas como independientes, el posterior sobreestima la certeza. Mitigación: efecto de función compartido y muestra humana; reportar B1 sin humana como "solo consistencia".
2. **Shrinkage que aplana la medida:** el pooling jerárquico comprime las diferencias entre grupos con pocas funciones. Mitigación: reportar con y sin pooling.
3. **Muestra humana pequeña** (300 funciones; EL2 escaso): matrices de confusión mal estimadas. Mitigación: modelo ordinal parsimonioso y priors débilmente informativos; reportar incertidumbre en vez de ocultarla.
4. **B2 sin observable:** el posterior es el prior; el riesgo es que parezca calibración. Mitigación: etiquetarlo escenario y mostrar prior frente a posterior.
5. **Confundir exposición ajustada por contexto con riesgo o adopción.** Mitigación: nombre y glosario propios; prohibido llamarla riesgo (001 §4.6).
6. **Cambio de periodo** si la partición es temporal. Mitigación: declarar y comparar ambas rondas.
7. **SINCO 2011 en trimestres antiguos** y posibles diferencias de codificación en la ENOE. Mitigación: restringir a SINCO 2019.
8. **Datos de segunda mano:** todo lo de INEGI en este documento viene de resúmenes de buscador.
9. **Complejidad:** la capa bayesiana añade piezas que el artículo debe explicar. La alternativa descriptiva es más barata y casi siempre suficiente para el objetivo declarado.
10. **Dependencias aún sin decidir** (modelo, presupuesto, revisores) pueden bloquear F2-F4.
11. **Mi lectura de 005 y 009 es indirecta** (no pude abrirlos).
12. **Herramienta de descarga en desarrollo (Registro 1):** `enoeR` es un paquete propio, con funciones marcadas "In Progress", sin versión ni commit visibles para mí, y con licencia declarada como MIT en el README pero NOASSERTION en la API de GitHub. Riesgo de que cambie entre descargas o de errores de lectura. Mitigación en 013: fijar commit, registrar hashes de cada archivo descargado y verificar un archivo contra la fuente de INEGI.

## 12. Alternativas consideradas

| Alternativa | Veredicto |
|---|---|
| A. Propuesta del usuario tal cual (asignar, aplicar a ENOE, dividir formal/informal, recalibrar parámetros de exposición en dos rondas) | Desaconsejada: sin observable, circular, borra la diferencia, forking paths. **No adoptada (Registro 1)** |
| B. B1 solamente (error de medición, sin ENOE) | Recomendada como núcleo bayesiano. **Adoptada para avanzar (Registro 1)** |
| C. B1 + descriptivo con ENOE (exposición congelada, estratos de contexto) | Recomendada como plan base. **Adoptada en la forma de reporte descriptivo por estratos (Registro 1; borrador 013)** |
| D. C + B2 (exposición ajustada por contexto con priors) | Opcional, solo si el humano necesita la cifra y acepta que es escenario. **Diferida (Registro 1)** |
| E. B3 calibración contra salarios o formalidad | Desaconsejada |
| F. Sin modelo bayesiano: intervalos bootstrap y min-max como en 010 §6.6 | Viable pero con peor tratamiento de incertidumbre; es el punto de comparación de B1 |
| G. Anotar un campo "aplicabilidad al contexto mexicano" por función (medición de B2 sin ENOE) | Posible variante de B2 que sí tendría referencia humana; requiere enmienda de rúbrica (regla 2) y más anotación; no desarrollada aquí |

## 13. Preguntas abiertas para el humano

1. ~~¿Se acepta reencuadrar el enfoque bayesiano como modelo de error de medición (B1) y desaconsejar la calibración contra resultados laborales (B3)?~~ **Respondida en lo esencial (Registro 1):** se avanza con B1; B3 no se persigue. Queda abierto si el humano quiere explorar un observable de calibración distinto.
2. ~~¿Se quiere una capa B2 o basta con el reporte descriptivo por estrato?~~ **Respondida (Registro 1):** reporte descriptivo por estratos; B2 diferido. 001 §10.7 sigue "requiere decisión".
3. ¿Partición temporal con brecha o por conglomerados? ¿Qué periodo es la ronda 1? (Propuestas en 013.)
4. ¿ENOE o ENOEN, y qué trimestres (desde 3T 2021 si se confirma SINCO 2019)? (Opciones en 013; `enoeR` cubre ambas.)
5. ¿Qué definición de informalidad se pre-registra (la oficial de INEGI, previa lectura de su metodología)?
6. ¿Se autoriza una dependencia bayesiana (PyMC, Stan, NumPyro) o se prefiere numpy propio con Gibbs conjugado y límites de modelo? (Necesaria para avanzar con B1 más allá del Gibbs conjugado.)
7. ¿Quién forma la muestra humana y con qué guía? Sin ella B1 mide consistencia y no exactitud.
8. ¿Hipótesis direccionales para la validación de constructo (H1, H2 y otras)? Deben salir del humano antes de ver datos.
9. ~~¿Regla de aceptación de B2 en la ronda 2 (umbral de mejora predictiva)?~~ **Sin efecto mientras B2 esté diferido.**
10. ¿Alguien puede abrir 005 y 009 y confirmar mi lectura indirecta?
11. ~~¿Se confirman E-1 y E-2 de 011 y se resuelven E-3 a E-8?~~ **Respondida en parte (Registro 1):** E-1, E-2, E-3 y E-8 aprobadas; E-4 a E-7 siguen pendientes.
12. (Nueva, Registro 1) ¿Se acepta R (y `enoeR`) como herramienta externa solo para descargar, y dónde se guardan los CSV (política de datos, 013)?

## 14. Lista de [NO VERIFICADO]

- Variables de la ENOE: tamaño del establecimiento, tipo de unidad económica, uso de computadora o internet en el trabajo, dígitos del código SINCO, nombre de las variables de panel y de factor de expansión.
- Versión de SINCO usada por la ENOE por trimestre (resumen: 2019 desde 3T 2021).
- ENOE frente a ENOEN: cuál aplica.
- Texto literal de la definición de informalidad de INEGI.
- Detalles del cálculo del factor de expansión y de la varianza con trimestres combinados.
- Si ENDUTIH cruza por ocupación; si trae variables de uso de IA.
- Cualquier observable de acceso/uso digital por ocupación que identifique `a_c`.
- Columnas de puntaje y `match_status` del matching de 005; contenido de 005 y 009.
- Potencia estadística de la muestra humana para estimar matrices de confusión (no calculada).
- Instalación y rendimiento de paquetes bayesianos en este equipo; tiempos de muestreo.
- Cifras de Ceballos y Guadarrama (58 % formales, 80 % informales): transmitidas por el orquestador, no verificadas por mí.
- Literatura regional (Gmyrek et al., 2024) leída solo en resumen.
- (Registro 1) Que la cita del Registro 1 provenga directamente del usuario (relayada por el orquestador).
- (Registro 1) Versión y commit de `enoeR`; texto de su LICENSE; comportamiento real de `enoe_load`/`enoe_list`; instalación de R en este equipo.

## 15. Fuentes consultadas (2026-10-19)

Archivos del proyecto: `CLAUDE.md`; `docs/decisions/001-definicion-exposicion.md`, `003-requisitos-tablas-sinco.md`, `010-metodos-exposicion-sinco.md`, `011-metodo-tipo-anthropic-eloundou-sinco.md`; `docs/rubric.md`; `docs/glossary.md`; `src/score/README.md`; `src/annotate/README.md`; `requirements.txt`; `docs/issues/datos-2026-10-19-sinco-anexo-equivalencia-descartado.md`.

Web (resúmenes de herramienta; los PDF de INEGI no fueron legibles):
- Versión de SINCO en la ENOE (resumen del buscador): https://inegi.org.mx/contenidos/programas/enoe/15ymas/doc/clasificaciones_enoe_123.pdf y https://inegi.org.mx/contenidos/programas/enoe/15ymas/doc/nota_nvas_clasificaciones.pdf (ilegibles para mi herramienta; consultados 2026-10-19). Adicional (Registro 1, solo resultado de búsqueda, no abierto): https://inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_nota_clasificaciones_trim3_2021.pdf (consultado 2026-10-19).
- Informalidad en la ENOE (resumen del buscador; matriz de Hussmanns, 15ª y 17ª CIET): https://www.snieg.mx/DocAcervoINN/documentacion/inf_nvo_acervo/SNIDS/ENOE/Informalidad_FINAL.pdf (ilegible); presentación del INEGI en la CEPAL https://www.cepal.org/sites/default/files/presentations/20190404_16._heredia-inegi.pdf (solo en resultados de búsqueda); Negrete (INEGI) https://www.wiego.org/sites/default/files/publications/files/Negrete_El.empleo.informal.Mexico.pdf (solo en resultados de búsqueda). Consultados 2026-10-19.
- Diseño muestral de la ENOE (resumen de fichas del catálogo de INEGI): https://www.inegi.org.mx/rnm/index.php/catalog/1105 y https://inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_diseno_muestral.pdf (este último es de la ENOE N). Consultados 2026-10-19.
- ENDUTIH (resumen del buscador): https://inegi.org.mx/contenidos/programas/dutih/2020/doc/nota_tecnica_endutih_2020.pdf y https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/endutih/ENDUTIH_24_RR.pdf. Consultados 2026-10-19.
- Dawid y Skene (1979), Applied Statistics 28(1): 20-28: https://ideas.repec.org/a/bla/jorssc/v28y1979i1p20-28.html ; Stan User's Guide, data coding models: https://mc-stan.org/docs/2_32/stan-users-guide/data-coding-models.html (solo en resultados de búsqueda). Consultados 2026-10-19.
- Gelman y Loken, "The garden of forking paths": resumen en https://forrt.org/glossary/english/garden_of_forking_paths/ (DOI del artículo 10.1511/2014.111.460 según esa página). Consultado 2026-10-19.
- `enoeR` (Registro 1): https://github.com/DiegoSReco/enoeR (WebFetch, resumen de herramienta, 2026-10-19; README leído además por el orquestador).
- Eloundou et al. (2023) y Massenkoff y McCrory (2026): solo vía 011 (verificados allí contra los PDF registrados en `data/raw/manifest.json`); no se reconsultaron.
