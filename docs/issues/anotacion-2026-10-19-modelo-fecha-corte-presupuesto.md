# Issue: modelo, proveedor, fecha de corte, temperatura y presupuesto sin definir

- 001 P3: la fecha de corte de capacidades y la version del modelo anotador "requieren decision". El usuario aun no indico modelo, proveedor ni tope de gasto. 001 tampoco fija temperatura ni numero de corridas (decision de diseno estadistico pendiente).
- Estado: `config.toml` los deja en "requiere decision"; el CLI no corre ningun proveedor real y se niega si la fecha de corte esta pendiente. No hay estimacion de costo: faltan modelo y precios.
- Opcion provisional: solo dry-run. Para el piloto real se necesita: modelo/proveedor, clave en variable de entorno, tope de gasto, fecha de corte, temperatura y numero de corridas.
