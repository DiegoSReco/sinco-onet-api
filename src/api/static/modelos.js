/* Exposicion teorica por modelos (decision 019). Todo viene de /api/exposicion y /api/modelos/comparacion (calculado por scripts en src/);
   aqui solo se dibuja: los unicos calculos son anchos de barra y posiciones. Siempre rotulado "sin validar; consistencia entre modelos, no exactitud".
   Se carga ANTES de app.js: usa sus ayudantes ($, esc, el, svgEl, nf, api, ...) solo dentro de funciones, que se llaman despues. */
const MOD = ["haiku", "sonnet", "opus"];
const NOM_M = { haiku: "Haiku", sonnet: "Sonnet", opus: "Opus" };
const CAMPOS_K = {
  exposure_class: "exposure_class (E0 a E2)",
  eloundou_fundida: "eloundou_class, EL3 fundida en EL2",
  eloundou_cruda: "eloundou_class, 4 clases",
};
const EXPO_AVISO_CORTO = "Sin validar. Mide consistencia entre modelos, no exactitud; los tres modelos son de la misma familia. No es riesgo de pérdida de empleo ni estimación para México.";
const k2 = (x) => (x === null || x === undefined ? "—" : Number(x).toFixed(2));
const pc1 = (x) => (x === null || x === undefined ? "—" : (x * 100).toFixed(0) + " %");

/* ---------- barras 0 a 1 por modelo ---------- */
function barraIdx(m, valor, extra) {
  const w = valor === null || valor === undefined ? 0 : Math.max(0, Math.min(1, valor)) * 100;
  return `<div class="mb"><span class="mn">${esc(NOM_M[m])}</span><div class="mt" role="img" aria-label="${esc(NOM_M[m])}: ${k2(valor)}"><i class="m-${m}" style="width:${w}%"></i></div><b>${k2(valor)}</b>${extra || ""}</div>`;
}
function bloqueCampo(titulo, v, pref, clases) {
  const idx = (m) => v.modelos[m][pref + "_idx"];
  const e = v.entre_modelos;
  const clasesHtml = MOD.map((m) => {
    const c = v.modelos[m][pref + "_clases"];
    const seg = clases.map((k, i) => `<span class="cs c${i}" style="width:${(c[k] || 0) * 100}%" title="${esc(NOM_M[m])} ${k}: ${pc1(c[k])}">${(c[k] || 0) > 0.09 ? Math.round(c[k] * 100) : ""}</span>`).join("");
    return `<div class="mb"><span class="mn">${esc(NOM_M[m])}</span><div class="cstack" role="img" aria-label="${esc(NOM_M[m])}: ${clases.map((k) => k + " " + pc1(c[k])).join(", ")}">${seg}</div></div>`;
  }).join("");
  return `<div class="xb"><h4>${esc(titulo)}</h4>` + MOD.map((m) => barraIdx(m, idx(m))).join("") +
    `<div class="sub">media entre modelos <b>${k2(e[pref + "_idx_media"])}</b> · de ${k2(e[pref + "_idx_min"])} a ${k2(e[pref + "_idx_max"])} (rango ${k2(e[pref + "_idx_rango"])})</div>` +
    `<details class="mini"><summary>Reparto de funciones por clase</summary>${clasesHtml}<div class="sub">${clases.join(" · ")}: de claro a oscuro</div></details></div>`;
}
function bandaB1(b, etq) {
  if (!b || b.idx === null || b.idx === undefined) return "";
  const lo = b.lo * 100, hi = b.hi * 100;
  return `<div class="b1r"><span class="mn">${esc(etq)}</span><div class="mt" role="img" aria-label="${esc(etq)}: ${k2(b.idx)}, intervalo ${k2(b.lo)} a ${k2(b.hi)}"><i class="b1i" style="left:${lo}%;width:${Math.max(hi - lo, 0.8)}%"></i><u style="left:${b.idx * 100}%"></u></div><b>${k2(b.idx)}</b><span class="sub">[${k2(b.lo)}, ${k2(b.hi)}]</span></div>`;
}
const EMP_NOTA = { ok: "Con coincidencia", baja_confianza: "Coincidencia de baja confianza", sin_coincidencia: "Sin coincidencia" };

/* ---------- tarjeta de un grupo (detalle SINCO y conexiones) ---------- */
function htmlExpo(e, compacta) {
  const queEs = e && e.que_es ? e.que_es : "", queNo = e && e.que_no_es ? e.que_no_es : "";
  const titulo = `<b>Exposición teórica por modelos</b><span class="tag">sin validar</span>${typeof ayudaHtml === "function" ? ayudaHtml(queEs, queNo) : ""}`;
  if (!e || e.estado === "no_disponible") return `<div class="prob vacia" role="note">${titulo}<div>Exposición no disponible: la tabla MAIN no existe en esta instalación.</div></div>`;
  if (e.estado === "sin_fila") return `<div class="prob vacia" role="note">${titulo}<div>${esc(cap(e.mensaje))}.</div></div>`;
  if (e.estado === "sin_anotacion") return `<div class="prob vacia" role="note">${titulo}<div>${esc(cap(e.mensaje))}.</div></div>`;
  const v = e.valores;
  let h = `<div class="prob expo" role="note">${titulo}<div class="sub">${esc(v.n_funciones)} funciones anotadas por Haiku, Sonnet y Opus (2 corridas cada uno). Índice de 0 (sin exposición) a 1.</div>`;
  h += `<div class="xgrid">${bloqueCampo("exposure_class", v, "exposure", ["E0", "E1", "E2"])}${bloqueCampo("eloundou_class", v, "eloundou", ["EL0", "EL1", "EL2"])}</div>`;
  const a = v.acuerdo_funciones, c = v.modelos;
  h += `<div class="sub">Función por función: los 3 modelos coinciden en ${pc1(a.exposure_frac_coinciden_3_modelos)} (exposure) y ${pc1(a.eloundou_frac_coinciden_3_modelos)} (eloundou); desacuerdo fuerte en ${pc1(a.exposure_frac_desacuerdo_fuerte)} y ${pc1(a.eloundou_frac_desacuerdo_fuerte)}.</div>`;
  h += `<div class="sub">Con cuello de botella físico: ${MOD.map((m) => `${NOM_M[m]} ${pc1(c[m].cuello_fisico_frac)}`).join(" · ")}.</div>`;
  h += `<div class="b1w"><b>B1 (índice ajustado por el desvío relativo de cada modelo)</b><span class="sub"> índice con intervalo al 90 %. ${esc(v.b1.nota)}</span>${bandaB1(v.b1.exposure, "exposure")}${bandaB1(v.b1.eloundou, "eloundou")}</div>`;
  if (!compacta) {
    const em = v.emparejamiento, cand = em.candidatos || [];
    h += `<div class="empw"><b>Emparejamiento con O*NET (embeddings, ${esc(em.modelo || "—")})</b><span class="sub"> ${esc(EMP_NOTA[em.match_status] || em.match_status || "")}${em.top1_coincide_otro_modelo === null ? "" : (em.top1_coincide_otro_modelo ? " · el otro modelo de embeddings coincide en la mejor opción" : " · el otro modelo de embeddings propone otra mejor opción")}</span>` +
      cand.map((m) => `<div class="mb"><span class="mn mnl">${esc(m.onet_soc_code)}</span><div class="mt" role="img" aria-label="peso ${k2(m.peso_softmax)}"><i class="m-peso" style="width:${(m.peso_softmax || 0) * 100}%"></i></div><b>${k2(m.peso_softmax)}</b></div><div class="sub emt">${esc(m.onet_titulo)} · similitud ${nf(m.similitud)}</div>`).join("") +
      `<div class="sub">${esc(em.aviso_peso)}</div></div>`;
  }
  return h + `<div class="sub">${esc(EXPO_AVISO_CORTO)}</div></div>`;
}

/* ---------- matriz de acuerdo y grafica de sesgo (DOM) ---------- */
function colorK(k) { if (k === null || k === undefined) return "transparent"; const t = Math.max(0, Math.min(1, (k - 0.4) / 0.5)); return `color-mix(in srgb, var(--ac) ${Math.round(15 + t * 65)}%, var(--panel))`; }
function matrizKappa(c, umbral) {
  const par = (a, b) => [a, b].sort().join("|");
  const g = el("div", "kmat");
  g.append(el("div", "kh", ""));
  MOD.forEach((m) => g.append(el("div", "kh", NOM_M[m])));
  MOD.forEach((r) => {
    g.append(el("div", "kh kl", NOM_M[r]));
    MOD.forEach((k) => {
      const v = r === k ? c.kappa_intra_modelo[r] : c.kappa_entre_modelos[par(r, k)];
      const cel = el("div", "kc" + (v !== null && v < umbral ? " bajo" : ""), k2(v));
      cel.style.background = colorK(v);
      cel.title = r === k ? `${NOM_M[r]} contra sí mismo (sus 2 corridas): ${k2(v)}` : `${NOM_M[r]} contra ${NOM_M[k]}: kappa medio de los 4 pares de corridas = ${k2(v)}`;
      g.append(cel);
    });
  });
  return g;
}
function graficaB1(b, titulo) {
  const A = b.anotadores, W = 560, L = 90, R = 40, H = 54 + A.length * 40;
  const lo = Math.min(0, ...A.map((a) => a.d_k_lo)) - 0.03, hi = Math.max(0, ...A.map((a) => a.d_k_hi)) + 0.03, sx = (v) => L + ((v - lo) / (hi - lo)) * (W - L - R);
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `Sesgo por modelo, ${titulo}`, width: "100%" }, "b1svg");
  const paso = hi - lo > 0.4 ? 0.1 : 0.05;
  for (let t = Math.ceil(lo / paso) * paso; t <= hi; t += paso) {
    const x = sx(+t.toFixed(3)), cero = Math.abs(t) < 1e-9;
    svg.append(svgEl("line", { x1: x, x2: x, y1: 16, y2: 22 + A.length * 40, stroke: "var(--bd2)", "stroke-width": cero ? 2 : 1 }));
    const tx = svgEl("text", { x, y: 40 + A.length * 40, "text-anchor": "middle", class: "b1t" }); tx.textContent = (t > 0 ? "+" : "") + t.toFixed(2); svg.append(tx);
  }
  A.forEach((a, i) => {
    const y = 36 + i * 40, fuera = a.d_k_lo > 0 || a.d_k_hi < 0, col = fuera ? "var(--s-baja)" : "var(--ac)";
    const n = svgEl("text", { x: L - 10, y: y + 4, "text-anchor": "end", class: "b1t" }); n.textContent = NOM_M[a.anotador] || a.anotador; svg.append(n);
    svg.append(svgEl("line", { x1: sx(a.d_k_lo), x2: sx(a.d_k_hi), y1: y, y2: y, stroke: col, "stroke-width": 4, "stroke-linecap": "round" }));
    svg.append(svgEl("circle", { cx: sx(a.d_k_media), cy: y, r: 6, fill: col }));
    const v = svgEl("text", { x: sx(a.d_k_media), y: y - 11, "text-anchor": "middle", class: "b1t" }); v.textContent = (a.d_k_media >= 0 ? "+" : "") + a.d_k_media.toFixed(3); svg.append(v);
  });
  return svg;
}
function notaB1(b) {
  const fuera = b.anotadores.filter((a) => a.d_k_lo > 0 || a.d_k_hi < 0).map((a) => NOM_M[a.anotador] || a.anotador);
  return (fuera.length ? `El intervalo no incluye el cero para: ${fuera.join(", ")}.` : "Los tres intervalos incluyen el cero: no hay evidencia de un sesgo sistemático entre modelos.") +
    ` Convergencia: R-hat máx. ${b.max_rhat.toFixed(3)} (límite ${b.umbrales.rhat_max}), ESS mín. ${Math.round(b.min_ess)} (mín. ${b.umbrales.ess_min}); ${b.convergio ? "convergió" : "NO convergió"}. ${fmt(b.n_items)} ítems, ${b.n_grupos} grupos.`;
}

/* ---------- bloque compacto del panel principal (Resumen) ---------- */
async function cargarResumenModelos() {
  const c = $("resumen-modelos"); if (!c) return;
  let d;
  try { d = await api("/api/modelos/comparacion"); } catch (e) { c.replaceChildren(el("p", "vacio", "No se pudo cargar la comparación entre modelos.")); return; }
  c.replaceChildren();
  if (d.estado !== "disponible") { c.append(el("p", "vacio", "Comparación entre modelos no disponible en esta instalación.")); return; }
  const h = el("h3", "", "Comparación entre modelos: Haiku, Sonnet y Opus"); h.id = "rm-h";
  const sub = el("p", "sub", "Los tres modelos anotaron las 3 542 funciones del catálogo SINCO. Esto muestra cuánto coinciden y si alguna se aparta del grupo. " + d.aviso);
  const campo = d.campos.exposure_class, minK = Math.min(...Object.values(campo.kappa_entre_modelos));
  const kp = el("div", "kpis");
  kp.append(kpi("ok", k2(minK), "", "Acuerdo mínimo entre modelos", "kappa ponderado de exposure_class, el par más bajo (umbral provisional 0.60)"),
    kpi("ok", k2(Math.min(...Object.values(campo.kappa_intra_modelo))), "", "Acuerdo mínimo dentro de un modelo", "entre sus dos corridas"),
    kpi(campo.regla_exclusion.excluidos.length ? "baja" : "ok", String(campo.regla_exclusion.excluidos.length), "de 3", "Modelos excluidos por la regla", "regla de 018 R1.3: kappa menor a 0.40 frente a los otros dos"),
    kpi(d.b1_ordinal_por_modelo.exposure_class && d.b1_ordinal_por_modelo.exposure_class.convergio ? "ok" : "baja", d.b1_ordinal_por_modelo.exposure_class && d.b1_ordinal_por_modelo.exposure_class.convergio ? "sí" : "no", "", "B1 convergió", "R-hat y ESS dentro de los umbrales"));
  const fila = el("div", "rm-fila");
  const m1 = el("div", "card"); m1.append(el("h4", "", "Acuerdo entre modelos (exposure_class)"), matrizKappa(campo, 0.6), el("div", "sub", "Diagonal: dos corridas del mismo modelo. Fuera de la diagonal: promedio entre corridas de dos modelos. Borde punteado: menor a 0.60."));
  const b = d.b1_ordinal_por_modelo.exposure_class;
  const m2 = el("div", "card"); m2.append(el("h4", "", "Sesgo de estimación por modelo (B1)"));
  if (b) { m2.append(graficaB1(b, "exposure_class"), el("div", "sub", notaB1(b))); } else m2.append(el("p", "vacio", "B1 no disponible."));
  fila.append(m1, m2);
  const mas = el("p", "sub"); mas.innerHTML = `<a class="ref" href="#modelos">Ver toda la comparación: otras rúbricas, sensibilidad al preámbulo, cuello físico y grupos con más desacuerdo →</a>`;
  c.append(h, sub, kp, fila, mas);
}

/* ---------- pestaña Modelos ---------- */
let modelosCargados = false;
const tblSimple = (cab, filas) => {
  const sc = el("div", "tabla-scroll"), t = el("table", "r-tab"), th = el("tr");
  cab.forEach((x) => th.append(el("th", "", x))); t.append(th);
  filas.forEach((f) => { const tr = el("tr"); f.forEach((x, i) => { const td = el("td", i === 0 ? "izq-t" : ""); if (x instanceof Node) td.append(x); else td.textContent = x; tr.append(td); }); t.append(tr); });
  sc.append(t); return sc;
};
function listaGrupos(res) {
  return tblSimple(["Grupo SINCO", "Haiku", "Sonnet", "Opus", "Media", "Rango"], res.map((r) => {
    const a = el("a", "ref", `${r.sinco_code} ${r.titulo}`); a.href = "#conexiones/" + r.sinco_code;
    return [a, k2(r.exposure_idx.haiku), k2(r.exposure_idx.sonnet), k2(r.exposure_idx.opus), k2(r.exposure_idx_media_modelos), k2(r.exposure_idx_rango_modelos)];
  }));
}
async function cargarModelos() {
  const cont = $("modelos-c"); esqueleto(cont, 3);
  let d, top, des, bajo;
  try {
    [d, top, des, bajo] = await Promise.all([api("/api/modelos/comparacion"), api("/api/exposicion?orden=exposicion_desc&solo_con_anotacion=true&limit=10"),
      api("/api/exposicion?orden=desacuerdo_desc&solo_con_anotacion=true&limit=10"), api("/api/exposicion?orden=exposicion_asc&solo_con_anotacion=true&limit=10")]);
  } catch (e) { errorCaja(cont, "No se pudo cargar la comparación entre modelos.", cargarModelos); return; }
  modelosCargados = true; cont.removeAttribute("aria-busy"); cont.replaceChildren();
  if (d.estado !== "disponible") { cont.append(el("p", "vacio", "Comparación entre modelos no disponible en esta instalación.")); return; }
  const sec = (titulo, ...hijos) => { const s = el("section", "card mod-sec"); s.append(el("h3", "", titulo), ...hijos); cont.append(s); return s; };
  const aviso = el("div", "c-aviso"); aviso.setAttribute("role", "note"); aviso.innerHTML = `<b>${esc(cap(d.etiqueta))}.</b> ${esc(d.aviso)}`; cont.append(aviso);

  // 1. acuerdo
  const selW = el("div", "ctl"); const lab = el("label", "", "Campo "); const sel = el("select"); sel.id = "sel-campo-k";
  Object.entries(CAMPOS_K).forEach(([k, v]) => { const o = el("option", "", v); o.value = k; sel.append(o); }); lab.append(sel); selW.append(lab);
  const hueco = el("div"), nota = el("div", "sub");
  const pinta = () => {
    const c = d.campos[sel.value]; hueco.replaceChildren(matrizKappa(c, c.umbral_uso_principal));
    nota.textContent = `Alfa de Krippendorff entre las 6 corridas: ${k2(c.alfa_krippendorff_ordinal_corridas)}. Acuerdo exacto entre las 2 corridas de cada modelo: ${MOD.map((m) => NOM_M[m] + " " + pc1(c.acuerdo_exacto_corridas[m])).join(", ")}. ` +
      (c.regla_exclusion.excluidos.length ? `Modelos excluidos por la regla: ${c.regla_exclusion.excluidos.join(", ")}.` : "Ningún modelo queda excluido por la regla de 018 R1.3 (kappa menor a 0.40 frente a los otros dos).");
  };
  sel.addEventListener("change", pinta); pinta();
  sec("1. ¿Cuánto coinciden los modelos?", el("p", "sub", "Kappa ponderado cuadrático: 1 = coinciden siempre, 0 = como el azar. Umbrales provisionales: 0.60 para usar un campo en cifras principales y 0.40 para excluir a un modelo."), selW, hueco, nota);

  // 2. reparto por corrida
  const conteos = d.conteos_por_corrida || {}, rows = el("div", "bars2");
  const orden = Object.entries(conteos).sort((a, b) => MOD.indexOf(a[1].modelo) - MOD.indexOf(b[1].modelo) || a[0].localeCompare(b[0]));
  const rep = (campo, clases) => {
    const w = el("div", "xb"); w.append(el("h4", "", campo));
    orden.forEach(([rid, v], i) => {
      const tot = clases.reduce((s, k) => s + (v[campo][k] || 0), 0);
      const seg = clases.map((k, j) => `<span class="cs c${j}" style="width:${((v[campo][k] || 0) / tot) * 100}%" title="${k}: ${v[campo][k] || 0}">${(v[campo][k] || 0) / tot > 0.08 ? Math.round(((v[campo][k] || 0) / tot) * 100) : ""}</span>`).join("");
      const f = el("div", "mb"); f.innerHTML = `<span class="mn">${esc(NOM_M[v.modelo])} ${(i % 2) + 1}</span><div class="cstack" role="img" aria-label="${esc(rid)}: ${clases.map((k) => k + " " + (v[campo][k] || 0)).join(", ")}">${seg}</div>`; w.append(f);
    });
    w.append(el("div", "sub", clases.join(" · ") + ": de claro a oscuro, en % de funciones")); return w;
  };
  rows.append(rep("exposure_class", ["E0", "E1", "E2"]), rep("eloundou_class", ["EL0", "EL1", "EL2"]));
  sec("2. Cómo reparte cada corrida sus etiquetas", el("p", "sub", "Seis corridas base (2 por modelo); EL3 se funde en EL2. Una corrida que se aparta mucho de las demás merece una mirada a su prompt."), rows);

  // 3. sesgo B1
  const b1 = d.b1_ordinal_por_modelo, g3 = el("div", "rm-fila");
  [["exposure_class", "exposure_class"], ["eloundou_class", "eloundou_class"]].forEach(([k, t]) => {
    if (!b1[k]) return; const c = el("div", "xb"); c.append(el("h4", "", t), graficaB1(b1[k], t), el("div", "sub", notaB1(b1[k]))); g3.append(c);
  });
  sec("3. Sesgo de estimación por modelo (B1)", el("p", "sub", "El modelo B1 estima cuánto sube o baja la clase cada modelo respecto al promedio de los tres (los tres suman cero). Positivo: sube. Si el intervalo cruza el cero, no hay evidencia de sesgo sistemático entre ellos. Un sesgo que comparten los tres no aparece aquí."), g3);

  // 4. sensibilidad al preambulo
  const sp = d.sensibilidad_preambulo;
  if (sp) {
    const f = Object.entries(sp.campos).map(([k, v]) => [k, k2(v.kappa_intra_v1[0]), k2(v.kappa_intra_v2[0]), k2(v.kappa_cruzado_v1_v2_medio), v.dif_media_v2_menos_v1 === undefined ? "—" : (v.dif_media_v2_menos_v1 >= 0 ? "+" : "") + v.dif_media_v2_menos_v1.toFixed(3)]);
    sec("4. ¿Importa el preámbulo del prompt?", el("p", "sub", "Sonnet con el preámbulo original de 2023 (v1) frente a una redacción actualizada (v2), 2 corridas cada una. Si el kappa cruzado es parecido al de las dos corridas de un mismo prompt, el cambio de redacción mueve poco el resultado. exposure_class no depende del párrafo: sirve de control."),
      tblSimple(["Campo", "Kappa entre corridas v1", "Kappa entre corridas v2", "Kappa cruzado v1 y v2", "Cambio en el índice medio"], f));
  }

  // 5. cuello fisico
  const cn = d.control_negativo_cuello_fisico;
  if (cn) sec("5. Control negativo: cuello de botella físico", el("p", "sub", "Las funciones marcadas con cuello de botella físico deben tener menor exposición en los tres modelos. Es un chequeo de cordura, no una validación."),
    tblSimple(["Modelo", "Índice medio sin cuello físico", "Índice medio con cuello físico", "Funciones sin / con"], MOD.map((m) => [NOM_M[m], k2(cn[m].sin_cuello_fisico.indice_medio), k2(cn[m].con_cuello_fisico.indice_medio), `${fmt(cn[m].sin_cuello_fisico.n)} / ${fmt(cn[m].con_cuello_fisico.n)}`])));

  // 6. por division
  const md = d.medias_por_division || {}, nomDiv = {};
  if (typeof tree !== "undefined" && tree) tree.raices.forEach((x) => (nomDiv[x.c] = x.t));
  const dv = el("div", "xb");
  Object.keys(md).sort().forEach((k) => {
    const v = md[k], w = el("div", "divb"); w.innerHTML = `<div class="dt"><b>${esc(k)}</b> ${esc(nomDiv[k] || "")} <span class="sub">(${v.n_grupos} grupos)</span></div>` + MOD.map((m) => barraIdx(m, v["exp_idx_" + m])).join(""); dv.append(w);
  });
  sec("6. Exposición media por división SINCO (exposure_class)", el("p", "sub", "Promedio simple de los índices de los grupos de cada división, por modelo. Es un resumen para comparar modelos, no una cifra de la economía: no pondera por empleo."), dv);

  // 7. listas
  const l7 = el("div", "rm-fila"), a = el("div", "xb"), bq = el("div", "xb"), c3 = el("div", "xb");
  a.append(el("h4", "", "Mayor exposición (media de los 3 modelos)"), listaGrupos(top.resultados));
  bq.append(el("h4", "", "Menor exposición"), listaGrupos(bajo.resultados));
  c3.append(el("h4", "", "Donde más discrepan los modelos"), listaGrupos(des.resultados));
  l7.append(a, bq); sec("7. Grupos que conviene mirar", el("p", "sub", "Diez grupos por criterio; haz clic para ver la conexión con O*NET y la exposición completa del grupo."), l7, c3);

  // 8. limites y descarga
  const lim = el("ul", "lim"); d.limites.forEach((x) => lim.append(el("li", "", x)));
  const dl = el("p"); dl.innerHTML = `<a class="btn-p" href="/api/download/main?formato=csv">Descargar tabla MAIN (CSV)</a> <a class="btn-g" href="/api/download/main?formato=parquet">Parquet</a> <span class="sub">Una fila por grupo unitario SINCO: emparejamiento con O*NET, exposición de los tres modelos, B1 y Frey-Osborne.</span>`;
  sec("8. Límites y datos", lim, dl);
}
