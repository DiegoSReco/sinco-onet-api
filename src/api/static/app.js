"use strict";
/* Interfaz de solo lectura SINCO 2019 / O*NET. Ninguna cifra es fija: todo sale de la API. Sin librerias ni CDN (CSP estricta). */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = (p) => fetch(p).then((r) => { if (!r.ok) { const e = new Error(p + " -> " + r.status); e.status = r.status; throw e; } return r.json(); });
const NIV = ["", "División", "Grupo principal", "Subgrupo", "Grupo unitario"];
const NS = "http://www.w3.org/2000/svg";
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : "");
const nf = (x, d = 3) => (x === null || x === undefined ? "—" : Number(x).toFixed(d));
const fmt = (n) => Number(n).toLocaleString("es-MX");
function el(tag, cls, txt) { const e = document.createElement(tag); if (cls) e.className = cls; if (txt !== undefined) e.textContent = txt; return e; }
function svgEl(tag, attrs, cls) { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v); if (cls) e.setAttribute("class", cls); return e; }
function anunciar(t) { $("estado-sr").textContent = ""; setTimeout(() => ($("estado-sr").textContent = t), 30); }

let tree, byCode = {}, root = null, selected = null, unidades = [], vista = "resumen";

/* ---------- avisos, estados de carga / error / vacio ---------- */
let tToast;
function aviso(t) { const e = $("toast"); e.textContent = t; e.hidden = false; clearTimeout(tToast); tToast = setTimeout(() => (e.hidden = true), 2400); }
function esqueleto(c, n = 2) { c.replaceChildren(...Array.from({ length: n }, () => el("div", "esq"))); c.setAttribute("aria-busy", "true"); }
function errorCaja(c, msg, reintentar) {
  const d = el("div", "error"); d.setAttribute("role", "alert");
  d.append(el("b", "", msg), el("span", "sub", "Revisa que el servidor siga en marcha y vuelve a intentarlo."));
  if (reintentar) { const b = el("button", "btn-p", "Reintentar"); b.type = "button"; b.addEventListener("click", reintentar); d.append(b); }
  c.removeAttribute("aria-busy"); c.replaceChildren(d);
}
function vacioCaja(c, titulo, detalle, acciones) {
  const d = el("div", "vacio-gr"); d.append(el("b", "", titulo));
  if (detalle) d.append(el("span", "", detalle));
  if (acciones && acciones.length) { const ch = el("div", "chips"); acciones.forEach((a) => ch.append(a)); d.append(ch); }
  c.removeAttribute("aria-busy"); c.replaceChildren(d);
}
function chipBtn(txt, fn) { const b = el("button", "chip", txt); b.type = "button"; b.addEventListener("click", fn); return b; }
function tip(e, html) {
  const t = $("tip"); t.innerHTML = html; t.hidden = false;
  const w = t.offsetWidth, h = t.offsetHeight; let x = e.clientX + 12, y = e.clientY + 12;
  if (x + w > innerWidth - 8) x = Math.max(8, innerWidth - w - 8);
  if (y + h > innerHeight - 8) y = Math.max(8, e.clientY - h - 12);
  t.style.left = x + "px"; t.style.top = y + "px";
}
const ocultarTip = () => ($("tip").hidden = true);

/* ---------- ayuda "?" accesible (hover, foco y clic) ---------- */
const PROB_QUE_ES = "Qué es: la probabilidad de automatización de Frey y Osborne (2013/2017) para ocupaciones de EE. UU. (SOC 2010), trasladada a este grupo SINCO con un emparejamiento automático (media ponderada por similitud de sus 2 O*NET).";
const PROB_QUE_NO = "Qué NO es: no es exposición a IA, ni riesgo de pérdida de empleo, ni una estimación para México. Depende de un emparejamiento NO validado y de parámetros provisionales.";
function ayudaHtml(queEs, queNo) {
  const t = queEs + " " + queNo;
  return `<button type="button" class="qm" aria-label="Qué es y qué no es. ${esc(t)}" data-es="${esc(queEs)}" data-no="${esc(queNo)}">?</button>`;
}
function activarAyudas(raiz) {
  raiz.querySelectorAll("button.qm").forEach((b) => {
    const show = () => { const r = b.getBoundingClientRect(); tip({ clientX: r.left, clientY: r.bottom }, `${esc(b.dataset.es)}<br><br><b>${esc(b.dataset.no)}</b>`); };
    b.addEventListener("mouseenter", show); b.addEventListener("focus", show); b.addEventListener("click", show);
    b.addEventListener("mouseleave", ocultarTip); b.addEventListener("blur", ocultarTip);
    b.addEventListener("keydown", (e) => { if (e.key === "Escape") ocultarTip(); });
  });
}

/* ---------- tema, copiar enlace ---------- */
const TEMAS = ["auto", "claro", "oscuro"];
function aplicarTema(t) {
  const r = document.documentElement;
  if (t === "claro") r.dataset.theme = "light"; else if (t === "oscuro") r.dataset.theme = "dark"; else delete r.dataset.theme;
  $("tema").textContent = "Tema: " + t;
}
let temaActual = "auto";
try { const g = localStorage.getItem("tema"); if (TEMAS.includes(g)) temaActual = g; } catch (e) { /* sin almacenamiento */ }
aplicarTema(temaActual);
$("tema").addEventListener("click", () => {
  temaActual = TEMAS[(TEMAS.indexOf(temaActual) + 1) % TEMAS.length]; aplicarTema(temaActual);
  try { localStorage.setItem("tema", temaActual); } catch (e) { /* ok */ }
});
async function copiarEnlace() {
  const url = location.href;
  try { await navigator.clipboard.writeText(url); aviso("Enlace copiado"); }
  catch (e) {
    const ta = el("textarea"); ta.value = url; ta.style.cssText = "position:fixed;opacity:0"; document.body.appendChild(ta); ta.select();
    let ok = false; try { ok = document.execCommand("copy"); } catch (_) { /* ok */ } ta.remove();
    aviso(ok ? "Enlace copiado" : "No se pudo copiar: copia la dirección del navegador");
  }
}
$("copiar").addEventListener("click", copiarEnlace);

/* ---------- enrutado por hash: #vista/arg?filtros ---------- */
const VISTAS = ["resumen", "modelos", "conexiones", "sinco", "onet", "meta"];
const TITULOS = { resumen: "Resumen", modelos: "Modelos", conexiones: "Conexiones", sinco: "Jerarquía SINCO", onet: "Ocupaciones O*NET", meta: "Fuentes" };
function parseHash() {
  let raw = ""; try { raw = decodeURIComponent(location.hash.slice(1)); } catch (e) { /* hash mal formado */ }
  const [ruta, qs] = raw.split("?"); const [a, b] = ruta.split("/"); const p = new URLSearchParams(qs || "");
  if (/^[1-9][0-9]{0,3}$/.test(a)) return { v: "sinco", arg: a, p };   // enlaces antiguos: #4213
  if (VISTAS.includes(a)) return { v: a, arg: b || "", p };
  return { v: "resumen", arg: "", p };
}
function hashDe(v, arg, params) {
  const p = new URLSearchParams(); for (const [k, val] of Object.entries(params || {})) if (val) p.set(k, val);
  const s = p.toString(); return "#" + v + (arg ? "/" + encodeURIComponent(arg) : "") + (s ? "?" + s : "");
}
function ir(v, arg, params) { const h = hashDe(v, arg, params); if (location.hash === h) aplicarHash(); else location.hash = h; }
function fijarHash(v, arg, params) { try { history.replaceState(null, "", hashDe(v, arg, params)); } catch (e) { /* ok */ } }
const filtrosCon = () => ({ div: fl.div, soc: fl.soc });
function hashVista(k) {
  if (k === "conexiones") return ir("conexiones", conActual, filtrosCon());
  if (k === "sinco") return ir("sinco", selected, root ? { raiz: root.c } : {});
  if (k === "onet") return ir("onet", onetSel, { q: $("q-onet").value.trim(), pag: onetOff ? String(onetOff / LIM + 1) : "" });
  ir(k);
}
function mostrarVista(v) {
  vista = v;
  for (const k of VISTAS) { $("v-" + k).hidden = k !== v; $("tab-" + k).classList.toggle("on", k === v); if (k === v) $("tab-" + k).setAttribute("aria-current", "page"); else $("tab-" + k).removeAttribute("aria-current"); }
  document.title = TITULOS[v] + " · SINCO 2019 y O*NET";
  ocultarTip();
  requestAnimationFrame(trazar);
}
for (const k of VISTAS) $("tab-" + k).addEventListener("click", () => { hashVista(k); const h = $("v-" + k).querySelector(".vh"); if (h) h.focus({ preventScroll: true }); });
async function aplicarHash() {
  const { v, arg, p } = parseHash(); mostrarVista(v);
  if (v === "resumen" && arg === "guia") { $("guia").open = true; $("guia").scrollIntoView({ block: "start" }); }
  else if (v === "conexiones") {
    fl.div = /^[1-9]$/.test(p.get("div") || "") ? p.get("div") : ""; fl.soc = /^[0-9]{2}$/.test(p.get("soc") || "") ? p.get("soc") : "";
    cargarFlujo();
    if (arg && arg !== conActual) cargarConexion(arg); else if (!arg) { conActual = null; conDatos = null; invitacionConexion(); }
  } else if (v === "sinco") {
    await arbolListo;
    if (p.get("raiz") && byCode[p.get("raiz")] && (!root || root.c !== p.get("raiz"))) { root = byCode[p.get("raiz")]; selected = null; dibujar(); ruta(); }
    if (arg && arg !== selected && byCode[arg]) elegir(arg, false);
  } else if (v === "onet") {
    const q = p.get("q") || "", pag = Math.max(1, parseInt(p.get("pag") || "1", 10) || 1);
    const cambia = $("q-onet").value !== q || onetOff !== (pag - 1) * LIM || !$("lista-onet").children.length;
    $("q-onet").value = q; onetOff = (pag - 1) * LIM; if (cambia) cargarOnet();
    if (arg && arg !== onetSel) detalleOnet(arg);
  } else if (v === "modelos" && !modelosCargados) cargarModelos();
  else if (v === "meta" && !metaCargada) cargarMeta();
}
window.addEventListener("hashchange", aplicarHash);

/* ---------- combobox accesible (busqueda con sugerencias) ---------- */
function combo(input, lista, buscar, alElegir, vacioTxt) {
  let items = [], act = -1, tmr, seq = 0;
  const selecc = () => items.map((x, i) => i).filter((i) => !items[i].cab);
  function cerrar() { lista.hidden = true; input.setAttribute("aria-expanded", "false"); input.removeAttribute("aria-activedescendant"); act = -1; }
  function pintar() {
    lista.replaceChildren();
    items.forEach((it, i) => {
      const d = el("div", it.cab ? "opt-cab" : "opt"); d.id = lista.id + "-" + i;
      if (it.cab) { d.setAttribute("role", "presentation"); d.textContent = it.cab; }
      else { d.setAttribute("role", "option"); d.setAttribute("aria-selected", String(i === act)); d.innerHTML = it.html; d.addEventListener("mousedown", (ev) => { ev.preventDefault(); elegirIdx(i); }); }
      lista.append(d);
    });
    lista.hidden = false; input.setAttribute("aria-expanded", "true");
    if (act >= 0) { input.setAttribute("aria-activedescendant", lista.id + "-" + act); lista.children[act].scrollIntoView({ block: "nearest" }); } else input.removeAttribute("aria-activedescendant");
  }
  function elegirIdx(i) { const it = items[i]; cerrar(); if (it && !it.cab) alElegir(it); }
  async function consultar() {
    const q = input.value.trim(), mi = ++seq;
    if (q.length < 2) { cerrar(); return; }
    try {
      const r = await buscar(q); if (mi !== seq) return;
      items = r.length ? r : [{ cab: vacioTxt || "Sin resultados" }]; act = -1; pintar();
      anunciar(r.length ? `${selecc().length} sugerencias` : "Sin resultados");
    } catch (e) { if (mi !== seq) return; items = [{ cab: "No se pudo buscar. Intenta de nuevo." }]; act = -1; pintar(); }
  }
  input.addEventListener("input", () => { clearTimeout(tmr); tmr = setTimeout(consultar, 200); });
  input.addEventListener("focus", () => { if (input.value.trim().length >= 2 && lista.hidden) consultar(); });
  input.addEventListener("blur", () => setTimeout(cerrar, 120));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { cerrar(); return; }
    if (lista.hidden && e.key === "ArrowDown") { consultar(); return; }
    if (lista.hidden) return;
    const s = selecc(); if (!s.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); const pos = s.indexOf(act); act = s[e.key === "ArrowDown" ? (pos + 1) % s.length : (pos <= 0 ? s.length - 1 : pos - 1)]; pintar();
    } else if (e.key === "Enter") { e.preventDefault(); elegirIdx(act >= 0 ? act : s[0]); }
  });
  return { cerrar };
}

/* ---------- datos del arbol SINCO ---------- */
function indexar(nodes, parent, depth) {
  let v = 0;
  for (const n of nodes) {
    n.parent = parent; n.d = depth; byCode[n.c] = n;
    n.v = n.ch.length ? indexar(n.ch, n, depth + 1) : 1;
    if (!n.ch.length && n.c.length === 4) unidades.push(n.c);
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
  const niveles = 5 - baseDepth;
  const R0 = 62, R1 = 292, dr = (R1 - R0) / niveles;
  const g = svgEl("g"); svg.appendChild(g);
  (function rec(nodes, a0, a1, lvl) {
    const tot = nodes.reduce((s, n) => s + n.v, 0);
    let a = a0;
    for (const n of nodes) {
      const b = a + (a1 - a0) * n.v / tot;
      const r0 = R0 + lvl * dr, r1 = r0 + dr;
      const p = svgEl("path", { d: arcPath(a, b, r0, r1), fill: color(n) });
      if (selected === n.c) p.setAttribute("class", "sel");
      p.addEventListener("click", () => elegir(n.c, true));
      p.addEventListener("mousemove", (e) => tip(e, `<b>${esc(n.c)}</b> ${esc(n.t)}<br><span class="sub">${NIV[n.n]}${n.c.length === 4 ? " · clic para ver detalle y conexiones" : " · clic para acercar"}</span>`));
      p.addEventListener("mouseleave", ocultarTip);
      g.appendChild(p);
      const am = (a + b) / 2, rm = (r0 + r1) / 2;
      if ((b - a) * rm > 20 && lvl < 3) {
        const t = svgEl("text", { x: rm * Math.sin(am), y: -rm * Math.cos(am) + 3 }); t.textContent = n.c; g.appendChild(t);
      }
      if (n.ch.length && lvl + 1 < niveles) rec(n.ch, a, b, lvl + 1);
      a = b;
    }
  })(hijos, 0, 2 * Math.PI, 0);
  const c = svgEl("circle", { r: R0 - 4 }); c.style.fill = "var(--inp)"; c.style.cursor = "pointer";
  c.addEventListener("click", () => { root = root ? root.parent : null; selected = null; dibujar(); ruta(); });
  svg.appendChild(c);
  const t = svgEl("text", { y: 4 }, "centro-txt"); t.textContent = root ? "↑ " + root.c : "SINCO 2019"; svg.appendChild(t);
  const lst = $("sun-lista"); lst.replaceChildren();
  for (const n of hijos) { const b = el("button", "", `${n.c} ${n.t}`); b.type = "button"; b.addEventListener("click", () => elegir(n.c, true)); lst.appendChild(b); }
}
function ruta() {
  const cadena = []; for (let n = root; n; n = n.parent) cadena.unshift(n);
  $("ruta").innerHTML = '<a href="#sinco" data-c="">SINCO</a>' + cadena.map((n) => ` › <a href="#sinco?raiz=${n.c}" data-c="${n.c}">${esc(n.c)} ${esc(n.t.slice(0, 40))}</a>`).join("");
  $("ruta").querySelectorAll("a").forEach((a) => a.addEventListener("click", (ev) => { ev.preventDefault(); root = a.dataset.c ? byCode[a.dataset.c] : null; selected = null; dibujar(); ruta(); guardarHashSinco(); }));
}
function guardarHashSinco() { if (vista === "sinco") fijarHash("sinco", selected, root ? { raiz: root.c } : {}); }
$("btn-raiz").addEventListener("click", () => { root = null; selected = null; dibujar(); ruta(); guardarHashSinco(); $("btn-con").disabled = true; });
$("btn-con").addEventListener("click", () => { if (selected && selected.length === 4) ir("conexiones", selected, filtrosCon()); });

/* ---------- seleccion y detalle SINCO ---------- */
async function elegir(code, zoom) {
  const n = byCode[code]; if (!n) return;
  selected = code;
  if (zoom && n.ch.length) root = n; else root = n.parent || null;
  dibujar(); ruta(); guardarHashSinco();
  const unit = code.length === 4;
  $("btn-con").disabled = !unit; $("btn-con").title = unit ? "Ver con qué ocupaciones O*NET se conecta" : "Elige un grupo unitario (anillo exterior)";
  const cont = $("detalle"); esqueleto(cont, 3);
  try {
    const d = await api("/api/sinco/" + code); if (selected !== code) return;
    cont.removeAttribute("aria-busy"); cont.innerHTML = htmlDetalle(d);
    cont.querySelectorAll("a.ref").forEach((a) => a.addEventListener("click", () => elegir(a.dataset.c, false)));
    activarAyudas(cont); cont.scrollTop = 0;
  } catch (e) { errorCaja(cont, "No se pudo cargar el detalle de " + code + ".", () => elegir(code, zoom)); }
}
function lista(items, f) { return items.length ? "<ul>" + items.map(f).join("") + "</ul>" : '<p class="vacio">Sin datos en el PDF para este nivel.</p>'; }
const AVISO_A1 = "coincidencias automáticas sin validar (Método A1, embeddings)";
function htmlCW(cw, claveOtro) {
  if (cw.estado === "disponible") {
    const filas = cw.filas;
    if (!filas.length) return '<div class="cw">Sin coincidencias registradas para este elemento.</div>';
    const a1 = filas.some((f) => /embeddings/i.test(f.fuente || "") || f.estado_validacion === "sin_validar");
    const sinValidar = filas.some((f) => f.estado_validacion === "sin_validar");
    let h = "";
    if (a1 && sinValidar) h += `<div class="cw aviso-a1" role="note"><b>Aviso: ${AVISO_A1}.</b> Son propuestas de similitud semántica, no una correspondencia oficial ni validada; la similitud no es una probabilidad.</div>`;
    h += `<div class="cw ok">${filas.length} coincidencia(s) registradas. ${esc(cw.aviso || "")}</div>`;
    return h + lista(filas, (f) => `<li class="match"><span class="cod">${esc(f[claveOtro])}</span>${f.onet_titulo ? esc(f.onet_titulo) : ""} <span class="sub">· ${esc(f.tipo_relacion)} · fuente: ${esc(f.fuente)}</span> <span class="tag">${esc(f.estado_validacion)}</span>` +
      (f.similitud !== undefined && f.similitud !== null ? `<div class="sub">similitud ${nf(f.similitud)} · rango ${esc(f.rango ?? "—")}` +
        (f.margen !== undefined && f.margen !== null ? ` · margen ${nf(f.margen)}` : "") + (f.baja_confianza ? ' · <span class="tag">baja confianza</span>' : "") +
        (f.modelo ? ` · modelo ${esc(f.modelo)}` : "") + (f.run_id ? ` · run ${esc(f.run_id)}` : "") + "</div>" : "") + "</li>");
  }
  if (cw.estado === "esquema_invalido") return `<div class="cw">Las coincidencias no se pueden mostrar: el archivo tiene un esquema inválido (${esc(cw.mensaje)}).</div>`;
  return `<div class="cw">Aún no hay coincidencias cargadas (${esc(cw.mensaje)}). No existe una correspondencia oficial SINCO–CIUO-08–O*NET; no se muestran emparejamientos inferidos.</div>`;
}
const MOTIVO_NA = { sin_coincidencia: "este grupo no tiene coincidencia con O*NET, así que no hay a qué trasladar el valor", sin_probabilidad_fo: "la ocupación de EE. UU. emparejada no tiene valor en el estudio de Frey y Osborne" };
function htmlProb(p) {
  const titulo = `<b>Probabilidad de automatización (Frey-Osborne)</b><span class="tag">NO validada</span>${ayudaHtml(PROB_QUE_ES, PROB_QUE_NO)}`;
  if (!p || p.estado === "no_disponible" || p.estado === "esquema_invalido")
    return `<div class="prob vacia" role="note">${titulo}<div>Probabilidad no disponible: la tabla de probabilidades no existe en esta instalación${p && p.estado === "esquema_invalido" ? " (esquema inválido: " + esc(p.mensaje) + ")" : ""}.</div></div>`;
  if (p.estado === "sin_fila") return `<div class="prob vacia" role="note">${titulo}<div>${esc(cap(p.mensaje))}.</div></div>`;
  const v = p.valores, pc = (x) => (x === null || x === undefined ? "—" : (x * 100).toFixed(1) + " %");
  const val = v.probabilidad_automatizacion_fo;
  return `<div class="prob" role="note">${titulo}<div class="valor">${val === null ? "sin valor" : pc(val)}</div>` +
    (val === null ? `<div class="sub">Sin valor porque ${esc(MOTIVO_NA[v.motivo_na] || v.motivo_na || "—")}.</div>` : "") +
    `<div class="sub">media uniforme ${pc(v.probabilidad_automatizacion_fo_media_uniforme)} · mín ${pc(v.probabilidad_automatizacion_fo_min)} · máx ${pc(v.probabilidad_automatizacion_fo_max)} · mejor coincidencia ${pc(v.probabilidad_automatizacion_fo_top1)}</div>` +
    `<div class="sub">candidatos ${esc(v.n_candidatos)} · cobertura de peso F-O ${nf(v.cobertura_peso_fo, 2)} (${esc(v.cobertura_fo || "—")}) · modelo ${esc(v.modelo)} · run ${esc(v.run_id)}</div>` +
    `<div class="sub">${esc(PROB_QUE_NO)}</div></div>`;
}
function htmlDetalle(d) {
  const n = d.nodo, unit = n.sinco_code.length === 4;
  let h = `<h2><span class="cod">${esc(n.sinco_code)}</span>${esc(n.titulo)}</h2><div class="sub">${NIV[n.sinco_code.length]} · página PDF ${n.pagina_pdf_estructura} (versión abreviada)</div>`;
  h += '<div class="sub">' + d.ancestros.map((a) => `<a class="ref" data-c="${a.sinco_code}">${esc(a.sinco_code)} ${esc(a.titulo)}</a>`).join(" › ") + "</div>";
  h += `<div class="acciones">${unit ? `<a class="btn-p" href="#conexiones/${n.sinco_code}">Ver conexiones con O*NET</a>` : '<span class="sub">Para ver conexiones elige un grupo unitario (4 dígitos) de la lista «Contiene».</span>'}</div>`;
  if (d.descripcion) {
    h += `<h3>Descripción</h3><p>${esc(d.descripcion.texto) || '<span class="vacio">Grupo residual: el PDF solo trae el título.</span>'}</p>`;
    h += `<div class="sub">PDF pp. ${d.descripcion.pagina_pdf_inicio}–${d.descripcion.pagina_pdf_fin}${d.descripcion.pagina_impresa_inicio ? " (impresa " + d.descripcion.pagina_impresa_inicio + ")" : ""}</div>`;
    if (d.descripcion.notas_extraccion) h += `<div class="sub">Nota de extracción: ${esc(d.descripcion.notas_extraccion)}</div>`;
  }
  if (d.hijos.length) h += `<h3>Contiene (${d.hijos.length})</h3>` + lista(d.hijos, (c) => `<li><a class="ref" data-c="${c.sinco_code}"><span class="cod">${c.sinco_code}</span>${esc(c.titulo)}</a></li>`);
  if (unit) {
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
  if (unit) h += "<h3>Exposición por modelos</h3>" + htmlExpo(d.exposicion_agentes, false);
  return h;
}

/* ---------- busqueda en la jerarquia SINCO ---------- */
combo($("q-sinco"), $("res-sinco"),
  async (q) => (await api("/api/sinco/search?q=" + encodeURIComponent(q) + "&limit=30")).resultados.map((x) => ({ code: x.sinco_code, html: `<span class="cod">${esc(x.sinco_code)}</span>${esc(x.titulo)}<small>${esc(cap(NIV[x.sinco_code.length].toLowerCase()))} · ${esc(x.motivo)}</small>` })),
  (it) => { $("q-sinco").value = ""; elegir(it.code, false); }, "Sin resultados. Prueba con otra palabra o con el código.");

/* ---------- buscador global ---------- */
const gc = combo($("q-global"), $("res-global"),
  async (q) => {
    const [s, o] = await Promise.all([api("/api/sinco/search?q=" + encodeURIComponent(q) + "&limit=6"), api("/api/onet/occupations?q=" + encodeURIComponent(q) + "&limit=5")]);
    const out = [];
    if (s.resultados.length) {
      out.push({ cab: "SINCO" });
      for (const x of s.resultados) out.push({ tipo: "sinco", code: x.sinco_code, html: `<span class="cod">${esc(x.sinco_code)}</span>${esc(x.titulo)}<small>${esc(NIV[x.sinco_code.length])}${x.sinco_code.length === 4 ? " · ver conexiones" : " · ver en la jerarquía"} · ${esc(x.motivo)}</small>` });
    }
    if (o.resultados.length) {
      out.push({ cab: "O*NET (en inglés)" });
      for (const x of o.resultados) out.push({ tipo: "onet", code: x.onet_soc_code, html: `<span class="cod">${esc(x.onet_soc_code)}</span>${esc(x.titulo_en)}<small>Ocupación O*NET · ver qué SINCO apuntan a ella</small>` });
    }
    return out;
  },
  (it) => { $("q-global").value = ""; if (it.tipo === "onet") ir("onet", it.code); else if (it.code.length === 4) ir("conexiones", it.code, filtrosCon()); else ir("sinco", it.code); },
  "Sin resultados en SINCO ni en O*NET. Prueba con otra palabra o con un código.");
document.addEventListener("keydown", (e) => {
  const t = e.target, escribiendo = t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName);
  if (e.key === "/" && !escribiendo && !e.ctrlKey && !e.metaKey) { e.preventDefault(); $("q-global").focus(); }
  else if (!escribiendo && vista === "conexiones" && conDatos && !e.altKey && !e.ctrlKey && !e.metaKey) {
    if (e.key === "ArrowLeft" && conDatos.anterior) ir("conexiones", conDatos.anterior.sinco_code, filtrosCon());
    else if (e.key === "ArrowRight" && conDatos.siguiente) ir("conexiones", conDatos.siguiente.sinco_code, filtrosCon());
  }
});

/* ---------- CONEXIONES SINCO <-> O*NET ---------- */
let conActual = null, conDatos = null, conSeq = 0, roCon = null;
const EST = {
  mejor_coincidencia: { txt: "Mejor coincidencia", cls: "ok", sw: "ok", def: "El O*NET más parecido a este grupo SINCO, con similitud suficiente." },
  segunda_opcion: { txt: "Segunda opción", cls: "seg", sw: "seg2", def: "El segundo O*NET más parecido. Puede ser un buen complemento de la mejor coincidencia." },
  baja_confianza: { txt: "Baja confianza", cls: "baja", sw: "baja", def: "Hay propuesta, pero la similitud es modesta o hay otra opción casi igual. Revísala con cuidado." },
  sin_coincidencia: { txt: "Sin coincidencia", cls: "sin", sw: "sin", def: "Ningún O*NET fue lo bastante parecido. Los candidatos se muestran solo como referencia." },
};
const chipEstado = (m) => `<span class="estado"><i class="sw ${EST[m.estado].sw}" aria-hidden="true"></i>${esc(cap(m.estado_etiqueta))}</span>`;
const picker = combo($("q-con"), $("res-con"),
  async (q) => (await api("/api/sinco/search?q=" + encodeURIComponent(q) + "&limit=100")).resultados.filter((x) => x.sinco_code.length === 4).slice(0, 12)
    .map((x) => ({ code: x.sinco_code, html: `<span class="cod">${esc(x.sinco_code)}</span>${esc(x.titulo)}<small>${esc(x.motivo)}</small>` })),
  (it) => ir("conexiones", it.code, filtrosCon()), "Sin grupos unitarios con ese texto. Prueba con un código de 4 dígitos o con otra palabra.");
$("q-con").addEventListener("focus", (e) => e.target.select());
$("con-ant").addEventListener("click", () => conDatos && conDatos.anterior && ir("conexiones", conDatos.anterior.sinco_code, filtrosCon()));
$("con-sig").addEventListener("click", () => conDatos && conDatos.siguiente && ir("conexiones", conDatos.siguiente.sinco_code, filtrosCon()));
$("con-azar").addEventListener("click", async () => { await arbolListo; if (unidades.length) ir("conexiones", unidades[Math.floor(Math.random() * unidades.length)], filtrosCon()); });

function actualizarNavCon(d) {
  const a = $("con-ant"), s = $("con-sig");
  a.disabled = !d || !d.anterior; s.disabled = !d || !d.siguiente;
  a.title = d && d.anterior ? `${d.anterior.sinco_code} ${d.anterior.titulo}` : ""; s.title = d && d.siguiente ? `${d.siguiente.sinco_code} ${d.siguiente.titulo}` : "";
  const h = $("con-herm"); h.replaceChildren();
  if (d && d.hermanos.length) {
    h.hidden = false; h.append(el("span", "", `Del mismo subgrupo (${d.sinco.subgrupo}${d.sinco.subgrupo_titulo ? " " + d.sinco.subgrupo_titulo : ""}):`));
    for (const x of d.hermanos) { const b = chipBtn(`${x.sinco_code} ${x.titulo.length > 38 ? x.titulo.slice(0, 36) + "…" : x.titulo}`, () => ir("conexiones", x.sinco_code, filtrosCon())); b.title = x.titulo; h.append(b); }
  } else h.hidden = true;
}
function invitacionConexion() {
  actualizarNavCon(null); $("con-extra").replaceChildren(); $("q-con").value = "";
  const L = $("con-lienzo");
  const ej = [0, 3, 6].map((i) => { const f = tree && tree.raices[i]; if (!f) return null; let n = f; while (n.ch.length) n = n.ch[0]; return n.c; }).filter(Boolean);
  vacioCaja(L, "Elige un grupo SINCO para ver sus conexiones", "Escribe un código o parte del título arriba. Verás una tarjeta del grupo, a la izquierda, unida con líneas a las ocupaciones O*NET que más se le parecen, a la derecha.",
    ej.map((c) => chipBtn(`${c} ${byCode[c] ? byCode[c].t.slice(0, 40) : ""}`, () => ir("conexiones", c, filtrosCon()))));
}
async function cargarConexion(code) {
  const seq = ++conSeq; conActual = code; const L = $("con-lienzo");
  esqueleto(L, 2); $("con-extra").replaceChildren();
  try {
    const d = await api("/api/conexiones/" + encodeURIComponent(code)); if (seq !== conSeq) return;
    conDatos = d; pintarConexion(d); fijarHash("conexiones", code, filtrosCon()); anunciar(`Conexión del grupo ${code} cargada`);
  } catch (e) {
    if (seq !== conSeq) return; conDatos = null; actualizarNavCon(null);
    if (e.status === 404) vacioCaja(L, `No encontramos el grupo «${code}»`, "Las conexiones se calculan por grupo unitario SINCO, que tiene 4 dígitos. Busca por código o por título en el cuadro de arriba.", [chipBtn("Ver uno al azar", () => $("con-azar").click())]);
    else errorCaja(L, "No se pudo cargar la conexión.", () => cargarConexion(code));
  }
}
function tarjetaSinco(d) {
  const s = d.sinco, a = el("article", "c-card c-sinco"); a.id = "c-sinco";
  a.setAttribute("aria-label", "Grupo SINCO " + s.sinco_code);
  a.innerHTML = `<div class="c-eyebrow">Grupo SINCO · División ${esc(s.division)} ${esc(s.division_titulo)}</div><div class="c-cod"><span class="cod">${esc(s.sinco_code)}</span></div><h3>${esc(s.titulo)}</h3>` +
    (s.descripcion_corta ? `<p>${esc(s.descripcion_corta)}</p>` : '<p class="sub">Grupo residual: el catálogo solo trae el título.</p>') +
    (s.ocupaciones_ejemplo.length ? `<div class="c-eyebrow">Ocupaciones de ejemplo</div><div class="ejemplos">${s.ocupaciones_ejemplo.map((o) => `<span>${esc(o.replace(/\.$/, ""))}</span>`).join("")}</div>` : "") +
    `<div class="acciones"><a class="btn-s" href="#sinco/${esc(s.sinco_code)}">Ver en la jerarquía</a></div>`;
  return a;
}
function tarjetaOnet(m, i) {
  const e = EST[m.estado], a = el("article", "c-card c-onet st-" + e.cls); a._m = m; a.dataset.i = i;
  a.setAttribute("aria-label", `${cap(m.estado_etiqueta)}: ${m.onet_titulo}`);
  const baja2 = m.baja_confianza && m.estado === "segunda_opcion" ? ' <span class="estado"><i class="sw baja" aria-hidden="true"></i>Baja confianza</span>' : "";
  a.innerHTML = `<div class="c-top">${chipEstado(m)}${baja2}</div><h3>${esc(m.onet_titulo)}</h3>` +
    `<div class="c-meta"><span class="cod">${esc(m.onet_soc_code)}</span><span class="sub">${esc(m.soc_grupo)} · ${esc(m.soc_grupo_nombre || "")}</span></div>` +
    `<p>${esc(m.onet_descripcion_corta)}</p>` +
    `<div class="sim"><div class="sim-lab"><span>Similitud (0 a 1)</span><b>${nf(m.similitud)}</b></div><div class="sim-pista" role="img" aria-label="Similitud ${nf(m.similitud)} en una escala de 0 a 1"><i></i></div></div>` +
    `<div class="acciones"><a class="btn-s" href="#onet/${esc(m.onet_soc_code)}">Ver ocupación O*NET y qué SINCO apuntan a ella</a></div>`;
  a.querySelector(".sim-pista i").style.width = Math.max(0, Math.min(1, m.similitud || 0)) * 100 + "%";
  return a;
}
function probCompacta(p) {
  const cab = `<h4>Probabilidad de automatización (Frey-Osborne) <span class="tag">NO validada</span>${ayudaHtml(PROB_QUE_ES, PROB_QUE_NO)}</h4>`;
  const pc = (x) => (x * 100).toFixed(1) + " %";
  if (!p || p.estado === "no_disponible" || p.estado === "esquema_invalido" || p.estado === "sin_fila" || !p.valores)
    return `<div class="prob vacia" role="note">${cab}<div>Probabilidad no disponible para este grupo.</div></div>`;
  const v = p.valores, val = v.probabilidad_automatizacion_fo;
  if (val === null) return `<div class="prob vacia" role="note">${cab}<div>Sin valor: ${esc(MOTIVO_NA[v.motivo_na] || v.motivo_na || "no disponible")}.</div></div>`;
  return `<div class="prob" role="note">${cab}<div class="valor">${pc(val)}</div><div class="sub">Dato de ocupaciones de EE. UU., trasladado por la coincidencia. No es exposición a IA ni riesgo de perder el empleo.</div></div>`;
}
function pintarConexion(d) {
  const L = $("con-lienzo"), s = d.sinco;
  L.removeAttribute("aria-busy"); L.replaceChildren(); $("con-extra").replaceChildren();
  $("q-con").value = `${s.sinco_code} ${s.titulo}`.slice(0, 80); actualizarNavCon(d);
  const sinCoin = d.estado_grupo === "sin_coincidencia";
  if (sinCoin) {
    const av = el("div", "c-aviso"); av.setAttribute("role", "note");
    av.innerHTML = "<b>Este grupo no tiene coincidencia.</b> El modelo no encontró una ocupación de O*NET lo bastante parecida. Abajo se muestran los candidatos más cercanos solo como referencia, no como propuesta.";
    L.append(av);
  }
  const con = el("div", "con"); con.id = "con";
  con.append(tarjetaSinco(d));
  const svg = svgEl("svg", { "aria-hidden": "true" }, "con-svg"); con.append(svg);
  if (d.estado === "disponible" && d.coincidencias.length) {
    const der = el("div", "c-der"); d.coincidencias.forEach((m, i) => der.append(tarjetaOnet(m, i))); con.append(der);
  } else {
    const v = el("div", "c-der"); const c = el("div", "vacio-gr");
    c.append(el("b", "", d.estado === "disponible" ? "Este grupo no tiene coincidencias" : "Aún no hay coincidencias cargadas"),
      el("span", "", d.estado === "disponible" ? "No hay filas para este grupo en la tabla de coincidencias." : (d.mensaje || "Las coincidencias no están disponibles.")));
    v.append(c); con.append(v);
  }
  L.append(con);
  if (roCon) roCon.disconnect();
  if (window.ResizeObserver) { roCon = new ResizeObserver(() => requestAnimationFrame(trazar)); roCon.observe(con); }
  requestAnimationFrame(trazar);

  const X = $("con-extra");
  const glos = el("div", "glos"); glos.setAttribute("aria-label", "Qué significa cada etiqueta");
  for (const k of ["mejor_coincidencia", "segunda_opcion", "baja_confianza", "sin_coincidencia"]) {
    const g = el("div"); g.innerHTML = `<i class="sw ${EST[k].sw}" aria-hidden="true"></i><span><b>${esc(EST[k].txt)}.</b> ${esc(EST[k].def)}</span>`; glos.append(g);
  }
  X.append(glos);
  const pie = el("div", "c-pie");
  const ex = el("div", "card"); ex.innerHTML = `<h4>Cómo se calculó</h4><p style="margin:0;font-size:13px">${esc(d.explicacion)}</p><p class="sub" style="margin:6px 0 0">La línea más gruesa y la barra más larga indican mayor similitud; el número es la similitud exacta. Grosor y barra usan la misma escala de 0 a 1.</p>`;
  const pr = el("div"); pr.innerHTML = probCompacta(d.probabilidad_automatizacion_fo);
  pie.append(ex, pr); X.append(pie);
  const xp = el("div", "c-expo"); xp.innerHTML = htmlExpo(d.exposicion_agentes, true); X.append(xp); activarAyudas(X);
  if (d.coincidencias.length) {
    X.append(tablaDet(["Rango", "O*NET", "Título (inglés)", "Similitud", "Margen", "Estado"],
      d.coincidencias.map((m) => [m.rango, m.onet_soc_code, m.onet_titulo, nf(m.similitud), nf(m.margen), cap(m.estado_etiqueta) + (m.baja_confianza && m.estado === "segunda_opcion" ? " (baja confianza)" : "")]), "Ver como tabla", 2));
  }
}
/* Lineas curvas SVG: grosor proporcional a la similitud (escala 0 a 1). Horizontales en escritorio; en movil bajan por el margen izquierdo. */
function trazar() {
  const con = $("con"); if (!con || con.offsetParent === null) return;
  const svg = con.querySelector("svg.con-svg"); svg.replaceChildren();
  const R = con.getBoundingClientRect(), Lr = $("c-sinco").getBoundingClientRect();
  const cards = [...con.querySelectorAll(".c-onet")]; if (!cards.length) return;
  svg.setAttribute("viewBox", `0 0 ${R.width} ${R.height}`);
  const apilado = cards[0].getBoundingClientRect().left < Lr.right - 10;
  const pills = [];
  cards.forEach((c, i) => {
    const m = c._m, rc = c.getBoundingClientRect(), e = EST[m.estado];
    const w = Math.max(2, 22 * (m.similitud || 0));
    let d, mx, my, x1, y1;
    if (!apilado) {
      const off = (i - (cards.length - 1) / 2) * Math.min(w + 4, 26);
      const x0 = Lr.right - R.left, y0 = Lr.top + Lr.height / 2 - R.top + off; x1 = rc.left - R.left; y1 = rc.top + rc.height / 2 - R.top;
      const dx = (x1 - x0) * 0.5; d = `M${x0},${y0}C${x0 + dx},${y0} ${x1 - dx},${y1} ${x1},${y1}`; mx = (x0 + x1) / 2; my = (y0 + y1) / 2;
    } else {
      const x0 = 14 + i * 20, y0 = Lr.bottom - R.top; x1 = rc.left - R.left; y1 = rc.top + 34 - R.top;
      d = `M${x0},${y0}C${x0},${y1} ${x0},${y1} ${x1},${y1}`; mx = null;
    }
    svg.append(svgEl("path", { d, "stroke-width": Math.min(w, apilado ? 12 : 30) }, "ln ln-" + e.cls));
    svg.append(svgEl("circle", { cx: x1, cy: y1, r: 5 }, "ln-pt ln-" + e.cls));
    if (mx !== null) pills.push([mx, my, nf(m.similitud)]);
  });
  for (const [x, y, t] of pills) {
    const g = svgEl("g", {}, "pill"); g.append(svgEl("rect", { x: x - 24, y: y - 11, width: 48, height: 22, rx: 11 }), svgEl("text", { x, y }));
    g.lastChild.textContent = t; svg.append(g);
  }
}
window.addEventListener("resize", () => requestAnimationFrame(trazar));
function tablaDet(cab, filas, resumenTxt, izqDesde) {
  const d = el("details", "r-det"); d.appendChild(el("summary", "", resumenTxt));
  const sc = el("div", "tabla-scroll"); const t = el("table", "r-tab"); const th = el("tr"); cab.forEach((c) => th.appendChild(el("th", "", c))); t.appendChild(th);
  for (const f of filas) { const tr = el("tr"); f.forEach((c, i) => tr.appendChild(el("td", izqDesde !== undefined && i <= izqDesde ? "izq-t" : "", c))); t.appendChild(tr); }
  sc.appendChild(t); d.appendChild(sc); return d;
}

/* ---------- panorama: cinta division SINCO -> gran grupo SOC (SVG propio) ---------- */
const fl = { div: "", soc: "" };
let flData = null, filas1 = null;
async function cargarFlujo() {
  const cont = $("flujo");
  if (flData) { dibujarFlujo(); return; }
  try { flData = await api("/api/conexiones/flujo"); } catch (e) { errorCaja(cont, "No se pudo cargar el panorama.", cargarFlujo); return; }
  dibujarFlujo();
}
function partir(txt, max) {
  const out = []; let l = "";
  for (const w of String(txt).split(" ")) { if ((l + " " + w).trim().length > max && l) { out.push(l); l = w; } else l = (l + " " + w).trim(); }
  if (l) out.push(l); return out;
}
function distribuir(items, k, gap, minLinea, anchoLinea, y0) {   // posiciones verticales de una columna de nodos
  let y = y0; const pos = {};
  for (const it of items) {
    const lineas = partir(it.etq, anchoLinea), h = it.n * k, slot = Math.max(h, (lineas.length + 1) * minLinea);
    pos[it.id] = { y, slot, h, lineas, n: it.n, cur: 0, ini: y + (slot - h) / 2 }; y += slot + gap;
  }
  return { pos, fin: y - gap };
}
function dibujarFlujo() {
  const cont = $("flujo"), f = flData; cont.removeAttribute("aria-busy"); cont.replaceChildren();
  if (f.estado !== "disponible") { vacioCaja(cont, "El panorama aún no está disponible", f.mensaje || "Faltan las coincidencias SINCO–O*NET."); return; }
  const nDiv = {}; f.enlaces.forEach((e) => (nDiv[e.division] = (nDiv[e.division] || 0) + e.n));
  const k = 460 / f.total_grupos;
  const izq = distribuir(f.divisiones.filter((d) => nDiv[d.division]).map((d) => ({ id: d.division, n: nDiv[d.division], etq: `${d.division} · ${d.nombre}` })), k, 10, 13.5, 30, 30);
  const der = distribuir(f.grupos_soc.map((g) => ({ id: g.soc_grupo, n: g.n, etq: `${g.soc_grupo} · ${g.nombre}` })), k, 6, 13.5, 36, 30);
  const H = Math.max(izq.fin, der.fin) + 16, xL = 230, nw = 14, xR = 700, W = 1050;
  const dyI = (H - 16 - 30 - (izq.fin - 30)) / 2; for (const p of Object.values(izq.pos)) { p.y += Math.max(0, dyI); p.ini += Math.max(0, dyI); }
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Diagrama de cintas: divisiones SINCO a la izquierda, grandes grupos SOC a la derecha; el ancho es el número de grupos SINCO. Hay una tabla equivalente debajo." }, "flujo-svg");
  svg.append(Object.assign(svgEl("text", { x: xL - 8, y: 14, "text-anchor": "end" }, "f-eje"), { textContent: "División SINCO" }));
  svg.append(Object.assign(svgEl("text", { x: xR + nw + 8, y: 14 }, "f-eje"), { textContent: "Gran grupo SOC (O*NET de mejor coincidencia)" }));
  const enl = f.enlaces.map((e) => ({ ...e }));
  enl.sort((a, b) => a.division.localeCompare(b.division) || a.soc_grupo.localeCompare(b.soc_grupo)); enl.forEach((e) => { e.yi = izq.pos[e.division].ini + izq.pos[e.division].cur; izq.pos[e.division].cur += e.n * k; });
  enl.sort((a, b) => a.soc_grupo.localeCompare(b.soc_grupo) || a.division.localeCompare(b.division)); enl.forEach((e) => { e.yd = der.pos[e.soc_grupo].ini + der.pos[e.soc_grupo].cur; der.pos[e.soc_grupo].cur += e.n * k; });
  const hayFiltro = fl.div || fl.soc, gR = svgEl("g");
  const nomSoc = Object.fromEntries(f.grupos_soc.map((g) => [g.soc_grupo, g.nombre])), nomDiv = Object.fromEntries(f.divisiones.map((d) => [d.division, d.nombre]));
  for (const e of enl) {
    const x0 = xL + nw, x1 = xR, xm = (x0 + x1) / 2, h = e.n * k;
    const d = `M${x0},${e.yi}C${xm},${e.yi} ${xm},${e.yd} ${x1},${e.yd}L${x1},${e.yd + h}C${xm},${e.yd + h} ${xm},${e.yi + h} ${x0},${e.yi + h}Z`;
    const act = hayFiltro && (!fl.div || fl.div === e.division) && (!fl.soc || fl.soc === e.soc_grupo);
    const r = svgEl("path", { d }, "f-rib" + (hayFiltro ? (act ? " act" : " dim") : ""));
    const txt = `División ${e.division} ${nomDiv[e.division]} → SOC ${e.soc_grupo} ${nomSoc[e.soc_grupo]}: ${e.n} grupos SINCO`;
    r.addEventListener("pointermove", (ev) => tip(ev, esc(txt))); r.addEventListener("pointerleave", ocultarTip);
    r.addEventListener("click", () => { ocultarTip(); if (fl.div === e.division && fl.soc === e.soc_grupo) { fl.div = ""; fl.soc = ""; } else { fl.div = e.division; fl.soc = e.soc_grupo; } alCambiarFlujo(); });
    gR.append(r);
  }
  svg.append(gR);
  const nodo = (id, p, x, lado, nombre, clave) => {
    const g = svgEl("g", { tabindex: "0", role: "button", "aria-pressed": String(fl[clave] === id), "aria-label": `${nombre}: ${p.n} grupos SINCO. ${fl[clave] === id ? "Quitar filtro" : "Filtrar"}` }, "f-nodo" + (fl[clave] === id ? " act" : ""));
    g.append(svgEl("rect", { x, y: p.ini, width: nw, height: Math.max(p.h, 2), rx: 2 }));
    const tx = lado === "i" ? x - 8 : x + nw + 8, ancla = lado === "i" ? "end" : "start", y0 = p.y + p.slot / 2 - (p.lineas.length * 13.5) / 2 + 10;
    p.lineas.forEach((l, i) => { const t = svgEl("text", { x: tx, y: y0 + i * 13.5, "text-anchor": ancla }); t.textContent = l; g.append(t); });
    const t2 = svgEl("text", { x: tx, y: y0 + p.lineas.length * 13.5, "text-anchor": ancla }, "f-n"); t2.textContent = `${p.n} grupos`; g.append(t2);
    const alt = () => { fl[clave] = fl[clave] === id ? "" : id; alCambiarFlujo(); };
    g.addEventListener("click", alt); g.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); alt(); } });
    svg.append(g);
  };
  for (const [id, p] of Object.entries(izq.pos)) nodo(id, p, xL, "i", `División ${id} ${nomDiv[id]}`, "div");
  for (const [id, p] of Object.entries(der.pos)) nodo(id, p, xR, "d", `Gran grupo SOC ${id} ${nomSoc[id]}`, "soc");
  const sc = el("div", "flujo-scroll"); sc.tabIndex = 0; sc.setAttribute("aria-label", "Diagrama de cintas (desplazable)"); sc.append(svg);
  const sel = el("div", "f-sel"); sel.id = "f-sel";
  cont.append(sc, sel, el("p", "sub", "Nombres de los grandes grupos SOC: " + f.soc_fuente + " Los grupos SINCO se asignan al gran grupo de su O*NET de mejor coincidencia (automática, sin validar)."),
    tablaDet(["División SINCO", "Gran grupo SOC", "Grupos SINCO"], f.enlaces.map((e) => [`${e.division} ${nomDiv[e.division]}`, `${e.soc_grupo} ${nomSoc[e.soc_grupo]}`, e.n]), "Ver como tabla", 1));
  pintarSeleccionFlujo(nomDiv, nomSoc);
}
function alCambiarFlujo() { dibujarFlujo(); if (vista === "conexiones") fijarHash("conexiones", conActual, filtrosCon()); }
async function pintarSeleccionFlujo(nomDiv, nomSoc) {
  const box = $("f-sel"); if (!box) return;
  if (!fl.div && !fl.soc) { box.append(el("p", "sub", "Elige una división, un gran grupo SOC o una cinta para ver qué grupos SINCO contiene.")); return; }
  esqueleto(box, 1);
  try { if (!filas1) filas1 = (await api("/api/download/dataset?formato=json&rango_max=1")).filas; }
  catch (e) { errorCaja(box, "No se pudo cargar la lista de grupos.", () => pintarSeleccionFlujo(nomDiv, nomSoc)); return; }
  if (!$("f-sel")) return;
  const rows = filas1.filter((r) => (!fl.div || String(r.division) === fl.div) && (!fl.soc || r.onet_soc_code.startsWith(fl.soc + "-")));
  box.removeAttribute("aria-busy"); box.replaceChildren();
  const cab = el("div", "f-sel-cab"); const desc = [fl.div ? `división ${fl.div} ${nomDiv[fl.div] || ""}` : "", fl.soc ? `gran grupo SOC ${fl.soc} ${nomSoc[fl.soc] || ""}` : ""].filter(Boolean).join(" y ");
  cab.append(el("b", "", `${fmt(rows.length)} grupos SINCO en ${desc}`));
  const q = el("button", "btn-g", "Quitar filtro"); q.type = "button"; q.addEventListener("click", () => { fl.div = ""; fl.soc = ""; alCambiarFlujo(); }); cab.append(q);
  box.append(cab);
  if (!rows.length) { box.append(el("p", "vacio", "Ningún grupo SINCO cumple esa combinación.")); return; }
  const lst = el("div", "f-lista");
  for (const r of rows) {
    const b = el("button"); b.type = "button";
    b.append(Object.assign(el("span", "cod"), { textContent: r.sinco_code }), el("span", "", r.sinco_titulo), el("span", "sub", `${r.onet_titulo} (${r.onet_soc_code})`),
      el("span", "sub", `${nf(r.similitud)} · ${ETQ[r.match_status] || r.match_status}`));
    b.addEventListener("click", () => ir("conexiones", r.sinco_code, filtrosCon())); lst.append(b);
  }
  box.append(lst);
}

/* ---------- O*NET ---------- */
let onetOff = 0, onetSel = null; const LIM = 40;
async function cargarOnet() {
  const q = $("q-onet").value.trim(), L = $("lista-onet");
  esqueleto(L, 2);
  let r;
  try { r = await api(`/api/onet/occupations?q=${encodeURIComponent(q)}&limit=${LIM}&offset=${onetOff}`); }
  catch (e) { errorCaja(L, "No se pudo cargar la lista de ocupaciones.", cargarOnet); return; }
  L.removeAttribute("aria-busy"); L.replaceChildren();
  if (!r.resultados.length) {
    vacioCaja(L, q ? `Sin resultados para «${q}»` : "No hay ocupaciones para mostrar", q ? "Las ocupaciones están en inglés. Prueba con una palabra como nurse o driver, o con un código como 29-1141." : "", q ? [chipBtn("Quitar búsqueda", () => { $("q-onet").value = ""; onetOff = 0; cargarOnet(); })] : []);
  }
  for (const o of r.resultados) {
    const b = el("button", "item" + (o.onet_soc_code === onetSel ? " on" : "")); b.type = "button"; b.dataset.s = o.onet_soc_code;
    b.innerHTML = `<span class="cod">${esc(o.onet_soc_code)}</span>${esc(o.titulo_en)}<span class="sub"> · ${o.n_tareas} tareas</span>`;
    b.addEventListener("click", () => ir("onet", o.onet_soc_code, { q, pag: onetOff ? String(onetOff / LIM + 1) : "" })); L.append(b);
  }
  $("onet-pag").textContent = r.total ? `${onetOff + 1}–${Math.min(onetOff + LIM, r.total)} de ${fmt(r.total)}` : "0 resultados";
  $("onet-prev").disabled = onetOff === 0; $("onet-next").disabled = onetOff + LIM >= r.total;
  if (vista === "onet") fijarHash("onet", onetSel, { q, pag: onetOff ? String(onetOff / LIM + 1) : "" });
}
async function detalleOnet(soc) {
  onetSel = soc; const cont = $("detalle-onet"); esqueleto(cont, 3);
  document.querySelectorAll("#lista-onet .item").forEach((b) => b.classList.toggle("on", b.dataset.s === soc));
  let d;
  try { d = await api("/api/onet/occupations/" + soc); if (onetSel !== soc) return; }
  catch (e) {
    if (e.status === 404) vacioCaja(cont, `No encontramos la ocupación ${soc}`, "Revisa el código (formato 11-1011.00) o búscala por título en la lista.");
    else errorCaja(cont, "No se pudo cargar la ocupación.", () => detalleOnet(soc)); return;
  }
  cont.removeAttribute("aria-busy");
  cont.innerHTML = `<h2><span class="cod">${esc(d.onet_soc_code)}</span>${esc(d.titulo_en)}</h2><p>${esc(d.descripcion_en)}</p>` +
    `<h3>SINCO que apuntan a esta ocupación</h3><div id="inv" class="inv"><div class="esq"></div></div>` +
    `<h3>Tareas (${d.n_tareas})</h3>` + lista(d.tareas, (t) => `<li>${esc(t.tarea_en)}</li>`) +
    '<div class="sub">Catálogo O*NET sin valoraciones ni cálculos. Fuente: O*NET (USDOL/ETA, CC BY 4.0).</div>';
  cont.scrollTop = 0;
  const inv = $("inv");
  try {
    const r = await api(`/api/onet/occupations/${soc}/sinco`); if (onetSel !== soc) return;
    if (r.estado !== "disponible") inv.innerHTML = `<div class="cw">Aún no hay coincidencias cargadas (${esc(r.mensaje)}).</div>`;
    else if (!r.filas.length) inv.innerHTML = '<div class="vacio-gr"><b>Ningún grupo SINCO apunta a esta ocupación</b><span>Ningún grupo tiene a esta ocupación entre sus dos mejores coincidencias. Es normal: el emparejamiento parte de SINCO y elige solo dos O*NET por grupo.</span></div>';
    else {
      inv.innerHTML = `<div class="cw aviso-a1" role="note">${esc(r.aviso)}</div>` +
        r.filas.map((x) => `<div class="match"><a class="cod" href="#conexiones/${esc(x.sinco_code)}">${esc(x.sinco_code)}</a><span>${esc(x.sinco_titulo)}</span> <span class="estado"><i class="sw ${EST[x.estado].sw}" aria-hidden="true"></i>${esc(cap(x.estado_etiqueta))}</span> <span class="sub">similitud ${nf(x.similitud)}</span> <a href="#conexiones/${esc(x.sinco_code)}">Ver conexión</a></div>`).join("");
    }
  } catch (e) { errorCaja(inv, "No se pudieron cargar los grupos SINCO.", () => detalleOnet(soc)); }
  if (vista === "onet") fijarHash("onet", soc, { q: $("q-onet").value.trim(), pag: onetOff ? String(onetOff / LIM + 1) : "" });
}
let to;
$("q-onet").addEventListener("input", () => { clearTimeout(to); to = setTimeout(() => { onetOff = 0; cargarOnet(); }, 250); });
$("onet-prev").addEventListener("click", () => { onetOff = Math.max(0, onetOff - LIM); cargarOnet(); });
$("onet-next").addEventListener("click", () => { onetOff += LIM; cargarOnet(); });

/* ---------- fuentes ---------- */
let metaCargada = false;
async function cargarMeta() {
  const cont = $("meta-c"); esqueleto(cont, 2);
  let m;
  try { m = await api("/api/meta"); } catch (e) { errorCaja(cont, "No se pudo cargar el estado de las fuentes.", cargarMeta); return; }
  metaCargada = true; cont.removeAttribute("aria-busy");
  const fila = (k, v) => `<tr><td>${esc(k)}</td><td>${v}</td></tr>`;
  cont.innerHTML = "<table class='meta'>" +
    fila("SINCO", `${esc(m.sinco.documento)}<br><span class="sub">${esc(m.sinco.url)}<br>sha256 ${esc(m.sinco.sha256)}<br>descarga ${esc(m.sinco.fecha_descarga)}</span>`) +
    fila("Niveles SINCO", Object.entries(m.sinco.niveles).map(([k, v]) => `${k}: ${v}`).join(" · ")) +
    fila("O*NET", `${esc(m.onet.version)}<br><span class="sub">${esc(m.onet.url)}<br>sha256 ${esc(m.onet.sha256)}</span>`) +
    fila("Coincidencias SINCO–O*NET", `<b>${esc(m.crosswalk.estado)}</b> ${esc(m.crosswalk.mensaje)} (${m.crosswalk.n_filas} filas)` +
      (m.crosswalk.estado === "disponible" ? `<br><span class="sub">${AVISO_A1}</span>` : "")) +
    fila("Probabilidad (Frey-Osborne)", `<b>${esc(m.probabilidad_automatizacion_fo.estado)}</b> ${esc(m.probabilidad_automatizacion_fo.mensaje)} · NO validada · modelo principal ${esc(m.probabilidad_automatizacion_fo.modelo_principal ?? "—")} (${m.probabilidad_automatizacion_fo.n_filas} filas)`) +
    fila("Exposición por modelos", `<b>${esc(m.exposicion_agentes.estado)}</b> ${esc(m.exposicion_agentes.mensaje || "")} · sin validar · consistencia entre modelos, no exactitud` + (m.exposicion_agentes.estado === "disponible" ? ` (${m.exposicion_agentes.n_con_anotacion} de ${m.exposicion_agentes.n_filas} grupos anotados; decisión 019)` : "")) +
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
  const out = $("d-info"); out.textContent = "Calculando…";
  try {
    const r = await fetch("/api/download/conteo?" + paramsDesc());
    const j = await r.json();
    out.textContent = r.ok ? `Se descargarán ${fmt(j.n_filas)} filas · modelo ${j.modelo} · probabilidad: ${j.probabilidad_automatizacion_fo.estado === "disponible" ? "incluida (NO validada)" : "no disponible (se omiten esas columnas)"}`
      : (r.status === 409 ? "No hay datos para descargar: " + j.error : "Revisa los filtros: " + (j.error || r.status));
    $("d-ir").disabled = !r.ok || j.n_filas === 0;
    if (r.ok && j.n_filas === 0) out.textContent = "Ningún grupo cumple esos filtros. Quita alguno para descargar.";
  } catch (e) { out.textContent = "No se pudo consultar el conteo. Intenta de nuevo."; $("d-ir").disabled = true; }
}
function prellenarDesc() {
  const code = (vista === "conexiones" && conActual) || (root && root.c) || selected || "";
  $("d-division").value = code ? code[0] : ""; $("d-prefijo").value = code;
  $("d-q").value = (vista === "sinco" ? $("q-sinco").value.trim() : "").slice(0, 100);
}
$("f-desc").addEventListener("submit", (e) => e.preventDefault());
document.querySelectorAll('input[name="alcance"]').forEach((r) => r.addEventListener("change", () => {
  $("filtros-desc").disabled = !filtrado(); if (filtrado()) prellenarDesc(); infoDesc();
}));
for (const id of ["d-division", "d-prefijo", "d-q", "d-solo", "d-rango"]) $(id).addEventListener("change", infoDesc);
$("descargar").addEventListener("toggle", () => { if ($("descargar").open) infoDesc(); });
document.addEventListener("click", (e) => { const d = $("descargar"); if (d.open && !d.contains(e.target)) d.open = false; });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("descargar").open) { $("descargar").open = false; $("descargar").querySelector("summary").focus(); } });
$("d-ir").addEventListener("click", () => {
  const p = paramsDesc(); p.set("formato", $("d-formato").value);
  const a = el("a"); a.href = "/api/download/dataset?" + p; a.download = ""; document.body.appendChild(a); a.click(); a.remove();
  aviso("Descarga iniciada");
});

/* ---------- resumen: KPIs y barras (HTML/CSS propios; cifras calculadas por /api/resumen) ---------- */
const AVISO_RES = "Coincidencias automáticas (Método A1, top-2) NO validadas; probabilidad de automatización (Frey-Osborne) no es la exposición por modelos";
const ETQ = { ok: "Con coincidencia", baja_confianza: "Baja confianza", sin_coincidencia: "Sin coincidencia", sin_dato: "Sin dato" };
const CLS = { ok: "ok", baja_confianza: "baja", sin_coincidencia: "sin", sin_dato: "sin" };
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
const tabla = (cab, filas, resumenTxt) => tablaDet(cab, filas, resumenTxt);
function irADivision(cod) { ir("sinco", "", { raiz: cod }); }
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
    b.addEventListener("pointerleave", ocultarTip); b.addEventListener("blur", ocultarTip);
    b.addEventListener("click", () => { ocultarTip(); irADivision(d.division); });
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
    c.addEventListener("pointerleave", ocultarTip);
    w.appendChild(c); eje.appendChild(el("span", "", b.desde.toFixed(2)));
  }
  card.append(w, eje, el("div", "sub", "Eje X: similitud coseno (no es una probabilidad). Eje Y: número de grupos."));
  card.appendChild(tabla(["Desde", "Hasta", "Grupos"], h.map((b) => [b.desde.toFixed(2), b.hasta.toFixed(2), b.n]), "Ver como tabla"));
  return card;
}
function pintarResumen(r) {
  const cont = $("resumen"); cont.removeAttribute("aria-busy"); cont.replaceChildren();
  cont.appendChild(el("h2", "", "Resumen: ¿cuántos grupos SINCO hacen match con O*NET?"));
  const aviso_ = el("div", "r-aviso", "Aviso: " + AVISO_RES + "."); aviso_.setAttribute("role", "note"); cont.appendChild(aviso_);
  if (r.estado !== "disponible") {
    cont.appendChild(el("div", "r-vacio", `Todavía no hay resumen (${r.mensaje || r.estado}). No se muestran cifras ni barras porque no hay coincidencias SINCO–O*NET cargadas.`)); return;
  }
  const ctl = el("div", "r-ctl"); const lab = el("label", "", "Modelo de embeddings ");
  const sel = el("select"); sel.id = "r-modelo";
  for (const m of r.modelos_disponibles) { const o = el("option", "", m + (m === r.modelo_principal ? " (principal)" : "")); o.value = m; o.selected = m === r.modelo; sel.appendChild(o); }
  sel.addEventListener("change", () => cargarResumen(sel.value)); lab.appendChild(sel); ctl.appendChild(lab);
  ctl.appendChild(el("span", "sub", `run ${(r.run_id || []).join(", ")}`));
  const lk = el("a", "btn-p", "Explorar conexiones"); lk.href = "#conexiones"; ctl.appendChild(lk); cont.appendChild(ctl);
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
  const c = $("resumen"); esqueleto(c, 3);
  try { pintarResumen(await api("/api/resumen" + (modelo ? "?modelo=" + encodeURIComponent(modelo) : ""))); }
  catch (e) { errorCaja(c, "No se pudo cargar el resumen.", () => cargarResumen(modelo)); }
}
$("guia-conexiones").addEventListener("click", () => ir("conexiones"));
$("guia-buscar").addEventListener("click", () => $("q-global").focus());
try { if (localStorage.getItem("guia") === "cerrada") $("guia").open = false; } catch (e) { /* ok */ }
$("guia").addEventListener("toggle", () => { try { localStorage.setItem("guia", $("guia").open ? "abierta" : "cerrada"); } catch (e) { /* ok */ } });

/* ---------- inicio ---------- */
cargarResumen();
cargarResumenModelos();
const arbolListo = (async () => {
  try {
    tree = await api("/api/sinco/tree"); indexar(tree.raices, null, 1);
    $("leyenda").innerHTML = tree.raices.map((d) => `<span><i style="background:${color(d)}"></i>${esc(d.c)} ${esc(d.t)}</span>`).join("");
    dibujar(); ruta();
    if (vista === "conexiones" && !conActual) invitacionConexion();
  } catch (e) { errorCaja($("detalle"), "No se pudo cargar el árbol SINCO.", () => location.reload()); }
})();
aplicarHash();
