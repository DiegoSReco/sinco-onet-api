# Funciones compartidas para convertir el PDF SINCO 2019 (INEGI) en tablas. No tiene efectos
# secundarios al cargarse. Requiere dplyr, stringr y 00_utils.R ya cargado.

NIVELES <- c("division", "grupo_principal", "subgrupo", "grupo_unitario")

# Normaliza para comparar titulos: minusculas y solo letras/numeros (ignora guiones de corte, espacios).
norm_txt <- function(x) str_replace_all(str_to_lower(x), "[^[:alnum:]]", "")

# Limpia el texto de una pagina: quita encabezado corrido y caracteres de control. Devuelve un tibble
# (linea, pagina_impresa): el numero impreso de pagina aparece como linea con solo digitos o pegado
# al inicio de otra linea (digitos + 4 o mas espacios + texto); se separa del texto.
limpia_lineas <- function(pag_txt) {
  l <- str_split(pag_txt, "\n")[[1]]
  l <- str_replace_all(l, "[\t]", " ")
  l <- str_remove_all(l, "[[:cntrl:]]")
  l <- str_remove_all(l, SINCO_ENCAB)
  l <- str_replace_all(l, "\u00ad$", "-")       # guion suave al fin de linea = guion de corte
  l <- str_remove_all(l, "\u00ad")
  fe <- str_detect(l, "Fe de erratas")           # marca de INEGI en paginas con fe de erratas
  l <- str_remove(l, "[[:space:]]*Fe de erratas")
  pegado <- str_match(l, "^[[:space:]]*([0-9]{1,3})[[:space:]]{4,}([^[:space:]].*)$")
  num <- rep(NA_integer_, length(l))
  ip <- !is.na(pegado[, 1])
  num[ip] <- as.integer(pegado[ip, 2]); l[ip] <- pegado[ip, 3]
  l <- str_trim(l)
  sol <- str_detect(l, "^[0-9]{1,3}$")
  num[sol] <- as.integer(l[sol])
  tibble(linea = l, pagina_impresa = num, solo_num = sol, fe_erratas = fe) |> filter(linea != "")
}

# ---- Catalogo (version abreviada, nivel grupo unitario) -------------------------------------
# Devuelve tibble(sinco_code, nivel, titulo, padre, pdf_page).
parse_sinco_catalogo <- function(pages) {
  lines <- unlist(lapply(seq_along(pages), function(i) str_split(pages[i], "\n")[[1]]))
  pg <- rep(seq_along(pages), vapply(pages, function(p) length(str_split(p, "\n")[[1]]), integer(1)))
  i_abrev_fin <- which(str_detect(lines, "^[[:space:]]*999 Ocupaciones no especificadas[[:space:]]*$"))[1]
  i_fin <- which(str_detect(lines, "^[[:space:]]*9999 Ocupaciones no especificadas[[:space:]]*$"))[1]
  if (is.na(i_abrev_fin) || is.na(i_fin) || i_fin <= i_abrev_fin)
    stop_with_issue("SINCO: no se localiza la estructura", "No se encontraron los marcadores de inicio/fin del listado.")
  idx <- (i_abrev_fin + 1):i_fin
  reg <- lines[idx]; rpg <- pg[idx]
  reg <- str_trim(str_remove_all(reg, "[[:cntrl:]]"))
  has <- str_detect(reg, paste0("^", SINCO_ENCAB))
  reg <- if_else(has, str_remove(reg, paste0("^", SINCO_ENCAB)),
                 str_remove(reg, paste0("[[:space:]]*", SINCO_ENCAB, ".*$")))
  reg <- str_trim(str_replace(reg, "[[:space:]]+Grupo unitario[[:space:]]*$", ""))
  keep <- reg != "" & !str_detect(reg, "^[0-9]{1,3}$") & !str_detect(reg, "^Grupo unitario$")
  reg <- reg[keep]; rpg <- rpg[keep]
  # Errata de formato del PDF (no de contenido): en la pagina del grupo principal 97 se imprime una
  # linea "971 Trabajadores repartidores de mensajeria..." duplicada (corresponde al subgrupo 972,
  # que aparece despues) y "971Trabajadores de paqueteria..." sin espacio.
  dup <- reg == "971 Trabajadores repartidores de mensajer\u00eda y mercanc\u00edas (a pie o en bicicleta)"
  reg <- reg[!dup]; rpg <- rpg[!dup]
  i971 <- str_detect(reg, "^971[^0-9[:space:]]")
  reg[i971] <- paste0("971 ", str_sub(reg[i971], 4))
  es_codigo <- str_detect(reg, "^[0-9]{1,4}[[:space:]]+[^[:space:]]")
  grp <- cumsum(es_codigo)
  reg <- reg[grp > 0]; rpg <- rpg[grp > 0]; grp <- grp[grp > 0]
  unidos <- tapply(reg, grp, function(x) {
    t <- x[1]
    for (y in x[-1]) t <- if (str_detect(t, "-$")) paste0(str_sub(t, 1, -2), y) else paste(t, y)
    t
  })
  pag1 <- tapply(rpg, grp, function(x) x[1])
  tibble(raw = as.character(unidos), pdf_page = as.integer(pag1)) |>
    mutate(sinco_code = str_extract(raw, "^[0-9]{1,4}"),
           titulo = str_squish(str_remove(raw, "^[0-9]{1,4}[[:space:]]+")),
           nivel = NIVELES[nchar(sinco_code)],
           padre = if_else(nchar(sinco_code) > 1, str_sub(sinco_code, 1, -2), NA_character_)) |>
    select(sinco_code, nivel, titulo, padre, pdf_page) |>
    distinct(sinco_code, .keep_all = TRUE)
}

# ---- Cuerpo (version ampliada) ---------------------------------------------------------------
# Rango de paginas fisicas de la version ampliada: desde la portada "Versión ampliada" (+1) hasta la
# pagina previa a la "Tabla de equivalencia SINCO 2011 - 2019".
rango_cuerpo <- function(pages) {
  ini <- which(str_detect(pages, "[(]SINCO[)] 2019[.] Versi\u00f3n ampliada"))
  fin <- which(str_detect(pages, "Tabla de equivalencia SINCO 2011 - 2019"))
  if (length(ini) != 1 || length(fin) != 1)
    stop_with_issue("SINCO: no se localiza la version ampliada", "Marcadores de inicio/fin no unicos.")
  c(ini + 1L, fin - 1L)
}

# Lineas limpias del cuerpo con su pagina fisica. El numero impreso de pagina (linea con solo digitos)
# se retira del texto y se devuelve aparte (attr "impresa": pagina fisica -> numero impreso).
lineas_cuerpo <- function(pages) {
  r <- rango_cuerpo(pages)
  out <- list(); imp <- integer(0); fe <- integer(0)
  for (p in r[1]:r[2]) {
    d <- limpia_lineas(pages[p])
    if (any(d$fe_erratas)) fe <- c(fe, p)
    if (any(!is.na(d$pagina_impresa))) imp[as.character(p)] <- d$pagina_impresa[!is.na(d$pagina_impresa)][1]
    l <- d$linea[!d$solo_num & d$linea != "Anexo" & !(d$fe_erratas & d$linea == "")]
    if (length(l)) out[[length(out) + 1]] <- tibble(pdf_page = p, linea = l)
  }
  res <- bind_rows(out)
  attr(res, "impresa") <- imp
  attr(res, "pag_fe_erratas") <- fe
  res
}

# Localiza los encabezados de cada codigo del catalogo, en orden. Devuelve tibble con fila inicial/final
# del encabezado (el titulo puede ocupar varias lineas) y si el titulo coincide con el del catalogo.
localiza_encabezados <- function(ln, cat) {
  n <- nrow(cat); L <- nrow(ln); k <- 1L; i <- 1L
  ini <- integer(n); fin <- integer(n); tit <- character(n)
  while (i <= L && k <= n) {
    code <- cat$sinco_code[k]
    pat <- paste0("^", code, "(?![0-9])[[:space:]]*")
    if (str_detect(ln$linea[i], pat)) {
      target <- norm_txt(cat$titulo[k])
      acc <- str_remove(ln$linea[i], pat); j <- i
      ok <- FALSE
      repeat {
        a <- norm_txt(acc)
        if (a == target) { ok <- TRUE; break }
        if (!startsWith(target, a) || j - i >= 5 || j >= L) break
        j <- j + 1L; acc <- paste(acc, ln$linea[j])
      }
      if (ok) { ini[k] <- i; fin[k] <- j; tit[k] <- acc; k <- k + 1L; i <- j + 1L; next }
    }
    i <- i + 1L
  }
  if (k <= n) stop_with_issue("SINCO: encabezado no localizado en la version ampliada",
    paste0("No se hallo el encabezado del codigo ", cat$sinco_code[k], " (", cat$titulo[k],
           ") en el orden esperado; se localizaron ", k - 1L, " de ", n, "."))
  tibble(sinco_code = cat$sinco_code, ini = ini, fin = fin, titulo_ampliado = str_squish(tit))
}

# ---- Texto de cada codigo ---------------------------------------------------------------------
# Vocabulario para decidir si un guion de fin de linea es de corte (se elimina) o parte de una palabra
# compuesta (se conserva, p. ej. "economico-administrativas"): se usan las palabras del propio documento.
construye_vocab <- function(lineas) {
  sin_corte <- str_remove(lineas, "[[:alpha:]]+-$")
  w <- str_to_lower(unlist(str_extract_all(sin_corte, "[[:alpha:]]+(?:-[[:alpha:]]+)*")))
  list(plain = unique(w[!str_detect(w, "-")]), hy = unique(w[str_detect(w, "-")]))
}

# Une lineas de un mismo bloque: resuelve guiones de corte y espacios.
une_lineas <- function(x, vocab) {
  if (!length(x)) return("")
  res <- x[1]
  for (y in x[-1]) {
    if (str_detect(res, "[[:alpha:]]-$") && str_detect(y, "^[[:lower:]]")) {
      lw <- str_remove(str_extract(res, "[[:alpha:]]+(?:-[[:alpha:]]+)*-$"), "-$")
      rw <- str_extract(y, "^[[:alpha:]]+")
      hy <- str_to_lower(paste0(lw, "-", rw)); jn <- str_to_lower(paste0(lw, rw))
      conserva <- (hy %in% vocab$hy) && !(jn %in% vocab$plain)
      res <- if (conserva) paste0(res, y) else paste0(str_remove(res, "-$"), y)
    } else res <- paste(res, y)
  }
  str_squish(res)
}

SECCIONES <- c(Ocupaciones = "ocupaciones", Funciones = "funciones", Incluye = "incluye", Excluye = "excluye")

# Divide el texto de cada codigo en descripcion y secciones (ocupaciones / funciones / incluye / excluye).
# Cada seccion es una lista de vinetas (lineas que inician con "•"; las demas continuan la previa).
parse_cuerpo <- function(ln, h) {
  vocab <- construye_vocab(ln$linea)
  n <- nrow(h); L <- nrow(ln)
  desc <- vector("list", n); items <- list(); anom <- list()
  for (k in seq_len(n)) {
    a <- h$fin[k] + 1L; b <- if (k < n) h$ini[k + 1L] - 1L else L
    seg <- if (a <= b) ln[a:b, ] else ln[0, ]
    lab <- str_match(seg$linea, "^(Ocupaciones|Funciones|Incluye|Excluye):?$")[, 2]
    sec <- rep("descripcion", nrow(seg)); cur <- "descripcion"
    for (r in seq_len(nrow(seg))) {
      if (!is.na(lab[r])) cur <- SECCIONES[[lab[r]]]
      sec[r] <- if (!is.na(lab[r])) "etiqueta" else cur
    }
    d <- seg[sec == "descripcion", ]
    desc[[k]] <- tibble(sinco_code = h$sinco_code[k],
                        descripcion = une_lineas(d$linea, vocab),
                        pdf_page_ini = h$pdf_page_ini[k],
                        pdf_page_fin = if (nrow(seg)) max(seg$pdf_page, h$pdf_page_ini[k]) else h$pdf_page_ini[k],
                        secciones = paste(unique(sec[sec != "etiqueta" & sec != "descripcion"]), collapse = ","))
    for (s in unique(sec[!sec %in% c("etiqueta", "descripcion")])) {
      sl <- seg[sec == s, ]
      esb <- str_detect(sl$linea, "^\u2022")
      if (!esb[1]) anom[[length(anom) + 1]] <- tibble(sinco_code = h$sinco_code[k], seccion = s, detalle = "seccion sin vineta inicial", linea = sl$linea[1])
      g <- cumsum(esb); g[g == 0] <- 0L
      # lineas previas a la primera vineta forman un item propio (orden 1)
      g <- if (esb[1]) g else g + 1L
      for (gi in unique(g)) {
        w <- sl[g == gi, ]
        if (nrow(w) > 1) {   # posible vineta perdida: linea con mayuscula inicial tras linea que termina en punto o guion
          sosp <- which(seq_len(nrow(w)) > 1 & str_detect(w$linea, "^[[:upper:]]") & str_detect(c("", w$linea[-nrow(w)]), "[.;-]$"))
          if (length(sosp)) anom[[length(anom) + 1]] <- tibble(sinco_code = h$sinco_code[k], seccion = s,
            detalle = "posible vineta perdida (linea con mayuscula inicial tras punto o guion)", linea = w$linea[sosp[1]])
        }
        txt <- str_remove(w$linea[1], "^\u2022[[:space:]]*")
        txt <- une_lineas(c(txt, w$linea[-1]), vocab)
        items[[length(items) + 1]] <- tibble(sinco_code = h$sinco_code[k], seccion = s,
                                             texto = txt, pdf_page = w$pdf_page[1])
      }
    }
  }
  list(descripcion = bind_rows(desc),
       items = bind_rows(items) |> group_by(sinco_code, seccion) |> mutate(orden = row_number()) |> ungroup(),
       anomalias = bind_rows(anom))
}

# Texto de paginas fisicas first..last en orden de lectura (sin -layout); util para paginas de texto corrido.
pdf_texto_simple <- function(first, last) {
  out <- tempfile(fileext = ".txt")
  system2(Sys.which("pdftotext"), c("-enc", "UTF-8", "-f", first, "-l", last, shQuote(path_raw("sinco_2019.pdf")), shQuote(out)))
  x <- readChar(out, file.size(out), useBytes = TRUE); Encoding(x) <- "UTF-8"
  x <- gsub("\r", "", x, fixed = TRUE)
  for (lig in list(c("ﬁ", "fi"), c("ﬂ", "fl"), c("ﬀ", "ff"))) x <- gsub(lig[1], lig[2], x, fixed = TRUE)
  str_split(x, "\n")[[1]]
}
