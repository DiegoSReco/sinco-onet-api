library(testthat)
library(arrow)
library(dplyr)
library(stringr)
library(digest)
library(jsonlite)

raiz <- local({
  d <- normalizePath(getwd(), winslash = "/")
  repeat {
    if (file.exists(file.path(d, "CLAUDE.md"))) break
    p <- dirname(d); if (identical(p, d)) stop("sin raiz"); d <- p
  }
  d
})
tb <- function(n) read_parquet(file.path(raiz, "data", "processed", paste0(n, ".parquet")))
niv <- c("division", "grupo_principal", "subgrupo", "grupo_unitario")

test_that("jerarquia: conteos oficiales del PDF, unicidad y arbol", {
  s <- tb("sinco")
  expect_equal(nrow(s), 714)
  expect_equal(as.integer(table(factor(s$nivel, levels = niv))), c(9L, 52L, 163L, 490L))
  expect_false(anyDuplicated(s$sinco_code) > 0)
  expect_type(s$sinco_code, "character")
  expect_true(all(grepl("^[1-9][0-9]{0,3}$", s$sinco_code)))
  expect_identical(s$nivel_num, nchar(s$sinco_code))
  expect_true(all(is.na(s$padre) == (s$nivel == "division")))
  expect_true(all(s$padre[!is.na(s$padre)] %in% s$sinco_code))
  expect_identical(s$padre[!is.na(s$padre)], substr(s$sinco_code[!is.na(s$padre)], 1, nchar(s$sinco_code[!is.na(s$padre)]) - 1))
  # cada division/grupo/subgrupo tiene al menos un hijo
  hijos <- unique(s$padre)
  expect_true(all(s$sinco_code[s$nivel != "grupo_unitario"] %in% hijos))
})

test_that("cifras oficiales del PDF coinciden con lo contado (salvo discrepancia documentada)", {
  ci <- tb("sinco_cifras_oficiales")
  n19 <- ci |> filter(concepto == "n_categorias", edicion == "2019")
  expect_true(all(n19$coincide))
  expect_equal(n19$valor_oficial, c(9, 52, 163, 490))
  n11 <- ci |> filter(concepto == "n_categorias", edicion == "2011")
  expect_equal(n11$valor_oficial, c(9, 53, 156, 468))   # cifras 2011 declaradas por el PDF (no son 2019)
  ex <- ci |> filter(concepto == "n_grupos_unitarios_con_excluye")
  # divisiones 1-8 coinciden; division 9 y total difieren (issue datos-2026-10-19-sinco-excluye-division9-discrepancia.md)
  expect_true(all(ex$coincide[ex$division %in% as.character(1:8)]))
  expect_equal(ex$valor_oficial[ex$division == "total"], 395)
  expect_equal(ex$valor_extraido[ex$division == "9"], 36)
})

test_that("integridad referencial de las tablas de texto", {
  s <- tb("sinco")
  for (n in c("sinco_descripcion", "sinco_ocupaciones_ejemplo", "sinco_funciones", "sinco_incluye_excluye")) {
    d <- tb(n); expect_type(d$sinco_code, "character"); expect_true(all(d$sinco_code %in% s$sinco_code), info = n)
  }
  d <- tb("sinco_descripcion")
  expect_equal(nrow(d), 714); expect_false(anyDuplicated(d$sinco_code) > 0)
  expect_setequal(d$sinco_code, s$sinco_code)
  expect_false(anyDuplicated(tb("sinco_ocupaciones_ejemplo")[c("sinco_code", "orden")]) > 0)
  expect_false(anyDuplicated(tb("sinco_funciones")[c("sinco_code", "orden")]) > 0)
  ie <- tb("sinco_incluye_excluye")
  expect_false(anyDuplicated(ie[c("sinco_code", "tipo", "orden")]) > 0)
  expect_true(all(ie$tipo %in% c("incluye", "excluye")))
  # ocupaciones, funciones, incluye/excluye solo en grupos unitarios
  ug <- s$sinco_code[s$nivel == "grupo_unitario"]
  expect_true(all(tb("sinco_ocupaciones_ejemplo")$sinco_code %in% ug))
  expect_true(all(tb("sinco_funciones")$sinco_code %in% ug))
  expect_true(all(ie$sinco_code %in% ug))
  r <- tb("sinco_referencias")
  expect_true(all(paste(r$sinco_code, r$tipo, r$orden) %in% paste(ie$sinco_code, ie$tipo, ie$orden)))
  expect_true(all(r$codigo_valido))
  expect_gt(mean(r$titulo_coincide), 0.99)
  e <- tb("sinco_fe_erratas")
  expect_true(all(na.omit(e$sinco_code) %in% s$sinco_code)); expect_false(any(e$aplicada_en_tablas))
})

test_that("cobertura de texto por nivel", {
  d <- tb("sinco_descripcion") |> left_join(tb("sinco") |> select(sinco_code, titulo), by = "sinco_code")
  ug <- d |> filter(nivel == "grupo_unitario")
  expect_true(all(nchar(ug$descripcion) > 40))                      # 100 % de grupos unitarios con descripcion
  expect_equal(sum(ug$n_ocupaciones > 0), 472)
  expect_equal(sum(ug$n_funciones > 0), 457)
  expect_equal(sum(ug$n_excluye > 0), 398)
  expect_equal(sum(ug$n_incluye > 0), 22)
  # sin funciones => residual ("Otros ..." o 9999 no especificadas)
  sin_f <- d |> filter(nivel == "grupo_unitario", n_funciones == 0)
  expect_true(all(grepl("^Otr[oa]s|no especificadas|no clasificados anteriormente", sin_f$titulo)))
  # niveles superiores: descripcion no vacia salvo residuales
  sup <- d |> filter(nivel != "grupo_unitario", descripcion == "")
  expect_true(all(grepl("^Otr[oa]s|no especificadas|no clasificados anteriormente", sup$titulo)))
  expect_equal(sum(d$nivel == "division" & d$descripcion != ""), 9)
})

test_that("calidad de texto: sin encabezados colados, ligaturas ni guiones de corte", {
  txt <- c(tb("sinco_descripcion")$descripcion, tb("sinco_ocupaciones_ejemplo")$ocupacion,
           tb("sinco_funciones")$funcion, tb("sinco_incluye_excluye")$texto)
  expect_false(any(grepl("INEGI\\. Sistema Nacional", txt)))
  expect_false(any(grepl("[ﬁﬂﬀ]", txt)))
  expect_false(any(grepl("[[:alpha:]]- [[:lower:]]", txt)))
  expect_false(any(grepl("^\\s|\\s$|\\s{2,}", txt)))
  expect_false(any(is.na(txt)))
})

test_that("trazabilidad: fuente y paginas", {
  f <- tb("sinco_fuente")
  m <- fromJSON(file.path(raiz, "data", "raw", "manifest.json"), simplifyVector = FALSE)
  h <- Filter(function(e) e$id == "sinco_2019_pdf", m)[[1]]$sha256
  expect_equal(nrow(f), 1)
  expect_identical(f$sha256, h)
  expect_identical(digest(file = file.path(raiz, f$archivo), algo = "sha256", serialize = FALSE), h)
  expect_match(f$url, "^https://www\\.inegi\\.org\\.mx/")
  expect_equal(f$n_paginas_pdf, 400)
  d <- tb("sinco_descripcion")
  expect_true(all(d$pdf_page_ini >= f$pagina_inicio_ampliada & d$pdf_page_fin <= f$pagina_fin_ampliada & d$pdf_page_fin >= d$pdf_page_ini))
  expect_true(all(tb("sinco_funciones")$pdf_page %in% tb("sinco_paginas")$pdf_page))
  # orden del documento: las paginas de inicio no decrecen siguiendo el orden del catalogo
  s <- tb("sinco"); o <- d$pdf_page_ini[match(s$sinco_code[order(s$orden)], d$sinco_code)]
  expect_false(is.unsorted(o))
})

test_that("glosario y fe de erratas", {
  g <- tb("sinco_glosario"); expect_equal(nrow(g), 21); expect_false(anyDuplicated(g$termino) > 0)
  expect_true(all(nchar(g$definicion) > 20))
  e <- tb("sinco_fe_erratas"); expect_equal(nrow(e), 3); expect_setequal(na.omit(e$sinco_code), c("5115", "9111"))
  expect_true(all(c("5115", "9111") %in% tb("sinco_descripcion")$sinco_code))
  expect_true(any(tb("sinco_ocupaciones_ejemplo")$afectado_por_errata))
})
