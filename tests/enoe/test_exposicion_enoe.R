# Pruebas del analisis de exposicion en la ENOE (decision 020). Desde la raiz del proyecto:
#   Rscript -e 'testthat::test_file("tests/enoe/test_exposicion_enoe.R")'
suppressPackageStartupMessages({ library(testthat); library(data.table) })
.raiz <- function() { d <- normalizePath(getwd(), winslash = "/"); repeat { if (file.exists(file.path(d, "CLAUDE.md"))) return(d); if (identical(dirname(d), d)) stop("sin raiz"); d <- dirname(d) } }
setwd(.raiz())   # testthat entra a la carpeta de la prueba; las rutas son relativas a la raiz
source(file.path("src", "enoe", "exposicion_enoe.R"))   # no ejecuta main(): solo define funciones

test_that("wmean y wquantile ponderan y no interpolan", {
  x <- c(1, 2, 3, 4); w <- c(1, 1, 1, 7)
  expect_equal(wmean(x, w), (1 + 2 + 3 + 28) / 10)
  expect_equal(wquantile(x, w, c(0.1, 0.3, 0.5, 0.99)), c(1, 3, 4, 4))          # inverso de la ecdf: 0.1, 0.2, 0.3, 1.0
  expect_true(all(wquantile(c(5, 1, 3), c(1, 1, 1), c(0.25, 0.5, 0.75)) %in% c(1, 3, 5)))
})

test_that("los multiplicadores de Rao y Wu conservan el total de pesos y no mueven estratos de una UPM", {
  est <- rep(c("a", "b", "c"), times = c(5, 1, 8))
  M <- multiplicadores_rw(est, B = 400, semilla = 1)
  expect_equal(dim(M), c(14, 400))
  expect_true(all(M[est == "b", ] == 1))
  for (h in c("a", "c")) expect_equal(colSums(M[est == h, , drop = FALSE]), rep(sum(est == h), 400))   # sum de n/(n-1) * conteos = n
  expect_equal(mean(M[est == "c", ]), 1, tolerance = 0.02)
  expect_identical(multiplicadores_rw(est, 5, 7), multiplicadores_rw(est, 5, 7))                         # misma semilla, mismas replicas
})

test_that("estima_dominio coincide con la media ponderada y su bootstrap la rodea", {
  set.seed(3)
  n <- 600; upm <- sample(1:60, n, replace = TRUE); est <- (upm - 1) %/% 10 + 1
  w <- runif(n, 100, 500); x <- rbinom(n, 1, 0.4) * 0.5 + rbinom(n, 1, 0.1) * 0.5
  V <- cbind(E = x, sobre_0.5 = as.numeric(x >= 0.5))
  upm_ids <- sort(unique(upm)); M <- multiplicadores_rw(est[match(upm_ids, upm)], 300, 11)
  mask <- rep(TRUE, n)
  r <- estima_dominio(w, V, match(upm, upm_ids), length(upm_ids), M, mask)
  expect_equal(unname(r$punto["E"]), wmean(x, w))
  expect_equal(unname(r$punto["sobre_0.5"]), wmean(as.numeric(x >= 0.5), w))
  expect_equal(unname(r$peso), sum(w))
  expect_true(abs(mean(r$boot[, "E"]) - r$punto["E"]) < 4 * sd(r$boot[, "E"]) + 1e-9)
  d1 <- upm %in% 1:30; r1 <- estima_dominio(w, V, match(upm, upm_ids), length(upm_ids), M, d1[match(seq_len(n), seq_len(n))])
  expect_equal(unname(r1$punto["E"]), wmean(x[d1], w[d1]))
})

pers_f <- file.path("data", "processed", "enoe", "enoe_exposicion_personas_2022T3_2025T3.parquet")
test_that("las salidas sobre la muestra real son consistentes", {
  skip_if_not(file.exists(pers_f), "falta correr src/enoe/exposicion_enoe.R")
  p <- arrow::read_parquet(pers_f); setDT(p)
  integridad <- jsonlite::fromJSON(file.path("data", "processed", "enoe", "enoe_integridad.json"))
  expect_equal(nrow(p), sum(vapply(integridad, function(z) z$filas_union, numeric(1))))                     # muestra completa: ninguna persona se pierde
  expect_equal(sort(unique(p$periodo)), c("2022T3", "2025T3"))
  llaves <- intersect(c("periodo", "ent", "con", "v_sel", "n_hog", "h_mud", "n_ren", "cd_a", "tipo", "mes_cal", "ca"), names(p))   # llaves de INEGI que usa enoe_join
  expect_false(anyDuplicated(p[, ..llaves]) > 0)                                                              # una fila por persona
  expect_true(all(is.na(p$E[!p$poblacion])))                                                                  # solo los ocupados de la poblacion objetivo reciben exposicion
  expect_true(all(p$E >= 0 & p$E <= 1, na.rm = TRUE) && all(p$alfa_S <= p$beta_S + 1e-9 & p$beta_S <= p$cota_sup_S + 1e-9, na.rm = TRUE))
  expect_true(all(p[cobertura == "con_medida", !is.na(E)]) && all(p[cobertura != "con_medida", is.na(E)]))
  cob <- fread(file.path("data", "processed", "enoe", "enoe_exposicion_cobertura.csv"))
  expect_equal(cob[, sum(pct_ponderado), by = periodo]$V1, c(100, 100), tolerance = 1e-6)
  res <- fread(file.path("data", "processed", "enoe", "enoe_exposicion_resumen.csv"), colClasses = c(categoria = "character"))
  expect_true(all(res[publicable == TRUE, n_muestra] >= PARAM$n_min))
  expect_true(all(res[publicable == TRUE, ic_lo_E <= media_E & media_E <= ic_hi_E]))
  expect_true(all(is.na(res[publicable == FALSE, media_E])))
  # el total ponderado de la tabla coincide con el de las personas con medida
  tot <- res[estrato == "total"]
  expect_equal(tot$n_ponderado, p[cobertura == "con_medida", sum(fac_tri), by = periodo][order(periodo)]$V1)
  # control negativo (013 sec. 8.3): las divisiones de trabajo manual (6, 7, 9) tienen menos exposicion que las de oficina y profesionistas (1, 2, 3)
  dv <- res[estrato == "division" & periodo == "2025T3"]
  expect_lt(max(dv[categoria %in% c("6", "7", "9"), media_E]), min(dv[categoria %in% c("1", "2", "3"), media_E]))
})

test_that("la exposicion usada es la congelada", {
  skip_if_not(file.exists(file.path("data", "processed", "enoe", "exposicion_congelada.json")))
  expect_silent(verifica_congelamiento())
})
