# 008 - Piloto de anotación de exposición (40 tareas, subagentes de Claude Code)

> **ESTADO: APROBADA por el usuario en lo elegido (sección 2); PENDIENTE DE REVISIÓN HUMANA en lo demás (secciones 3 a 7).** Autor: agente de métodos. Fecha: 2026-10-19. Este documento registra decisiones; no ejecuta anotaciones ni calcula cifras (reglas 1 y 7 de CLAUDE.md).

## 1. Pregunta

¿Cómo se ejecuta el piloto de anotación de exposición por tarea (decisión 001, rúbrica versión 1 de 006) de forma reproducible hasta donde sea posible, sin gasto de API y sin tratar sus resultados como finales?

## 2. Lo que el usuario eligió (APROBADO)

Selecciones del usuario (2026-10-19), tal como las transmitió el coordinador:
- Modelo: "**Claude Sonnet 5.5 por API (Recomendado)**".
- Presupuesto: "**Sin API; usar solo subagentes**".
- Corridas: "**3 corridas, temperatura 1.0 (Recomendado)**".
- Texto y corte: "**Inglés original; corte = fecha de la corrida (Recomendado)**".
- Antecedente (007 §6): anotación "Solo preparar y piloto chico".

Registro (sin ampliar):
1. **Piloto de 40 tareas** (código en `src/annotate`, prompt versionado `ann-v1`), anotadas por **subagentes de Claude Code con Sonnet 5.5**, **sin API y sin gasto de API**.
2. **3 corridas independientes**: cada una la hace un subagente nuevo, sin acceso a las otras corridas ni a sus resultados.
3. **Temperatura 1.0 solicitada, pero NO controlable en subagentes.** Debe registrarse así ("temperatura solicitada 1.0; no controlable"), sin afirmar que se controló. Consecuencias: reproducibilidad limitada; las 3 corridas no son réplicas con un parámetro verificable; no puede reconstruirse el muestreo ni fijarse semilla.
4. **Registro del modelo** (regla 4): `claude-sonnet-5-5 (subagente Claude Code)`, más `prompt_version = ann-v1`, fecha y `run_id` por corrida.
5. **Texto en inglés original**, con `task_text_es` **nulo**. Esto resuelve provisionalmente, **solo para el piloto**, el problema de traducción frente a inglés; no lo resuelve para la corrida completa.
6. **Fecha de corte de capacidades = fecha de cada corrida.** Esto resuelve la pregunta 3 de 001 (§10, "fecha de corte") **solo para el piloto**; la fecha se registra por corrida.
7. **Los resultados del piloto NO son resultados finales y NO se agregan a exposición** (`E_o`, `share_E2`, `share_any`): sirven para probar el esquema, el prompt y medir acuerdo entre corridas. Ninguna cifra del piloto entra al artículo (regla 6).

## 3. Ambigüedad resuelta por el orquestador (a confirmar por el humano)

El usuario eligió "Claude Sonnet 5.5 **por API**" en la primera pregunta y "**Sin API**; usar solo subagentes" en la segunda: se contradicen. El orquestador resolvió que **prevalece "Sin API"** por ser explícita (presupuesto) y **mantiene el modelo Sonnet 5.5**, ejecutado vía subagentes. **Pendiente de confirmación del usuario.** Si el usuario quería API, cambian el registro del modelo, la capacidad de fijar temperatura y el gasto.

## 4. Alternativas consideradas

| Alternativa | Comentario |
|---|---|
| A. Subagentes de Claude Code, Sonnet 5.5, 3 corridas (**elegida**) | Sin costo de API; independencia entre corridas por subagente nuevo; temperatura y semilla no controlables; reproducibilidad limitada |
| B. API de Anthropic con temperatura 1.0 y parámetros fijados | Registro completo de parámetros; implica gasto y dependencias no aprobadas (005 R.2 excluye APIs de pago); descartada por "Sin API" |
| C. Anotación humana de las 40 tareas | No elegida; sería útil como referencia humana posterior (001 §8) |
| D. Una sola corrida | No permite medir acuerdo entre corridas |

## 5. Diseño del piloto (propuesto; pendiente de revisión humana en lo no elegido)

- **Esquema por registro** (001 §7): `run_id`, `prompt_version`, `model`, `run_date`, `onet_soc`, `task_id`, `task_text_en`, `task_text_es` (nulo), `exposure_class` (E0/E1/E2), `physical_bottleneck`, `confidence`, `rationale`, `task_type`. Campo adicional recomendado: `temperature_requested = 1.0` y `temperature_controlled = false`.
- **Selección de las 40 tareas:** no está fijada por el usuario ni por 001. **Requiere decisión** (criterio y semilla de selección; p. ej. aleatoria estratificada por ocupación y por `task_type`). Si se usa aleatoriedad, registrar la semilla en `src/` y el hash de la lista de tareas.
- **Independencia:** cada corrida con subagente nuevo, mismas tareas, mismo prompt `ann-v1`, sin ver las demás. El contenido del prompt debe quedar versionado en `src/annotate`.
- **Validación del esquema:** un registro por (`run_id`, `task_id`); si un entregable no cumple el esquema, issue en `docs/issues/` y detenerse (regla 5).
- **Medidas de acuerdo entre corridas** (propuestas en 001 §4.3 y §8): kappa ponderado ordinal y alfa de Krippendorff ordinal sobre `exposure_class`; acuerdo exacto; con 40 tareas y 3 corridas los intervalos serán amplios y deben reportarse como exploratorios (bootstrap sobre tareas, con semilla registrada). **Umbrales de "acuerdo aceptable": requieren decisión** (no hay valor recomendado en 001).
- **Tareas sin tipo:** el coordinador señala 418 tareas sin tipo core/supplemental en los datos; no se resolvió aquí cómo tratarlas en la corrida completa. Para el piloto, el `task_type` de esas tareas debe registrarse como nulo, sin imputar.
- **Qué NO se hace:** no se calcula `E_o`, no se agrega a SINCO, no se relaciona con la probabilidad de Frey-Osborne, no se publican cifras.

## 6. Riesgos

1. **Temperatura no controlable:** las 3 corridas pueden estar menos dispersas o más de lo que sugeriría 1.0; no se puede afirmar nada sobre ello. Mitigación: registrar "solicitada, no controlable" y no interpretar la variabilidad como propiedad del modelo con T = 1.0.
2. **Independencia limitada:** subagentes del mismo modelo comparten sesgos; el acuerdo entre corridas mide consistencia, no validez (001 §8 pide además submuestra humana).
3. **Modelo con nombre `claude-sonnet-5-5 (subagente Claude Code)`:** no se garantiza que versión y configuración de inferencia sean idénticas entre corridas; el registro de fecha es el único ancla.
4. **Inglés original:** evita ruido de traducción en el piloto, pero no valida la anotación sobre el texto traducido que usará la corrida completa (001 §6.4: anotar inglés y español en una submuestra). Pendiente.
5. **Piloto pequeño (40 tareas):** poca potencia para estimar acuerdo; riesgo de extrapolar.
6. **Sesgo del anotador LLM** (001 §6.6): puede sobrecalificar tareas cognitivas; `physical_bottleneck` y una futura submuestra humana lo mitigan.
7. **Contradicción API / sin API:** ver sección 3.
8. **Fecha de corte = fecha de la corrida:** si las corridas se hacen en fechas distintas, las capacidades de referencia difieren; registrar la fecha por corrida y reportarla.

## 7. Lo que sigue requiriendo decisión humana (no cubierto por las elecciones del usuario)

1. **Corrida completa:** modelo y vía (subagentes, API u otra), presupuesto, número de corridas, y si se anota inglés, español o ambos.
2. **Traducción frente a inglés** para la corrida completa (el piloto usa inglés original).
3. **Tareas sin tipo core/supplemental** (418 según el coordinador): cómo tratarlas en la medida principal (001 §4.4 usa solo tareas centrales).
4. **Selección de las 40 tareas** (criterio, semilla) y umbrales de acuerdo.
5. **Confirmar** la resolución de la contradicción API / sin API (sección 3).
6. **Fecha de corte** para la corrida completa (001 P3): el piloto usa la fecha de cada corrida; la corrida completa debe fijar una fecha o versión común.
7. Referencia humana (submuestra anotada por personas, 001 §8): quiénes y cuántas.

## 8. Fuentes

Sin fuentes externas nuevas. Se basa en CLAUDE.md (reglas 1, 4, 5, 6, 7), decisiones 001 (§4.3, §6, §7, §8, §10), 005 (R.2), 006, 007 §6 y las selecciones del usuario transmitidas por el coordinador. Lo dicho de `src/annotate`, el prompt `ann-v1` y las 418 tareas sin tipo viene del coordinador; no lo verifiqué.
