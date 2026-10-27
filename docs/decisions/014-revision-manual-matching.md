# 014. Revision manual de emparejamientos SINCO -> O*NET de baja confianza y sin coincidencia; embeddings interlingues

Estado: **PENDIENTE DE REVISION HUMANA**. Excepcion: la solicitud de que el usuario revise a mano los casos de baja confianza y sin coincidencia y de que se actualice el emparejamiento con esa revision fue pedida expresamente por el usuario (2026-10-19). Todo lo demas (la politica detallada, los criterios, los experimentos) es propuesta y no esta aprobado.
Fecha: 2026-10-19. Autor: agente de metodos.
Relacionada con: 005 (metodo de emparejamiento; no pude abrir su archivo, ver "Limites de esta decision"), 011/012 (exposicion por SINCO y calibracion), issue `docs/issues/emparejamiento-2026-10-19-parametros-provisionales-y-sin-coincidencia.md`.

## Limites de esta decision (que se verifico y que no)
Verificado leyendo archivos del proyecto: `src/match/texts.py`, `src/match/config.toml` y el issue citado. Verificado en fichas de modelos (consultadas 2026-10-19): bge-m3 y multilingual-e5-large. NO leido: el archivo de la decision 005 (no localice su nombre exacto con las herramientas disponibles), los resultados parquet/json (las cifras 58, 25, 255, 45.7 %, rangos de similitud y margenes las tomo del encargo del usuario y del issue, no las recalcule), y ninguna literatura academica sobre recuperacion interlingue. Todo lo que dependa de ello va marcado [NO VERIFICADO].

---

## Parte A. Pregunta tecnica: hay problemas en comparar SINCO (espanol) con O*NET (ingles) por embeddings?

### A.1 Respuesta corta
Si, hay riesgos reales, pero con la evidencia actual **no se puede afirmar ni descartar** que explican los fallos observados. Los modelos usados son multilingues y el diseno actual es asimetrico en idioma, longitud y nivel de detalle; eso son factores de riesgo plausibles. La hipotesis de un fallo de recuperacion interlingue en oficios (issue) **no esta demostrada**: los datos observados son compatibles tambien con (a) ausencia de equivalente fino en O*NET, (b) texto asimetrico, (c) regla relativa de `sin_coincidencia` (ver A.3).

### A.2 Lo verificado
(a) Modelos multilingues.
- bge-m3: la ficha dice que soporta mas de 100 idiomas, admite entradas de hasta 8192 tokens, no requiere instrucciones en la consulta, y tiene una seccion de resultados interlinguees (MKQA) cuyas cifras no pude leer en la consulta. Fuente: https://huggingface.co/BAAI/bge-m3 (consultada 2026-10-19).
- multilingual-e5-large: se inicializa de xlm-roberta-large, soporta los 100 idiomas de xlm-roberta; la ficha advierte que "low-resource languages may see performance degradation"; limite de 512 tokens, con truncamiento; exige prefijo "query: " o "passage: " tambien en texto no ingles; sugiere "query: " para tareas simetricas. La ficha no describe limitaciones interlinguees especificas. Fuente: https://huggingface.co/intfloat/multilingual-e5-large (consultada 2026-10-19). El espanol no es de bajos recursos [NO VERIFICADO en la ficha; es conocimiento general].

(b) Configuracion real (`src/match/texts.py`, `src/match/config.toml`).
- SINCO (consulta): titulo ampliado + ocupaciones ejemplo (hasta 50) + descripcion + funciones, con etiquetas en espanol ("Ocupaciones: ", "Descripcion: ", "Funciones: ").
- O*NET (documento): titulo + descripcion, con etiqueta "Description: ". Sin tareas, sin traduccion.
- bge-m3: sin prefijos, max_length 1024. e5: "query: " en ambos lados, max_length 512. Segun el encargo del usuario, 24 textos SINCO quedan truncados con e5 y ninguno con bge-m3 (cifra no recalculada por mi). Prioridad de truncamiento: titulo, ocupaciones, descripcion, funciones, es decir, lo que se pierde primero en e5 son las funciones.
- Nota: el codigo dice que los textos SINCO "rara vez pasan de ~700 tokens", mientras e5 corta a 512: la comparacion entre modelos mezcla modelo y cantidad de texto visto.

(c) Resultados observados (issue y encargo; no recalculados).
- 25 `sin_coincidencia` por bge-m3, incluyendo 7121 Albaniles y 7513 pan y reposteria.
- Acuerdo top-1 entre modelos 45.7 %; mismo gran grupo SOC 67.1 %; Spearman de la probabilidad F-O 0.84 (n = 396).
- e5 muy comprimido (rango 1 de 0.838 a 0.912; margen mediano 0.0057) frente a bge-m3 (media 0.717; mediana del margen 0.021). Un coseno comprimido es esperable en e5 (propiedad de entrenamiento con temperatura baja) [NO VERIFICADO: no lo lei en la ficha ni en el paper], y por eso delta/tau/umbrales se fijaron por modelo.

### A.3 Observacion clave: `sin_coincidencia` es relativa
Por construccion (cuantil 0.05 de sim_top1) marca siempre 25 de 490 grupos, haya o no equivalente. Que 7121 y 7513 aparezcan ahi indica que tienen la similitud top-1 mas baja del modelo, no que no exista equivalente. Pero que oficios muy conocidos (albanil, panadero) tengan similitud baja **si** es una senal que merece diagnostico. Lectura posible (no demostrada): O*NET describe "Construction Laborers", "Bricklayers", "Bakers" con descripcion corta y tecnica, mientras el texto SINCO es largo, con lista de ocupaciones locales y funciones; el coseno de un texto largo y diverso contra uno corto tiende a bajar [NO VERIFICADO como fenomeno general].

### A.4 Riesgos conocidos de la recuperacion cruzada de idiomas y de textos asimetricos
Todos [NO VERIFICADO] salvo lo indicado, pues no lei literatura sobre el tema; se plantean como hipotesis a contrastar con los experimentos de A.5.
1. Sesgo de idioma: en modelos multilingues, un texto tiende a parecerse mas a textos del mismo idioma que a su traduccion; entre varios candidatos ingleses esto afecta poco el ranking relativo (todos son ingles), pero comprime el coseno absoluto y puede degradar la ordenacion fina.
2. Asimetria de longitud y estructura: consulta larga con cuatro campos frente a documento corto con dos. Se promedia el contenido semantico del texto largo (ocupaciones ejemplo diversas), diluyendo el oficio central.
3. Registro y nivel de detalle: SINCO 2019 es un clasificador mexicano a nivel grupo unitario (490 grupos), O*NET-SOC tiene ~1000 ocupaciones con granularidad distinta; relacion 1:N y N:1. Gentilicios, modismos y oficios locales (p. ej. terminos de oficio sin equivalente exacto) pueden no tener ocupacion homologa.
4. Ausencia de tareas O*NET en el lado ingles: la ventaja de O*NET es justamente su detalle de tareas; el documento usa solo titulo y descripcion, mientras SINCO aporta funciones. Hay asimetria de informacion a favor de SINCO.
5. Prefijos: e5 con "query: " en ambos lados es lo que la ficha sugiere para tareas simetricas, pero la tarea aqui es mas parecida a recuperacion asimetrica; no esta probado cual es mejor.
6. Truncamiento diferencial entre modelos (24 textos en e5), que confunde la comparacion de modelos.
7. Confusion entre ausencia de equivalente (decision del usuario) y fallo de recuperacion: sin referencia humana no son distinguibles.

### A.5 Experimentos baratos, sin API (propuesta; todos requieren aprobacion antes de implementarse, regla 7)
Todos se evaluan contra la misma referencia: la revision manual (Parte B) y la muestra de oro (255 grupos) cuando tenga revisores, con precision@1, @2 (k_top=2 es lo que alimenta la probabilidad), recall@10 de la ocupacion correcta, y tasa de `sin_coincidencia` espurea. Reportar IC bootstrap por grupos y comparar variantes de forma pareada (McNemar o bootstrap pareado).
- (i) **A2: SINCO traducido al ingles** (variante A2 de 005). Traduccion automatica local (modelo abierto; dependencia nueva, no aprobada) o por tabla; costo: tiempo de computo y nueva fuente de error; sesgo: la traduccion de terminos de oficio locales puede introducir errores propios y el efecto de la traduccion se confunde con el del modelo. Registrar version de traduccion en el hash.
- (ii) **Texto minimo**: solo titulo SINCO vs titulo O*NET; titulo + descripcion; titulo + descripcion + funciones (actual). Cuantifica cuanto aporta cada campo y si el texto largo diluye.
- (iii) **Tareas O*NET en el lado ingles** (titulo + descripcion + tareas centrales, con truncamiento registrado). Compara con (ii) para aislar la asimetria de informacion.
- (iv) **Igualar truncamiento** entre modelos (p. ej. e5 con max 512 tambien para bge-m3) para separar efecto de modelo de efecto de truncamiento.
- (v) **Analisis por division SINCO** (1 a 9) de similitud top-1, `sin_coincidencia`, precision contra la revision. Hipotesis a contrastar: fallos concentrados en oficios (divisiones 6-9). Prueba: razon de proporciones con IC; si no se concentra, la hipotesis interlingue de oficios pierde apoyo.
- (vi) **Reranqueo con modelo cruzado o LLM** como contraste sobre el top-10. Requiere dependencias o API no aprobadas; se deja solo como opcion. Con LLM, avisar que introduce una segunda fuente no independiente de la que se quiere validar si luego se usa LLM en la anotacion.
- Control adicional barato: para los 83 grupos revisados, contar cuantas veces la ocupacion correcta estaba en el top-10 (recall@10) y en que rango. Si casi siempre esta en el top-10, el problema es de ordenacion/umbral, no de recuperacion.

---

## Parte B. Politica de revision manual

### B.1 Pregunta
Como revisar y corregir, de forma auditable, los emparejamientos de baja confianza (58 grupos, `baja_confianza`) y sin coincidencia (25) del modelo principal bge-m3, sin contaminar la validacion ni perder trazabilidad?

### B.2 Alternativas consideradas
1. No corregir; solo reportar la bandera. Pro: sin sesgo de seleccion. Contra: el usuario ya pidio revisar y hay errores evidentes (albanil).
2. Revision manual que reemplaza los pares automaticos del grupo (propuesta). Pro: simple, trazable. Contra: sesgo de seleccion (B.5).
3. Revision manual que solo anade candidatos (sin reemplazar). Pro: conserva el automatico. Contra: mezcla ponderaciones; dificil de interpretar.
4. Revision doble de todos los casos. Pro: permite kappa. Contra: costo; hoy hay un solo revisor.

### B.3 Decision propuesta (provisional, pendiente de revision humana)
Implementacion por un agente en dos scripts en `src/` (aqui solo se registra la politica):
- **Exportacion**: un script genera un CSV con, por cada grupo en baja confianza o sin coincidencia (83), el texto SINCO, el top-10 de candidatos O*NET con titulo y rangos, y columnas para decision. Decision: por determinar si se muestran las similitudes (ver B.6 sobre ceguera).
- **Aplicacion**: otro script lee el CSV lleno y valida el esquema (regla 5: si no cumple, issue y detenerse).
- Codigos de decision por grupo:
  - ACEPTAR_RANGO1 / ACEPTAR_RANGO2 / ACEPTAR_AMBOS: se conservan esos candidatos del automatico.
  - OTRO: el revisor da uno o mas codigos O*NET-SOC; deben existir en el catalogo O*NET del proyecto.
  - NINGUNO: sin equivalente en O*NET; probabilidad F-O NA con `motivo_na = sin_equivalente_onet_revision_manual`.
  - DUDA: se ignora (el grupo queda con el emparejamiento automatico y su bandera).
- La decision manual **reemplaza** los pares automaticos del grupo. Filas nuevas con `fuente='manual'` y `estado_validacion='revision_manual_1_revisor'` (un solo revisor: no es validacion doble y no debe llamarse validado).
- Pesos de la probabilidad de automatizacion (Frey-Osborne): uniformes entre los pares manuales, salvo pesos dados por el revisor (el revisor no ordena por similitud).
- Auditoria completa: copia del archivo previo (sin sobrescribir), tabla de cambios (grupo, pares antes, pares despues, decision, fecha), nueva corrida en `match_corridas` con run_id y hash del CSV de revision; `data/raw/manifest.json` no aplica (el CSV es insumo del proyecto, ver B.8).
- **Muestra de oro** (255 grupos, candidatos de la corrida anterior, aun sin revisores): NO se modifica. Los grupos corregidos manualmente que esten en ella se marcan (`corregido_manual=True`) para poder excluirlos o analizarlos aparte.
- Siempre reportar dos versiones: "automatico" y "automatico + revision manual".

### B.4 Razonamiento
- Reemplazar evita que un par automatico erroneo conserve peso. Los pesos uniformes evitan inventar un orden que el revisor no dio.
- Etiquetar `revision_manual_1_revisor` evita sobrestimar la calidad.
- No tocar la muestra de oro mantiene una referencia independiente del arreglo.

### B.5 Preguntas abiertas
1. **Sesgo de seleccion y circularidad.** Corregir a mano solo los peores casos mejora la precision aparente del conjunto. Cualquier metrica de validacion debe calcularse sobre la muestra de oro ciega y sobre el matching automatico, no sobre el corregido. Si ademas la revision se usa para calibrar umbrales (tau, delta, cuantiles) y luego se evalua con ella, hay circularidad. Propuesta: separar los grupos revisados en calibracion y evaluacion, o usar la muestra de oro para evaluar y la revision solo para corregir. Decide el usuario.
2. **El revisor ve similitudes y no es ciego.** Ver rangos y similitudes sesga hacia aceptar el top-1 (anclaje). Opciones: ocultar similitudes y ordenar candidatos aleatoriamente; o mostrar y asumir el sesgo. Si el CSV muestra el orden, la tasa de ACEPTAR_RANGO1 sobreestima la precision del modelo.
3. **Criterio de NINGUNO.** Es ausencia real de equivalente en O*NET o fallo de recuperacion (el equivalente existe pero no aparece en el top-10)? El decisor es el usuario. Propuesta: pedir al revisor distinguir con un campo `nota` y, ante duda, buscar manualmente en O*NET antes de marcar NINGUNO; los NINGUNO deberian listarse aparte.
4. **Que hacer con DUDA.** Propuesta actual: se ignora (queda el automatico). Alternativa: tratarlo como NA y excluir de la exposicion; o segunda revision. Efecto: ignorar mantiene un emparejamiento que el propio revisor desconfia.
5. **Un revisor o dos.** Con uno no hay kappa ni estimacion de error del revisor. Propuesta: un segundo revisor sobre una submuestra de los casos manuales y kappa de Cohen (o alfa de Krippendorff si hay mas de dos) sobre la decision. Umbrales de aceptacion no definidos.
6. **Revisar tambien los grupos `ok` por muestreo.** Necesario para estimar la tasa de error del `ok`; sin esto, no se sabe si la bandera discrimina. Propuesta: muestra aleatoria estratificada de `ok` (tamano por definir con intervalo de Wilson para la tasa de error), revisada en ciego mezclada con los de baja confianza. Preguntar al usuario si quiere hacerlo. (La muestra de oro cubre parte de esto cuando tenga revisores.)
7. **Versionado y reproducibilidad.** El CSV lleno pasa a ser un insumo con hash (sha256) y fecha. El manifest actual es para `data/raw/`, que es inmutable; el CSV es una decision humana y podria vivir en otra ruta de insumos con su propio registro. Ubicacion y esquema por decidir; esta decision no escribe en `data/`.
8. **Propagacion a B1.** El matching manual reduce el error de matching pero no su incertidumbre: los intervalos por SINCO deben seguir incluyendo incertidumbre de emparejamiento. Una decision manual de un solo revisor no es certeza: propuesta tratar los pares manuales con una probabilidad de error estimada en la submuestra doble revisada (si existe), no con cero. [Detalle de B1 en 011/012; no lo reabri aqui.]
9. **Efecto sobre la exposicion por SINCO (011/012).** Los grupos NINGUNO quedan sin probabilidad F-O y sin exposicion; hay que decidir si se excluyen o se imputan en el agregado nacional, porque la exclusion de oficios cambia el agregado (los oficios son mas frecuentes en el empleo mexicano [NO VERIFICADO con ENOE]). Reportar cobertura (% de empleo con valor).
10. **Probabilidades ya publicadas.** El repositorio publico tiene la version automatica. Actualizar implica nuevo commit y cambio de cifras citadas; el usuario decide cuando. Propuesta: no sobrescribir; publicar como version nueva con etiqueta de corrida y mantener ambas.
11. **Dependencia del modelo.** Se revisan los casos del bge-m3 principal; con e5 el conjunto de baja confianza difiere (top-1 acuerdo 45.7 %). La revision corrige un modelo, no el metodo. Queda por decidir si los pares manuales tambien sustituyen en la salida alternativa (e5).
12. **Reglas de umbral.** `sin_coincidencia` por cuantil fija 25 por construccion. Tras la revision se puede estimar cuantos eran realmente sin equivalente y proponer un umbral absoluto calibrado (ligado a 005 secc. 8.1).

### B.6 Pruebas de validacion propuestas
- Sobre automatico: precision@1/@2 y recall@10 contra la muestra de oro con IC bootstrap por grupo (cuando haya revisores).
- Sobre bandera: tasa de error de baja_confianza vs ok (requiere B.5.6); AUC de la bandera si la hay.
- Sobre el cambio: tabla de cambios, % de grupos cuya decision difiere del rango 1, cambio en la media ponderada de P(FO) por division y en el Spearman con la version automatica; sensibilidad de la exposicion agregada a automatico vs automatico+manual.
- Todo script con semilla y registrado en `match_corridas`.

### B.7 Riesgos
- Sesgo de anclaje y circularidad (B.5.1-2).
- Un solo revisor: errores sin detectar; confundir "revisado" con "validado".
- Reemplazo puede introducir errores nuevos y borrar candidatos correctos.
- Pesos uniformes pueden sobreponderar un par secundario.
- Divergencia entre la version publicada y la local si no se versiona.
- Experimentos A.5: riesgo de sobreajustar el metodo a 83 + 255 grupos; correccion por multiples comparaciones en las variantes.

### B.8 Fuentes y fecha de consulta
- https://huggingface.co/BAAI/bge-m3 (2026-10-19)
- https://huggingface.co/intfloat/multilingual-e5-large (2026-10-19)
- Archivos del proyecto: `src/match/texts.py`, `src/match/config.toml`, `docs/issues/emparejamiento-2026-10-19-parametros-provisionales-y-sin-coincidencia.md` (2026-10-19).
- No se consulto literatura academica sobre recuperacion interlingue ni sobre revision manual/kappa; esas afirmaciones estan marcadas [NO VERIFICADO] o se plantean como hipotesis.

**Estado: PENDIENTE DE REVISION HUMANA** (salvo lo que el usuario solicito expresamente el 2026-10-19: revisar a mano y actualizar con el archivo).
