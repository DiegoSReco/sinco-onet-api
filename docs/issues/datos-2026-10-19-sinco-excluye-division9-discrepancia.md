# Discrepancia interna del PDF: grupos unitarios con "Excluye" en la division 9

Estado: abierto, informativo (no bloquea). Extraccion no modificada.

El cuadro del PDF "Total de grupos unitarios del SINCO 2019 que cuentan con el rubro de excluye por division"
(PDF p. 21, impresa 14) declara 395 en total (80.6 %) y 33 en la division 9 (58.9 %).
Contando directamente las secciones "Excluye:" de la version ampliada se obtiene 398 en total y 36 en la division 9;
las divisiones 1-8 coinciden exactamente (41, 140, 11, 16, 28, 29, 51, 46).

Evidencia de que el cuadro del PDF es el inconsistente y no la extraccion: 33 / 58.9 % implica una base de 56 grupos unitarios,
pero la division 9 tiene 60 (cuadro comparativo, PDF p. 17: 60 grupos unitarios; 36 / 60 = 60.0 %).
Los 36 grupos unitarios de la division 9 con "Excluye" (verificables en data/processed/sinco_incluye_excluye.parquet):
9111 9112 9113 9121 9123 9124 9213 9221 9222 9231 9232 9234 9235 9311 9321 9331 9411 9601 9611 9621 9622 9623 9631 9641 9642 9643 9651 9661 9662 9664 9712 9713 9721 9722 9723 9732.
No se corrige el contenido de INEGI. La tabla sinco_cifras_oficiales conserva valor_oficial, valor_extraido y coincide=FALSE.
