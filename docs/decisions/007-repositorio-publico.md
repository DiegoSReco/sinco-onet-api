# 007 - Repositorio público en GitHub: solo código y documentación

> **ESTADO: PENDIENTE DE REVISIÓN HUMANA**, salvo lo que el usuario ya decidió, marcado abajo como APROBADO con su cita. Autor: agente de métodos. Fecha: 2026-10-19. No se creó ningún repositorio ni se publicó nada; esta decisión no tiene permisos para hacerlo.

## 1. Pregunta

¿Cómo se publica el proyecto en un repositorio de GitHub para el despliegue sin exponer datos cuya licencia o términos de redistribución no están resueltos, y qué debe revisarse antes de hacerlo público?

## 2. Lo que el usuario ya decidió (APROBADO)

Citas textuales del usuario (2026-10-19): "Si es necesario crea un repositorio en mi cuenta de github para el despliegue." y, ante opciones, eligió el repositorio "**Público, solo código y docs**".

Registro (sin ampliar):
- **APROBADO:** repositorio de GitHub **público**, en la cuenta **DiegoSReco** (usuario de git indicado en el contexto del proyecto), con **solo código y documentación**: `src/`, `tests/`, `docs/`, `Dockerfile`, y el `manifest.json` de `data/raw/` con URLs y hashes.
- **APROBADO:** **sin `data/`**: ni `data/raw/`, ni `data/processed/`, ni vectores/embeddings, ni cachés de modelos.
- Lo anterior no equivale a aprobar el hosting público de la API con datos (decisión 004: sigue "requiere decisión") ni la licencia del código (abierta, abajo).
- El nombre del repositorio y quién lo crea (`gh` o manualmente) no los fijó el usuario: **requiere decisión**.

## 2.1 Estado actual reportado por el coordinador (2026-10-19, tras el reinicio de sesión)

- **`.gitignore` ya excluye `data/`**; se versiona solo `data/raw/manifest.json`. (Según el coordinador; no leí el `.gitignore` ni ejecuté `git ls-files`. La casilla de la checklist sobre `.gitignore` sigue requiriendo verificación humana.)
- **`docs/rubric.md` y `docs/glossary.md` se aplicaron en versión 1 según la decisión 006**; 006 pasa a "aplicada". Yo leí ambos archivos hoy y corresponden al texto de 006 (ver 006, sección 10). Consecuencia para la publicación: ambos documentos son públicos, y su versión 1 no incluye cifras ni datos con licencia.
- La decisión 004 ya registra la opción B (FastAPI + starlette + uvicorn) como vigente (Registro 3); el despliegue público con datos sigue "requiere decisión".

## 3. Alternativas consideradas

| Alternativa | Comentario |
|---|---|
| A. Público, solo código y docs (**elegida por el usuario**) | Reproducible: los datos se obtienen con los scripts y las URLs/hashes del manifest. Evita redistribuir datos con licencia sin resolver |
| B. Público con datos procesados | Rechazada por el usuario; chocaría con licencias sin resolver (sección 4) |
| C. Privado | No elegida; no permite despliegue abierto ni verificación por terceros |
| D. Público solo con código (sin docs) | No elegida; la trazabilidad metodológica quedaría fuera |

## 4. Razones y riesgos

1. **Licencia del PDF de Frey y Osborne sin resolver.** El PDF no declara licencia (issue de datos, 2026-10-19). Las probabilidades por ocupación (derivadas del apéndice) no deben publicarse en el repositorio hasta resolverlo (ver 005 R.7, "Requiere decisión").
2. **Datos de INEGI sin revisión de términos de redistribución.** El texto de SINCO viene de un PDF de INEGI; no se revisaron los términos de redistribución (004 los menciona como "término de libre uso, citar fuente", **[NO VERIFICADO]** por mí contra una fuente primaria). Por eso no se sube `data/` ni texto largo del PDF.
3. **O*NET es CC BY 4.0** (según 004; no verifiqué la licencia hoy): exige atribución (USDOL/ETA) y no sugerir aval; debe quedar en el README y en la interfaz.
4. **Los documentos de `docs/` serán públicos con decisiones "pendientes de revisión" y marcas [NO VERIFICADO].** Esto es transparente, pero puede leerse como resultados definitivos o como fuentes verificadas. Riesgo reputacional y de malinterpretación (p. ej., confundir probabilidad de automatización con exposición o con pérdida de empleo).
5. **Datos personales y secretos:** los documentos mencionan correos (p. ej. el de INEGI en 003) y rutas locales; el contexto del proyecto incluye el correo del usuario. Requiere revisión (checklist).
6. **Resultados NO validados.** Todo lo derivado del emparejamiento está marcado NO validado (005 R.4); publicar cifras de ese tipo sin ese rótulo violaría el espíritu de la regla 6.
7. **Historia de git:** si alguna vez se confirmó un dato con licencia sin resolver, publicar el repositorio también publica su historia. Hay que verificar el historial, no solo el árbol actual.
8. **Mantenimiento:** un repositorio público implica responsabilidad sobre issues, seguridad de dependencias (fastapi, starlette, uvicorn; decisión 004) y reproducibilidad.

## 5. Checklist previa a publicar (todas las casillas requieren confirmación humana; nada se ha verificado aún)

- [ ] **Datos con licencia sin resolver en `docs/`:** buscar y quitar o abstraer (a) cifras de probabilidades de Frey-Osborne por ocupación, (b) texto largo copiado del PDF de INEGI (p. ej. en `docs/sinco_pdf_exploracion.md` y `docs/diccionario_datos_sinco.md`), (c) texto de O*NET sin atribución. Citas breves con fuente son una decisión humana; no se fija un umbral aquí.
- [ ] **Sin `data/`:** `.gitignore` que excluya `data/raw/`, `data/processed/`, vectores, cachés de modelos (`~/.cache/huggingface`, etc.), y verificar con `git ls-files` que no hay archivos de datos. Conservar solo el `manifest.json` de `data/raw/` (con URLs, hashes y fechas). El coordinador reporta que el `.gitignore` ya excluye `data/` y versiona solo `data/raw/manifest.json` (sección 2.1); falta verificar con `git ls-files`, incluida la historia.
- [ ] **Secretos, rutas personales y correos:** buscar claves de API, tokens, `C:\Users\Diego\...`, correos personales o institucionales en código, docs, issues y configuración. Reemplazar por rutas relativas o variables.
- [ ] **Historial de git:** revisar que ningún commit anterior contenga datos, secretos o rutas personales; si los hay, decidir entre reescribir historia o publicar un repositorio nuevo con un solo commit inicial. (Decisión humana.)
- [ ] **`.claude/agents/`:** decidir si se publica. Contiene definiciones de agentes del proyecto (p. ej. `anotator.md`) que pueden incluir instrucciones internas. **Requiere decisión.** Alternativa: publicarlo como parte de la transparencia metodológica (las reglas del proyecto ya están en CLAUDE.md) o excluirlo.
- [ ] **CLAUDE.md:** decidir si se publica (contiene reglas y stack; no se detectaron secretos en lo leído).
- [ ] **Licencia del código:** **pregunta abierta; no se decide aquí.** Opciones habituales: MIT, Apache-2.0 u otra; implica elegir también la licencia de la documentación (p. ej. CC BY). Sin licencia, el código público no es reutilizable por terceros.
- [ ] **README:** con (a) qué es el proyecto y que mide exposición, no pérdida de empleo; (b) estado de las decisiones (pendientes marcadas) y que los resultados están NO validados; (c) atribuciones: O*NET (CC BY 4.0, USDOL/ETA), INEGI/SINCO 2019, Frey y Osborne (2013), BLS (puente ISCO-08 -> SOC 2010); (d) **cómo obtener los datos con `run_all.R`** (scripts en `src/ingest/`, con URLs y hashes del manifest); (e) cómo correr la API y las pruebas; (f) cómo citar.
- [ ] **Dockerfile:** que no copie `data/` ni secretos; que los datos se monten o se descarguen en tiempo de ejecución con los scripts. Docker no estaba instalado (004); no verificado.
- [ ] **Pruebas:** `pytest` sin dependencias de `data/` o con datos sintéticos, para que el CI funcione en un repositorio sin datos. Si hay CI, no subir datos como artefactos.
- [ ] **Despliegue público con datos:** sigue pendiente (hosting, licencias, autenticación, CORS). El repositorio público no implica una instancia pública con datos.
- [ ] **Revisión final por una persona** del árbol completo y del historial antes de cambiar la visibilidad a público.

## 6. Otras instrucciones del usuario registradas en esta fecha (contexto, sin ampliar)

Citas textuales: "Continua con: Exposicion, Crosswalk y matching, Despliegue (continua con la opcion B 'FastApi')." y las opciones elegidas: anotación "**Solo preparar y piloto chico**"; matching "**Tabla de revisión humana de la muestra de oro**".
- Despliegue: registrado en la decisión 004 (Registro 3).
- Anotación: según la instrucción del coordinador, comprende aplicar 006 a `rubric.md` y `glossary.md` (ya aplicado; ver 2.1 y 006 §10), esquema y prompt versionado, y un piloto de unas decenas de tareas con el modelo que el usuario indique, **sin corrida completa**. El modelo no está indicado: **requiere decisión**; el número exacto de tareas del piloto tampoco ("unas decenas" no es un valor).
- Matching: la tabla de revisión humana de la muestra de oro se genera ahora (scripts en `src/match/oro*.py`, según el coordinador; no los verifiqué). Los revisores y el umbral de kappa siguen "requiere decisión" (005 R.7; 003 §5).

## 7. Preguntas abiertas

1. Licencia del código (MIT, Apache-2.0 u otra) y de la documentación. **Requiere decisión; no se propone valor.**
2. Nombre del repositorio y método de creación. **Requiere decisión.**
3. ¿Se publica `.claude/agents/` y `CLAUDE.md`? **Requiere decisión.**
4. Historial de git: ¿reescribir o repositorio nuevo con commit inicial limpio? **Requiere decisión** tras revisar el historial.
5. Resolver la licencia del PDF de Frey-Osborne y los términos de redistribución de INEGI antes de publicar cualquier dato derivado. **Requiere decisión/verificación.**
6. Hosting público con datos (004). **Requiere decisión.**

## 8. Fuentes

Sin fuentes externas nuevas consultadas. Se basa en CLAUDE.md, decisiones 004, 005 (R.7) y 006, el issue de datos de Frey-Osborne, `docs/rubric.md` y `docs/glossary.md` (leídos hoy) y las citas del usuario. Las afirmaciones sobre licencias de O*NET e INEGI provienen de 004 y no las verifiqué en fuentes primarias hoy. Lo dicho del `.gitignore`, `src/match/oro*.py` y el estado de la aplicación proviene del coordinador, salvo rúbrica y glosario, que leí.
