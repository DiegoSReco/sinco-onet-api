# Emparejamiento A1: puente O*NET 2019 -> SOC 2010 -> Frey-Osborne; multiplicidad, cobertura parcial y codigos fuera del puente

Origen: `src/match/pfo.py`; cifras de `data/processed/match_cobertura.json` (corrida `match-A1-20261019T161025-21e0f487`). Complementa
`docs/issues/datos-2026-10-19-frey-osborne-puente-discrepancias.md`. No bloquea; todo `sin_validar`. Nada se imputa.

## Lo que 005 ya fija y se implemento tal cual
- Un O*NET 2019 con varios SOC 2010 se propaga como conjunto con pesos uniformes (005 R.7); se reportan `p_min`, `p_max`, `n_soc2010`.
- Dos O*NET con el mismo SOC 2010 se colapsan antes de ponderar (005 5.6).
- O*NET sin puente (4: 15-1299.04, .05, .06, .07) -> sin probabilidad, se cuenta (`bandera_sin_puente`; hoy 0 grupos SINCO los tienen en su conjunto S).

## Lo que 005 no resuelve y se uso una opcion provisional
1. **Cobertura parcial.** Cuando algun SOC 2010 alcanzado desde el conjunto S no tiene probabilidad F-O (la tabla tiene 702 SOC; el puente alcanza mas), la media se calcula **solo sobre los SOC con probabilidad, renormalizando los pesos**, y se reporta `cobertura_peso_fo` (fraccion del peso cubierta), `cobertura_fo` (completa/parcial/ninguna) y `bandera_soc_sin_fo`. Alternativa: NA si la cobertura no es completa. En bge-m3: completa 344, parcial 112, ninguna 34 (de 490); en e5: 225, 235, 30. Los grupos con cobertura "ninguna" quedan NA con `motivo_na = sin_probabilidad_fo` (34 en bge-m3).
2. **Cuantas ocupaciones O*NET tienen varios SOC 2010.** El script cuenta 43 ocupaciones O*NET 2019 con mas de un SOC 2010 en el puente completo (lista en `match_cobertura.json`, clave `puente_o_net_2019_con_varios_soc2010`); el issue de datos y 005 hablan de 25 porque cuentan solo las que alcanzan probabilidad F-O. No es contradiccion, pero la cifra a citar depende de la definicion. `bandera_multi_soc2010`: 51 grupos SINCO (bge-m3) y 136 (e5) tienen alguna en su conjunto S.
3. **Codigos F-O fuera del puente (17):** 13-1078, 15-1150, 15-1179, 15-1799, 25-1000, 25-3999, 29-1060, 29-1111, 29-2037, 29-2799, 29-9799, 31-9799, 39-4831, 45-2090, 47-4799, 49-9799, 51-9399. Opcion provisional: quedan **sin enlace** (nunca alcanzables desde O*NET), sin correspondencia manual (p. ej. 29-1111 -> 29-1141 no se hace). 005 R.7/R.8 lo marca "requiere decision".
4. **Licencia del PDF de F-O y verificacion de la transcripcion:** sin cambios; siguen pendientes (005 R.7). Las salidas con probabilidades F-O no deben redistribuirse publicamente hasta decidir la licencia.

## Que se necesita
Decidir: (a) renormalizar vs NA en cobertura parcial; (b) tratamiento de los 17 codigos; (c) la definicion canonica de "ocupaciones con varios SOC 2010" para reportes.
