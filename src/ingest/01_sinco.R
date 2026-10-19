# Ingesta SINCO 2019 (INEGI), parte 1: jerarquia (4 niveles) desde la version abreviada del PDF oficial.
# Produce data/processed/sinco.parquet:
#   sinco_code, nivel, titulo, padre (columnas originales) + nivel_num, division, grupo_principal,
#   subgrupo, orden, pdf_page_estructura (pagina fisica del PDF donde aparece en la version abreviada).
# Valida contra las cifras oficiales del propio PDF (9 / 52 / 163 / 490) leidas del documento.
suppressPackageStartupMessages({ library(dplyr); library(stringr); library(arrow) })
.d <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]), winslash = "/"))
source(file.path(.d, "00_utils.R")); source(file.path(.d, "00_sinco_lib.R"))

URL <- "https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/702825198411.pdf"
download_raw("sinco_2019_pdf", URL, "sinco_2019.pdf", "SINCO 2019 (INEGI, 2020)",
             "Sistema Nacional de Clasificacion de Ocupaciones 2019, documento oficial (PDF)")
pages <- sinco_pdf_pages()
cat_ <- parse_sinco_catalogo(pages)

# Cifras oficiales leidas del PDF: fila "Total" del cuadro comparativo 2011 vs 2019 (ultimas 4 cifras = 2019).
tot <- unlist(str_extract_all(pages[str_detect(pages, "Comparativo de orden cuantitativo")][1], "(?m)^[[:space:]]*Total[[:space:]]+[0-9 ]+$"))
cif <- as.integer(str_extract_all(tot[1], "[0-9]+")[[1]])
if (length(cif) != 8) stop_with_issue("SINCO: no se pudo leer el cuadro oficial de conteos", "No se hallo la fila Total de 8 cifras.")
oficial <- setNames(cif[5:8], NIVELES)

cuenta <- table(factor(cat_$nivel, levels = NIVELES))
message("Conteos obtenidos: ", paste(names(cuenta), cuenta, collapse = "; "))
message("Oficial (PDF 2019): ", paste(names(oficial), oficial, collapse = "; "))
if (any(as.integer(cuenta) != oficial))
  stop_with_issue("SINCO: conteos no coinciden con la cifra oficial",
    paste0("Obtenido: ", paste(names(cuenta), cuenta, collapse = ", "),
           ". Oficial: ", paste(names(oficial), oficial, collapse = ", "), "."))
if (!all(cat_$padre[!is.na(cat_$padre)] %in% cat_$sinco_code))
  stop_with_issue("SINCO: padres huerfanos", "Hay codigos cuyo padre no existe en el catalogo.")

df <- cat_ |>
  mutate(nivel_num = nchar(sinco_code),
         division = str_sub(sinco_code, 1, 1),
         grupo_principal = if_else(nivel_num >= 2, str_sub(sinco_code, 1, 2), NA_character_),
         subgrupo = if_else(nivel_num >= 3, str_sub(sinco_code, 1, 3), NA_character_),
         orden = row_number()) |>
  select(sinco_code, nivel, titulo, padre, nivel_num, division, grupo_principal, subgrupo, orden,
         pdf_page_estructura = pdf_page)
stopifnot(!anyDuplicated(df$sinco_code))
write_parquet_checked(df, "sinco.parquet")
message("OK sinco.parquet: ", nrow(df), " filas x ", ncol(df))
