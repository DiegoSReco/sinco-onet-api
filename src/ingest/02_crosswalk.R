# Crosswalk SINCO 2019 - ISCO-08 - O*NET-SOC. Produce data/processed/crosswalk.parquet
# (sinco_code, isco08_code, onet_soc_code, tipo_relacion, notas).
# ESTADO: BLOQUEADO. No existe (hasta donde se pudo verificar) una tabla oficial SINCO 2019 - CIUO-08
# publicada por INEGI. Si se descarga y registra la tabla oficial BLS ISCO-08 -> SOC 2010 (el cliente
# R/httr2 la obtiene; curl con UA por defecto recibe 403), pero falta el eslabon SINCO -> ISCO-08 y el
# paso SOC 2010 -> O*NET-SOC es 1:N (decision metodologica). Este script no inventa correspondencias:
# se detiene con un issue (reglas 2, 6 y 8).
suppressPackageStartupMessages({ library(dplyr); library(arrow) })
source(file.path(dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]), winslash = "/")), "00_utils.R"))

BLS_URL <- "https://www.bls.gov/soc/ISCO_SOC_Crosswalk.xls"
f_sinco_isco <- Filter(file.exists, c(path_raw("sinco2019_ciuo08.xlsx"), path_raw("sinco2019_ciuo08.csv")))

bls <- tryCatch(
  download_raw("bls_isco08_soc2010", BLS_URL, "bls_isco08_soc2010.xls", "BLS ISCO-08 a SOC 2010 (2012)",
               "Crosswalk oficial BLS ISCO-08 a 2010 SOC"),
  error = function(e) NULL)

causas <- c(
  if (is.null(bls)) paste0("La descarga de ", BLS_URL, " fallo."),
  if (!length(f_sinco_isco)) "No hay tabla oficial SINCO 2019 - CIUO-08: el PDF del SINCO 2019 no incluye correspondencia con CIUO-08 y no se encontro otra publicada por INEGI/SNIEG."
)
if (length(causas))
  stop_with_issue("Crosswalk SINCO-ISCO08-ONET bloqueado", paste(causas, collapse = " "),
    c("Proveer manualmente (decision humana) la tabla SINCO-CIUO-08 oficial, o solicitarla a INEGI (atencion.usuarios@inegi.org.mx).",
      "El XLS oficial de BLS ISCO-08 -> SOC 2010 ya esta en data/raw/ (ver manifest.json); falta el eslabon SINCO -> ISCO-08.",
      "Decision metodologica (no tomada por este agente): construir SINCO-ISCO por mapeo manual/semi-automatico a nivel de titulos; requiere registro en docs/decisions/.",
      "Alternativa para ISCO-08 a O*NET-SOC: la cadena ISCO-08 -> SOC 2010 (BLS) -> O*NET-SOC 2019 (taxonomia O*NET) es 1:N y N:1; la resolucion es decision de metodologia."))
stop("Insumos presentes pero la logica de union no esta implementada: requiere decision metodologica previa.")
