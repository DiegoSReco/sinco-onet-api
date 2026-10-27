# Issue: calibrate (B1) - parametros provisionales y decisiones pendientes (2026-10-19)

`src/calibrate/b1_dawid_skene.py` implementa la version basica de B1 (decision 012, opcion sin dependencias nuevas). Lo siguiente no esta fijado por ninguna decision; los valores de `src/calibrate/config.toml` son PROVISIONAL (regla 7). Salidas rotuladas "PROVISIONAL, SIN VALIDAR" o "PILOTO, NO RESULTADO".

1. **Hiperparametros**: prior Dirichlet de las filas de confusion (`debil` diag 2/off 1; `fuerte` diag 20/off 1; humano diag 20/off 1) y de la prevalencia (alpha 1). 012 pide al menos dos niveles de informatividad; los valores no tienen respaldo. Hiperparametros fijos, sin jerarquia.
2. **Muestreo**: 4 cadenas, 3000 iteraciones, 1000 de descarte, adelgazamiento 2, semilla 20261019.
3. **Diagnosticos**: umbral R-hat 1.05 y ESS minimo 100. Valores a fijar por un humano.
4. **Nivel del intervalo creible**: 0.90 (012: 90 % u 80 %).
5. **Fusion EL3 -> EL2** en `eloundou_class` (012/011); depende de E-2 de 011, no aplicada al esquema `Annotation`. Hoy ese campo se lee de un parquet con columnas `run_id`, `task_id`, `eloundou_class`.
6. **Dependencia entre corridas**: el modelo las trata como independientes. Sin muestra humana solo mide consistencia; con muestra humana tambien hace falta `--unidad modelo` para identificar el sesgo comun. Falta decidir si basta o se aprueba un paquete bayesiano para el modelo ordinal jerarquico con efecto de funcion (012 sec. 9, pregunta 6). Colapso por modelo: la moda de las corridas con empate = ausente (provisional).
7. **Referencia humana**: quien la forma, con que guia, y si la adjudicacion cuenta como un anotador mas (012 pregunta 7). Formato supuesto: columnas `task_id`, `clase_humana`, opcional revisor. El diseno de muestreo estratificado por clase del LLM no se modela mas alla de la ignorabilidad de la verosimilitud conjunta.
8. **Unidad del item**: hoy `task_id` (ruta O). La ruta S (funciones SINCO, clave `sinco_code`+`orden`) requiere el esquema de 011 E-5, aun sin aprobar. No hay prior por grupo/division (pooling de 012).
9. **Criterio de piloto**: se reutiliza el de `src/score/config.toml` (tambien PROVISIONAL).
