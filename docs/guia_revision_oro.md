# Guia para revisores: muestra de oro del emparejamiento SINCO 2019 -> O*NET-SOC

Version de la guia: v0 (borrador para el piloto; puede reformularse tras el piloto, 005 secc. 8.1). Estado: **provisional**.

## 1. Que se le pide
Para cada grupo unitario SINCO 2019 (ficha) se le muestra su texto oficial y una lista de ocupaciones de O*NET-SOC (en ingles). Su tarea es juzgar **si cada ocupacion O*NET describe el mismo trabajo** que el grupo SINCO. Usted decide con base en el contenido del trabajo (que se hace, que se supervisa, que conocimientos requiere), no en que los titulos se parezcan.

Trabaje **solo y sin consultar al otro revisor** hasta entregar su archivo. La independencia es lo que permite medir el acuerdo.

## 2. Que NO debe hacer
- **No consulte probabilidades de automatizacion** (Frey y Osborne u otras), ni medidas de exposicion a IA, ni riesgo de perdida de empleo, ni ninguna tabla que las contenga. Su juicio es solo sobre la equivalencia de ocupaciones. Conocer esas cifras podria sesgarlo.
- No busque como se generaron las listas, ni intente adivinar que metodo propuso cada candidato. La lista esta mezclada a proposito y contiene candidatos que no son correctos.
- No ordene, filtre, inserte ni borre filas o columnas en la hoja (use solo las celdas de respuesta). No edite codigos ni textos.
- No use traductores automaticos o asistentes de IA para decidir.

## 3. El archivo
Archivo CSV (UTF-8) que abre en Excel. Si los acentos se ven mal, use Datos > Desde texto/CSV y elija codificacion UTF-8. **Al guardar, conserve el formato CSV.** (Si su Excel guarda con punto y coma, no hay problema.)

Cada ficha ocupa varias filas contiguas, todas con el mismo `ficha_id`:
- Primera fila de la ficha: ademas muestra `sinco_descripcion`, `sinco_funciones` y `sinco_ocupaciones_ejemplo` (texto del catalogo SINCO 2019). Estas celdas solo estan en esa fila; son largas, ensanche la columna o use la barra de formulas.
- Una fila por candidato O*NET (`cand_id` = c01, c02, ...): codigo, titulo en ingles y descripcion breve.
- Una **ultima fila `OTRO`** (para la decision global de la ficha).

La lista incluye entre unos 7 y 12 candidatos, en orden aleatorio. Algunos pueden ser claramente ajenos: valorelos igual.

## 4. Columnas que usted llena
| Columna | Donde | Valores |
|---|---|---|
| `valoracion` | **cada fila de candidato** (obligatoria) | `exacto`, `parcial` o `incorrecto` |
| `es_mejor` | un solo candidato por ficha | `si` (en blanco en los demas) |
| `ninguno_otro` | fila `OTRO` | `si` solo si ningun candidato es aceptable ni mejor |
| `otro_soc` | fila `OTRO` | codigo SOC / O*NET-SOC o titulo de una ocupacion mejor que no esta en la lista (texto libre; opcional si no la conoce) |
| `confianza` | fila `OTRO` (obligatoria) | `alta`, `media` o `baja` (su confianza en el conjunto de la ficha) |
| `comentarios` | cualquier fila | texto libre: dudas, ambiguedades, por que |

### Criterios de valoracion (provisionales)
- **exacto**: la ocupacion O*NET corresponde, en lo esencial, al mismo trabajo que el grupo SINCO (puede diferir en detalles menores o en nivel de especializacion).
- **parcial**: comparte una parte importante del trabajo, o es mas amplia o mas estrecha que el grupo SINCO, o cubre solo algunas de las ocupaciones que el grupo incluye.
- **incorrecto**: el trabajo es esencialmente distinto, aunque haya palabras en comun (por ejemplo, mismo material o herramienta pero otra funcion).

Las listas "ocupaciones ejemplo" y "funciones" del SINCO pesan mas que el titulo. Las notas de "incluye/excluye" no se muestran; si el texto le parece ambiguo, anotelo en `comentarios`.

### Regla de la decision global de cada ficha
Marque **exactamente una** de estas dos opciones:
1. `es_mejor = si` en el candidato que mejor corresponde (debe ser `exacto` o `parcial`), o
2. `ninguno_otro = si` en la fila `OTRO` (si hay un mejor SOC fuera de la lista, indiquelo en `otro_soc`). En este caso ningun candidato puede quedar como `exacto`.

Las ocupaciones tipo "All Other" (otras no clasificadas) pueden ser equivalentes de un grupo SINCO residual ("Otros ..."): valorelas por el mismo criterio de contenido.

## 5. Practica
- Si no conoce el oficio, lea las funciones y ocupaciones ejemplo; no hace falta conocimiento externo. Anote en `comentarios` y baje la `confianza`.
- No hay respuestas "correctas" conocidas por quien le entrega la hoja. Una valoracion dudosa no es un error.
- Piloto: las primeras fichas (identificador `P###`) sirven para afinar esta guia. Despues del piloto puede cambiar el texto de criterios; se le avisara.

## 6. Entrega
Envie el CSV lleno al coordinador con el nombre `revisor_<su letra>_lleno.csv`. Se validara su esquema (todas las valoraciones llenas, una decision global por ficha, confianza); si hay errores, se le devolvera la lista de filas a corregir.

Referencia: `docs/decisions/005-emparejamiento-embeddings.md`, secc. 8.1. Los parametros de esta revision (cantidad de candidatos, distractores, umbral de acuerdo) estan marcados como provisionales en `src/match/oro_config.toml`.
