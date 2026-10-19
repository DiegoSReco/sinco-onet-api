# 007 - Repositorio público en GitHub: código, documentación y datos seleccionados

> **ESTADO: APROBADA y EJECUTADA en lo decidido por el usuario (2026-10-19)**; lo no verificado o sin resolver queda marcado abajo como pendiente de revisión humana. Autor: agente de métodos. Fecha: 2026-10-19. Esta versión reemplaza la formulación inicial "solo código y docs" por lo realmente aprobado y ejecutado. Repositorio: https://github.com/DiegoSReco/sinco-onet-api (público, rama `main`). Lo que se publicó lo reportó el coordinador; yo no abrí el repositorio ni ejecuté `git ls-files`.

## 1. Pregunta

¿Cómo se publica el proyecto en un repositorio de GitHub para el despliegue sin exponer datos cuya licencia o términos de redistribución no están resueltos, y qué debe revisarse antes y después de hacerlo público?

## 2. Decisiones del usuario (APROBADAS y ejecutadas)

Citas textuales del usuario (2026-10-19): "Si es necesario crea un repositorio en mi cuenta de github para el despliegue." y, ante opciones, eligió el repositorio "**Público, solo código y docs**". Posteriormente, por selección (transmitido por el coordinador), el usuario decidió el alcance final de datos y contenido; **esa selección posterior prevalece sobre la fórmula inicial "solo código y docs"** en lo que se contradicen (ver 2.1). Además respondió "Si" a la propuesta de actualizar esta decisión.

Decisiones por selección:
- **Nombre:** `sinco-onet-api`.
- **Licencia del código:** **MIT.** (Resuelve la pregunta abierta de licencia del código. La licencia de la documentación y de los datos publicados no se fijó: ver 7.)
- **Datos:** "**Todo menos Frey-Osborne**".
- **Contenido extra:** solo `docs/decisions` y los diccionarios.
- **Historia:** repositorio nuevo con un solo commit (rama orphan); no se reescribió la historia local.

### 2.1 Qué se publicó y qué no (según el coordinador; no verificado por mí)

**Publicado:**
- Código: `src/`, `tests/`, `Dockerfile` (no construido; ver 5).
- Diccionarios de datos y `docs/decisions/`.
- Datos: las 10 tablas del catálogo SINCO **sin** `sinco_probabilidad_fo`; las tablas de O*NET (ocupaciones, tareas, ratings); el puente O*NET 2010-2019; el crosswalk A1; `match_candidatos`; `match_corridas`; `match_sinco_resumen`; y `data/raw/manifest.json`.
- Historia: un solo commit sin `CLAUDE.md` ni `.claude/agents`.

**NO publicado:**
- El PDF de Frey-Osborne y las tablas de Frey-Osborne (incluida `sinco_probabilidad_fo`).
- `match_cobertura.json` (contiene estadísticas derivadas de Frey-Osborne).
- Vectores (embeddings) y cachés de modelos.
- Los archivos `oro_*` (fichas de la muestra de oro) y las anotaciones del piloto.
- `CLAUDE.md` y `.claude/agents/`.
- `docs/issues/`.
- El PDF de SINCO (según el coordinador, no se publican PDF; no confirmé el de SINCO en particular).

**Diferencia con la fórmula inicial:** la decisión inicial excluía todo `data/` (solo `manifest.json`). La selección posterior publica tablas de datos (catálogo SINCO, O*NET, puente, resultados del emparejamiento) y excluye específicamente lo ligado a Frey-Osborne. Los datos se publican a pesar de que el `.gitignore` excluye `data/` (el coordinador no explicó el mecanismo, p. ej. excepciones o forzado); no lo verifiqué.

## 3. Alternativas consideradas

| Alternativa | Comentario |
|---|---|
| A. Público, solo código y docs (elección inicial) | Reproducible por scripts y manifest; superada por la selección posterior |
| B. Público con todos los datos | No elegida: la licencia de Frey-Osborne sigue sin resolverse |
| C. Público con "todo menos Frey-Osborne" (**elegida y ejecutada**) | Permite desplegar y reproducir sin tocar lo de licencia sin resolver; asume que la redistribución de los datos de INEGI y O*NET es aceptable (ver riesgos) |
| D. Privado | No elegida |

## 4. Razones y riesgos

1. **Licencia del PDF de Frey y Osborne sin resolver** (issue de datos, 2026-10-19). Es la razón por la que Frey-Osborne queda fuera, incluidas las estadísticas derivadas (`match_cobertura.json`). **Sigue sin resolverse** (005 R.7).
2. **Términos de redistribución de INEGI NO revisados.** Se publicaron las tablas del catálogo SINCO, derivadas de un PDF de INEGI. 004 menciona "término de libre uso, citar fuente", que **no verifiqué en una fuente primaria**. Riesgo abierto: la publicación de esas tablas se hizo sin esa revisión.
3. **O*NET es CC BY 4.0** (según 004; no verifiqué hoy): se publican ocupaciones, tareas y ratings; exige atribución a USDOL/ETA y no sugerir aval. **No verifiqué que el README contenga la atribución.**
4. **`docs/decisions/` publicados contienen decisiones "pendientes de revisión" y marcas [NO VERIFICADO],** y pueden leerse como resultados finales o como fuentes verificadas. Además **enlazan a `docs/issues/`, que no se publica** (enlaces rotos y razonamiento no auditable para terceros), y mencionan `CLAUDE.md` y `docs/rubric.md`/`docs/glossary.md` (CLAUDE.md no se publicó; rúbrica y glosario solo si estaban dentro de lo publicado: no lo sé).
5. **Datos personales y correos:** los documentos mencionan un correo institucional de INEGI (003) y el contexto del proyecto incluye el correo del usuario. La revisión del coordinador no halló correos ni rutas personales en código y docs; esa afirmación no es mía y el correo de INEGI en 003 es institucional y público, **pero conviene confirmarlo**.
6. **Resultados NO validados:** el crosswalk A1, `match_candidatos`, `match_corridas` y `match_sinco_resumen` son resultados del emparejamiento marcados NO validados (005 R.4). Publicarlos sin ese rótulo en el README/dataset violaría el espíritu de la regla 6. **No verifiqué que los archivos publicados lo lleven.**
7. **Posible fuga de Frey-Osborne por derivación:** `match_sinco_resumen` y `match_candidatos` podrían contener columnas derivadas de Frey-Osborne (p. ej. `p_FO_*` de 005 §5.7). El coordinador dijo que `match_cobertura.json` sí tiene estadísticas derivadas de F-O y se excluyó; no me consta que las otras tablas publicadas carezcan de ellas. **Requiere verificación.**
8. **Historia:** se publicó una rama orphan nueva, por lo que la historia local (con posibles datos o rutas) no se publicó. La historia local sin reescribir sigue existiendo en el equipo.
9. **Mantenimiento y seguridad:** un repositorio público implica responsabilidad sobre dependencias (fastapi, starlette, uvicorn y la transitiva `opentelemetry-api`; decisión 004) y sobre una API que no debe exponerse sin decidir hosting.
10. **Sin `CLAUDE.md` ni `.claude/agents/` publicados:** las reglas del proyecto, que los documentos citan por número (reglas 1 a 7), no son legibles para terceros desde el repositorio.

## 5. Checklist (estado tras la ejecución)

Leyenda: [V] verificado por el coordinador (afirmación del coordinador, no mía); [NV] no verificado; [P] pendiente.

- [V] **Rutas personales, correos y claves:** búsqueda sin hallazgos en código y docs, según el coordinador. [V] Manifest y tablas publicadas sin rutas locales, según el coordinador.
- [V] **Historia:** repositorio nuevo, un solo commit, rama orphan; no se reescribió la historia local.
- [V] **`.claude/agents/` y `CLAUDE.md`:** no se publican (decidido).
- [V] **Licencia del código:** MIT (decidida).
- [V] **Frey-Osborne fuera** del repositorio: PDF, tablas, `sinco_probabilidad_fo` y `match_cobertura.json`.
- [NV] **Dockerfile:** no se construyó; no se probó que no copie `data/` ni secretos.
- [NV] **Términos de redistribución de INEGI:** no revisados; las tablas del catálogo SINCO ya están publicadas.
- [NV] **Atribución de O*NET (CC BY 4.0)** en el README y en la interfaz: no verificada.
- [NV] **README** con (a) qué es el proyecto (exposición, no pérdida de empleo), (b) estado de las decisiones y resultados NO validados, (c) atribuciones (O*NET, INEGI/SINCO 2019, Frey y Osborne 2013 como referencia, BLS), (d) cómo obtener los datos con `run_all.R`, (e) cómo correr la API y las pruebas, (f) cómo citar: no verificado.
- [NV] **Que las tablas publicadas no contengan columnas derivadas de Frey-Osborne** (riesgo 7).
- [NV] **Que los resultados publicados lleven el rótulo NO validado** (riesgo 6).
- [NV] **`.gitignore` y `git ls-files`:** que el árbol publicado contenga exactamente lo listado en 2.1.
- [P] **Licencia de Frey-Osborne:** sigue sin resolver; por eso F-O queda fuera. Mientras tanto, la mención de códigos F-O en `docs/decisions` (005 R.7) es de códigos, no de probabilidades.
- [P] **Enlaces de `docs/decisions` a `docs/issues`** (no publicado): decidir si se publican los issues, se retiran los enlaces o se añade una nota.
- [P] **Pruebas:** que `pytest` funcione en el repositorio sin datos no publicados (p. ej. sin Frey-Osborne, sin `oro_*`) o con datos sintéticos; no verificado.
- [P] **Despliegue público con datos:** sigue pendiente (hosting, licencias, autenticación, CORS). El repositorio público no implica una instancia pública.
- [P] **Revisión final por una persona** del árbol publicado y de los datos incluidos.

## 6. Otras instrucciones del usuario registradas en esta fecha (contexto, sin ampliar)

Citas: "Continua con: Exposicion, Crosswalk y matching, Despliegue (continua con la opcion B 'FastApi')." y las opciones: anotación "Solo preparar y piloto chico"; matching "Tabla de revisión humana de la muestra de oro".
- Despliegue: decisión 004 (Registro 3, opción B; Registro 4 pendiente de confirmación).
- Anotación: decisión 008 (piloto de 40 tareas con subagentes). `rubric.md` y `glossary.md` se aplicaron en versión 1 según 006.
- Matching: tabla de revisión humana de la muestra de oro con scripts en `src/match/oro*.py` (según el coordinador); las fichas `oro_*` **no** se publican. Los revisores y el umbral de kappa siguen "requiere decisión" (005 R.7; 003 §5).

## 7. Preguntas abiertas

1. Licencia de la documentación (`docs/decisions`, diccionarios) y de los datos publicados (catálogo SINCO, O*NET, resultados del emparejamiento). MIT se decidió solo para el código. **Requiere decisión.**
2. Revisar los términos de redistribución de INEGI para las tablas del catálogo SINCO ya publicadas. **Requiere verificación; si resultara no permitido, retirar datos.**
3. Resolver la licencia de Frey-Osborne (condiciona cualquier publicación futura de probabilidades). **Requiere decisión/verificación.**
4. Enlaces de `docs/decisions` a `docs/issues` no publicados. **Requiere decisión.**
5. Verificación de lo marcado [NV] en la sección 5. **Requiere confirmación humana.**
6. Hosting público con datos (004). **Requiere decisión.**
7. ¿Publicar `CLAUDE.md`? (Se decidió no publicarlo; los documentos citan sus reglas.) Opcional: añadir una nota en el README que resuma las reglas citadas.

## 8. Fuentes

Sin fuentes externas nuevas consultadas. Se basa en CLAUDE.md, decisiones 004, 005 (R.7), 006 y 008, el issue de datos de Frey-Osborne y las citas y selecciones del usuario transmitidas por el coordinador. Lo dicho sobre el contenido real del repositorio publicado, la revisión de rutas/correos/claves, el `.gitignore` y `src/match/oro*.py` proviene del coordinador y no fue verificado por mí. Las afirmaciones sobre licencias de O*NET e INEGI provienen de 004 y no las verifiqué en fuentes primarias hoy.
