.# Revision manual de matches SINCO -> O*NET: politica de aplicacion PROVISIONAL

Origen: `src/match/revision_manual.py` (subcomandos `exportar` y `aplicar`), parametros en `src/match/revision_manual_config.toml`.
Peticion del usuario (2026-10-19): revisar a mano los matches de baja confianza y sin coincidencia, devolver el archivo y actualizar.
Estado: **provisional, sin validar**. La decision formal la registra otro agente en `docs/decisions/` (regla 7; ver `014-revision-manual-matching.md`);
hasta entonces nada de esto es metodologia aprobada y no se citan cifras en el articulo (regla 6). Al escribir este issue `aplicar` NO se ha
ejecutado sobre los datos reales (el usuario aun no revisa): solo se ejecuto `exportar`.

## Politica implementada (todo en config, no en codigo)
1. **Alcance de la revision**: grupos unitarios con `match_status` = `baja_confianza` o `sin_coincidencia` en el modelo principal (bge-m3).
   Al exportar: 58 + 25 = 83 (lo calcula el script). `aplicar` acepta cualquier grupo unitario existente del archivo.
2. **La decision REEMPLAZA los pares automaticos del grupo** en `crosswalk.parquet`: `ACEPTAR_RANGO1` = solo el rango 1; `ACEPTAR_RANGO2` = solo el rango 2;
   `ACEPTAR_AMBOS` = los dos automaticos; `OTRO` = los codigos manuales (1 o 2, en el orden dado); `NINGUNO` = sin pares (el grupo no tiene
   equivalente en O*NET segun el revisor); `DUDA` y filas sin decision se ignoran (DUDA se lista). Los pares automaticos se toman de
   `match_candidatos` (modelo principal, rango <= 2), no del crosswalk vigente, para que revisar de nuevo un grupo reemplace la revision previa.
3. Filas nuevas: `fuente = manual`, `estado_validacion = revision_manual_1_revisor` (un solo revisor, sin segunda lectura; no es `validado`),
   `run_id = manual-<fecha>-<hash8 del CSV>`, `tipo_relacion` recalculado, `modelo` = principal (la API filtra por modelo). Conservan
   `rango`/`similitud`/`similitud_alt`/`rango_alt` automaticos cuando el codigo esta en el top-10 guardado; `rango` solo se conserva si es 1 o 2
   (la API oculta rango > 2 con `rango_max = 2`); NA fuera de los candidatos (el rango real queda en `notas`). `match_status`, `baja_confianza` y `margen`
   siguen siendo los de la recuperacion automatica (describen el metodo, no la revision).
4. **Probabilidad de automatizacion (Frey-Osborne)**: se recalcula SOLO para los grupos revisados y SOLO en las filas del modelo principal, con la
   logica de `src/match/pfo.py` (`agregar_sinco(..., pesos=)`, parametro nuevo opcional; sin pesos el comportamiento no cambia) y las mismas tablas
   (puente O*NET 2019 -> SOC 2010, tabla F-O). **Pesos: los del revisor (`peso_1`, `peso_2`, normalizados) si los dio; si no, uniformes** entre los
   pares manuales. **Diferencia con la ponderacion automatica**: esta es softmax(sim/tau) con tau = 0.05 (bge-m3), que con margenes pequenos queda cerca
   de 50/50 pero favorece al de mayor similitud; el revisor no ordena por similitud, por eso pesos iguales. Para dos pares la media uniforme y la
   ponderada por el revisor pueden diferir de la automatica aunque los pares sean los mismos. `probabilidad_automatizacion_fo_top1` = primer par del
   conjunto final (rango 1 en ACEPTAR_RANGO1/AMBOS; el unico par en ACEPTAR_RANGO2; `onet_manual_1` en OTRO).
   La regla NA de `sin_coincidencia` NO se aplica a grupos revisados con pares (el revisor la resuelve). `NINGUNO`: probabilidad NA con
   `motivo_na = sin_equivalente_onet_revision_manual`, `n_candidatos = 0`, `cobertura_fo = ninguna`.
5. **Auditoria**: antes de escribir se archivan `crosswalk`, `sinco_probabilidad_fo`, `match_corridas` (y la tabla de cambios si existe) en
   `data/processed/revision_manual/previo_<fecha>[_n]/` (nunca se sobrescribe un archivo previo), se copia el CSV aplicado a
   `revision_manual/aplicadas/`, se escribe `aplicacion_<run_id>.json`, se agrega `data/processed/revision_manual_cambios.parquet`
   (sinco_code, decision, pares y probabilidad antes/despues, pesos usados, revisor, fecha, `en_muestra_oro`, ...; historico acumulativo) y se registra la
   corrida en `match_corridas` (`metodo = revision_manual`, hash del CSV y config en `parametros`; campos de embeddings con valores neutros `n/a`/ceros;
   las corridas anteriores se conservan).
6. **Muestra de oro**: los grupos corregidos que estan en `oro_muestra.parquet` quedan marcados (`en_muestra_oro`). No se modifica `oro_*`
   ni las fichas. **Riesgo**: la muestra de oro se construyo con los candidatos automaticos; una correccion manual a un grupo de la muestra cambia
   el crosswalk contra el que luego se evaluaria. Pendiente decidir si esos grupos se excluyen de la calibracion/evaluacion.
7. **Todo o nada y rechazo**: el CSV se valida completo (columnas, `sinco_code` unitarios existentes y sin duplicados, `decision` permitida, codigos en
   `onet_ocupaciones`, coherencia por decision, pesos > 0, `confianza_revisor`, `revisor` obligatorio en filas aplicables o `--revisor`). Si hay errores:
   issue `docs/issues/revision-manual-<fecha>-validacion-fallida.md` con las filas a corregir, codigo de salida 2, sin tocar ningun dato. La salida se valida
   contra los esquemas antes de escribir (regla 5).
8. **Idempotencia**: si el resultado coincide con lo vigente (salvo `run_id`), no se escribe ni se archiva nada.

## Efectos colaterales y cambios en otros modulos (a revisar)
- `tipo_relacion` y `n_sinco_mismo_top1_soc` son propiedades de grafo/cluster: se recalculan sobre toda la tabla, asi que un grupo NO revisado puede cambiar en
  esas dos columnas si comparte O*NET/SOC con uno revisado (el script reporta cuantas filas en `aplicacion_<run_id>.json`). El resto de columnas de los grupos
  no revisados queda identico.
- `src/match/schemas.py`: `estado_validacion` admite `revision_manual_1_revisor`; `CrosswalkFila.rango` y `.similitud` son opcionales (pares manuales fuera del top-2/top-10); `PFoFila.motivo_na` admite
  `sin_equivalente_onet_revision_manual` y `n_candidatos >= 0`. `src/api/service.py`: el `Literal` de `estado_validacion` del crosswalk admite `revision_manual_1_revisor`
  (sin ello la API declararia todo el crosswalk `esquema_invalido`). Las etiquetas globales de la API ("sin_validar") no cambian.
- `tests/match/test_salidas.py` se hizo tolerante a filas manuales (fuente `manual`, grupos `NINGUNO` sin filas); no afloja nada para las filas automaticas.
- Grupos `NINGUNO` no tienen filas en el crosswalk; `src/score` (exposicion) debe tratarlos como sin equivalente (no como faltante).
- `crosswalk.parquet` y `sinco_probabilidad_fo.parquet` estan publicados en el repositorio; `revision_manual/` y `revision_manual_cambios.parquet` no (ignorados). Publicar
  el crosswalk actualizado es decision del usuario.
- El archivo de revision muestra similitudes; **no es la muestra de oro ciega** y la revision de un solo revisor no sustituye la validacion con la oro.
