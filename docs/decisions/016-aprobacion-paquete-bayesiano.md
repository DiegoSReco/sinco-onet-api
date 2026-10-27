# 016 - Aprobación de un paquete bayesiano (PyMC, Stan o NumPyro) para el modelo ordinal jerárquico de B1/B2

- Fecha: 2026-10-22
- Autor: orquestador (registro de la instrucción del usuario)
- Relacionada con: 012 (§9, pregunta 6; tabla "Paquetes bayesianos"), 015 (pendiente del paquete), issue `docs/issues/calibracion-2026-10-19-parametros-provisionales.md` (punto 6).

## Registro de aprobación
Cita textual del usuario (2026-10-22): "Aprobado PyMC, Stan o NumPyro".

## Qué se aprueba (lectura mía, sin ampliar)
- Se aprueba **añadir como dependencia uno** de los tres paquetes, para implementar el modelo ordinal jerárquico con efecto de función que 012 describe y que el Gibbs propio (`src/calibrate/b1_dawid_skene.py`, versión `b1-0.1`) no cubre.
- El usuario no eligió uno. La elección se hace por viabilidad de instalación en este equipo y se registra al instalar (sección siguiente).

## Qué NO se aprueba
- No se instala ni se ejecuta nada por esta decisión; no se modifica `requirements.txt` hasta elegir.
- No reemplaza a `b1-0.1`: se conserva como línea base para comparar.
- No levanta las demás compuertas de 012/013 (muestra humana, firma del pre-registro, exposición congelada, términos de INEGI). Sin muestra humana el resultado sigue siendo consistencia entre corridas, no exactitud.
- No autoriza descargar datos de la ENOE.

## Criterio de elección (propuesto, pendiente de confirmar)
Entorno verificado el 2026-10-22: Python 3.14.3 (.venv), numpy 2.5.4, scipy 1.18.1; sin PyMC, NumPyro, JAX ni cmdstanpy.
1. Probar en un entorno aislado (no el .venv del proyecto) si hay ruedas (wheels) para Python 3.14: primero NumPyro (requiere JAX), luego PyMC (requiere PyTensor); Stan (CmdStan) requiere compilador C++ en Windows **[NO VERIFICADO]**.
2. Elegir el primero que instale sin compilar y que reproduzca B1 básico (mismos datos y priors) con diferencias dentro del error de Monte Carlo.
3. Fijar versión exacta en `requirements.txt`, registrar la elección aquí (enmienda) y mantener R-hat <= 1.05 y ESS >= 100 como diagnósticos.
4. Si ninguno instala en Python 3.14, se necesita decidir entre usar otra versión de Python para `src/calibrate` o seguir con el Gibbs propio.

## Estado
Aprobado en el mecanismo; paquete concreto **pendiente** de la prueba de instalación.

## Enmienda 1 (2026-10-22): resultado de la prueba de instalación
Entorno aislado (venv fuera del repositorio), Python 3.14.3, solo ruedas binarias (`--only-binary=:all:`).
- **NumPyro 0.22.0 (JAX/jaxlib 0.12.0.1):** instala sin compilar. Prueba de humo: Dawid-Skene con datos sintéticos (300 ítems, 3 anotadores, 3 clases), NUTS, 4 cadenas. Resultado: R-hat máx. 1.005, ESS mín. 1195; prevalencias y diagonales de confusión cercanas a los valores verdaderos (p. ej. 0.53/0.26/0.21 frente a 0.5/0.3/0.2).
- **PyMC 6.3.2 (PyTensor 3.3.4):** el resolutor de pip encontró ruedas para todo (simulación de instalación); **no se ejecutó ningún modelo**.
- **Stan (cmdstanpy 1.3.0):** el paquete instala, pero no hay compilador C++ (`g++`, `gcc`, `make` no están en el PATH) y CmdStan no está instalado: no utilizable hoy.
- **Hallazgo metodológico:** con inicialización aleatoria, las cadenas no convergieron (R-hat ~10, ESS ~2) por intercambio de etiquetas (label switching) propio de Dawid-Skene; con `init_to_median` convergió. La implementación definitiva debe fijar la inicialización o una restricción de identificabilidad, y verificar R-hat/ESS.
- **Elección provisional:** NumPyro (criterio 2 de arriba, cumplido). Falta confirmación del usuario, fijar la versión en `requirements.txt` (no se modificó) y reproducir B1 básico con los datos reales del piloto.
- Código de la prueba (temporal, no versionado): carpeta de scratchpad de la sesión.

## Enmienda 2 (2026-10-22): confirmación del usuario y reproducción de B1 en el piloto
- **Confirmación:** el usuario confirmó NumPyro ("confirmo", 2026-10-22). Versiones fijadas en `requirements-calibrate.txt` (numpyro 0.22.0, jax y jaxlib 0.12.0.1), instaladas en el `.venv`. No se tocó `requirements.txt`.
- **Código:** `src/calibrate/b1_numpyro.py` (mismo modelo y priors de `config.toml`, NUTS con `init_to_median`, importación perezosa) y `tests/calibrate/test_b1_numpyro.py`.
- **Reproducción sobre el piloto** (3 corridas x 40 tareas, `exposure_class`; salida solo en pantalla, nada escrito en `data/`): con ambos priors, Gibbs y NumPyro convergen (NumPyro R-hat máx. ~1.0007, ESS mín. ~3500). Diferencias: prevalencias <= 0.004, diagonales de confusión <= 0.003, acuerdo de clase modal 100 %. Dentro del error de Monte Carlo (criterio 2).
- **Sigue siendo** consistencia entre corridas, no exactitud (sin muestra humana); sigue "PILOTO, NO RESULTADO".
- **Pendiente:** modelo ordinal jerárquico con efecto de función (aún no implementado) y decisión sobre su especificación.
