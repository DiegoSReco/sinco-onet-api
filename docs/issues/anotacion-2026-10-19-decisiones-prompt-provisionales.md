# Issue: decisiones provisionales de diseno del prompt ann-v1

No estan en 001; se documentan para revision:
1. El prompt incluye el titulo de la ocupacion O*NET como contexto de la tarea (la rubrica no lo prohibe ni lo exige).
2. Instrucciones y `rationale` en espanol; tarea en ingles.
3. Se exige JSON puro (sin bloques de codigo); respuestas fuera de formato se reintentan.
4. Limite de 600 caracteres en `rationale`; la regla de "1 o 2 frases" no se verifica automaticamente.
5. Sin umbral de tiempo (001 3.3 [NO VERIFICADO]).
6. Piloto: una tarea por ocupacion, ronda entre grupos mayores SOC, semilla 20261019 (config). Tamano 40 propuesto por el agente.
