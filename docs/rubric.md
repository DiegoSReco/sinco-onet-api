# Rúbrica de anotación (versión 1; decisiones 001 y 006)

Se anota cada tarea de O*NET. Esta rúbrica mide **exposición** (propiedad técnica de la tarea). No mide adopción, rentabilidad, regulación ni pérdida de empleo.

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

No se admiten puntajes continuos libres del anotador.

## Mapa numérico (fijado en configuración, no en código)
Medida principal: E0 = 0, E1 = 0.5, E2 = 1.
Sensibilidad: límite inferior (E0 = E1 = 0, E2 = 1) y límite superior (E0 = 0, E1 = E2 = 1).

## Agregación (resumen; detalle en la decisión 001, sección 4.4)
Por ocupación O*NET-SOC: promedio de los puntajes de las tareas centrales con pesos iguales. Variante: incluir tareas suplementarias y ponderar por importancia/frecuencia/relevancia de O*NET. Se reportan además `share_E2` y `share_any`.

## Trazabilidad
Cada corrida registra `prompt_version`, modelo, fecha y `run_id`, además de versión de O*NET, versión de traducción y semilla/temperatura.
