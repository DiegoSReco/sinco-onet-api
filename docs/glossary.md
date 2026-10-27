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
