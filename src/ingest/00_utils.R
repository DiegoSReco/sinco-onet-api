# Utilidades compartidas de ingesta: raiz del proyecto, descarga, SHA-256, manifiesto.
suppressPackageStartupMessages({
  library(httr2)
  library(digest)
  library(jsonlite)
})

project_root <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", args[grepl("^--file=", args)])
  start <- if (length(f)) dirname(normalizePath(f[1], winslash = "/")) else getwd()
  d <- start
  repeat {
    if (file.exists(file.path(d, "CLAUDE.md"))) return(normalizePath(d, winslash = "/"))
    parent <- dirname(d)
    if (identical(parent, d)) stop("No se encontro la raiz del proyecto (CLAUDE.md).")
    d <- parent
  }
}

path_raw       <- function(...) file.path(project_root(), "data", "raw", ...)
path_processed <- function(...) file.path(project_root(), "data", "processed", ...)
manifest_path  <- function() path_raw("manifest.json")

sha256_file <- function(path) digest(file = path, algo = "sha256", serialize = FALSE)

read_manifest <- function() {
  p <- manifest_path()
  if (!file.exists(p)) return(list())
  fromJSON(p, simplifyVector = FALSE)
}

write_manifest <- function(entries) {
  write(toJSON(entries, auto_unbox = TRUE, pretty = TRUE, null = "null"), manifest_path())
}

# Registra (o verifica) una entrada. Si el id ya existe con otro hash, error (inmutabilidad).
register_manifest <- function(id, url, file, version, descripcion) {
  entries <- read_manifest()
  hash <- sha256_file(file)
  rel <- sub(paste0("^", project_root(), "/"), "", normalizePath(file, winslash = "/"))
  new <- list(id = id, url = url, archivo = rel, version = version,
              descripcion = descripcion,
              fecha_descarga = format(Sys.Date(), "%Y-%m-%d"),
              bytes = file.size(file), sha256 = hash)
  idx <- which(vapply(entries, function(e) identical(e$id, id), logical(1)))
  if (length(idx)) {
    if (!identical(entries[[idx]]$sha256, hash))
      stop("Hash distinto al registrado para ", id, ". Los archivos raw son inmutables; ",
           "crear una version con fecha en el nombre.")
    return(invisible(entries[[idx]]))
  }
  entries[[length(entries) + 1]] <- new
  write_manifest(entries)
  invisible(new)
}

# Descarga a data/raw sin sobrescribir. Si el archivo existe, solo verifica contra el manifiesto.
download_raw <- function(id, url, filename, version, descripcion) {
  dest <- path_raw(filename)
  dir.create(dirname(dest), showWarnings = FALSE, recursive = TRUE)
  if (!file.exists(dest)) {
    tmp <- tempfile()
    message("Descargando ", url)
    request(url) |>
      req_user_agent("sinco-ia-ingest/0.1 (investigacion academica)") |>
      req_timeout(600) |>
      req_perform(path = tmp)
    if (!file.copy(tmp, dest, overwrite = FALSE)) stop("No se pudo escribir ", dest)
  } else {
    message("Ya existe (inmutable, no se sobrescribe): ", dest)
  }
  register_manifest(id, url, dest, version, descripcion)
  dest
}

verify_manifest <- function() {
  ok <- vapply(read_manifest(), function(e) {
    f <- file.path(project_root(), e$archivo)
    file.exists(f) && identical(sha256_file(f), e$sha256)
  }, logical(1))
  ok
}

# Escribe issue y detiene (regla 6).
stop_with_issue <- function(titulo, causa, opciones = NULL) {
  dir <- file.path(project_root(), "docs", "issues")
  dir.create(dir, showWarnings = FALSE, recursive = TRUE)
  f <- file.path(dir, paste0("datos-", format(Sys.Date(), "%Y-%m-%d"), "-", gsub("[^a-z0-9]+", "-", tolower(titulo)), ".md"))
  txt <- c(paste("#", titulo), "", paste("Causa:", causa), "",
           if (!is.null(opciones)) c("Opciones:", paste0(seq_along(opciones), ". ", opciones), ""))
  writeLines(txt, f)
  stop(titulo, ": ", causa, " (ver ", f, ")", call. = FALSE)
}

write_parquet_checked <- function(df, name) {
  dir.create(path_processed(), showWarnings = FALSE, recursive = TRUE)
  arrow::write_parquet(df, path_processed(name))
  invisible(path_processed(name))
}

# ---- Utilidades de lectura del PDF SINCO 2019 -------------------------------------------------
# Devuelve un vector con el texto de cada pagina fisica del PDF (UTF-8, sin CR), extraido con
# pdftotext -layout. Verifica antes el hash del PDF contra el manifiesto.
sinco_pdf_pages <- function() {
  pdf <- path_raw("sinco_2019.pdf")
  m <- Filter(function(e) identical(e$id, "sinco_2019_pdf"), read_manifest())
  if (!file.exists(pdf) || !length(m) || !identical(sha256_file(pdf), m[[1]]$sha256))
    stop_with_issue("SINCO PDF: hash no coincide", "data/raw/sinco_2019.pdf falta o su SHA-256 no coincide con manifest.json.")
  px <- Sys.which("pdftotext")
  if (!nzchar(px)) stop_with_issue("pdftotext no disponible",
    "Se requiere pdftotext para extraer el SINCO del PDF oficial; no esta en el PATH.",
    c("Instalar poppler/xpdf", "Usar un paquete R para PDF (pdftools) previa autorizacion"))
  out <- tempfile(fileext = ".txt")
  system2(px, c("-enc", "UTF-8", "-layout", shQuote(pdf), shQuote(out)))
  x <- readChar(out, file.size(out), useBytes = TRUE)
  Encoding(x) <- "UTF-8"
  x <- gsub("\r", "", x, fixed = TRUE)
  # Correccion de formato (no de contenido): ligaturas tipograficas del PDF a letras separadas.
  for (lig in list(c("ﬁ", "fi"), c("ﬂ", "fl"), c("ﬀ", "ff"), c("ﬃ", "ffi"), c("ﬄ", "ffl")))
    x <- gsub(lig[1], lig[2], x, fixed = TRUE)
  p <- strsplit(x, "\f", fixed = TRUE)[[1]]
  attr(p, "pdftotext") <- trimws(paste(suppressWarnings(system2(px, "-v", stdout = TRUE, stderr = TRUE))[1]))
  p
}

# Encabezado corrido de cada pagina del PDF (se elimina del texto).
SINCO_ENCAB <- "INEGI[.] Sistema Nacional de Clasificación de Ocupaciones 2019[.] SINCO[.]?([[:space:]]*2020[.]?)?"
