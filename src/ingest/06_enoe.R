# Ingesta de la ENOE para el analisis de exposicion (decision 020): 2022T3 (ENOE-N) y 2025T3 (ENOE).
#  1. Congela la exposicion (compuerta G1 de 013): hash de la tabla MAIN antes de tocar un solo microdato.
#  2. Descarga los ZIP de INEGI a data/raw/enoe/ (inmutables, con hash en data/raw/manifest.json).
#  3. Con el paquete `enoeR` (DiegoSReco/enoeR): enoe_load() de SDEM y COE1T y enoe_join(level = "person"): una fila por persona.
#  4. Escribe data/processed/enoe/enoe_personas_<anio>T<trim>.parquet y un registro de integridad.
# Los microdatos NO se publican (013 sec. 11; .gitignore). Este script solo mira controles de integridad: no calcula exposicion.
suppressPackageStartupMessages({ library(data.table); library(arrow); library(enoeR); library(jsonlite) })
.d <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]), winslash = "/"))
source(file.path(.d, "00_utils.R"))

PERIODOS <- data.frame(anio = c(2022L, 2025L), trim = c(3L, 3L))
BASE_URL <- "https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos"
url_zip <- function(a, q) {   # mismas reglas que enoeR:::.build_url
  if (a >= 2023L) sprintf("%s/enoe_%d_trim%d_csv.zip", BASE_URL, a, q) else sprintf("%s/enoe_n_%d_trim%d_csv.zip", BASE_URL, a, q)
}
dir_out <- path_processed("enoe"); dir.create(dir_out, showWarnings = FALSE, recursive = TRUE)

# ---- 1. Congelar la exposicion (G1) --------------------------------------------------------------------------------
main_pq  <- path_processed("main_sinco_comp_table.parquet")
main_meta <- path_processed("main_sinco_comp_table_meta.json")
if (!file.exists(main_pq)) stop_with_issue("Exposicion no congelada", "Falta data/processed/main_sinco_comp_table.parquet (python -m src.main_sinco_comp_table).")
fz_path <- file.path(dir_out, "exposicion_congelada.json")
hash_main <- sha256_file(main_pq)
if (file.exists(fz_path)) {
  fz <- fromJSON(fz_path, simplifyVector = FALSE)
  if (!identical(fz$main_sha256, hash_main))
    stop_with_issue("Exposicion congelada distinta", paste0("La tabla MAIN cambio desde el congelamiento (", fz$fecha_congelamiento,
      "). Registrar la desviacion (013 sec. 14) y congelar de nuevo con una decision nueva."))
  message("Exposicion ya congelada (", fz$fecha_congelamiento, "), hash coincide.")
} else {
  mm <- fromJSON(main_meta, simplifyVector = FALSE)
  fz <- list(decision = "020", fecha_congelamiento = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
             main_sha256 = hash_main, main_meta_sha256 = sha256_file(main_meta), main_version = mm$version,
             corridas_base = mm$corridas, modelo_embeddings = mm$modelo_embeddings_principal,
             medida_principal = "exp_idx_media_modelos (promedio de exposure_class, mapa 0/0.5/1, media simple de Haiku, Sonnet y Opus)",
             medidas_comparacion = c("alfa_S_media_modelos", "beta_S_media_modelos", "cota_sup_S_media_modelos"),
             sensibilidad = c("exp_idx_haiku", "exp_idx_sonnet", "exp_idx_opus", "b1_exp_idx"),
             regla = "La ENOE no modifica ningun campo de esta exposicion (013 sec. 3).")
  write(toJSON(fz, auto_unbox = TRUE, pretty = TRUE), fz_path)
  message("Exposicion congelada: ", substr(hash_main, 1, 16), "...")
}

# ---- 2 y 3. Descarga, carga y union a nivel persona ---------------------------------------------------------------
registro <- list()
for (i in seq_len(nrow(PERIODOS))) {
  a <- PERIODOS$anio[i]; q <- PERIODOS$trim[i]; tag <- sprintf("%dT%d", a, q)
  u <- url_zip(a, q)
  zip <- download_raw(sprintf("enoe_%d_t%d_csv_zip", a, q), u, file.path("enoe", basename(u)),
    sprintf("INEGI, ENOE%s %d trimestre %d (microdatos csv)", if (a <= 2022L) "-N" else "", a, q),
    "Microdatos de la ENOE (SDEM, COE1T, COE2T, HOG, VIV). Insumo del analisis de exposicion (decision 020). No se publica en el repositorio.")
  message("== ", tag, ": enoe_load(sdem, coe1t) + enoe_join(level = 'person')")
  tablas <- enoeR::enoe_load(a, q, tables = c("sdem", "coe1t"), quiet = FALSE)
  personas <- enoeR::enoe_join(tablas, level = "person")
  chk <- attr(personas, "enoe_checks")
  personas <- as.data.table(personas)
  personas[, periodo := tag]
  out <- file.path(dir_out, sprintf("enoe_personas_%s.parquet", tag))
  arrow::write_parquet(personas, out)
  registro[[tag]] <- list(periodo = tag, zip = sub(paste0("^", project_root(), "/"), "", zip), zip_sha256 = sha256_file(zip),
    filas_sdem = nrow(tablas$sdem), filas_coe1t = nrow(tablas$coe1t), filas_union = nrow(personas), columnas = ncol(personas),
    checks = if (is.null(chk)) NULL else as.data.frame(chk), parquet = sub(paste0("^", project_root(), "/"), "", out))
  message("   filas SDEM ", nrow(tablas$sdem), " | COE1T ", nrow(tablas$coe1t), " | union ", nrow(personas), " x ", ncol(personas))
  rm(tablas, personas); gc(verbose = FALSE)
}
write(toJSON(registro, auto_unbox = TRUE, pretty = TRUE, dataframe = "rows"), file.path(dir_out, "enoe_integridad.json"))
message("== Ingesta ENOE completa. Registro: data/processed/enoe/enoe_integridad.json")
