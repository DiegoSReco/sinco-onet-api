# Glosario (versión 1; decisiones 001, 005 y 006)

- Exposición: grado en que un sistema de IA podría ejecutar una tarea, o reducir sustancialmente el esfuerzo humano para ejecutarla, con calidad comparable. Es una propiedad técnica de la tarea; no implica adopción ni pérdida de empleo.
- Exposición de una ocupación (`E_o`): promedio de los puntajes de exposición de sus tareas centrales (E0 = 0, E1 = 0.5, E2 = 1), con pesos iguales como medida principal.
- `share_E2`: proporción de tareas de una ocupación con `exposure_class` E2. `share_any`: proporción con E1 o E2. Son las lecturas de "fracción de tareas".
- `exposure_class`: clase ordinal de la tarea (E0 sin exposición, E1 exposición con apoyo, E2 exposición directa).
- `physical_bottleneck`: indicador de que la tarea exige presencia física o destreza manual como componente central.
- Pérdida de empleo: fenómeno distinto de la exposición. Los escenarios de pérdida se reportan aparte y con supuestos explícitos; no se derivan mecánicamente de la exposición.
- Probabilidad de automatización (Frey-Osborne): probabilidad de computarización de una ocupación completa de EE. UU. (Frey y Osborne, 2013), trasladada a SINCO 2019 mediante emparejamiento. No es exposición ni riesgo de pérdida de empleo; se usa como variable comparativa. Los resultados del emparejamiento se rotulan NO validados hasta pasar la muestra de oro.
- SINCO: Sistema Nacional de Clasificación de Ocupaciones 2019 (INEGI).
- Grupo unitario (SINCO): nivel de 4 dígitos, unidad principal de análisis y reporte.
- CIUO-08: Clasificación Internacional Uniforme de Ocupaciones 2008 (ISCO-08).
- O*NET-SOC: clasificación de ocupaciones de O*NET.
- Crosswalk: correspondencia entre clasificaciones; puede ser 1:1, 1:N, N:1 o M:N. Se conserva el tipo de relación y la incertidumbre.
