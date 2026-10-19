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

test_that("Frey-Osborne: 702 filas, unicidad, rangos y etiquetas", {
  f <- tb("frey_osborne_probabilidades")
  expect_named(f, c("rank_fo", "soc_2010", "ocupacion", "probabilidad_automatizacion_fo", "etiqueta_entrenamiento", "pdf_page", "fuente"))
  expect_equal(nrow(f), 702)
  expect_identical(f$rank_fo, 1:702)
  expect_false(anyDuplicated(f$soc_2010) > 0)
  expect_false(anyDuplicated(f$ocupacion) > 0)
  expect_true(all(grepl("^[0-9]{2}-[0-9]{4}$", f$soc_2010)))
  expect_type(f$soc_2010, "character")
  expect_true(all(f$probabilidad_automatizacion_fo >= 0 & f$probabilidad_automatizacion_fo <= 1))
  expect_false(is.unsorted(f$probabilidad_automatizacion_fo))
  expect_equal(sum(!is.na(f$etiqueta_entrenamiento)), 70)
  expect_true(all(f$etiqueta_entrenamiento %in% c(0L, 1L, NA)))
  expect_false(any(is.na(f$ocupacion) | grepl("[0-9]", f$ocupacion)))
  # valores publicados en el paper (comprobacion puntual de la alineacion rango/codigo/probabilidad)
  v <- setNames(f$probabilidad_automatizacion_fo, f$ocupacion)
  expect_equal(v[["Recreational Therapists"]], 0.0028); expect_equal(v[["Registered Nurses"]], 0.009)
  expect_equal(v[["Chief Executives"]], 0.015); expect_equal(v[["Lawyers"]], 0.035)
  expect_equal(v[["Cashiers"]], 0.97); expect_equal(v[["Telemarketers"]], 0.99)
})

test_that("puente O*NET-SOC 2010 -> 2019: esquema y unicidad", {
  b <- tb("puente_onet_soc2019_soc2010")
  expect_named(b, c("onet_soc_2010_code", "onet_soc_2010_titulo", "onet_soc_2019_code", "onet_soc_2019_titulo", "soc_2010", "fuente"))
  expect_equal(nrow(b), 1164)
  expect_false(anyDuplicated(b[c("onet_soc_2010_code", "onet_soc_2019_code")]) > 0)
  expect_false(anyNA(b))
  expect_true(all(grepl("^[0-9]{2}-[0-9]{4}[.][0-9]{2}$", c(b$onet_soc_2010_code, b$onet_soc_2019_code))))
  expect_identical(b$soc_2010, substr(b$onet_soc_2010_code, 1, 7))
  expect_equal(n_distinct(b$onet_soc_2010_code), 1110)
})

test_that("cobertura (solo reporte, sin imputar): Frey-Osborne frente al puente y a O*NET 31.0", {
  f <- tb("frey_osborne_probabilidades"); b <- tb("puente_onet_soc2019_soc2010"); o <- tb("onet_ocupaciones")
  expect_equal(nrow(o), 1016)
  expect_equal(sum(f$soc_2010 %in% b$soc_2010), 685)          # 17 codigos de Frey-Osborne no estan como SOC 2010 en el puente
  expect_equal(sum(o$onet_soc_code %in% b$onet_soc_2019_code), 1012)
  via <- o |> select(onet_soc_code) |>
    inner_join(distinct(b, onet_soc_2019_code, soc_2010), by = c("onet_soc_code" = "onet_soc_2019_code")) |>
    inner_join(select(f, soc_2010, probabilidad_automatizacion_fo), by = "soc_2010") |>
    group_by(onet_soc_code) |> summarise(n_soc = n(), .groups = "drop")
  expect_equal(nrow(via), 811)                                  # ocupaciones O*NET con al menos una probabilidad por via directa
  expect_equal(sum(via$n_soc == 1), 786); expect_equal(sum(via$n_soc > 1), 25)
  expect_equal(sum(substr(o$onet_soc_code, 1, 7) %in% f$soc_2010), 721)   # alternativa: prefijo directo (SOC 2018 vs 2010)
})

test_that("manifiesto registra las fuentes nuevas con url, hash y archivo vigente", {
  m <- fromJSON(file.path(raiz, "data", "raw", "manifest.json"), simplifyVector = FALSE)
  for (id in c("frey_osborne_2013_pdf", "onet_soc_2010_to_2019_crosswalk")) {
    e <- Filter(function(x) x$id == id, m)
    expect_length(e, 1)
    e <- e[[1]]
    expect_match(e$url, "^https://")
    expect_identical(digest(file = file.path(raiz, e$archivo), algo = "sha256", serialize = FALSE), e$sha256)
  }
})
