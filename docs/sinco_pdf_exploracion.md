# Exploracion del PDF oficial SINCO 2019 (INEGI)

Fuente: `data/raw/sinco_2019.pdf` (sha256 `6a8a80d6e193ecb466d2b3d85478b62c310476dc84d6b6a15b1af2530176f5f6`, ver `data/raw/manifest.json`).
URL: https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/702825198411.pdf
Catalogacion en la fuente: "Sistema Nacional de Clasificacion de Ocupaciones 2019 : SINCO", INEGI, c2020, viii + 403 p.
El PDF tiene 400 paginas fisicas (`pdf_page`); la numeracion impresa (`pagina_impresa`) difiere (portada y romanos) y se desfasa en
las paginas 227-230 por la fe de erratas. Extraccion: `pdftotext -layout -enc UTF-8` (Xpdf 4.00). Correcciones de formato (no de contenido):
ligaturas tipograficas (fi, fl, ff) a letras sueltas; encabezado corrido retirado; guiones de corte de linea resueltos con el vocabulario del propio documento.

## Mapa del documento (paginas fisicas del PDF)

| Seccion | pdf_page aprox. | Contenido | Tabla |
|---|---|---|---|
| Portada, catalogacion, presentacion, indice | 1-8 | texto institucional | no se extrae |
| Introduccion, Aspectos generales (fundamentos, antecedentes, utilidad, proceso de actualizacion, principios, conceptos, criterios, estructura, titulos y descripciones) | 9-32 | metodologia de INEGI; cuadro comparativo 2011/2019 (p. 17); cuadro de grupos unitarios con "excluye" (p. 21); 4 niveles de competencia de la CIUO-08 (p. 25-26) | solo cifras oficiales -> `sinco_cifras_oficiales` |
| Version abreviada | ~40-62 (listado de grupos unitarios en 44-61) | divisiones, grupos principales, subgrupos, grupos unitarios (codigo + titulo) | `sinco` |
| Version ampliada | 63-356 (294 paginas) | para cada codigo: descripcion; en grupos unitarios ademas Ocupaciones (ejemplos), Funciones, Incluye, Excluye | `sinco_descripcion`, `sinco_ocupaciones_ejemplo`, `sinco_funciones`, `sinco_incluye_excluye`, `sinco_referencias` |
| Anexo: tabla de equivalencia SINCO 2011-2019 | 357-392 | correspondencia de codigos 2019 vs 2011 | DESCARTADO (ver issue) |
| Glosario | 393-395 | 21 terminos | `sinco_glosario` |
| Bibliografia | 396-399 | referencias | no se extrae |
| Fe de erratas | 400 | 3 notas (2024-2025) | `sinco_fe_erratas` |

(Los rangos exactos de la version ampliada quedan en `sinco_fuente`: `pagina_inicio_ampliada`, `pagina_fin_ampliada`.)

## Que hay por nivel

- Division (9), grupo principal (52), subgrupo (163): titulo y un parrafo de descripcion. 9 grupos principales y 17 subgrupos son residuales ("Otros ... no clasificados anteriormente", "Ocupaciones no especificadas") y solo traen el titulo (sin descripcion).
- Grupo unitario (490): descripcion (siempre); Ocupaciones ejemplo (472 de 490), Funciones (457), Incluye (22), Excluye (398). Los 33 sin Funciones son todos residuales ("Otros ..." y 9999); no hay vacios inexplicados. Un grupo (7351) trae "Incluye" sin vineta (una sola linea, conservada tal cual).
- Referencias en Incluye/Excluye: 953 referencias a codigos (p. ej. "(4211 Empleados de ventas ...)"); los 953 codigos existen en el catalogo y 952 coinciden ademas con el titulo del catalogo.
- No hay en el PDF: correspondencia con CIUO-08, SCIAN ni O*NET; solo menciona la CIUO-08 como referente metodologico (prosa, principio 'e' y definiciones de competencia). Confirmado buscando "CIUO", "SCIAN" y las tablas del anexo.
- No hay un indice alfabetico de titulos de ocupaciones ni cifras de empleo.
- Las "ocupaciones ejemplo" son titulos de ocupaciones especificas (1642 en total): candidatas naturales para emparejamientos por titulo; usarlas en el crosswalk es decision de metodologia.
- Nivel de competencias (1-4): el PDF lo define en prosa (p. 25-26) pero no lo asigna a cada division/codigo en una tabla; no se extrae.

## Conciliacion de conteos de niveles (490 / 468 / 489)

Conteo directo en el PDF 2019 (version abreviada y ampliada coinciden, 714 codigos, sin duplicados ni huerfanos):

| Nivel | Contado en `sinco` | Declarado por el PDF 2019 | Declarado por el PDF para SINCO 2011 |
|---|---|---|---|
| Division | 9 | 9 | 9 |
| Grupo principal | 52 | 52 | 53 |
| Subgrupo | 163 | 163 | 156 |
| Grupo unitario | 490 | 490 | 468 |

Evidencia textual:
- PDF p. 17 (impresa 10), "Comparativo de orden cuantitativo entre los elementos que conforman cada nivel de desagrupacion del SINCO 2011 y el de 2019": fila Total `9 53 156 468 | 9 52 163 490` (2011 | 2019). El mismo cuadro por division (columna 2019 de grupos unitarios: 60, 159, 21, 17, 33, 33, 58, 49, 60 = 490) coincide con el catalogo por division (grupos principales 8,9,3,4,4,4,7,4,9 y subgrupos 16,39,10,8,13,10,24,19,24 tambien).
- PDF p. 17: "el SINCO 2019 cuenta con un grupo principal menos, asi como siete subgrupos y 22 grupos unitarios mas que su version de 2011" (53-1 = 52; 156+7 = 163; 468+22 = 490).
- PDF p. 21: "de los 468 grupos unitarios existentes [en 2011]" y "dentro de los 490 grupos unitarios del SINCO 2019". PDF p. 27-31 (Estructura): "52 grupos principales", "163 subgrupos", "490 grupos unitarios".

Conclusion: las cifras 468 / 53 / 156 (resumen de busqueda de la presentacion SNIEG) corresponden a SINCO **2011**, no a 2019; el resumen las habia invertido respecto del PDF oficial. No hay mezcla de versiones ni error de parseo: las cifras del parquet son las 2019.
La cifra "489 ocupaciones" del articulo de Desarrollo y Sociedad (Uniandes): no se pudo leer el articulo (la pagina solo devolvio el encabezado), por lo que **no esta verificada** y no aparece en el PDF. Observacion aritmetica no verificada: 490 menos el grupo residual 9999 "Ocupaciones no especificadas" = 489; la version a la que se refiere el articulo es desconocida.

## Discrepancias internas del PDF (no corregidas)
- Excluye: ver `docs/issues/datos-2026-10-19-sinco-excluye-division9-discrepancia.md` (395 declarado vs 398 contado; division 9: 33 vs 36).
- Fe de erratas: el PDF corrige ejemplos de 5115 Cantineros (p. impresa 227) y la clave del Excluye de 9111 (p. impresa 331); la pagina 230 fue integrada despues. Las tablas conservan el texto original y marcan `afectado_por_errata`; `sinco_fe_erratas` trae "dice" y "debe decir". Aplicarlas es decision de metodologia.
- En 2281 (`sinco_descripcion.notas_extraccion`) una funcion termina en "telecomunicaciones-" y la siguiente no lleva vineta en el PDF fuente (quedan fusionadas en un item): se conserva como esta.
- El listado abreviado imprime un renglon "971 Trabajadores repartidores de mensajeria..." duplicado y "971Trabajadores" sin espacio; se corrige solo el formato (ver `00_sinco_lib.R`).
