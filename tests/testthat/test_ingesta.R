library(testthat)
library(arrow)
library(jsonlite)
library(digest)

raiz <- local({
  d <- normalizePath(getwd(), winslash = "/")
  repeat {
    if (file.exists(file.path(d, "CLAUDE.md"))) break
    p <- dirname(d); if (identical(p, d)) stop("sin raiz"); d <- p
  }
  d
})
proc <- function(f) file.path(raiz, "data", "processed", f)

test_that("manifest.json: hashes coinciden con los archivos actuales", {
  m <- fromJSON(file.path(raiz, "data", "raw", "manifest.json"), simplifyVector = FALSE)
  expect_gt(length(m), 0)
  for (e in m) {
    expect_true(all(c("id", "url", "archivo", "version", "fecha_descarga", "sha256") %in% names(e)))
    expect_match(e$url, "^https://")
    f <- file.path(raiz, e$archivo)
    expect_true(file.exists(f), info = e$id)
    expect_identical(digest(file = f, algo = "sha256", serialize = FALSE), e$sha256, info = e$id)
  }
})

test_that("sinco.parquet: esquema y conteos oficiales", {
  d <- read_parquet(proc("sinco.parquet"))
  expect_true(all(c("sinco_code", "nivel", "titulo", "padre") %in% names(d)))
  expect_type(d$sinco_code, "character")
  expect_false(anyDuplicated(d$sinco_code) > 0)
  expect_true(all(grepl("^[1-9][0-9]{0,3}$", d$sinco_code)))
  expect_identical(as.integer(nchar(d$sinco_code)), match(d$nivel, c("division", "grupo_principal", "subgrupo", "grupo_unitario")))
  expect_equal(sum(d$nivel == "division"), 9)
  expect_equal(sum(d$nivel == "grupo_principal"), 52)
  expect_equal(sum(d$nivel == "subgrupo"), 163)
  expect_equal(sum(d$nivel == "grupo_unitario"), 490)
  expect_true(all(d$padre[!is.na(d$padre)] %in% d$sinco_code))
  expect_false(any(is.na(d$titulo) | d$titulo == ""))
})

test_that("tareas_onet_en.parquet: esquema y conteos minimos", {
  d <- read_parquet(proc("tareas_onet_en.parquet"))
  expect_named(d, c("task_id", "onet_soc_code", "tarea_en"))
  expect_type(d$task_id, "character")
  expect_type(d$onet_soc_code, "character")
  expect_true(all(grepl("^[0-9]{2}-[0-9]{4}[.][0-9]{2}$", d$onet_soc_code)))
  expect_false(anyDuplicated(d[c("task_id", "onet_soc_code")]) > 0)
  expect_false(anyNA(d))
  expect_gt(nrow(d), 15000)
  expect_gt(length(unique(d$onet_soc_code)), 800)
})

test_that("tablas auxiliares de O*NET existen y son consistentes", {
  r <- read_parquet(proc("tareas_onet_ratings.parquet"))
  expect_true(all(c("onet_soc_code", "task_id", "scale_id", "category", "data_value") %in% names(r)))
  expect_true(all(r$scale_id %in% c("FT", "IM", "RT")))
  o <- read_parquet(proc("onet_ocupaciones.parquet"))
  expect_true(all(read_parquet(proc("tareas_onet_en.parquet"))$onet_soc_code %in% o$onet_soc_code))
})

test_that("crosswalk.parquet: esquema (omitida si aun no existe; ver docs/issues/)", {
  skip_if_not(file.exists(proc("crosswalk.parquet")),
              "crosswalk.parquet no existe: bloqueado, ver docs/issues/datos-*-crosswalk-*.md")
  d <- read_parquet(proc("crosswalk.parquet"))
  expect_named(d, c("sinco_code", "isco08_code", "onet_soc_code", "tipo_relacion", "notas"))
  expect_type(d$sinco_code, "character")
  expect_type(d$isco08_code, "character")
})
