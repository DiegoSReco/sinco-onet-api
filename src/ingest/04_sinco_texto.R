# Ingesta SINCO 2019 (INEGI), parte 2: texto de la version ampliada (descripcion, ocupaciones ejemplo,
# funciones, incluye/excluye, referencias), fe de erratas, glosario, cifras oficiales y trazabilidad.
# Fuente unica: data/raw/sinco_2019.pdf (hash verificado contra manifest.json). El anexo de
# equivalencia SINCO 2011-2019 queda fuera de alcance (ver docs/issues/datos-2026-10-19-sinco-anexo-equivalencia-descartado.md).
# Tablas (Parquet en data/processed/): sinco_descripcion, sinco_ocupaciones_ejemplo, sinco_funciones,
# sinco_incluye_excluye, sinco_referencias, sinco_fe_erratas, sinco_glosario, sinco_cifras_oficiales,
# sinco_paginas, sinco_fuente. Todos los codigos son texto.
suppressPackageStartupMessages({ library(dplyr); library(stringr); library(arrow); library(jsonlite) })
.d <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]), winslash = "/"))
source(file.path(.d, "00_utils.R")); source(file.path(.d, "00_sinco_lib.R"))

pages <- sinco_pdf_pages()
cat_ <- parse_sinco_catalogo(pages)

# ---- Cuerpo ------------------------------------------------------------------------------------
ln <- lineas_cuerpo(pages)
imp <- attr(ln, "impresa"); pag_fe <- attr(ln, "pag_fe_erratas")
h <- localiza_encabezados(ln, cat_)
h$pdf_page_ini <- ln$pdf_page[h$ini]
r <- parse_cuerpo(ln, h)
if (nrow(r$anomalias) > 0 && any(r$anomalias$detalle != "seccion sin vineta inicial"))
  message("Aviso: ", sum(r$anomalias$detalle != "seccion sin vineta inicial"), " posibles vinetas perdidas (ver sinco_descripcion$notas_extraccion)")

r_rng <- rango_cuerpo(pages)
paginas <- tibble(pdf_page = r_rng[1]:r_rng[2]) |>
  mutate(pagina_impresa = unname(imp[as.character(pdf_page)]), marca_fe_erratas = pdf_page %in% pag_fe)
imp_de <- function(p) paginas$pagina_impresa[match(p, paginas$pdf_page)]

# ---- Fe de erratas (pagina final del PDF) ------------------------------------------------------
p_err <- which(str_detect(pages, "FE DE ERRATAS"))
if (length(p_err) != 1) stop_with_issue("SINCO: fe de erratas no localizada", "Marcador FE DE ERRATAS no unico.")
et <- str_squish(paste(pdf_texto_simple(p_err, p_err), collapse = " "))
fechas <- str_extract_all(et, "[0-9]{2} de [[:alpha:]]+")[[1]]; anios <- str_extract_all(et, "202[0-9]")[[1]]
dice <- str_match_all(et, "Dice: (.*?) (?=Debe decir:)")[[1]][, 2]
debe <- str_match_all(et, "Debe decir: (.*?)( Se ajust|$)")[[1]][, 2]
if (length(dice) != 2 || length(debe) != 2 || length(fechas) != 3 || length(anios) != 3)
  stop_with_issue("SINCO: fe de erratas con formato inesperado", paste0("dice=", length(dice), " debe=", length(debe), " fechas=", length(fechas)))

mes <- c(abril = 4, septiembre = 9)
iso <- function(f, a) sprintf("%s-%02d-%02d", a, mes[str_extract(f, "[[:alpha:]]+$")], as.integer(str_extract(f, "^[0-9]{2}")))
limpia_e <- function(x) str_squish(str_remove_all(str_remove_all(x, "[0-9]{2} de [[:alpha:]]+"), "(^| )(227|331|2025)( |$)"))
erratas <- tibble(
  errata_id = 1:3,
  sinco_code = c(NA, "5115", "9111"),
  pagina_impresa = c(230L, 227L, 331L),
  seccion = c(NA, "ocupaciones", "excluye"),
  nota = c("Se integró la página número 230 debido a que no fue incluida en la publicación inicial.",
           "Cambio de ejemplos en el grupo unitario 5115 Cantineros",
           "Se ajustó la clave del excluye del grupo unitario 9111 Trabajadores de apoyo en actividades agrícolas"),
  texto_dice = c(NA, limpia_e(dice[1]), limpia_e(dice[2])),
  texto_debe_decir = c(NA, limpia_e(debe[1]), limpia_e(debe[2])),
  fecha = unname(iso(fechas, anios)),
  pdf_page_fuente = p_err,
  aplicada_en_tablas = FALSE)   # el contenido de INEGI no se modifica; aplicarla es decision de metodologia
stopifnot(all(na.omit(erratas$sinco_code) %in% cat_$sinco_code))

# ---- Tablas de texto ---------------------------------------------------------------------------
it <- r$items
cuenta <- function(sec) { x <- table(factor(it$sinco_code[it$seccion == sec], levels = cat_$sinco_code)); as.integer(x[cat_$sinco_code]) }
afecta <- function(code, sec) paste(code, sec) %in% paste(na.omit(erratas$sinco_code), na.omit(erratas$seccion))
descripcion <- r$descripcion |>
  transmute(sinco_code, nivel = cat_$nivel[match(sinco_code, cat_$sinco_code)],
            titulo_ampliado = h$titulo_ampliado[match(sinco_code, h$sinco_code)],
            descripcion, pdf_page_ini, pdf_page_fin, pagina_impresa_ini = imp_de(pdf_page_ini)) |>
  mutate(n_ocupaciones = cuenta("ocupaciones"), n_funciones = cuenta("funciones"),
         n_incluye = cuenta("incluye"), n_excluye = cuenta("excluye"), n_caracteres = nchar(descripcion),
         notas_extraccion = NA_character_)
if (nrow(r$anomalias)) {
  a <- r$anomalias |> group_by(sinco_code) |> summarise(n = paste(paste0(seccion, ": ", detalle), collapse = " | "))
  descripcion$notas_extraccion[match(a$sinco_code, descripcion$sinco_code)] <- a$n
}
mk <- function(sec, col) it |> filter(seccion == sec) |>
  transmute(sinco_code, orden, !!col := texto, pdf_page, pagina_impresa = imp_de(pdf_page))
ocupaciones <- mk("ocupaciones", "ocupacion") |> mutate(afectado_por_errata = afecta(sinco_code, "ocupaciones"))
funciones <- mk("funciones", "funcion")
inc_exc <- it |> filter(seccion %in% c("incluye", "excluye")) |>
  transmute(sinco_code, tipo = seccion, orden, texto, pdf_page, pagina_impresa = imp_de(pdf_page)) |>
  mutate(afectado_por_errata = afecta(sinco_code, tipo))

# Referencias a otros codigos dentro de incluye/excluye (p. ej. "(4211 Empleados de ventas...)").
# Se extraen como datos: codigo_referido, si existe en el catalogo y si el titulo que sigue coincide.
refs <- list()
for (i in seq_len(nrow(inc_exc))) {
  m <- str_locate_all(inc_exc$texto[i], "(?<![0-9])[1-9][0-9]{0,3}(?![0-9])[[:space:]]+(?=[[:upper:]])")[[1]]
  if (!nrow(m)) next
  cod <- str_trim(str_sub(inc_exc$texto[i], m[, 1], m[, 2]))
  resto <- str_sub(inc_exc$texto[i], m[, 2] + 1L)
  refs[[length(refs) + 1]] <- tibble(sinco_code = inc_exc$sinco_code[i], tipo = inc_exc$tipo[i], orden = inc_exc$orden[i],
                                     codigo_referido = cod, resto = resto)
}
referencias <- bind_rows(refs) |>
  mutate(codigo_valido = codigo_referido %in% cat_$sinco_code,
         titulo_catalogo = cat_$titulo[match(codigo_referido, cat_$sinco_code)],
         titulo_coincide = codigo_valido & startsWith(norm_txt(resto), str_sub(norm_txt(titulo_catalogo), 1, 12)),
         auto_referencia = codigo_referido == sinco_code) |>
  select(sinco_code, tipo, orden, codigo_referido, codigo_valido, titulo_coincide, auto_referencia)

# ---- Glosario (paginas finales) ----------------------------------------------------------------
p_glo <- which(str_detect(pages, "^[[:space:]]*Glosario[[:space:]]*\n"))[1]
gl <- pdf_texto_simple(p_glo + 1L, p_glo + 2L)
gl <- str_squish(str_remove_all(gl, SINCO_ENCAB))
gl <- gl[gl != "" & !str_detect(gl, "^[A-Z]$") & !str_detect(gl, "^[0-9]{1,3}$") & gl != "Glosario"]
glos <- tibble(termino = character(), definicion = character())
for (x in gl) {
  m <- str_match(x, "^([^.]{2,60})[.] (.+)$")
  if (is.na(m[1, 1]) && str_starts(x, "Experiencia laboral "))   # el PDF omite el punto tras el termino
    m <- cbind(x, "Experiencia laboral", str_remove(x, "^Experiencia laboral "))
  if (is.na(m[1, 1])) { glos$definicion[nrow(glos)] <- paste(glos$definicion[nrow(glos)], x); next }
  glos <- bind_rows(glos, tibble(termino = m[1, 2], definicion = m[1, 3]))
}
glos <- glos |> mutate(glosario_id = row_number(), pdf_page = p_glo + 1L) |> select(glosario_id, termino, definicion, pdf_page)

# ---- Cifras oficiales declaradas en el PDF -----------------------------------------------------
p_cmp <- which(str_detect(pages, "Comparativo de orden cuantitativo"))[1]
tot <- as.integer(str_extract_all(str_extract(pages[p_cmp], "(?m)^[[:space:]]*Total[[:space:]]+[0-9 ]+$"), "[0-9]+")[[1]])
p_exc <- which(str_detect(pages, "que cuentan con el rubro de excluye"))[1]
pe <- str_sub(pages[p_exc], str_locate(pages[p_exc], "rubro de")[1, 1])
filas <- str_match_all(pe, "(?m)[[:space:]](Total|[1-9])[[:space:]]+([0-9]+)[[:space:]]+[0-9.]+[[:space:]]*$")[[1]]
divs <- c("Total", as.character(1:9))
v_exc <- as.numeric(filas[match(divs, filas[, 2]), 3])
ug <- cat_$sinco_code[cat_$nivel == "grupo_unitario"]
con_ex <- unique(inc_exc$sinco_code[inc_exc$tipo == "excluye" & inc_exc$sinco_code %in% ug])
ext_exc <- c(length(con_ex), as.numeric(table(factor(substr(con_ex, 1, 1), levels = as.character(1:9)))))
cifras <- bind_rows(
  tibble(concepto = "n_categorias", edicion = rep(c("2011", "2019"), each = 4), nivel = rep(NIVELES, 2), division = NA_character_,
         valor_oficial = as.numeric(tot), pdf_page = p_cmp,
         valor_extraido = c(rep(NA_real_, 4), as.numeric(table(factor(cat_$nivel, levels = NIVELES))))),
  tibble(concepto = "n_grupos_unitarios_con_excluye", edicion = "2019", nivel = "grupo_unitario", division = tolower(divs),
         valor_oficial = v_exc, pdf_page = p_exc, valor_extraido = ext_exc)) |>
  mutate(coincide = valor_oficial == valor_extraido)

# ---- Fuente / trazabilidad ---------------------------------------------------------------------
m <- Filter(function(e) identical(e$id, "sinco_2019_pdf"), read_manifest())[[1]]
fuente <- tibble(documento = "SINCO 2019 (INEGI, 2020)", url = m$url, archivo = m$archivo, sha256 = m$sha256, bytes = as.numeric(m$bytes),
                 fecha_descarga = m$fecha_descarga, n_paginas_pdf = length(pages), pagina_inicio_ampliada = r_rng[1], pagina_fin_ampliada = r_rng[2],
                 extractor = paste(attr(pages, "pdftotext"), "-layout -enc UTF-8"), script = "src/ingest/04_sinco_texto.R",
                 fecha_procesamiento = format(Sys.Date(), "%Y-%m-%d"))

# ---- Validaciones y escritura ------------------------------------------------------------------
stopifnot(!anyDuplicated(descripcion$sinco_code), nrow(descripcion) == nrow(cat_),
          all(descripcion$descripcion[descripcion$nivel == "grupo_unitario"] != ""))
stopifnot(!anyDuplicated(ocupaciones[c("sinco_code", "orden")]), !anyDuplicated(funciones[c("sinco_code", "orden")]),
          !anyDuplicated(inc_exc[c("sinco_code", "tipo", "orden")]), all(it$sinco_code %in% cat_$sinco_code))
out <- list(sinco_descripcion = descripcion, sinco_ocupaciones_ejemplo = ocupaciones, sinco_funciones = funciones,
            sinco_incluye_excluye = inc_exc, sinco_referencias = referencias, sinco_fe_erratas = erratas,
            sinco_glosario = glos, sinco_cifras_oficiales = cifras, sinco_paginas = paginas, sinco_fuente = fuente)
for (n in names(out)) {
  write_parquet_checked(out[[n]], paste0(n, ".parquet"))
  message(sprintf("OK %-28s %6d filas x %2d cols", n, nrow(out[[n]]), ncol(out[[n]])))
}
print(as.data.frame(cifras[, c("concepto", "edicion", "nivel", "division", "valor_oficial", "valor_extraido", "coincide")]))
