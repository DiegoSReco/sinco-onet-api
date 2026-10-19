# 006 - Cambios propuestos a docs/rubric.md y docs/glossary.md

> **ESTADO: APROBADA por el usuario (2026-10-19) y APLICADA (versión 1 de `docs/rubric.md` y `docs/glossary.md`).** Ver "Registro de aplicación" (sección 10). Autor: agente de métodos. Fecha: 2026-10-19.

## 1. Pregunta

¿Qué cambios exactos requieren `docs/rubric.md` y `docs/glossary.md` para alinearse con la decisión 001 (separar `exposure_class` E0/E1/E2 de `physical_bottleneck`, definición única de exposición, y nombrar aparte la "probabilidad de automatización (Frey-Osborne)")?

## 2. Base de la decisión (regla 2 de CLAUDE.md)

Regla 2: no modificar `docs/rubric.md` ni `docs/glossary.md` sin decisión registrada en `docs/decisions/`.
- Aprobación de 001 (cita del usuario, 2026-10-19): "Aprobado 004, 001 y 003. La solicitud de la tabla no la necesitamos ya estan las tablas del catálogo".
- Respuesta posterior del usuario, a la pregunta del agente de métodos de si la aprobación incluía modificar `rubric.md` y `glossary.md` (cita textual): "Si, aprobar pendientes incluyendo uvicorn."
- Registro del agente de métodos: la aprobación de 001 más esa respuesta constituyen la decisión registrada exigida por la regla 2. Esta decisión 006 es el documento donde queda el texto exacto.
- Interpretación (sin ampliar): "Si" se tomó como confirmación de que las propuestas concretas de 001 (secciones 4.3, 4.4 y 4.6) se aprueban también para el contenido de la rúbrica y el glosario. No aprueba cambios distintos de los aquí listados; no aprueba valores numéricos nuevos.

## 3. Estado anterior (leído 2026-10-19, antes de aplicar)

`docs/rubric.md` (borrador, 8 líneas):
```
# Rúbrica de anotación (BORRADOR, pendiente de decisión en docs/decisions/)

Puntaje de exposición por tarea, de 0 a 1.
- 0: la tarea requiere presencia física o destreza manual que la IA no puede ejecutar.
- 0.5: la IA puede apoyar pero un humano debe ejecutar o validar.
- 1: la IA puede ejecutar la tarea completa con los datos disponibles.

Confianza: alta, media o baja según ambigüedad de la tarea.
```
`docs/glossary.md` (borrador, 6 líneas):
```
# Glosario (BORRADOR)

- Exposición: fracción de tareas de una ocupación que un sistema de IA puede ejecutar.
- SINCO: Sistema Nacional de Clasificación de Ocupaciones 2019 (INEGI).
- CIUO-08: Clasificación Internacional Uniforme de Ocupaciones 2008 (ISCO-08).
- O*NET-SOC: clasificación de ocupaciones de O*NET.
```

## 4. Problemas que se corrigen (de 001 §2)

1. El glosario habla de una *fracción de tareas* (conteo binario); la rúbrica produce un puntaje gradual. Se unifica: puntaje por tarea `e_t` (E0/E1/E2 -> 0/0.5/1) y, aparte, `share_E2` y `share_any` como "fracción de tareas".
2. La rúbrica ancla el 0 en un motivo físico y el 0.5 en el rol humano, mezclando capacidad técnica y rol humano. Se separa: `exposure_class` (ordinal) y `physical_bottleneck` (booleano).
3. Se añade la distinción entre exposición y "probabilidad de automatización (Frey-Osborne)" (decisión 005, R.1b) y la prohibición de llamar a la exposición "riesgo de pérdida de empleo" (001 §4.6).

## 5. Diff propuesto: docs/rubric.md

Reemplazo completo del archivo (el original es de 8 líneas; todas cambian):

```diff
--- a/docs/rubric.md
+++ b/docs/rubric.md
@@ -1,8 +1,37 @@
-# Rúbrica de anotación (BORRADOR, pendiente de decisión en docs/decisions/)
-
-Puntaje de exposición por tarea, de 0 a 1.
-- 0: la tarea requiere presencia física o destreza manual que la IA no puede ejecutar.
-- 0.5: la IA puede apoyar pero un humano debe ejecutar o validar.
-- 1: la IA puede ejecutar la tarea completa con los datos disponibles.
-
-Confianza: alta, media o baja según ambigüedad de la tarea.
+# Rúbrica de anotación (versión 1; decisiones 001 y 006)
+
+Se anota cada tarea de O*NET. Esta rúbrica mide **exposición** (propiedad técnica de la tarea). No mide adopción, rentabilidad, regulación ni pérdida de empleo.
+
+## Concepto
+Exposición = grado en que un sistema de IA (modelos de lenguaje y software o herramientas construidas sobre ellos, con las capacidades documentadas en la fecha de anotación) podría ejecutar la tarea, o reducir sustancialmente el esfuerzo humano para ejecutarla, manteniendo calidad comparable. Es neutral respecto de si la IA sustituye o complementa.
+
+## Campos por tarea
+1. `exposure_class` (ordinal):
+   - `E0` sin exposición: la IA actual no reduce el esfuerzo de forma material.
+   - `E1` exposición con apoyo: la IA reduce sustancialmente el esfuerzo, pero un humano ejecuta, supervisa o valida el resultado.
+   - `E2` exposición directa: la IA (con herramientas razonables disponibles) puede completar la tarea.
+2. `physical_bottleneck` (booleano): la tarea exige presencia física o destreza manual como componente central. Se registra aparte; un cero por motivo físico no equivale a "la IA no es capaz" en sentido cognitivo.
+3. `confidence`: alta, media o baja según la ambigüedad de la tarea.
+4. `rationale`: texto breve para auditoría.
+
+No se admiten puntajes continuos libres del anotador.
+
+## Mapa numérico (fijado en configuración, no en código)
+Medida principal: E0 = 0, E1 = 0.5, E2 = 1.
+Sensibilidad: límite inferior (E0 = E1 = 0, E2 = 1) y límite superior (E0 = 0, E1 = E2 = 1).
+
+## Agregación (resumen; detalle en la decisión 001, sección 4.4)
+Por ocupación O*NET-SOC: promedio de los puntajes de las tareas centrales con pesos iguales. Variante: incluir tareas suplementarias y ponderar por importancia/frecuencia/relevancia de O*NET. Se reportan además `share_E2` y `share_any`.
+
+## Trazabilidad
+Cada corrida registra `prompt_version`, modelo, fecha y `run_id`, además de versión de O*NET, versión de traducción y semilla/temperatura.
```

Notas: (a) el cuerpo del archivo nuevo debe coincidir exactamente con las líneas `+` sin el prefijo; (b) los hunks `-1,8 +1,37` son aproximados; lo normativo es el texto, no los números de línea.

## 6. Diff propuesto: docs/glossary.md

```diff
--- a/docs/glossary.md
+++ b/docs/glossary.md
@@ -1,6 +1,22 @@
-# Glosario (BORRADOR)
-
-- Exposición: fracción de tareas de una ocupación que un sistema de IA puede ejecutar.
+# Glosario (versión 1; decisiones 001, 005 y 006)
+
+- Exposición: grado en que un sistema de IA podría ejecutar una tarea, o reducir sustancialmente el esfuerzo humano para ejecutarla, con calidad comparable. Es una propiedad técnica de la tarea; no implica adopción ni pérdida de empleo.
+- Exposición de una ocupación (`E_o`): promedio de los puntajes de exposición de sus tareas centrales (E0 = 0, E1 = 0.5, E2 = 1), con pesos iguales como medida principal.
+- `share_E2`: proporción de tareas de una ocupación con `exposure_class` E2. `share_any`: proporción con E1 o E2. Son las lecturas de "fracción de tareas".
+- `exposure_class`: clase ordinal de la tarea (E0 sin exposición, E1 exposición con apoyo, E2 exposición directa).
+- `physical_bottleneck`: indicador de que la tarea exige presencia física o destreza manual como componente central.
+- Pérdida de empleo: fenómeno distinto de la exposición. Los escenarios de pérdida se reportan aparte y con supuestos explícitos; no se derivan mecánicamente de la exposición.
+- Probabilidad de automatización (Frey-Osborne): probabilidad de computarización de una ocupación completa de EE. UU. (Frey y Osborne, 2013), trasladada a SINCO 2019 mediante emparejamiento. No es exposición ni riesgo de pérdida de empleo; se usa como variable comparativa. Los resultados del emparejamiento se rotulan NO validados hasta pasar la muestra de oro.
 - SINCO: Sistema Nacional de Clasificación de Ocupaciones 2019 (INEGI).
+- Grupo unitario (SINCO): nivel de 4 dígitos, unidad principal de análisis y reporte.
 - CIUO-08: Clasificación Internacional Uniforme de Ocupaciones 2008 (ISCO-08).
 - O*NET-SOC: clasificación de ocupaciones de O*NET.
+- Crosswalk: correspondencia entre clasificaciones; puede ser 1:1, 1:N, N:1 o M:N. Se conserva el tipo de relación y la incertidumbre.
```

Notas: igual que arriba; lo normativo es el texto de las líneas `+`.

## 7. Alternativas consideradas

| Alternativa | Comentario |
|---|---|
| A. Aplicar el diff propuesto (recomendada; **aplicada**) | Alinea los documentos con 001 aprobada |
| B. Mantener los borradores | Mantiene la contradicción glosario/rúbrica señalada en 001 §2 |
| C. Aplicar solo el glosario | Dejaría la rúbrica con los ejes mezclados |

## 8. Riesgos

1. La rúbrica operativa se ancla en E0/E1/E2; los umbrales de tiempo de Eloundou et al. siguen **[NO VERIFICADO]** (001 §3.3); la rúbrica no declara umbral de tiempo para E1 y E2.
2. Los textos del diff son una redacción del agente de métodos que condensa 001.
3. Los números de línea de los hunks son aproximados.
4. Cualquier cambio sustantivo adicional a la rúbrica o al glosario requiere nueva decisión (regla 2).

## 9. Fuentes

Decisiones 001 (§2, §4.3, §4.4, §4.6) y 005 (R.1b); `docs/rubric.md` y `docs/glossary.md` leídos el 2026-10-19; CLAUDE.md (regla 2). Sin fuentes externas nuevas.

## 10. Registro de aplicación (2026-10-19)

- Según el coordinador, 006 se aplicó a `docs/rubric.md` y `docs/glossary.md` en **versión 1**. Verificación del agente de métodos: leí ambos archivos hoy y su encabezado y contenido corresponden al texto de las líneas `+` de las secciones 5 y 6 (rúbrica "versión 1; decisiones 001 y 006"; glosario "versión 1; decisiones 001, 005 y 006"). No hice una comparación carácter por carácter.
- Origen de la autorización: aprobación de 001 más la respuesta "Si, aprobar pendientes incluyendo uvicorn." (sección 2), y la instrucción del usuario de aplicar 006 dentro de "anotación: Solo preparar y piloto chico".
- Desde la aplicación, los cambios adicionales a esos archivos requieren una nueva decisión registrada (regla 2).
- Pendiente (no resuelto por esta decisión): modelo para el piloto de anotación y número de tareas del piloto ("unas decenas"): requiere decisión del usuario.
