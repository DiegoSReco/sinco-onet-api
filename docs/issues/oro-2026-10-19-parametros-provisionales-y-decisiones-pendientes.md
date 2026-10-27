# Muestra de oro del emparejamiento A1: parametros provisionales y decisiones que 005 deja abiertas

Origen: `src/match/oro.py`, `src/match/oro_resultados.py`, `src/match/oro_config.toml` (decision 005, secc. 8.1, R.7 "Requiere decision" 4, 7, 8). No bloquea la generacion de fichas; **bloquea el uso de resultados** hasta resolver los puntos marcados (R). Todo `sin_validar`; no se reportan cifras del articulo con esto (regla 6).

## Valores provisionales usados (no fijados por 005)
| Punto | Valor provisional | Nota |
|---|---|---|
| Poblacion (P12: 490/468/489) | 490 grupos unitarios del parquet `sinco` | **R**: debe conciliarse antes de tomar la muestra como definitiva |
| Tamano | principal 200 (005); piloto 55 (005: 50-60) | piloto disjunto de la principal, extraido de los 290 restantes |
| Estratos | division (9) x tipo de caso (acuerdo / discrepancia / sin_coincidencia, entre los dos modelos y el estado del principal) | 005 menciona tambien margen en terciles, presencia de funciones y residuales; se **reportan** como columnas (`tercil_margen`, `tiene_funciones`, `residual_*`) pero no son estratos (demasiadas celdas). No hay "A vs B" (Metodo B no implementado) |
| Asignacion | proporcional a N_h x f_h; f = 1.5 para discrepancia y sin_coincidencia, 1 para acuerdo; minimo 2 por estrato (principal), 1 (piloto) | factor de sobremuestreo sin valor en 005. Peso de diseno = N_h / n_h (exacto, MAS dentro del estrato; el del piloto es relativo a la poblacion restante) |
| Calibracion / prueba | 50 / 50 dentro de estrato, solo en la principal | 005 8.1 |
| Candidatos | top-5 de cada modelo, union sin duplicados (7-12 por ficha) + 2 distractores al azar fuera del top-10 de ambos | 005 menciona A1, A2, B y modelos alternativos; solo existen dos modelos. Distractores permiten medir atencion |
| Orden | mezcla independiente por revisor (candidatos y fichas) | |
| Etiquetas | por candidato {exacto, parcial, incorrecto} + un mejor o "ninguno/otro SOC" + confianza | 005 8.1 |
| Aceptable (para precision/recall) | exacto o parcial. Consenso "estricto" = ambos aceptan; "laxo" = alguno acepta; tambien por revisor | **R**: 005 no define como resolver desacuerdos entre revisores en el conjunto aceptable (menciona un tercero, no implementado) |
| Umbral de kappa | 0.60 (nominal) | **R**: 005 pide fijarlo antes de ver datos y no recomienda valor; convencion 0.6-0.8 no verificada |
| Bootstrap | B = 1000, por ficha | 005 8.3 "a decidir" |
| Revisores | A y B, sin identificar | **R**: quienes son (conocimiento de clasificaciones, 003 P4) |
| Descripcion O*NET | primeros 300 caracteres en limite de palabra | |

## Limites conocidos
- Sesgo de pooling: precision/recall solo ven lo que los dos modelos recuperan (mas los distractores); el campo `otro_soc` lo mitiga pero el recall se calcula solo contra los candidatos mostrados.
- No se implemento tercer revisor ni adjudicacion de desacuerdos, ni doble revision parcial (005 la plantea como alternativa).
- Los "excluye" del SINCO no se muestran (consistente con 005 5.1); los revisores podrian necesitarlos en fronteras. A decidir tras el piloto.
- La guia (`docs/guia_revision_oro.md`) es borrador para el piloto; ajustar si kappa < umbral (005 8.1).
- Sin datos de revision real: las pruebas de consolidacion usan datos sinteticos.
