# src/calibrate/ - B1: error de medicion bayesiano tipo Dawid-Skene (decision 012)

Estado: codigo y pruebas con datos sinteticos. **No hay resultados**: solo existe el piloto (3 corridas x 40 tareas del mismo modelo). Ninguna cifra de este modulo se cita en el articulo (regla 6). No usa datos de empleo ni de probabilidades de automatizacion, no descarga nada y no calcula exposicion agregada (eso es `src/score`).

## Modelo
`z_i ~ Cat(pi)`, `pi ~ Dir(alpha)`; `y_ik | z_i=c ~ Cat(Theta_k[c,:])`, `Theta_k[c,:] ~ Dir(beta_k[c,:])`. i = item (tarea o funcion), k = anotador (corrida del LLM, o revisor humano de referencia). Gibbs conjugado propio en numpy (sin dependencias nuevas), varias cadenas con semillas derivadas de `SeedSequence(semilla)`, descarte y adelgazamiento configurables. Diagnosticos propios: R-hat dividido, ESS aproximado (Geyer) y traza de la log-verosimilitud marginal.
- Prior de cada fila de `Theta_k`: pseudo-conteos `diag` en la diagonal y `off` fuera (`debil` o `fuerte`, `--prior`); anotadores humanos usan `[prior.humano]`. Hiperparametros FIJOS en `config.toml` (no hay jerarquia sobre ellos; 012 pide jerarquia y modelo ordinal con efecto de funcion, que requeririan un paquete no aprobado: no implementado).
- Campo ordinal: `--campo exposure_class` (E0/E1/E2, esquema `Annotation`, cargador de `src/score`) o `--campo eloundou_class` (parquet con `run_id`, `task_id`, `eloundou_class`; EL3 se funde en EL2 por config, PROVISIONAL, 011 sec. 5).
- Unidad de anotador: `--unidad corrida` (defecto) o `modelo` (las corridas de un mismo modelo se colapsan a su moda por item; empate = ausente).

## Lo que mide y lo que NO
- **Sin referencia humana**: solo **consistencia entre corridas, NO exactitud**. Corridas del mismo LLM no son independientes (comparten sesgo, 012) y el modelo las trata como independientes; los posteriores son falsamente precisos. Todas las salidas lo rotulan (`lectura`, `tipo_medida`, resumen).
- **Con referencia** (`--referencia` parquet/CSV con `task_id` y `clase_humana`; `--ref-revisor` para varios revisores, cada uno es un anotador; la adjudicacion tambien): se estima exactitud y sesgo ordinal *respecto de la referencia*, que no es verdad externa. Prueba sintetica: con las corridas como anotadores independientes, la referencia **no basta** para recuperar un sesgo comun del LLM (viola la independencia condicional); con `--unidad modelo` (una vista por modelo) si se recupera. Los items sin referencia aportan a `Theta` por el modelo completo (la seleccion por etiqueta del LLM es ignorable en la verosimilitud conjunta).
- `ausencia de anotaciones`: cada item usa solo sus observaciones disponibles; un item con una sola anotacion queda dominado por el prior (alta entropia).

## Salidas (`data/processed/calibracion/`, excluida por `.gitignore`)
`b1_<campo>[_PILOTO]_{items,confusion,prevalencias,medidas,diagnosticos,traza_loglik}.parquet` y `_meta.json`. Los metadatos van tambien en el schema de cada Parquet (`b1_meta`): run ids, modelo/prompt por corrida, sha256 de entradas y config, semilla, muestreo, versiones, fecha UTC, convergencia, resumen.
- `items`: probabilidades posteriores `prob_<clase>`, `clase_modal`, `prob_modal`, `entropia_bits`, `entropia_normalizada`.
- `confusion`: matriz posterior por anotador (media, intervalo creible `nivel_intervalo`). `prevalencias`. `medidas`: `exactitud` (con referencia) o `acuerdo_con_clase_latente` (sin), y `sesgo_ordinal`.

## CLI
```
.venv\Scripts\python -m src.calibrate.b1_dawid_skene --anotaciones DIR_O_ARCHIVOS [--campo ...] [--referencia ...] [--unidad ...] [--prior ...] [--semilla ...] [--n-cadenas --n-iter --descarte --adelgazamiento] [--salida-dir ...] [--permitir-piloto] [--sobrescribir]
```
Salida 0 ok; 2 rechazado por piloto (criterio reutilizado de `src/score/config.toml [piloto]`); 3 entrada fuera de esquema (issue en `docs/issues/`, regla 5); 4 salidas ya existen; 5 no encontrado. Con `--permitir-piloto`: sufijo `_PILOTO` y etiqueta `PILOTO, NO RESULTADO` (solo prueba de humo). Si no convergen R-hat/ESS el resumen lo advierte (no detiene).

## Pruebas
`.venv\Scripts\python -m pytest tests/calibrate`
