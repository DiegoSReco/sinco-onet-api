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
  c.setAttribute("r", R0 - 4); c.setAttribute("fill", "#0e1620"); c.style.cursor = "pointer";
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
    return h + lista(filas, (f) => `<li><span class="cod">${esc(f[claveOtro])}</span> ${esc(f.tipo_relacion)} · fuente: ${esc(f.fuente)} · <span class="tag">${esc(f.estado_validacion)}</span>` +
      (f.similitud !== undefined && f.similitud !== null ? `<div class="sub">similitud ${nf(f.similitud)} · rango ${esc(f.rango ?? "—")}` +
        (f.margen !== undefined && f.margen !== null ? ` · margen ${nf(f.margen)}` : "") + (f.baja_confianza ? ' · <span class="tag">baja confianza</span>' : "") +
        (f.modelo ? ` · modelo ${esc(f.modelo)}` : "") + (f.run_id ? ` · run ${esc(f.run_id)}` : "") + "</div>" : "") + "</li>");
  }
  if (cw.estado === "esquema_invalido") return `<div class="cw">Crosswalk con esquema inválido: ${esc(cw.mensaje)}</div>`;
  return `<div class="cw">⌛ ${esc(cw.mensaje)}. No existe una correspondencia oficial SINCO–CIUO-08–O*NET; no se muestran emparejamientos inferidos.</div>`;
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
    fila("Tablas (filas)", Object.entries(m.tablas).map(([k, v]) => `${k}: ${v}`).join("<br>")) +
    fila("Atribución", esc(m.atribucion)) + "</table>";
}

/* ---------- pestañas ---------- */
function pestana(t) {
  for (const k of ["sinco", "onet", "meta"]) { $("v-" + k).hidden = k !== t; $("tab-" + k).classList.toggle("on", k === t); }
  if (t === "onet" && !$("lista-onet").children.length) cargarOnet();
  if (t === "meta") cargarMeta();
}
for (const k of ["sinco", "onet", "meta"]) $("tab-" + k).addEventListener("click", () => pestana(k));

/* ---------- inicio ---------- */
(async () => {
  tree = await api("/api/sinco/tree"); indexar(tree.raices, null, 1);
  $("leyenda").innerHTML = tree.raices.map((d) => `<span><i style="background:${color(d)}"></i>${esc(d.c)} ${esc(d.t)}</span>`).join("");
  dibujar(); ruta();
  const h = location.hash.slice(1);   // enlaces directos: #4213 | #onet | #meta
  if (/^[1-9][0-9]{0,3}$/.test(h)) elegir(h, false); else if (h === "onet" || h === "meta") pestana(h);
})();
