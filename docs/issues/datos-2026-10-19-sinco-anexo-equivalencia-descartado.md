# Anexo "Tabla de equivalencia SINCO 2011 - 2019": descartado por ahora

Estado: DESCARTADO por instruccion del usuario (opcion 1). No hay codigo ni tabla de este anexo en src/ingest/ ni en data/processed/.

Que es: tabla de dos columnas (2019 | 2011) en las paginas PDF 357-392 (impresas aprox. 359-394) del SINCO 2019.
Es la unica correspondencia entre clasificaciones que trae el PDF (no hay correspondencia con CIUO-08 ni SCIAN).

Hallazgos de un intento exploratorio (no conservado en el repositorio), para quien lo retome:
- pdftotext -layout (Xpdf 4.00 en este equipo; no soporta recortes -x/-y/-W/-H ni -bbox) entrega ambas columnas en la misma linea.
- Las celdas combinadas desplazan los codigos 2011 algunas lineas respecto de su fila 2019 (p. ej. PDF p. 372: el "4" de 2011 aparece dos lineas antes que el "4" de 2019), por lo que alinear por fila falla.
- Extraer solo codigos y alinear las dos secuencias por subsecuencia comun mas larga dio: 714/714 codigos 2019 (= catalogo, mismo orden) y 468 codigos 2011 de 4 digitos (coincide con las 468 del cuadro oficial), pero solo 52/53 de 2 digitos y 149/156 de 3 digitos; 57 filas no ancladas (changes de codigo, nuevos, bloques ambiguos como 7515 -> 7518/759/7599 o 420/4201 -> 430/4301/431).
- Mejora posterior sugerida: render por coordenadas (pdfplumber/pymupdf en Python, previa aprobacion) o captura manual verificada; resolver los bloques ambiguos es decision de metodologia.
