# Diccionario de datos: tablas SINCO 2019 (data/processed/*.parquet)

Generadas por `src/ingest/01_sinco.R` y `src/ingest/04_sinco_texto.R` (librerias en `00_utils.R`, `00_sinco_lib.R`) a partir de
`data/raw/sinco_2019.pdf`. Todos los codigos son texto (`character`) sin ceros a la izquierda (los codigos SINCO no empiezan en 0).
`pdf_page` = pagina fisica del PDF (1 a 400); `pagina_impresa` = numero impreso en la pagina (NA si no se pudo detectar). Version y hash de fuente: `sinco_fuente`.

## Modelo relacional

```
sinco (PK sinco_code; FK padre -> sinco.sinco_code)
 |-- 1:1  sinco_descripcion        (PK sinco_code, FK -> sinco)
 |-- 1:N  sinco_ocupaciones_ejemplo (PK sinco_code+orden, FK -> sinco)      [solo grupos unitarios]
 |-- 1:N  sinco_funciones           (PK sinco_code+orden, FK -> sinco)      [solo grupos unitarios]
 |-- 1:N  sinco_incluye_excluye     (PK sinco_code+tipo+orden, FK -> sinco) [solo grupos unitarios]
        |-- 1:N sinco_referencias   (FK sinco_code+tipo+orden -> sinco_incluye_excluye; codigo_referido -> sinco)
sinco_fe_erratas (FK sinco_code -> sinco, nullable)   sinco_glosario   sinco_cifras_oficiales   sinco_paginas   sinco_fuente (1 fila)
```

## sinco (714 x 10)
| Columna | Tipo | Descripcion |
|---|---|---|
| sinco_code | texto, PK | codigo de 1 a 4 digitos |
| nivel | texto | division (9), grupo_principal (52), subgrupo (163), grupo_unitario (490) |
| titulo | texto | titulo oficial (version abreviada) |
| padre | texto, FK | codigo del nivel inmediato superior; NA en divisiones |
| nivel_num | entero | 1-4 (= numero de digitos) |
| division, grupo_principal, subgrupo | texto | prefijos del codigo (NA si el nivel es mas alto) |
| orden | entero | orden de aparicion en el PDF |
| pdf_page_estructura | entero | pagina fisica en la version abreviada |

## sinco_descripcion (714 x 13) cardinalidad 1:1 con sinco
sinco_code, nivel, titulo_ampliado (titulo en la version ampliada; coincide con `sinco.titulo` salvo formato), descripcion (texto completo; vacio solo en 9 grupos principales y 17 subgrupos residuales), pdf_page_ini, pdf_page_fin, pagina_impresa_ini, n_ocupaciones, n_funciones, n_incluye, n_excluye (conteos de items), n_caracteres, notas_extraccion (texto si se detecto una anomalia de extraccion; NA normalmente).

## sinco_ocupaciones_ejemplo (1642 x 6)
sinco_code, orden (entero, PK con sinco_code), ocupacion (titulo de ocupacion ejemplo), pdf_page, pagina_impresa, afectado_por_errata (lgl; TRUE para 5115 segun la fe de erratas). Cobertura: 472 de 490 grupos unitarios.

## sinco_funciones (3542 x 5)
sinco_code, orden, funcion, pdf_page, pagina_impresa. Cobertura: 457 de 490 grupos unitarios (los 33 restantes son residuales y no traen funciones).

## sinco_incluye_excluye (953 x 7)
sinco_code, tipo ("incluye" 22 | "excluye" 931), orden, texto, pdf_page, pagina_impresa, afectado_por_errata (lgl; TRUE para 9111 excluye). Cobertura: 398 grupos unitarios con "excluye" y 22 con "incluye".

## sinco_referencias (953 x 7)
Una fila por codigo referido dentro del texto de `sinco_incluye_excluye` (p. ej. "(4211 Empleados de ventas ...)"): sinco_code, tipo, orden (llave al item), codigo_referido (texto), codigo_valido (existe en `sinco`), titulo_coincide (el texto que sigue al codigo comienza como el titulo del catalogo), auto_referencia. Son datos extraidos, no un crosswalk.

## sinco_fe_erratas (3 x 10)
errata_id, sinco_code (NA en la nota de pagina 230), pagina_impresa, seccion, nota, texto_dice, texto_debe_decir, fecha (ISO), pdf_page_fuente, aplicada_en_tablas (siempre FALSE: no se modifica contenido de INEGI).

## sinco_glosario (21 x 4)
glosario_id, termino, definicion, pdf_page.

## sinco_cifras_oficiales (18 x 8)
Cifras declaradas por el PDF frente a lo contado: concepto ("n_categorias" 2011/2019 por nivel; "n_grupos_unitarios_con_excluye" por division y total), edicion, nivel, division, valor_oficial, pdf_page, valor_extraido, coincide. Las cifras de 2011 no se recuentan (NA). Diferencias conocidas: excluye total (395 vs 398) y division 9 (33 vs 36), ver issue.

## sinco_paginas (294 x 3)
pdf_page (63-356 = version ampliada), pagina_impresa, marca_fe_erratas (pagina con marca "Fe de erratas" de INEGI).

## sinco_fuente (1 x 12)
documento, url, archivo, sha256, bytes, fecha_descarga, n_paginas_pdf, pagina_inicio_ampliada, pagina_fin_ampliada, extractor, script, fecha_procesamiento.

## Notas de calidad
- Texto: una sola cadena por campo; guiones de corte de linea eliminados (se conservan guiones de palabras compuestas si aparecen asi en el documento); parrafos de la descripcion unidos con un espacio.
- Fuera de alcance (decision del usuario): anexo de equivalencia SINCO 2011-2019 (ver issue). No hay correspondencia CIUO-08 en el PDF.
- Reconciliacion con `docs/decisions/003-requisitos-tablas-sinco.md`: campos esenciales (descripcion, funciones, incluye/excluye, ocupaciones ejemplo, pagina, hash) cubiertos; la tabla de equivalencia 2011 (deseable) queda pendiente; el criterio de cobertura 100 % de descripcion se cumple en grupos unitarios (490/490).
