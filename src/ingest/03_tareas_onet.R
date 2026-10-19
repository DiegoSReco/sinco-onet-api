# Ingesta de tablas de tareas de O*NET (version 31.0, formato texto delimitado por tabuladores).
# Produce: tareas_onet_en.parquet (task_id, onet_soc_code, tarea_en),
#          tareas_onet_ratings.parquet, onet_ocupaciones.parquet
suppressPackageStartupMessages({ library(dplyr); library(readr); library(janitor); library(arrow) })
source(file.path(dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]), winslash = "/")), "00_utils.R"))

ONET_VERSION <- "31.0"
URL <- "https://www.onetcenter.org/dl_files/database/db_31_0_text.zip"
zipf <- download_raw("onet_31_0_text", URL, "onet_db_31_0_text.zip", paste0("O*NET ", ONET_VERSION, " (August 2026 Release)"),
                     "O*NET Database 31.0, formato texto (tab-delimitado), release del sitio onetcenter.org")

tmp <- tempfile(); dir.create(tmp)
utils::unzip(zipf, exdir = tmp)
dd <- file.path(tmp, "db_31_0_text")

leer <- function(nombre, na = character()) {
  f <- file.path(dd, nombre)
  if (!file.exists(f)) stop_with_issue(paste("O*NET: falta", nombre), paste("No esta", nombre, "en el zip descargado."))
  read_tsv(f, col_types = cols(.default = col_character()), na = na, progress = FALSE) |> clean_names()
}
exigir <- function(df, cols, nombre) {
  falt <- setdiff(cols, names(df))
  if (length(falt)) stop_with_issue(paste("O*NET: esquema inesperado en", nombre),
    paste("Faltan columnas:", paste(falt, collapse = ", "), ". Presentes:", paste(names(df), collapse = ", ")))
}

ts <- leer("Task Statements.txt")
exigir(ts, c("o_net_soc_code", "task_id", "task"), "Task Statements")
tareas <- ts |>
  transmute(task_id = task_id, onet_soc_code = o_net_soc_code, tarea_en = task) |>
  distinct()
if (anyDuplicated(tareas[c("task_id", "onet_soc_code")]))
  stop_with_issue("O*NET: duplicados en tareas", "Pares (task_id, onet_soc_code) duplicados con texto distinto.")
if (anyNA(tareas) || any(tareas$tarea_en == ""))
  stop_with_issue("O*NET: tareas vacias", "Hay valores faltantes en task_id, onet_soc_code o tarea_en.")

tr <- leer("Task Ratings.txt", na = "n/a")
exigir(tr, c("o_net_soc_code", "task_id", "scale_id", "category", "data_value"), "Task Ratings")
ratings <- tr |>
  rename(onet_soc_code = o_net_soc_code) |>
  mutate(across(c(category, data_value, n, standard_error, lower_ci_bound, upper_ci_bound), as.numeric)) |>
  distinct()

oc <- leer("Occupation Data.txt")
exigir(oc, c("o_net_soc_code", "title", "description"), "Occupation Data")
ocup <- oc |> rename(onet_soc_code = o_net_soc_code, titulo_en = title, descripcion_en = description) |> distinct()

if (!all(tareas$onet_soc_code %in% ocup$onet_soc_code))
  stop_with_issue("O*NET: tareas sin ocupacion", "Hay onet_soc_code en tareas ausentes en Occupation Data.")

write_parquet_checked(tareas, "tareas_onet_en.parquet")
write_parquet_checked(ratings, "tareas_onet_ratings.parquet")
write_parquet_checked(ocup, "onet_ocupaciones.parquet")
message("OK tareas_onet_en: ", nrow(tareas), " filas; ratings: ", nrow(ratings), "; ocupaciones: ", nrow(ocup))
