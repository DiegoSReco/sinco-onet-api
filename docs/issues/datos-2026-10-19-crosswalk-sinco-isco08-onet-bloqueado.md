# Crosswalk SINCO-ISCO08-ONET bloqueado

Causa: No hay tabla oficial SINCO 2019 - CIUO-08: el PDF del SINCO 2019 no incluye correspondencia con CIUO-08 y no se encontro otra publicada por INEGI/SNIEG.

Opciones:
1. Proveer manualmente (decision humana) la tabla SINCO-CIUO-08 oficial, o solicitarla a INEGI (atencion.usuarios@inegi.org.mx).
2. El XLS oficial de BLS ISCO-08 -> SOC 2010 ya esta en data/raw/ (ver manifest.json); falta el eslabon SINCO -> ISCO-08.
3. Decision metodologica (no tomada por este agente): construir SINCO-ISCO por mapeo manual/semi-automatico a nivel de titulos; requiere registro en docs/decisions/.
4. Alternativa para ISCO-08 a O*NET-SOC: la cadena ISCO-08 -> SOC 2010 (BLS) -> O*NET-SOC 2019 (taxonomia O*NET) es 1:N y N:1; la resolucion es decision de metodologia.

