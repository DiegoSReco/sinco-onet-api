# Ingesta de datos externos (solo extraccion, sin derivar nada):
#  (a) Probabilidad de computarizacion de Frey y Osborne (2013) por ocupacion SOC 2010 (apendice del paper, 702 filas).
#      NO es exposicion a IA: es "probabilidad de automatizacion (Frey-Osborne)", dato tal como lo publican los autores.
#  (b) Puente oficial del O*NET Center entre O*NET-SOC 2010 y O*NET-SOC 2019 (version crosswalk de la taxonomia).
# Produce data/processed/frey_osborne_probabilidades.parquet y puente_onet_soc2019_soc2010.parquet.
suppressPackageStartupMessages({ library(dplyr); library(stringr); library(arrow); library(readr) })
.d <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]), winslash = "/"))
source(file.path(.d, "00_utils.R"))

# ---- (a) Frey & Osborne --------------------------------------------------------------------------
FO_URL <- "https://www.oxfordmartin.ox.ac.uk/downloads/academic/The_Future_of_Employment.pdf"
fo_pdf <- download_raw("frey_osborne_2013_pdf", FO_URL, "frey_osborne_future_of_employment_2013.pdf",
  "Frey & Osborne, The Future of Employment (Oxford Martin School working paper, 17 sept 2013)",
  "Apendice (pp. 57-72 del PDF): 702 ocupaciones SOC 2010 con rango, probabilidad de computarizacion y etiqueta de entrenamiento. Licencia: el PDF no declara ninguna; derechos de los autores/Oxford Martin (uso academico con cita; no verificado).")
px <- Sys.which("pdftotext"); if (!nzchar(px)) stop_with_issue("pdftotext no disponible", "Se requiere pdftotext.")
leer <- function(first, last, layout) {
  out <- tempfile(fileext = ".txt")
  system2(px, c(if (layout) "-layout", "-enc", "UTF-8", "-f", first, "-l", last, shQuote(fo_pdf), shQuote(out)))
  x <- readChar(out, file.size(out), useBytes = TRUE); Encoding(x) <- "UTF-8"
  for (lig in list(c("ﬁ", "fi"), c("ﬂ", "fl"), c("ﬀ", "ff"))) x <- gsub(lig[1], lig[2], x, fixed = TRUE)  # ligaturas
  gsub("\r", "", x, fixed = TRUE)
}
tot <- leer(1, 100, FALSE)
pgs <- str_split(tot, "\f")[[1]]
p_ini <- which(str_detect(pgs, "Rank Probability"))
if (length(p_ini) != 16 || !identical(p_ini, p_ini[1]:p_ini[16]))
  stop_with_issue("Frey-Osborne: apendice no localizado", paste("Paginas con 'Rank Probability':", paste(p_ini, collapse = ",")))

filas <- list()
for (p in p_ini) {
  s <- pgs[p]
  i_soc <- str_locate(s, "SOC code")[1, 1]; i_occ <- str_locate(s, "\nOccupation")[1, 1]
  rk <- str_sub(s, str_locate(s, "Rank Probability")[1, 1], i_soc - 1L)
  socs <- str_extract_all(str_sub(s, i_soc, i_occ), "[0-9]{2}-[0-9]{4}")[[1]]
  m <- str_locate_all(rk, "(?<![0-9.])[0-9]{1,3}[.][[:space:]]+(0[.][0-9]+|1)(?![0-9.])")[[1]]
  ent <- str_match(str_sub(rk, m[, 1], m[, 2]), "([0-9]+)[.][[:space:]]+([0-9.]+)")
  lab <- vapply(seq_len(nrow(m)), function(k) {
    seg <- str_sub(rk, m[k, 2] + 1L, if (k < nrow(m)) m[k + 1L, 1] - 1L else nchar(rk))
    mm <- str_match(seg, "^[[:space:]]*([01])[[:space:]]*$")[1, 2]; as.integer(mm)
  }, integer(1))
  if (length(socs) != nrow(m))
    stop_with_issue("Frey-Osborne: filas y codigos SOC no cuadran", paste0("Pagina ", p, ": ", nrow(m), " rangos vs ", length(socs), " codigos."))
  # nombres: del texto con -layout (una linea por codigo SOC)
  ly <- str_split(leer(p, p, TRUE), "\n")[[1]]
  ly <- ly[str_detect(ly, "[0-9]{2}-[0-9]{4}[[:space:]]{2,}")]
  nm <- str_match(ly, "([0-9]{2}-[0-9]{4})[[:space:]]{2,}([^[:space:]].*?)[[:space:]]*$")
  if (!identical(nm[, 2], socs))
    stop_with_issue("Frey-Osborne: orden de codigos SOC distinto entre extracciones", paste("Pagina", p))
  filas[[length(filas) + 1]] <- tibble(rank_fo = as.integer(ent[, 2]), probabilidad_automatizacion_fo = as.numeric(ent[, 3]),
                                       etiqueta_entrenamiento = lab, soc_2010 = socs, prefijo = str_squish(nm[, 3]), pdf_page = p)
}
fo <- bind_rows(filas)
# Nombres completos: con -layout los nombres largos se parten en varias lineas (solo la primera lleva el codigo SOC);
# el texto en orden de lectura trae la columna "Occupation" completa pero sin separadores. Se segmenta el texto completo
# usando como anclas los prefijos de cada linea (en orden); se verifica que cada ancla aparezca donde se espera.
fo$ocupacion <- NA_character_
for (p in p_ini) {
  s <- pgs[p]; i_occ <- str_locate(s, "
Occupation")[1, 1]
  txt <- str_squish(str_remove(str_sub(s, i_occ + 1L), "^Occupation"))
  txt <- str_squish(str_remove(txt, "[[:space:]][0-9]{2}$"))   # numero de pagina impreso
  idx <- which(fo$pdf_page == p); pref <- str_remove(fo$prefijo[idx], "-$"); cur <- 1L; ini <- integer(length(idx))
  for (k in seq_along(idx)) {
    if (substr(txt, cur, cur + nchar(pref[k]) - 1L) != pref[k])
      stop_with_issue("Frey-Osborne: nombre de ocupacion no localizado", paste0("Pagina ", p, ", ", fo$soc_2010[idx[k]], ": ", pref[k]))
    ini[k] <- cur
    if (k < length(idx)) {
      nx <- str_locate(str_sub(txt, cur + nchar(pref[k])), fixed(pref[k + 1L]))[1, 1]
      if (is.na(nx)) stop_with_issue("Frey-Osborne: ancla siguiente no hallada", paste0("Pagina ", p, ", ", fo$soc_2010[idx[k]]))
      cur <- cur + nchar(pref[k]) + nx - 1L
    }
  }
  fin <- c(ini[-1] - 1L, nchar(txt))
  fo$ocupacion[idx] <- str_trim(substring(txt, ini, fin))
}
fo <- fo |> select(rank_fo, soc_2010, ocupacion, probabilidad_automatizacion_fo, etiqueta_entrenamiento, pdf_page) |>
  mutate(fuente = "Frey & Osborne (2013), The Future of Employment, apendice")

# Comprobaciones de integridad (si fallan: issue y se detiene)
chk <- c(nrow(fo) == 702, identical(fo$rank_fo, 1:702), !anyNA(fo$ocupacion),
         all(fo$probabilidad_automatizacion_fo >= 0 & fo$probabilidad_automatizacion_fo <= 1),
         !is.unsorted(fo$probabilidad_automatizacion_fo), sum(!is.na(fo$etiqueta_entrenamiento)) == 70)
nombres <- c("702 filas", "rangos 1..702", "sin nombres vacios", "probabilidad en [0,1]", "orden no decreciente por probabilidad", "70 etiquetas de entrenamiento")
if (!all(chk)) stop_with_issue("Frey-Osborne: validacion fallida", paste("No cumple:", paste(nombres[!chk], collapse = "; ")))
if (any(str_detect(fo$ocupacion, "[0-9]")) || any(nchar(fo$ocupacion) < 4))
  stop_with_issue("Frey-Osborne: nombres de ocupacion sospechosos", "Hay nombres con digitos o demasiado cortos.")
write_parquet_checked(fo, "frey_osborne_probabilidades.parquet")
message("OK frey_osborne_probabilidades: ", nrow(fo), " filas; SOC 2010 unicos: ", n_distinct(fo$soc_2010))

# ---- (b) Puente O*NET-SOC 2010 <-> O*NET-SOC 2019 ----------------------------------------------
PU_URL <- "https://www.onetcenter.org/taxonomy/2019/walk/2010_to_2019_Crosswalk.csv?fmt=csv"   # enlace exacto de la pagina oficial (sin ?fmt=csv devuelve HTML)
pu_csv <- download_raw("onet_soc_2010_to_2019_crosswalk", PU_URL, "onet_soc_2010_to_2019_crosswalk.csv",
  "O*NET-SOC 2010 a O*NET-SOC 2019 (O*NET Center, taxonomia 2019)",
  "Crosswalk oficial de versiones de la taxonomia O*NET-SOC (CSV). Pagina: https://www.onetcenter.org/taxonomy/2019/walk.html. Licencia O*NET: CC BY 4.0.")
if (str_detect(readLines(pu_csv, n = 1, warn = FALSE), regex("<!DOCTYPE|<html", ignore_case = TRUE)))
  stop_with_issue("Puente O*NET: la descarga es HTML, no CSV", paste("URL:", PU_URL))
pu <- read_csv(pu_csv, col_types = cols(.default = col_character()), show_col_types = FALSE)
esperado <- c("O*NET-SOC 2010 Code", "O*NET-SOC 2010 Title", "O*NET-SOC 2019 Code", "O*NET-SOC 2019 Title")
if (!identical(names(pu), esperado)) stop_with_issue("Puente O*NET: columnas inesperadas", paste(names(pu), collapse = " | "))
pu <- pu |> transmute(onet_soc_2010_code = `O*NET-SOC 2010 Code`, onet_soc_2010_titulo = `O*NET-SOC 2010 Title`,
                      onet_soc_2019_code = `O*NET-SOC 2019 Code`, onet_soc_2019_titulo = `O*NET-SOC 2019 Title`) |>
  distinct() |>
  # SOC 2010 = los 7 primeros caracteres del codigo O*NET-SOC 2010 (XX-XXXX.YY extiende a SOC XX-XXXX); corte estructural, no inferencia
  mutate(soc_2010 = str_sub(onet_soc_2010_code, 1, 7), fuente = "O*NET Center, 2010_to_2019_Crosswalk.csv")
if (anyNA(pu) || !all(str_detect(pu$onet_soc_2010_code, "^[0-9]{2}-[0-9]{4}[.][0-9]{2}$")) || !all(str_detect(pu$onet_soc_2019_code, "^[0-9]{2}-[0-9]{4}[.][0-9]{2}$")))
  stop_with_issue("Puente O*NET: codigos con formato inesperado", "Hay NA o codigos fuera de XX-XXXX.YY.")
write_parquet_checked(pu, "puente_onet_soc2019_soc2010.parquet")
message("OK puente_onet_soc2019_soc2010: ", nrow(pu), " filas")
