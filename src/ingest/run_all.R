# Ejecuta la ingesta en orden: 01 (jerarquia SINCO), 04 (texto SINCO), 02 (crosswalk), 03 (tareas O*NET), 05 (Frey-Osborne y puente O*NET-SOC).
# Se detiene ante el primer error inesperado. El paso 02 esta BLOQUEADO POR DISENO (no existe tabla oficial
# SINCO-CIUO-08; ver docs/issues/datos-2026-10-19-crosswalk-sinco-isco08-onet-bloqueado.md): ese bloqueo
# conocido se reporta como aviso y la ingesta continua. Cualquier otro fallo detiene todo.
args <- commandArgs(FALSE)
dir <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", args, value = TRUE)[1]), winslash = "/"))
rscript <- file.path(R.home("bin"), "Rscript")
BLOQUEO_CONOCIDO <- "Crosswalk SINCO-ISCO08-ONET bloqueado"
estado <- character()
for (s in c("01_sinco.R", "04_sinco_texto.R", "02_crosswalk.R", "03_tareas_onet.R", "05_frey_osborne.R")) {
  message("== Ejecutando ", s)
  out <- suppressWarnings(system2(rscript, shQuote(file.path(dir, s)), stdout = TRUE, stderr = TRUE))
  status <- attr(out, "status"); if (is.null(status)) status <- 0L
  cat(grep("package .* was built under|^Aviso:?$|^Warning", out, value = TRUE, invert = TRUE), sep = "\n")
  if (status == 0L) { estado[s] <- "OK"; next }
  if (s == "02_crosswalk.R" && any(grepl(BLOQUEO_CONOCIDO, out, fixed = TRUE))) {
    message("AVISO: ", s, " bloqueado por diseno (decision metodologica pendiente); se continua.")
    estado[s] <- "BLOQUEADO_CONOCIDO"; next
  }
  stop("Fallo ", s, " (estado ", status, "). Se detiene la ingesta.", call. = FALSE)
}
message("== Ingesta completa: ", paste(names(estado), estado, sep = "=", collapse = "; "))
