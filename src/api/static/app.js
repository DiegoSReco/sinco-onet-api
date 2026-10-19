"use strict";
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(p + " -> " + r.status); return r.json(); });
const NIV = ["", "División", "Grupo principal", "Subgrupo", "Grupo unitario"];
const NS = "http://www.w3.org/2000/svg";

let tree, byCode = {}, root = null, selected = null;

/* ---------- datos ---------- */
function indexar(nodes, parent, depth) {
  let v = 0;
  for (const n of nodes) {
    n.parent = parent; n.d = depth; byCode[n.c] = n;
    n.v = n.ch.length ? indexar(n.ch, n, depth + 1) : 1;
    v += n.v;
  }
  return v;
}
const hue = (c) => (parseInt(c[0], 10) - 1) * 40;
const color = (n) => `hsl(${hue(n.c)}, ${70 - n.d * 8}%, ${38 + n.d * 7}%)`;

/* ---------- sunburst ---------- */
function arcPath(a0, a1, r0, r1) {
  if (a1 - a0 >= 2 * Math.PI - 1e-4) a1 = a0 + 2 * Math.PI - 1e-4;
  const p = (r, a) => [r * Math.sin(a), -r * Math.cos(a)];
  const [x0, y0] = p(r1, a0), [x1, y1] = p(r1, a1), [x2, y2] = p(r0, a1), [x3, y3] = p(r0, a0);
  const l = a1 - a0 > Math.PI ? 1 : 0;
  return `M${x0},${y0}A${r1},${r1} 0 ${l} 1 ${x1},${y1}L${x2},${y2}A${r0},${r0} 0 ${l} 0 ${x3},${y3}Z`;
}
function dibujar() {
  const svg = $("sun"); svg.innerHTML = "";
  const hijos = root ? root.ch : tree.raices;
  const baseDepth = root ? root.d + 1 : 1;
  const niveles = 5 - baseDepth;           // niveles visibles bajo la raiz actual
  const R0 = 62, R1 = 292, dr = (R1 - R0) / niveles;
  const total = hijos.reduce((s, n) => s + n.v, 0);
  const g = document.createElementNS(NS, "g"); svg.appendChild(g);
  (function rec(nodes, a0, a1, lvl) {
    const tot = nodes.reduce((s, n) => s + n.v, 0);
    let a = a0;
    for (const n of nodes) {
      const b = a + (a1 - a0) * n.v / tot;
      const r0 = R0 + lvl * dr, r1 = r0 + dr;
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", arcPath(a, b, r0, r1)); p.setAttribute("fill", color(n));
      if (selected === n.c) p.setAttribute("class", "sel");
      p.addEventListener("click", () => elegir(n.c, true));
      p.addEventListener("mousemove", (e) => tip(e, `<b>${esc(n.c)}</b> ${esc(n.t)}<br><span class="sub">${NIV[n.n]}</span>`));
      p.addEventListener("mouseleave", () => ($("tip").hidden = true));
      g.appendChild(p);
      const am = (a + b) / 2, rm = (r0 + r1) / 2;
      if ((b - a) * rm > 20 && lvl < 3) {
        const t = document.createElementNS(NS, "text");
        t.setAttribute("x", rm * Math.sin(am)); t.setAttribute("y", -rm * Math.cos(am) + 3); t.textContent = n.c; g.appendChild(t);
      }
      if (n.ch.length && lvl + 1 < niveles) rec(n.ch, a, b, lvl + 1);
      a = b;
    }
  })(hijos, 0, 2 * Math.PI, 0);
  const c = document.createElementNS(NS, "circle");
  c.setAttribute("r", R0 - 4); c.style.fill = "var(--inp)"; c.style.cursor = "pointer";
  c.addEventListener("click", () => { root = root ? root.parent : null; selected = null; dibujar(); ruta(); });
  svg.appendChild(c);
  const t = document.createElementNS(NS, "text"); t.setAttribute("class", "centro-txt");
  t.textContent = root ? "↑ " + root.c : "SINCO 2019"; t.setAttribute("y", 4); svg.appendChild(t);
}
function tip(e, html) { const t = $("tip"); t.innerHTML = html; t.hidden = false; t.style.left = e.clientX + 12 + "px"; t.style.top = e.clientY + 12 + "px"; }
function ruta() {
  const cadena = []; for (let n = root; n; n = n.parent) cadena.unshift(n);
  $("ruta").innerHTML = '<a data-c="">SINCO</a>' + cadena.map((n) => ` › <a data-c="${n.c}">${esc(n.c)} ${esc(n.t.slice(0, 40))}</a>`).join("");
  $("ruta").querySelectorAll("a").forEach((a) => a.addEventListener("click", () => { root = a.dataset.c ? byCode[a.dataset.c] : null; dibujar(); ruta(); }));
}

/* ---------- seleccion y detalle ---------- */
async function elegir(code, zoom) {
  const n = byCode[code]; if (!n) return;
  selected = code;
  if (zoom && n.ch.length) root = n; else if (!zoom || !n.ch.length) root = n.parent || null;
  dibujar(); ruta();
  const d = await api("/api/sinco/" + code);
  $("detalle").innerHTML = htmlDetalle(d);
  $("detalle").querySelectorAll("a.ref").forEach((a) => a.addEventListener("click", () => elegir(a.dataset.c, false)));
  $("detalle").scrollTop = 0;
}
function lista(items, f) { return items.length ? "<ul>" + items.map(f).join("") + "</ul>" : '<p class="vacio">Sin datos en el PDF para este nivel.</p>'; }
const AVISO_A1 = "coincidencias automáticas sin validar (Método A1, embeddings)";
const nf = (x, d = 3) => (x === null || x === undefined ? "—" : Number(x).toFixed(d));
function htmlCW(cw, claveOtro) {
  if (cw.estado === "disponible") {
    const filas = cw.filas;
    const a1 = filas.some((f) => /embeddings/i.test(f.fuente || "") || f.estado_validacion === "sin_validar");
    const sinValidar = filas.some((f) => f.estado_validacion === "sin_validar");
    let h = "";
    if (a1 && sinValidar) h += `<div class="cw aviso-a1" role="note"><b>⚠ ${AVISO_A1}.</b> Son propuestas de similitud semántica, no una correspondencia oficial ni validada; la similitud no es una probabilidad.</div>`;
    h += `<div class="cw ok">${filas.length} coincidencia(s) registradas. ${esc(cw.aviso || "")}</div>`;
    return h + lista(filas, (f) => `<li class="match"><span class="cod">${esc(f[claveOtro])}</span>${f.onet_titulo ? esc(f.onet_titulo) : ""} <span class="sub">· ${esc(f.tipo_relacion)} · fuente: ${esc(f.fuente)}</span> <span class="tag">${esc(f.estado_validacion)}</span>` +
      (f.similitud !== undefined && f.similitud !== null ? `<div class="sub">similitud ${nf(f.similitud)} · rango ${esc(f.rango ?? "—")}` +
        (f.margen !== undefined && f.margen !== null ? ` · margen ${nf(f.margen)}` : "") + (f.baja_confianza ? ' · <span class="tag">baja confianza</span>' : "") +
        (f.modelo ? ` · modelo ${esc(f.modelo)}` : "") + (f.run_id ? ` · run ${esc(f.run_id)}` : "") + "</div>" : "") + "</li>");
  }
  if (cw.estado === "esquema_invalido") return `<div class="cw">Crosswalk con esquema inválido: ${esc(cw.mensaje)}</div>`;
  return `<div class="cw">⌛ ${esc(cw.mensaje)}. No existe una correspondencia oficial SINCO–CIUO-08–O*NET; no se muestran emparejamientos inferidos.</div>`;
}
const PROB_QUE_ES = "Qué es: la probabilidad de automatización de Frey y Osborne (2013/2017) para ocupaciones de EE. UU. (SOC 2010), trasladada a este grupo SINCO con un emparejamiento automático (media ponderada por similitud de sus 2 O*NET).";
const PROB_QUE_NO = "Qué NO es: no es exposición a IA, ni riesgo de pérdida de empleo, ni una estimación para México. Depende de un emparejamiento NO validado y de parámetros provisionales.";
function htmlProb(p) {
  const tip = `<button type="button" class="qm" aria-label="Qué es y qué no es" title="${esc(PROB_QUE_ES + " " + PROB_QUE_NO)}">?</button>`;
  const titulo = `<b>Probabilidad de automatización (Frey-Osborne)</b><span class="tag">NO validada</span>${tip}`;
  if (!p || p.estado === "no_disponible" || p.estado === "esquema_invalido")
    return `<div class="prob vacia" role="note">${titulo}<div>Probabilidad no disponible: la tabla de probabilidades no existe en esta instalación${p && p.estado === "esquema_invalido" ? " (esquema inválido: " + esc(p.mensaje) + ")" : ""}.</div></div>`;
  if (p.estado === "sin_fila") return `<div class="prob vacia" role="note">${titulo}<div>${esc(p.mensaje)}.</div></div>`;
  const v = p.valores, pc = (x) => (x === null || x === undefined ? "—" : (x * 100).toFixed(1) + " %");
  const val = v.probabilidad_automatizacion_fo;
  return `<div class="prob" role="note">${titulo}<div class="valor">${val === null ? "sin valor" : pc(val)}</div>` +
    (val === null ? `<div class="sub">NA por: ${esc(v.motivo_na || "—")}</div>` : "") +
    `<div class="sub">media uniforme ${pc(v.probabilidad_automatizacion_fo_media_uniforme)} · mín ${pc(v.probabilidad_automatizacion_fo_min)} · máx ${pc(v.probabilidad_automatizacion_fo_max)} · top-1 ${pc(v.probabilidad_automatizacion_fo_top1)}</div>` +
    `<div class="sub">candidatos ${esc(v.n_candidatos)} · cobertura de peso F-O ${nf(v.cobertura_peso_fo, 2)} (${esc(v.cobertura_fo || "—")}) · modelo ${esc(v.modelo)} · run ${esc(v.run_id)}</div>` +
    `<div class="sub">${esc(PROB_QUE_NO)}</div></div>`;
}
function htmlDetalle(d) {
  const n = d.nodo;
  let h = `<h2><span class="cod">${esc(n.sinco_code)}</span>${esc(n.titulo)}</h2><div class="sub">${NIV[n.sinco_code.length]} · página PDF ${n.pagina_pdf_estructura} (versión abreviada)</div>`;
  h += '<div class="sub">' + d.ancestros.map((a) => `<a class="ref" data-c="${a.sinco_code}">${esc(a.sinco_code)} ${esc(a.titulo)}</a>`).join(" › ") + "</div>";
  if (d.descripcion) {
    h += `<h3>Descripción</h3><p>${esc(d.descripcion.texto) || '<span class="vacio">Grupo residual: el PDF solo trae el título.</span>'}</p>`;
    h += `<div class="sub">PDF pp. ${d.descripcion.pagina_pdf_inicio}–${d.descripcion.pagina_pdf_fin}${d.descripcion.pagina_impresa_inicio ? " (impresa " + d.descripcion.pagina_impresa_inicio + ")" : ""}</div>`;
    if (d.descripcion.notas_extraccion) h += `<div class="sub">Nota de extracción: ${esc(d.descripcion.notas_extraccion)}</div>`;
  }
  if (d.hijos.length) h += `<h3>Contiene (${d.hijos.length})</h3>` + lista(d.hijos, (c) => `<li><a class="ref" data-c="${c.sinco_code}"><span class="cod">${c.sinco_code}</span>${esc(c.titulo)}</a></li>`);
  if (n.sinco_code.length === 4) {
    h += `<h3>Ocupaciones ejemplo (${d.ocupaciones_ejemplo.length})</h3>` + lista(d.ocupaciones_ejemplo, (o) => `<li>${esc(o.ocupacion)}${o.afectado_por_errata ? '<span class="tag">fe de erratas</span>' : ""}</li>`);
    h += `<h3>Funciones (${d.funciones.length})</h3>` + lista(d.funciones, (f) => `<li>${esc(f.funcion)}</li>`);
    for (const tipo of ["incluye", "excluye"]) {
      const it = d.incluye_excluye.filter((x) => x.tipo === tipo);
      if (!it.length) continue;
      h += `<h3>${tipo === "incluye" ? "Incluye" : "Excluye"} (${it.length})</h3>` + lista(it, (x) => {
        let t = esc(x.texto);
        for (const r of x.referencias) t = t.replace(esc(r.codigo) + " ", `<a class="ref" data-c="${r.codigo}">${esc(r.codigo)}</a> `);
        return `<li>${t}${x.afectado_por_errata ? '<span class="tag">fe de erratas</span>' : ""}</li>`;
      });
    }
    if (d.fe_de_erratas.length) h += "<h3>Fe de erratas de INEGI</h3>" + lista(d.fe_de_erratas, (e) => `<li>p. ${e.pagina_impresa}: ${esc(e.nota)}<br><span class="sub">Dice: ${esc(e.texto_dice)}<br>Debe decir: ${esc(e.texto_debe_decir)}</span></li>`);
  }
  h += "<h3>Coincidencias con O*NET</h3>" + htmlCW(d.coincidencias_onet, "onet_soc_code");
  h += "<h3>Probabilidad de automatización</h3>" + htmlProb(d.probabilidad_automatizacion_fo);
  return h;
}

/* ---------- busqueda SINCO ---------- */
let tq;
$("q-sinco").addEventListener("input", (e) => {
  clearTimeout(tq); const q = e.target.value.trim();
  if (q.length < 2) { $("res-sinco").hidden = true; return; }
  tq = setTimeout(async () => {
    const r = await api("/api/sinco/search?q=" + encodeURIComponent(q));
    $("res-sinco").hidden = false;
    $("res-sinco").innerHTML = r.resultados.map((x) => `<div data-c="${x.sinco_code}"><span class="cod">${x.sinco_code}</span>${esc(x.titulo)}<div class="sub">${esc(x.motivo)}</div></div>`).join("") || '<div class="vacio">Sin resultados</div>';
    $("res-sinco").querySelectorAll("div[data-c]").forEach((d) => d.addEventListener("click", () => { $("res-sinco").hidden = true; elegir(d.dataset.c, false); }));
  }, 250);
});
$("btn-raiz").addEventListener("click", () => { root = null; selected = null; dibujar(); ruta(); });

/* ---------- O*NET ---------- */
let onetOff = 0; const LIM = 40;
async function cargarOnet() {
  const q = $("q-onet").value.trim();
  const r = await api(`/api/onet/occupations?q=${encodeURIComponent(q)}&limit=${LIM}&offset=${onetOff}`);
  $("lista-onet").innerHTML = r.resultados.map((o) => `<div data-s="${o.onet_soc_code}"><span class="cod">${o.onet_soc_code}</span>${esc(o.titulo_en)}<span class="sub"> · ${o.n_tareas} tareas</span></div>`).join("") || '<div class="vacio">Sin resultados</div>';
  $("lista-onet").querySelectorAll("div[data-s]").forEach((d) => d.addEventListener("click", () => detalleOnet(d.dataset.s)));
  $("onet-pag").textContent = `${r.total ? onetOff + 1 : 0}–${Math.min(onetOff + LIM, r.total)} de ${r.total}`;
  $("onet-prev").disabled = onetOff === 0; $("onet-next").disabled = onetOff + LIM >= r.total;
}
async function detalleOnet(soc) {
  const d = await api("/api/onet/occupations/" + soc);
  $("detalle-onet").innerHTML = `<h2><span class="cod">${esc(d.onet_soc_code)}</span>${esc(d.titulo_en)}</h2><p>${esc(d.descripcion_en)}</p>` +
    `<h3>Tareas (${d.n_tareas})</h3>` + lista(d.tareas, (t) => `<li>${esc(t.tarea_en)}</li>`) +
    "<h3>Coincidencias con SINCO</h3>" + htmlCW(d.coincidencias_sinco, "sinco_code") +
    '<div class="sub">Catálogo O*NET sin valoraciones ni cálculos. Fuente: O*NET (USDOL/ETA, CC BY 4.0).</div>';
}
let to;
$("q-onet").addEventListener("input", () => { clearTimeout(to); to = setTimeout(() => { onetOff = 0; cargarOnet(); }, 250); });
$("onet-prev").addEventListener("click", () => { onetOff = Math.max(0, onetOff - LIM); cargarOnet(); });
$("onet-next").addEventListener("click", () => { onetOff += LIM; cargarOnet(); });

/* ---------- fuentes ---------- */
async function cargarMeta() {
  const m = await api("/api/meta");
  const fila = (k, v) => `<tr><td>${esc(k)}</td><td>${v}</td></tr>`;
  $("meta").innerHTML = "<h2>Fuentes y estado</h2><table class='meta'>" +
    fila("SINCO", `${esc(m.sinco.documento)}<br><span class="sub">${esc(m.sinco.url)}<br>sha256 ${esc(m.sinco.sha256)}<br>descarga ${esc(m.sinco.fecha_descarga)}</span>`) +
    fila("Niveles SINCO", Object.entries(m.sinco.niveles).map(([k, v]) => `${k}: ${v}`).join(" · ")) +
    fila("O*NET", `${esc(m.onet.version)}<br><span class="sub">${esc(m.onet.url)}<br>sha256 ${esc(m.onet.sha256)}</span>`) +
    fila("Crosswalk", `<b>${esc(m.crosswalk.estado)}</b> ${esc(m.crosswalk.mensaje)} (${m.crosswalk.n_filas} filas)` +
      (m.crosswalk.estado === "disponible" ? `<br><span class="sub">${AVISO_A1}</span>` : "")) +
    fila("Probabilidad (Frey-Osborne)", `<b>${esc(m.probabilidad_automatizacion_fo.estado)}</b> ${esc(m.probabilidad_automatizacion_fo.mensaje)} · NO validada · modelo principal ${esc(m.probabilidad_automatizacion_fo.modelo_principal ?? "—")} (${m.probabilidad_automatizacion_fo.n_filas} filas)`) +
    fila("Tablas (filas)", Object.entries(m.tablas).map(([k, v]) => `${k}: ${v}`).join("<br>")) +
    fila("Atribución", esc(m.atribucion)) + "</table>";
}

/* ---------- descarga ---------- */
const filtrado = () => document.querySelector('input[name="alcance"]:checked').value === "filtrado";
function paramsDesc() {
  const p = new URLSearchParams();
  if (filtrado()) {
    if ($("d-division").value) p.set("division", $("d-division").value);
    const pre = $("d-prefijo").value.trim(); if (pre) p.set("sinco_prefix", pre);
    const q = $("d-q").value.trim(); if (q) p.set("q", q);
    if ($("d-solo").checked) p.set("solo_con_probabilidad", "true");
  }
  p.set("rango_max", $("d-rango").value);
  return p;
}
async function infoDesc() {
  try {
    const r = await fetch("/api/download/conteo?" + paramsDesc());
    const j = await r.json();
    $("d-info").textContent = r.ok ? `${j.n_filas} filas · modelo ${j.modelo} · probabilidad: ${j.probabilidad_automatizacion_fo.estado === "disponible" ? "incluida (NO validada)" : "no disponible (se omiten esas columnas)"}`
      : (r.status === 409 ? "Sin datos: " + j.error : "Parámetros inválidos: " + (j.error || r.status));
    $("d-ir").disabled = !r.ok;
  } catch (e) { $("d-info").textContent = "No se pudo consultar el conteo."; }
}
function prellenarDesc() {
  const code = (root && root.c) || selected || "";
  $("d-division").value = code ? code[0] : ""; $("d-prefijo").value = code;
  $("d-q").value = $("q-sinco").value.trim().slice(0, 100);
}
document.querySelectorAll('input[name="alcance"]').forEach((r) => r.addEventListener("change", () => {
  $("filtros-desc").disabled = !filtrado(); if (filtrado()) prellenarDesc(); infoDesc();
}));
for (const id of ["d-division", "d-prefijo", "d-q", "d-solo", "d-rango"]) $(id).addEventListener("change", infoDesc);
$("descargar").addEventListener("toggle", () => { if ($("descargar").open) infoDesc(); });
$("d-ir").addEventListener("click", () => {
  const p = paramsDesc(); p.set("formato", $("d-formato").value);
  const a = document.createElement("a"); a.href = "/api/download/dataset?" + p; a.download = ""; document.body.appendChild(a); a.click(); a.remove();
});

/* ---------- resumen: KPIs y barras (HTML/CSS propios; cifras calculadas por /api/resumen) ---------- */
const AVISO_RES = "Coincidencias automáticas (Método A1, top-2) NO validadas; probabilidad de automatización (Frey-Osborne) ≠ exposición a IA";
const ETQ = { ok: "Con coincidencia", baja_confianza: "Baja confianza", sin_coincidencia: "Sin coincidencia", sin_dato: "Sin dato" };
const CLS = { ok: "ok", baja_confianza: "baja", sin_coincidencia: "sin", sin_dato: "sin" };
const fmt = (n) => Number(n).toLocaleString("es-MX");
function el(tag, cls, txt) { const e = document.createElement(tag); if (cls) e.className = cls; if (txt !== undefined) e.textContent = txt; return e; }
function kpi(cls, valor, suf, etq, nota) {
  const k = el("div", "kpi " + cls); const v = el("div", "v", valor);
  if (suf) { v.appendChild(document.createTextNode(" ")); v.appendChild(el("small", "", suf)); }
  k.append(v, el("div", "l", etq), el("div", "n", nota)); return k;
}
function leyenda(estados) {
  const l = el("div", "leg"); l.setAttribute("aria-hidden", "true");
  for (const e of estados) { const s = el("span"); s.appendChild(el("i", "sw " + CLS[e])); s.appendChild(document.createTextNode(ETQ[e])); l.appendChild(s); }
  return l;
}
function tabla(cab, filas, resumenTxt) {
  const d = el("details", "r-det"); d.appendChild(el("summary", "", resumenTxt));
  const t = el("table", "r-tab"); const th = el("tr"); cab.forEach((c) => th.appendChild(el("th", "", c))); t.appendChild(th);
  for (const f of filas) { const tr = el("tr"); f.forEach((c) => tr.appendChild(el("td", "", c))); t.appendChild(tr); }
  d.appendChild(t); return d;
}
function irADivision(cod) {
  pestana("sinco");
  if (byCode[cod]) { root = byCode[cod]; selected = null; dibujar(); ruta(); }
}
function barrasDivision(r, estados) {
  const card = el("div", "card"); card.appendChild(el("h3", "", "Grupos unitarios por división SINCO y estado de coincidencia"));
  card.appendChild(leyenda(estados));
  const max = Math.max(...r.por_division.map((d) => d.total));
  for (const d of r.por_division) {
    const b = el("button", "brow"); b.type = "button";
    b.setAttribute("aria-label", `División ${d.division} ${d.nombre}: ` + estados.map((e) => `${ETQ[e]} ${d[e]}`).join(", ") + `, total ${d.total}. Clic: ver en el diagrama.`);
    b.append(el("span", "nom", `${d.division} · ${d.nombre}`), el("span", "tot", fmt(d.total)));
    const pista = el("div", "pista"); pista.style.width = (100 * d.total / max) + "%";
    for (const e of estados) {
      if (!d[e]) continue;
      const s = el("div", "seg " + CLS[e]); s.style.flex = d[e] + " 1 0"; s.style.minWidth = "3px";
      if (d[e] / d.total > 0.07 && d[e] / max > 0.04) s.textContent = d[e];
      pista.appendChild(s);
    }
    const mostrar = (ev) => {
      const rc = b.getBoundingClientRect(), x = ev.clientX ?? rc.left + 40, y = ev.clientY ?? rc.top;
      tip({ clientX: x, clientY: y }, `<b>${esc(d.division)} ${esc(d.nombre)}</b><br>` + estados.map((e) => `${esc(ETQ[e])}: <b>${d[e]}</b>`).join("<br>") + `<br>Total: <b>${d.total}</b>`);
    };
    b.addEventListener("pointermove", mostrar); b.addEventListener("focus", mostrar);
    b.addEventListener("pointerleave", () => ($("tip").hidden = true)); b.addEventListener("blur", () => ($("tip").hidden = true));
    b.addEventListener("click", () => { $("tip").hidden = true; irADivision(d.division); });
    b.appendChild(pista); card.appendChild(b);
  }
  card.appendChild(tabla(["División", ...estados.map((e) => ETQ[e]), "Total"], r.por_division.map((d) => [`${d.division} ${d.nombre}`, ...estados.map((e) => d[e]), d.total]), "Ver como tabla"));
  return card;
}
function barrasEstado(r) {
  const card = el("div", "card"); card.appendChild(el("h3", "", "Total de grupos unitarios por estado de coincidencia"));
  const max = Math.max(...r.por_estado.map((e) => e.n), 1);
  for (const e of r.por_estado) {
    const row = el("div", "brow"); row.setAttribute("role", "img"); row.setAttribute("aria-label", `${e.etiqueta}: ${e.n} grupos (${e.pct} %)`);
    row.style.cursor = "default";
    row.append(el("span", "nom", e.etiqueta), el("span", "tot", `${fmt(e.n)} · ${e.pct} %`));
    const pista = el("div", "pista"); const s = el("div", "seg " + CLS[e.estado]); s.style.width = (100 * e.n / max) + "%"; pista.appendChild(s);
    row.appendChild(pista); card.appendChild(row);
  }
  card.appendChild(tabla(["Estado", "Grupos", "%"], r.por_estado.map((e) => [e.etiqueta, e.n, e.pct]), "Ver como tabla"));
  return card;
}
function histograma(r) {
  const h = r.histograma_similitud_rango1, card = el("div", "card");
  card.appendChild(el("h3", "", "Similitud (coseno) del mejor match, grupos unitarios"));
  if (!h.length) { card.appendChild(el("p", "vacio", "Sin datos de similitud.")); return card; }
  const max = Math.max(...h.map((b) => b.n), 1);
  const w = el("div", "h-wrap"); w.setAttribute("role", "img");
  w.setAttribute("aria-label", "Histograma de similitud del rango 1: " + h.map((b) => `${b.desde.toFixed(2)} a ${b.hasta.toFixed(2)}: ${b.n}`).join("; "));
  const eje = el("div", "h-eje");
  for (const b of h) {
    const c = el("div", "h-col"); c.append(el("span", "", b.n)); const i = el("i"); i.style.height = (80 * b.n / max) + "%"; c.appendChild(i);
    c.addEventListener("pointermove", (ev) => tip(ev, `Similitud ${b.desde.toFixed(2)} a ${b.hasta.toFixed(2)}: <b>${b.n}</b> grupos`));
    c.addEventListener("pointerleave", () => ($("tip").hidden = true));
    w.appendChild(c); eje.appendChild(el("span", "", b.desde.toFixed(2)));
  }
  card.append(w, eje, el("div", "sub", "Eje X: similitud coseno (no es una probabilidad). Eje Y: número de grupos."));
  card.appendChild(tabla(["Desde", "Hasta", "Grupos"], h.map((b) => [b.desde.toFixed(2), b.hasta.toFixed(2), b.n]), "Ver como tabla"));
  return card;
}
function pintarResumen(r) {
  const cont = $("resumen"); cont.replaceChildren();
  cont.appendChild(el("h2", "", "Resumen: ¿cuántos grupos SINCO hacen match con O*NET?"));
  const aviso = el("div", "r-aviso", "⚠ " + AVISO_RES + "."); aviso.setAttribute("role", "note"); cont.appendChild(aviso);
  if (r.estado !== "disponible") {
    cont.appendChild(el("div", "r-vacio", `Sin resumen: ${r.mensaje || r.estado}. No se muestran cifras ni barras porque no hay coincidencias SINCO–O*NET cargadas.`)); return;
  }
  const ctl = el("div", "r-ctl"); const lab = el("label", "", "Modelo de embeddings ");
  const sel = el("select"); sel.id = "r-modelo";
  for (const m of r.modelos_disponibles) { const o = el("option", "", m + (m === r.modelo_principal ? " (principal)" : "")); o.value = m; o.selected = m === r.modelo; sel.appendChild(o); }
  sel.addEventListener("change", () => cargarResumen(sel.value)); lab.appendChild(sel); ctl.appendChild(lab);
  ctl.appendChild(el("span", "sub", `run ${(r.run_id || []).join(", ")}`)); cont.appendChild(ctl);
  const k = r.kpis, kp = el("div", "kpis");
  kp.append(
    kpi("", fmt(k.grupos_unitarios), "", "Grupos unitarios SINCO", "Catálogo SINCO 2019, nivel grupo unitario"),
    kpi("ok", fmt(k.con_match), `${k.pct_con_match} %`, "Con match con O*NET", `Confiable: ${fmt(k.con_match_confiable)} (${k.pct_con_match_confiable} %) + baja confianza`),
    kpi("baja", fmt(k.baja_confianza), `${k.pct_baja_confianza} %`, "Match de baja confianza", "Hay propuesta, pero con similitud o margen bajo"),
    kpi("sin", fmt(k.sin_coincidencia), `${k.pct_sin_coincidencia} %`, "Sin coincidencia", "El modelo no superó los umbrales provisionales"),
    kpi("", fmt(k.onet_distintas_emparejadas), `de ${fmt(k.onet_total)} · ${k.pct_onet_emparejadas} %`, "Ocupaciones O*NET emparejadas", "Distintas, en el top-2 de grupos con coincidencia"),
    kpi("", k.similitud_rango1_media === null ? "—" : k.similitud_rango1_media.toFixed(3), k.similitud_rango1_mediana === null ? "" : `mediana ${k.similitud_rango1_mediana.toFixed(3)}`, "Similitud media del mejor match", "Coseno del rango 1; no es una probabilidad"));
  const p = r.probabilidad_automatizacion_fo;
  if (p.estado === "disponible") {
    kp.appendChild(kpi("", fmt(p.n_con_valor), `de ${fmt(p.n_grupos)} · ${p.pct_con_valor} %`, "Con probabilidad de automatización (F-O)",
      `NO validada. Sin valor: ${fmt(p.n_na)} (` + (p.causas_na.map((c) => `${c.causa}: ${c.n}`).join("; ") || "—") + ")"));
  } else kp.appendChild(kpi("sin", "—", "", "Probabilidad de automatización (F-O)", "probabilidad no disponible"));
  const tr = k.tipos_relacion.length ? k.tipos_relacion.map((x) => `${x.tipo}: ${fmt(x.n_pares)}`).join(" · ") : "no disponible para este modelo";
  kp.appendChild(kpi("", fmt(k.pares_top2), "pares", "Pares SINCO–O*NET (top-2)", "Tipos de relación: " + tr));
  cont.appendChild(kp);
  const estados = r.por_estado.map((e) => e.estado);
  const g = el("div", "r-grid"); g.appendChild(barrasDivision(r, estados));
  const der = el("div"); const he = histograma(r); he.style.marginTop = "14px"; der.append(barrasEstado(r), he); g.appendChild(der);
  cont.appendChild(g);
  cont.appendChild(el("p", "sub", r.notas.join(" ")));
}
async function cargarResumen(modelo) {
  try { pintarResumen(await api("/api/resumen" + (modelo ? "?modelo=" + encodeURIComponent(modelo) : ""))); }
  catch (e) { $("resumen").replaceChildren(el("p", "vacio", "No se pudo cargar el resumen.")); }
}

/* ---------- pestañas ---------- */
function pestana(t) {
  for (const k of ["resumen", "sinco", "onet", "meta"]) { $("v-" + k).hidden = k !== t; $("tab-" + k).classList.toggle("on", k === t); }
  if (t === "onet" && !$("lista-onet").children.length) cargarOnet();
  if (t === "meta") cargarMeta();
}
for (const k of ["resumen", "sinco", "onet", "meta"]) $("tab-" + k).addEventListener("click", () => pestana(k));

/* ---------- inicio ---------- */
cargarResumen();
(async () => {
  tree = await api("/api/sinco/tree"); indexar(tree.raices, null, 1);
  $("leyenda").innerHTML = tree.raices.map((d) => `<span><i style="background:${color(d)}"></i>${esc(d.c)} ${esc(d.t)}</span>`).join("");
  dibujar(); ruta();
  const h = location.hash.slice(1);   // enlaces directos: #4213 | #onet | #meta
  if (/^[1-9][0-9]{0,3}$/.test(h)) { pestana("sinco"); elegir(h, false); } else if (h === "onet" || h === "meta" || h === "sinco") pestana(h);
})();
