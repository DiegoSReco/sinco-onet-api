# Medida de exposicion en la muestra de la ENOE: 2022T3 y 2025T3 (decision 020). Script en R porque la union SDEM + COE1T usa `enoeR`.
#
# Entradas (de src/ingest/06_enoe.R y de la tabla MAIN congelada):
#   data/processed/enoe/enoe_personas_2022T3.parquet, enoe_personas_2025T3.parquet   (una fila por persona; p3 = ocupacion principal, SINCO)
#   data/processed/main_sinco_comp_table.parquet                                       (exposicion por grupo unitario SINCO, hash congelado)
# Salidas en data/processed/enoe/ (NO se publican: microdatos, 013 sec. 11):
#   enoe_exposicion_personas_2022T3_2025T3.parquet   TABLA DE LA MUESTRA COMPLETA de los dos periodos, con la exposicion de cada persona ocupada
#   enoe_exposicion_resumen.csv                      media, cuantiles, proporciones con exposicion alta e intervalos, por periodo y estrato
#   enoe_exposicion_diferencias.csv                  2025T3 menos 2022T3 por estrato, con intervalo
#   enoe_exposicion_cobertura.csv                    cobertura de la union ocupacion -> catalogo SINCO
#   enoe_exposicion_cambio_por_grupo.csv             contribucion de cada grupo SINCO al cambio de la media (composicion ocupacional)
#   enoe_exposicion_meta.json                        parametros, semilla, hashes, versiones
# Todo se lee como: exposicion teorica por anotacion de modelos, sin validar; consistencia entre modelos, no exactitud. La exposicion es
# constante dentro de un grupo SINCO: cualquier diferencia entre estratos o periodos es COMPOSICION OCUPACIONAL (no un cambio en ninguna ocupacion).
#
#   Rscript src/enoe/exposicion_enoe.R
suppressPackageStartupMessages({ library(data.table); library(arrow); library(jsonlite); library(digest) })

# ---- parametros fijados antes de calcular (decision 020, sec. 4) -------------------------------------------------------------------
PARAM <- list(periodos = c("2022T3", "2025T3"), edad_min = 15L, semilla = 20261026L, B = 200L, nivel = 0.90,
              n_min = 30L, cv_max = 0.30, umbrales = c(0.25, 0.50, 0.75), cuantiles = c(0.10, 0.25, 0.50, 0.75, 0.90),
              medidas = c(E = "exp_idx_media_modelos", alfa_S = "alfa_S_media_modelos", beta_S = "beta_S_media_modelos", cota_sup_S = "cota_sup_S_media_modelos",
                          E_haiku = "exp_idx_haiku", E_sonnet = "exp_idx_sonnet", E_opus = "exp_idx_opus"))
ROTULO <- "Exposicion teorica por anotacion de modelos (Haiku, Sonnet, Opus), sin validar. Mide consistencia entre modelos, no exactitud; no es riesgo de perdida de empleo."

raiz_proyecto <- function() {
  f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
  d <- if (length(f)) dirname(normalizePath(f[1], winslash = "/")) else normalizePath(getwd(), winslash = "/")
  repeat {
    if (file.exists(file.path(d, "CLAUDE.md"))) return(d)
    if (identical(dirname(d), d)) stop("No se encontro la raiz del proyecto (CLAUDE.md).")
    d <- dirname(d)
  }
}
P <- function(...) file.path(raiz_proyecto(), "data", "processed", ...)

# ---- estadisticos ponderados --------------------------------------------------------------------------------------------------------
wmean <- function(x, w) sum(w * x) / sum(w)
# Cuantil ponderado: inverso de la ecdf ponderada, sin interpolacion (013 sec. 7): el menor x con ecdf >= p.
wquantile <- function(x, w, p) {
  o <- order(x); x <- x[o]; cw <- cumsum(w[o]) / sum(w)
  vapply(p, function(pp) x[which(cw >= pp - 1e-12)[1]], numeric(1))
}

# Multiplicadores del bootstrap reescalado de Rao y Wu: en cada estrato de diseno con n_h UPM se remuestrean n_h - 1 UPM con reemplazo y se reescala
# el factor por n_h / (n_h - 1). Estratos con una sola UPM no aportan varianza (multiplicador 1). Devuelve una matriz UPM x B.
multiplicadores_rw <- function(estrato, B, semilla) {
  set.seed(semilla)
  M <- matrix(1, nrow = length(estrato), ncol = B)
  for (h in unique(estrato)) {
    idx <- which(estrato == h); n <- length(idx)
    if (n >= 2L) M[idx, ] <- rmultinom(B, size = n - 1L, prob = rep(1 / n, n)) * (n / (n - 1))
  }
  M
}

# ---- insumos ------------------------------------------------------------------------------------------------------------------------------
verifica_congelamiento <- function() {
  fz <- fromJSON(P("enoe", "exposicion_congelada.json"), simplifyVector = FALSE)
  h <- digest(file = P("main_sinco_comp_table.parquet"), algo = "sha256", serialize = FALSE)
  if (!identical(h, fz$main_sha256)) stop("La tabla MAIN cambio desde el congelamiento (decision 020): registrar la desviacion antes de seguir.")
  fz
}

carga_personas <- function() {
  claves <- c("ent", "con", "v_sel", "n_hog", "h_mud", "n_ren", "cd_a", "tipo", "mes_cal", "ca")
  vars <- c(claves, "periodo", "r_def", "c_res", "eda", "sex", "cs_p13_1", "fac_tri", "upm", "est_d_tri", "clase1", "clase2", "emp_ppal", "tue_ppal", "rama", "ingocup", "p3")
  rbindlist(lapply(PARAM$periodos, function(t) as.data.table(read_parquet(P("enoe", sprintf("enoe_personas_%s.parquet", t)), col_select = any_of(vars)))), fill = TRUE)
}

prepara <- function(d, main) {
  d <- copy(d)
  d[, poblacion := (clase2 == 1 & r_def == 0 & c_res %in% c(1, 3) & eda >= PARAM$edad_min) %in% TRUE]   # ocupados 15+, entrevista completa, residentes (reglas de INEGI)
  d[, sinco_code := fifelse(poblacion & !is.na(p3), sprintf("%04d", as.integer(round(p3))), NA_character_)]
  mm <- main[, c("sinco_code", "tiene_anotacion", unname(PARAM$medidas)), with = FALSE]
  d <- merge(d, mm, by = "sinco_code", all.x = TRUE, sort = FALSE)
  d[, cobertura := fcase(!poblacion, "fuera_de_poblacion",
                         is.na(sinco_code), "sin_codigo",
                         is.na(tiene_anotacion), "codigo_fuera_de_catalogo",
                         !tiene_anotacion, "grupo_sin_funciones",
                         default = "con_medida")]
  d[, con_medida := cobertura == "con_medida"]
  d[, division := fifelse(is.na(sinco_code), NA_character_, substr(sinco_code, 1, 1))]
  d[, sexo := fcase(sex == 1, "hombre", sex == 2, "mujer", default = "no_especificado")]
  d[, edad_grupo := as.character(cut(eda, c(14, 24, 34, 44, 54, 64, Inf), labels = c("15-24", "25-34", "35-44", "45-54", "55-64", "65+")))]
  # Escolaridad (cs_p13_1; agrupacion PROVISIONAL, a confirmar con el diccionario de INEGI): normal y carrera tecnica en media superior
  d[, escolaridad := fcase(cs_p13_1 %in% 0:2, "hasta_primaria", cs_p13_1 == 3, "secundaria", cs_p13_1 %in% 4:6, "media_superior",
                           cs_p13_1 %in% 7:9, "superior", default = "no_especificado")]
  d[, formalidad := fcase(emp_ppal == 1, "informal", emp_ppal == 2, "formal", default = "no_especificado")]
  d[, entidad := sprintf("%02d", as.integer(ent))]
  d
}

# ---- estimacion por dominio -------------------------------------------------------------------------------------------------------------
# V: matriz de valores (n x k) de la poblacion con medida; devuelve estimacion puntual y replicas bootstrap de las medias y de las
# proporciones sobre umbral para el dominio `mask`.
estima_dominio <- function(w, V, upm_idx, nupm, M, mask) {
  S <- matrix(0, nrow = nupm, ncol = ncol(V) + 1L, dimnames = list(NULL, c(colnames(V), "w")))
  ww <- w[mask]; ix <- upm_idx[mask]
  agg <- rowsum(cbind(V[mask, , drop = FALSE] * ww, ww), group = ix, reorder = FALSE)
  S[as.integer(rownames(agg)), ] <- agg
  pt <- colSums(S); punto <- pt[seq_len(ncol(V))] / pt[ncol(V) + 1L]
  R <- crossprod(M, S)                                   # B x (k + 1): totales de cada replica
  list(punto = punto, boot = R[, seq_len(ncol(V)), drop = FALSE] / R[, ncol(V) + 1L], peso = pt[ncol(V) + 1L])
}

main <- function() {
  fz <- verifica_congelamiento()
  main_t <- as.data.table(read_parquet(P("main_sinco_comp_table.parquet")))
  d <- prepara(carga_personas(), main_t)
  message("Personas: ", format(nrow(d), big.mark = ","), " | ocupados 15+: ", format(sum(d$poblacion), big.mark = ","))

  # --- tabla de la muestra completa (ambos periodos) -------------------------------------------------------------------------------------
  setnames(d, unname(PARAM$medidas), names(PARAM$medidas))    # nombres cortos: E, alfa_S, beta_S, cota_sup_S, E_haiku, E_sonnet, E_opus
  cols_pers <- c(intersect(c("periodo", "ent", "con", "v_sel", "n_hog", "h_mud", "n_ren", "cd_a", "tipo", "mes_cal", "ca", "fac_tri", "upm", "est_d_tri", "r_def", "c_res",
                             "clase1", "clase2", "eda", "sexo", "escolaridad", "formalidad", "tue_ppal", "rama", "ingocup", "p3", "poblacion", "sinco_code", "division",
                             "cobertura"), names(d)), names(PARAM$medidas))
  pers <- copy(d[, ..cols_pers])
  pers[, rotulo := ROTULO]
  write_parquet(pers, P("enoe", "enoe_exposicion_personas_2022T3_2025T3.parquet"))

  # --- cobertura ---------------------------------------------------------------------------------------------------------------------------------
  cob <- d[poblacion == TRUE, .(n_muestra = .N, n_ponderado = sum(fac_tri)), by = .(periodo, cobertura)]
  cob[, pct_ponderado := 100 * n_ponderado / sum(n_ponderado), by = periodo]
  fwrite(cob[order(periodo, -n_ponderado)], P("enoe", "enoe_exposicion_cobertura.csv"))

  # --- estratos ------------------------------------------------------------------------------------------------------------------------------------
  estratos <- c("total", "sexo", "edad_grupo", "escolaridad", "formalidad", "entidad", "division")
  d[, total := "todos"]
  medn <- names(PARAM$medidas); th <- PARAM$umbrales
  filas <- list(); difs <- list(); rep_pe <- list()
  for (pe in PARAM$periodos) {
    s <- d[periodo == pe]; s <- s[!is.na(fac_tri) & !is.na(upm) & !is.na(est_d_tri)]
    clave <- paste(s$est_d_tri, s$upm); upm_ids <- unique(clave)
    upm_idx <- match(clave, upm_ids); est_upm <- s$est_d_tri[match(upm_ids, clave)]
    M <- multiplicadores_rw(est_upm, PARAM$B, PARAM$semilla + match(pe, PARAM$periodos))
    pm <- s[con_medida == TRUE]                                           # poblacion con medida; los dominios se evaluan dentro de s completa
    V <- cbind(as.matrix(pm[, ..medn]), sapply(th, function(t) as.numeric(pm$E >= t)))
    colnames(V) <- c(medn, paste0("sobre_", th))
    ixp <- match(paste(pm$est_d_tri, pm$upm), upm_ids)
    for (es in estratos) for (cat in sort(unique(na.omit(pm[[es]])))) {
      mask <- pm[[es]] == cat
      r <- estima_dominio(pm$fac_tri, V, ixp, length(upm_ids), M, mask)
      q <- wquantile(pm$E[mask], pm$fac_tri[mask], PARAM$cuantiles)
      a <- (1 - PARAM$nivel) / 2
      se <- apply(r$boot, 2, sd); lo <- apply(r$boot, 2, quantile, a); hi <- apply(r$boot, 2, quantile, 1 - a)
      n_m <- sum(mask)
      cv <- se["E"] / r$punto["E"]
      pub <- n_m >= PARAM$n_min && is.finite(cv) && cv <= PARAM$cv_max
      # pob. total del estrato (con y sin medida) para la cobertura por estrato
      tot_e <- sum(s$fac_tri[s$poblacion & s[[es]] == cat], na.rm = TRUE)
      filas[[length(filas) + 1L]] <- data.table(
        periodo = pe, estrato = es, categoria = cat, n_muestra = n_m, n_ponderado = r$peso, pct_cobertura = 100 * r$peso / tot_e,
        media_E = r$punto["E"], ee_E = se["E"], ic_lo_E = lo["E"], ic_hi_E = hi["E"], cv_E = cv,
        p10_E = q[1], p25_E = q[2], mediana_E = q[3], p75_E = q[4], p90_E = q[5],
        media_alfa_S = r$punto["alfa_S"], media_beta_S = r$punto["beta_S"], media_cota_sup_S = r$punto["cota_sup_S"],
        ic_lo_cota_sup_S = lo["cota_sup_S"], ic_hi_cota_sup_S = hi["cota_sup_S"],
        media_E_haiku = r$punto["E_haiku"], media_E_sonnet = r$punto["E_sonnet"], media_E_opus = r$punto["E_opus"],
        rango_E_modelos = max(r$punto[c("E_haiku", "E_sonnet", "E_opus")]) - min(r$punto[c("E_haiku", "E_sonnet", "E_opus")]),
        pct_sobre_0.25 = 100 * r$punto["sobre_0.25"], pct_sobre_0.50 = 100 * r$punto["sobre_0.5"], pct_sobre_0.75 = 100 * r$punto["sobre_0.75"],
        ic_lo_sobre_0.50 = 100 * lo["sobre_0.5"], ic_hi_sobre_0.50 = 100 * hi["sobre_0.5"], publicable = pub)
      rep_pe[[paste(pe, es, cat)]] <- list(punto = r$punto, boot = r$boot, n = n_m)
    }
  }
  res <- rbindlist(filas)
  # Celdas no publicables: se conserva la fila pero se vacian las estimaciones (013 sec. 7)
  num <- setdiff(names(res), c("periodo", "estrato", "categoria", "n_muestra", "n_ponderado", "pct_cobertura", "publicable"))
  res[publicable == FALSE, (num) := NA_real_]
  fwrite(res[order(estrato, categoria, periodo)], P("enoe", "enoe_exposicion_resumen.csv"))

  # --- diferencias 2025T3 - 2022T3 (replicas independientes: no comparten viviendas) --------------------------------------------------------
  p0 <- PARAM$periodos[1]; p1 <- PARAM$periodos[2]; a <- (1 - PARAM$nivel) / 2
  for (k in names(rep_pe)[startsWith(names(rep_pe), p1)]) {
    k0 <- sub(p1, p0, k, fixed = TRUE); if (is.null(rep_pe[[k0]])) next
    for (m in c("E", "alfa_S", "beta_S", "cota_sup_S", "sobre_0.5")) {
      dif <- rep_pe[[k]]$boot[, m] - rep_pe[[k0]]$boot[, m]
      est <- rep_pe[[k]]$punto[[m]] - rep_pe[[k0]]$punto[[m]]
      partes <- strsplit(sub(paste0("^", p1, " "), "", k), " ")[[1]]
      difs[[length(difs) + 1L]] <- data.table(estrato = partes[1], categoria = paste(partes[-1], collapse = " "), medida = m, media_2022T3 = rep_pe[[k0]]$punto[[m]],
        media_2025T3 = rep_pe[[k]]$punto[[m]], diferencia = est, ee = sd(dif), ic_lo = unname(quantile(dif, a)), ic_hi = unname(quantile(dif, 1 - a)),
        n_2022T3 = rep_pe[[k0]]$n, n_2025T3 = rep_pe[[k]]$n)
    }
  }
  dd <- rbindlist(difs)
  dd[, publicable := n_2022T3 >= PARAM$n_min & n_2025T3 >= PARAM$n_min]
  dd[publicable == FALSE, c("media_2022T3", "media_2025T3", "diferencia", "ee", "ic_lo", "ic_hi") := NA_real_]
  fwrite(dd[order(estrato, categoria, medida)], P("enoe", "enoe_exposicion_diferencias.csv"))

  # --- cambio por grupo SINCO: Delta E = suma_g Delta p_g * (E_g - E_2022), descriptivo --------------------------------------------------------
  g <- d[con_medida == TRUE & !is.na(fac_tri), .(w = sum(fac_tri)), by = .(periodo, sinco_code)]
  g[, p := w / sum(w), by = periodo]
  gw <- dcast(g, sinco_code ~ periodo, value.var = "p", fill = 0); setnames(gw, PARAM$periodos, c("p_2022T3", "p_2025T3"))
  gw <- merge(gw, main_t[, .(sinco_code, titulo, division, E_g = exp_idx_media_modelos)], by = "sinco_code")
  E22 <- sum(gw$p_2022T3 * gw$E_g)
  gw[, `:=`(delta_p = p_2025T3 - p_2022T3, contribucion = (p_2025T3 - p_2022T3) * (E_g - E22))]
  fwrite(gw[order(-abs(contribucion))], P("enoe", "enoe_exposicion_cambio_por_grupo.csv"))

  # --- meta ----------------------------------------------------------------------------------------------------------------------------------------
  write(toJSON(list(decision = "020", rotulo = ROTULO, fecha_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z", tz = "UTC"), parametros = PARAM,
                    exposicion_congelada_sha256 = fz$main_sha256, r_version = R.version.string, enoeR = as.character(packageVersion("enoeR")),
                    n_personas = nrow(d), n_ocupados = sum(d$poblacion), nota = "Exploratorio con plan previo (013 sin firmar). Composicion ocupacional con exposicion fija."),
              auto_unbox = TRUE, pretty = TRUE), P("enoe", "enoe_exposicion_meta.json"))

  # --- resumen en consola ----------------------------------------------------------------------------------------------------------------------
  tot <- res[estrato == "total"]
  cat("\n== Exposicion media (total ocupados 15+, con medida) ==\n")
  print(tot[, .(periodo, n_muestra, millones = round(n_ponderado / 1e6, 2), cobertura = round(pct_cobertura, 1), E = round(media_E, 3), ic = sprintf("[%.3f, %.3f]", ic_lo_E, ic_hi_E),
                alfa_S = round(media_alfa_S, 3), beta_S = round(media_beta_S, 3), cota_sup_S = round(media_cota_sup_S, 3), pct_E_mayor_0.5 = round(pct_sobre_0.50, 1))])
  cat("\n== Diferencia 2025T3 - 2022T3 (total) ==\n"); print(dd[estrato == "total", .(medida, diferencia = round(diferencia, 4), ic = sprintf("[%.4f, %.4f]", ic_lo, ic_hi))])
  invisible(NULL)
}

if (sys.nframe() == 0L) main()
