# Exposición en la muestra de la ENOE (decisión 020)

Todo en R, porque la unión de tablas usa el paquete `enoeR` (DiegoSReco/enoeR). Los datos no se publican (`.gitignore`; 013 sec. 11).

1. `python -m src.main_sinco_comp_table` genera la tabla MAIN (exposición por grupo unitario SINCO).
2. `Rscript src/ingest/06_enoe.R`: congela la exposición (hash en `data/processed/enoe/exposicion_congelada.json`), baja los ZIP de INEGI a `data/raw/enoe/` (hash en `data/raw/manifest.json`), carga SDEM y COE1T con `enoe_load()` y los une a nivel persona con `enoe_join(level = "person")` para 2022T3 y 2025T3.
3. `Rscript src/enoe/exposicion_enoe.R`: asigna la exposición a cada persona ocupada por su `p3` (SINCO) y calcula medias, cuantiles, proporciones, cobertura, diferencias entre periodos y el cambio por grupo.
4. `Rscript -e 'testthat::test_file("tests/enoe/test_exposicion_enoe.R")'`.

Salida principal: `data/processed/enoe/enoe_exposicion_personas_2022T3_2025T3.parquet` (la muestra completa de los dos periodos). Resúmenes: `enoe_exposicion_resumen.csv`, `_diferencias.csv`, `_cobertura.csv`, `_cambio_por_grupo.csv`, `_meta.json`.

Lectura obligatoria: exposición teórica por anotación de modelos, sin validar; consistencia entre modelos, no exactitud. La exposición es constante dentro de un grupo SINCO, así que toda diferencia entre estratos o periodos es composición ocupacional. No es riesgo de pérdida de empleo.
