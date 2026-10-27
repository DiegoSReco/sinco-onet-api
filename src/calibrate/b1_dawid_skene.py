"""B1 (decision 012): modelo bayesiano de error de medicion tipo Dawid-Skene, muestreador de Gibbs propio.

Modelo (version basica, 012 sec. 5 y 9, opcion sin dependencias nuevas):
  z_i ~ Categorica(pi),            pi ~ Dirichlet(alpha)
  y_ik | z_i = c ~ Categorica(Theta_k[c, :]),   Theta_k[c, :] ~ Dirichlet(beta_k[c, :])
i = item (tarea o funcion), k = 'anotador' (corrida del LLM o revisor humano). Condicionalmente conjugado.

LIMITES (no se esconden):
- Las corridas del MISMO modelo y prompt NO son anotadores independientes (comparten sesgo). Este modelo las trata
  como independientes dado z (supuesto clasico), de modo que, SIN referencia humana, el posterior es falsamente
  preciso y lo unico que mide es consistencia entre corridas, NO exactitud. Los resultados se etiquetan asi.
- No es el modelo ordinal jerarquico con efecto de funcion de 012 (requeriria un paquete no aprobado).
- Mide error de medicion; no calcula exposicion agregada (eso es src/score) ni usa datos de empleo.

Cifras: todas salen de este script (regla 1). Estado: PROVISIONAL, SIN VALIDAR (o PILOTO, NO RESULTADO).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import sys
import time
import tomllib
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).with_name("config.toml")
MODELO = "dawid_skene_gibbs_conjugado"
VERSION_MODELO = "b1-0.1"


class EsquemaIncumplido(Exception):
    """Un entregable de entrada no cumple su esquema (regla 5: issue y detenerse)."""


class PilotoNoPermitido(Exception):
    """Las anotaciones son piloto y no se paso --permitir-piloto."""


# --------------------------------------------------------------------------- configuracion
def cargar_config(path: Path | str = CONFIG_PATH) -> dict:
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    for sec in ("campos", "muestreo", "prior", "diagnosticos", "salida", "entrada"):
        if sec not in cfg:
            raise ValueError(f"config calibrate: falta la seccion [{sec}]")
    m = cfg["muestreo"]
    if not (m["n_cadenas"] >= 1 and m["adelgazamiento"] >= 1 and 0 <= m["descarte"] < m["n_iter"]):
        raise ValueError("config calibrate: muestreo invalido (n_cadenas>=1, adelgazamiento>=1, 0<=descarte<n_iter)")
    if (m["n_iter"] - m["descarte"]) // m["adelgazamiento"] < 4:
        raise ValueError("config calibrate: quedan menos de 4 iteraciones guardadas por cadena")
    if not 0 < cfg["salida"]["nivel_intervalo"] < 1:
        raise ValueError("config calibrate: salida.nivel_intervalo debe estar en (0, 1)")
    for nombre in ("debil", "fuerte", "humano"):
        p = cfg["prior"][nombre]
        if p["diag"] <= 0 or p["off"] <= 0:
            raise ValueError(f"config calibrate: prior.{nombre} requiere diag > 0 y off > 0")
    if cfg["prior"]["seleccion"] not in ("debil", "fuerte"):
        raise ValueError("config calibrate: prior.seleccion debe ser 'debil' o 'fuerte'")
    return cfg


def _sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- carga de datos
def _aplicar_clases(etiquetas: pd.Series, campo_cfg: dict, origen: str) -> pd.Series:
    clases = list(campo_cfg["clases"])
    fusion = dict(campo_cfg.get("fusion", {}))
    e = etiquetas.map(lambda x: fusion.get(x, x))
    malas = sorted(set(e) - set(clases))
    if malas:
        raise EsquemaIncumplido(f"{origen}: clases fuera de {clases} (fusion {fusion}): {malas}")
    return e


def cargar_anotaciones_llm(rutas, campo: str, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (largo, corridas). largo: item, anotador, clase, es_referencia=False.
    corridas: run_id, model, prompt_version, run_date, onet_soc (si existe) por item/anotador para trazabilidad.

    exposure_class: reutiliza el cargador de src/score (valida el esquema Annotation).
    Otro campo (p. ej. eloundou_class): parquet con columnas run_id, task_id y el campo (no esta en Annotation).
    """
    if campo not in cfg["campos"]:
        raise ValueError(f"campo desconocido {campo!r}; opciones: {list(cfg['campos'])}")
    from src.score import exposicion as score  # carga/valida; no calcula exposicion
    try:
        if campo == "exposure_class":
            ann = score.cargar_anotaciones(rutas)
        else:
            frames = []
            for p in score._expandir(rutas):
                t = pd.read_parquet(p)
                falt = {"run_id", "task_id", campo} - set(t.columns)
                if falt:
                    raise EsquemaIncumplido(f"{p}: faltan columnas {sorted(falt)}")
                frames.append(t)
            ann = pd.concat(frames, ignore_index=True)
            if ann.duplicated(["run_id", "task_id"]).any():
                raise EsquemaIncumplido("(run_id, task_id) repetido")
    except score.EsquemaIncumplido as e:
        raise EsquemaIncumplido(str(e)) from e
    ann = ann.copy()
    ann[campo] = _aplicar_clases(ann[campo].astype(str), cfg["campos"][campo], "anotaciones")
    largo = pd.DataFrame({"item": ann["task_id"].astype(str), "anotador": ann["run_id"].astype(str),
                          "clase": ann[campo], "es_referencia": False})
    return largo, ann


def cargar_referencia(path, campo: str, cfg: dict, col_item="task_id", col_clase="clase_humana",
                      col_revisor: Optional[str] = None) -> pd.DataFrame:
    """Etiquetas humanas de referencia (parquet o CSV). Cada revisor es un anotador (012: la adjudicacion
    tambien es un anotador mas, no la verdad). Sin columna de revisor: un solo anotador 'humano'."""
    p = Path(path)
    t = pd.read_csv(p, dtype=str) if p.suffix.lower() == ".csv" else pd.read_parquet(p)
    for c in (col_item, col_clase):
        if c not in t.columns:
            raise EsquemaIncumplido(f"referencia {p}: falta la columna {c!r}")
    if col_revisor and col_revisor not in t.columns:
        raise EsquemaIncumplido(f"referencia {p}: falta la columna {col_revisor!r}")
    anot = ("humano:" + t[col_revisor].astype(str)) if col_revisor else pd.Series("humano", index=t.index)
    out = pd.DataFrame({"item": t[col_item].astype(str), "anotador": anot.astype(str),
                        "clase": _aplicar_clases(t[col_clase].astype(str), cfg["campos"][campo], f"referencia {p}"),
                        "es_referencia": True})
    if out.duplicated(["item", "anotador"]).any():
        raise EsquemaIncumplido(f"referencia {p}: (item, anotador) repetido")
    return out


def colapsar_por_grupo(largo: pd.DataFrame, grupos: dict[str, str]) -> pd.DataFrame:
    """Unidad 'modelo': las corridas de un mismo grupo (modelo) se reemplazan por UN anotador cuya etiqueta por item
    es la moda de sus corridas; si hay empate entre clases, la observacion queda ausente (no se elige al azar).
    Motivo: corridas del mismo modelo comparten sesgo y no son independientes (012); tratarlas como una sola
    'vista' permite que la referencia humana separe el sesgo comun. Pierde el desacuerdo entre corridas.
    Los anotadores de referencia humana no se tocan."""
    h = largo[largo["es_referencia"]]
    m = largo[~largo["es_referencia"]].copy()
    m["anotador"] = m["anotador"].map(lambda r: grupos.get(r, r))
    c = m.groupby(["item", "anotador", "clase"]).size().rename("n").reset_index()
    mx = c.groupby(["item", "anotador"])["n"].transform("max")
    top = c[c["n"] == mx]
    unico = top.groupby(["item", "anotador"])["clase"].transform("size") == 1
    out = top[unico][["item", "anotador", "clase"]].assign(es_referencia=False)
    return pd.concat([out, h], ignore_index=True)


# --------------------------------------------------------------------------- piloto
def detectar_piloto(ann: Optional[pd.DataFrame], universo: Optional[pd.DataFrame], runs: list[str]) -> list[str]:
    """Razones por las que las entradas son piloto. Reutiliza el criterio de src/score (config [piloto])."""
    from src.score import exposicion as score
    cs = score.cargar_config()
    razones: list[str] = []
    if ann is not None and universo is not None and {"model", "onet_soc", "task_id", "run_id"} <= set(ann.columns):
        razones += score.detectar_piloto(ann, universo, cs)
    else:
        pref = tuple(cs["piloto"]["prefijos_run_id"])
        malos = sorted(r for r in runs if r.lower().startswith(pref))
        if malos:
            razones.append(f"run_id de piloto/prueba: {malos}")
        if ann is not None and "model" in ann.columns:
            mods = sorted(set(ann["model"]) & set(cs["piloto"]["modelos_no_resultado"]))
            if mods:
                razones.append(f"modelo de prueba: {mods}")
    return razones


# --------------------------------------------------------------------------- modelo
class Datos:
    """Observaciones en formato disperso (permite anotaciones faltantes por item)."""

    def __init__(self, largo: pd.DataFrame, clases: list[str]):
        if largo.empty:
            raise EsquemaIncumplido("no hay anotaciones")
        if largo.duplicated(["item", "anotador"]).any():
            raise EsquemaIncumplido("(item, anotador) repetido")
        self.clases = list(clases)
        self.items = sorted(largo["item"].unique())
        # anotadores LLM primero (orden alfabetico), referencias humanas despues
        a = largo.groupby("anotador")["es_referencia"].max()
        self.anotadores = sorted(a.index[~a]) + sorted(a.index[a])
        self.es_ref = np.array([bool(a[k]) for k in self.anotadores])
        ix = {v: i for i, v in enumerate(self.items)}
        ka = {v: i for i, v in enumerate(self.anotadores)}
        cl = {v: i for i, v in enumerate(self.clases)}
        self.item = largo["item"].map(ix).to_numpy(np.int64)
        self.ann = largo["anotador"].map(ka).to_numpy(np.int64)
        self.y = largo["clase"].map(cl).to_numpy(np.int64)
        self.n_items, self.n_ann, self.C = len(self.items), len(self.anotadores), len(self.clases)
        self.n_obs_item = np.bincount(self.item, minlength=self.n_items)
        self.item_con_ref = np.zeros(self.n_items, bool)
        self.item_con_ref[self.item[self.es_ref[self.ann]]] = True

    @property
    def n_obs(self) -> int:
        return len(self.y)


def matriz_prior(diag: float, off: float, C: int) -> np.ndarray:
    return np.full((C, C), float(off)) + np.eye(C) * (float(diag) - float(off))


def construir_prior(datos: Datos, cfg: dict, nivel: Optional[str] = None) -> np.ndarray:
    nivel = nivel or cfg["prior"]["seleccion"]
    out = np.empty((datos.n_ann, datos.C, datos.C))
    for k in range(datos.n_ann):
        p = cfg["prior"]["humano"] if datos.es_ref[k] else cfg["prior"][nivel]
        out[k] = matriz_prior(p["diag"], p["off"], datos.C)
    return out


def _dirichlet(rng: np.random.Generator, a: np.ndarray) -> np.ndarray:
    """Dirichlet por la ultima dimension, vectorizado (gammas normalizadas)."""
    g = rng.gamma(a)
    g = np.maximum(g, 1e-300)
    return g / g.sum(axis=-1, keepdims=True)


def _logsumexp(x: np.ndarray) -> np.ndarray:
    m = x.max(axis=1, keepdims=True)
    return (m + np.log(np.exp(x - m).sum(axis=1, keepdims=True)))[:, 0]


def _z_inicial(d: Datos, rng: np.random.Generator, cadena: int) -> np.ndarray:
    """Cadena 0: voto de mayoria (empates al azar). Otras: muestra del voto suavizado mezclado con uniforme (sobredispersion)."""
    votos = np.zeros((d.n_items, d.C))
    np.add.at(votos, (d.item, d.y), 1.0)
    if cadena == 0:
        votos = votos + rng.random(votos.shape) * 1e-3
        return votos.argmax(axis=1)
    p = votos / votos.sum(axis=1, keepdims=True)
    p = 0.6 * p + 0.4 / d.C
    return (p.cumsum(1) < rng.random((d.n_items, 1))).sum(1).clip(0, d.C - 1)


def gibbs_cadena(d: Datos, prior_theta: np.ndarray, alpha_pi: float, n_iter: int, descarte: int, thin: int,
                 rng: np.random.Generator, cadena: int = 0) -> dict:
    """Una cadena. Devuelve trazas completas de loglik y, tras descarte/adelgazamiento, sorteos de pi, Theta y
    conteos posteriores de z por item."""
    C, K, N = d.C, d.n_ann, d.n_items
    z = _z_inicial(d, rng, cadena)
    guardadas = (n_iter - descarte) // thin
    pis = np.empty((guardadas, C)); thetas = np.empty((guardadas, K, C, C))
    zcount = np.zeros((N, C)); loglik = np.empty(n_iter)
    flat_base = d.ann * C * C
    j = 0
    for it in range(n_iter):
        pi = _dirichlet(rng, np.bincount(z, minlength=C) + alpha_pi)
        cnt = np.bincount(flat_base + z[d.item] * C + d.y, minlength=K * C * C).reshape(K, C, C)
        theta = _dirichlet(rng, prior_theta + cnt)
        logt = np.log(theta)
        L = np.tile(np.log(pi), (N, 1))
        for c in range(C):
            L[:, c] += np.bincount(d.item, weights=logt[d.ann, c, d.y], minlength=N)
        lse = _logsumexp(L)
        loglik[it] = lse.sum()
        P = np.exp(L - lse[:, None])
        z = (P.cumsum(1) < rng.random((N, 1))).sum(1).clip(0, C - 1)
        if it >= descarte and (it - descarte) % thin == 0 and j < guardadas:
            pis[j] = pi; thetas[j] = theta; zcount += np.eye(C)[z]; j += 1
    return {"pi": pis, "theta": thetas, "zcount": zcount, "loglik": loglik, "n_guardadas": j}


# --------------------------------------------------------------------------- diagnosticos
def rhat_dividido(x: np.ndarray) -> float:
    """R-hat dividido (Gelman-Rubin con cada cadena partida en dos). x: (cadenas, iteraciones)."""
    x = np.asarray(x, float)
    n = x.shape[1] // 2
    if n < 2:
        return float("nan")
    s = np.concatenate([x[:, :n], x[:, n:2 * n]], axis=0)
    W = s.var(axis=1, ddof=1).mean()
    if W <= 1e-300:
        return 1.0 if np.allclose(s, s[0, 0]) else float("inf")
    B = n * s.mean(axis=1).var(ddof=1)
    return float(np.sqrt(((n - 1) / n * W + B / n) / W))


def ess_aprox(x: np.ndarray) -> float:
    """Tamano efectivo aproximado (autocorrelaciones combinadas entre cadenas, suma de pares de Geyer)."""
    x = np.asarray(x, float)
    m, n = x.shape
    if n < 4:
        return float("nan")
    xc = x - x.mean(axis=1, keepdims=True)
    f = np.fft.rfft(xc, n=2 * n, axis=1)
    acov = np.fft.irfft(f * np.conj(f), axis=1)[:, :n] / n * (n / (n - 1))
    W = acov[:, 0].mean()
    var_plus = W * (n - 1) / n + (x.mean(axis=1).var(ddof=1) if m > 1 else 0.0)
    if var_plus <= 1e-300:
        return float(m * n)
    rho = 1.0 - (W - acov.mean(axis=0)) / var_plus
    rho[0] = 1.0
    suma, prev = 0.0, np.inf
    for t in range(0, n - 1, 2):
        par = rho[t] + rho[t + 1]
        if par <= 0:
            break
        par = min(par, prev)           # monotonia
        suma += par; prev = par
    tau = max(-1.0 + 2.0 * suma, 1.0 / np.log10(m * n) if m * n > 10 else 1.0)
    return float(min(m * n / tau, m * n * np.log10(m * n)))


def tabla_diagnosticos(cadenas: list[dict], d: Datos, cfg: dict) -> pd.DataFrame:
    """R-hat y ESS para pi, la diagonal de cada Theta_k y la verosimilitud marginal (post-descarte)."""
    desc = cfg["muestreo"]["descarte"]
    filas = []

    def agrega(nombre, x):
        filas.append({"parametro": nombre, "rhat": rhat_dividido(x), "ess": ess_aprox(x)})

    for c, cl in enumerate(d.clases):
        agrega(f"pi[{cl}]", np.stack([ch["pi"][:, c] for ch in cadenas]))
    for k, a in enumerate(d.anotadores):
        for c, cl in enumerate(d.clases):
            agrega(f"theta[{a}][{cl}->{cl}]", np.stack([ch["theta"][:, k, c, c] for ch in cadenas]))
    agrega("loglik_marginal", np.stack([ch["loglik"][desc:] for ch in cadenas]))
    t = pd.DataFrame(filas)
    t["convergio"] = (t["rhat"] < cfg["diagnosticos"]["umbral_rhat"]) & (t["ess"] >= cfg["diagnosticos"]["umbral_ess"])
    return t


# --------------------------------------------------------------------------- ajuste completo
def ajustar(largo: pd.DataFrame, clases: list[str], cfg: dict, prior: Optional[str] = None,
            semilla: Optional[int] = None, n_cadenas: Optional[int] = None, n_iter: Optional[int] = None,
            descarte: Optional[int] = None, adelgazamiento: Optional[int] = None) -> dict:
    m = cfg["muestreo"]
    semilla = m["semilla"] if semilla is None else semilla
    n_cadenas = n_cadenas or m["n_cadenas"]; n_iter = n_iter or m["n_iter"]
    descarte = m["descarte"] if descarte is None else descarte
    adelgazamiento = adelgazamiento or m["adelgazamiento"]
    cfg_m = {**cfg, "muestreo": {**m, "semilla": semilla, "n_cadenas": n_cadenas, "n_iter": n_iter,
                                 "descarte": descarte, "adelgazamiento": adelgazamiento}}
    d = Datos(largo, clases)
    prior_theta = construir_prior(d, cfg_m, prior)
    alpha_pi = cfg["prior"]["prevalencia"]["alpha"]
    seeds = np.random.SeedSequence(semilla).spawn(n_cadenas)
    t0 = time.perf_counter()
    cadenas = [gibbs_cadena(d, prior_theta, alpha_pi, n_iter, descarte, adelgazamiento,
                            np.random.default_rng(s), cadena=i) for i, s in enumerate(seeds)]
    tiempo = time.perf_counter() - t0
    diag = tabla_diagnosticos(cadenas, d, cfg_m)
    return {"datos": d, "cadenas": cadenas, "diagnosticos": diag, "cfg": cfg_m, "prior": prior or cfg["prior"]["seleccion"],
            "prior_theta": prior_theta, "tiempo_muestreo_s": tiempo, "semilla": semilla,
            "convergio": bool(diag["convergio"].all())}


# --------------------------------------------------------------------------- resumenes posteriores
def _q(x: np.ndarray, nivel: float, axis=0):
    lo = (1 - nivel) / 2
    return np.quantile(x, lo, axis=axis), np.quantile(x, 1 - lo, axis=axis)


def _entropia(P: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -np.where(P > 0, P * np.log2(P), 0.0).sum(axis=1)
    return h


def resumir(res: dict, etiqueta: str, campo: str, con_referencia: bool) -> dict[str, pd.DataFrame]:
    d: Datos = res["datos"]; cfg = res["cfg"]; nivel = cfg["salida"]["nivel_intervalo"]
    cad = res["cadenas"]
    medida = cfg["salida"]["medida_con_humana"] if con_referencia else cfg["salida"]["medida_sin_humana"]
    pi = np.concatenate([c["pi"] for c in cad]); th = np.concatenate([c["theta"] for c in cad])
    zc = sum(c["zcount"] for c in cad); P = zc / zc.sum(axis=1, keepdims=True)
    modal = P.argmax(axis=1)
    cl = np.array(d.clases)
    items = pd.DataFrame({"campo": campo, "item": d.items, "n_anotaciones": d.n_obs_item.astype(np.int64),
                          "tiene_referencia_humana": d.item_con_ref, "clase_modal": cl[modal],
                          "prob_modal": P.max(axis=1), "entropia_bits": _entropia(P),
                          "entropia_normalizada": _entropia(P) / np.log2(d.C) if d.C > 1 else 0.0})
    for c, nombre in enumerate(d.clases):
        items[f"prob_{nombre}"] = P[:, c]
    items["etiqueta"] = etiqueta; items["lectura"] = medida

    lo, hi = _q(th, nivel)
    mu = th.mean(axis=0)
    filas = []
    for k, a in enumerate(d.anotadores):
        for c in range(d.C):
            for y in range(d.C):
                filas.append({"campo": campo, "anotador": a, "es_referencia_humana": bool(d.es_ref[k]),
                              "clase_verdadera": d.clases[c], "clase_observada": d.clases[y],
                              "media": mu[k, c, y], "lo": lo[k, c, y], "hi": hi[k, c, y],
                              "nivel_intervalo": nivel, "etiqueta": etiqueta, "lectura": medida})
    conf = pd.DataFrame(filas)

    plo, phi = _q(pi, nivel)
    prev = pd.DataFrame({"campo": campo, "clase": d.clases, "media": pi.mean(axis=0), "lo": plo, "hi": phi,
                         "nivel_intervalo": nivel, "etiqueta": etiqueta, "lectura": medida})

    # exactitud (sum_c pi_c Theta[c,c]) y sesgo ordinal (media del nivel observado menos nivel verdadero)
    nivel_ord = np.arange(d.C, dtype=float)
    exact = np.einsum("sc,skcc->sk", pi, th)
    sesgo = np.einsum("sc,skcy,y->sk", pi, th, nivel_ord) - (pi @ nivel_ord)[:, None]
    filas = []
    for k, a in enumerate(d.anotadores):
        for nombre, x, interp in (("exactitud" if con_referencia else "acuerdo_con_clase_latente", exact[:, k], medida),
                                  ("sesgo_ordinal", sesgo[:, k], medida)):
            l, h = _q(x, nivel)
            filas.append({"campo": campo, "anotador": a, "es_referencia_humana": bool(d.es_ref[k]), "medida": nombre,
                          "media": x.mean(), "lo": l, "hi": h, "nivel_intervalo": nivel, "tipo_medida": interp,
                          "etiqueta": etiqueta})
    medidas = pd.DataFrame(filas)

    trazas = pd.DataFrame([{"cadena": i, "iteracion": t, "loglik_marginal": float(v), "descarte": t < cfg["muestreo"]["descarte"],
                            "campo": campo, "etiqueta": etiqueta}
                           for i, c in enumerate(cad) for t, v in enumerate(c["loglik"])])
    diag = res["diagnosticos"].assign(campo=campo, etiqueta=etiqueta)
    return {"items": items, "confusion": conf, "prevalencias": prev, "medidas": medidas, "diagnosticos": diag, "traza_loglik": trazas}


# --------------------------------------------------------------------------- esquemas de salida
_S = pa.string(); _F = pa.float64(); _B = pa.bool_(); _I = pa.int64()
ESQUEMAS_BASE = {
    "confusion": pa.schema([("campo", _S), ("anotador", _S), ("es_referencia_humana", _B), ("clase_verdadera", _S),
                            ("clase_observada", _S), ("media", _F), ("lo", _F), ("hi", _F), ("nivel_intervalo", _F),
                            ("etiqueta", _S), ("lectura", _S)]),
    "prevalencias": pa.schema([("campo", _S), ("clase", _S), ("media", _F), ("lo", _F), ("hi", _F),
                               ("nivel_intervalo", _F), ("etiqueta", _S), ("lectura", _S)]),
    "medidas": pa.schema([("campo", _S), ("anotador", _S), ("es_referencia_humana", _B), ("medida", _S), ("media", _F),
                          ("lo", _F), ("hi", _F), ("nivel_intervalo", _F), ("tipo_medida", _S), ("etiqueta", _S)]),
    "diagnosticos": pa.schema([("parametro", _S), ("rhat", _F), ("ess", _F), ("convergio", _B), ("campo", _S), ("etiqueta", _S)]),
    "traza_loglik": pa.schema([("cadena", _I), ("iteracion", _I), ("loglik_marginal", _F), ("descarte", _B),
                               ("campo", _S), ("etiqueta", _S)]),
}


def esquema_items(clases: list[str]) -> pa.Schema:
    return pa.schema([("campo", _S), ("item", _S), ("n_anotaciones", _I), ("tiene_referencia_humana", _B),
                      ("clase_modal", _S), ("prob_modal", _F), ("entropia_bits", _F), ("entropia_normalizada", _F)]
                     + [(f"prob_{c}", _F) for c in clases] + [("etiqueta", _S), ("lectura", _S)])


def escribir_tabla(df: pd.DataFrame, schema: pa.Schema, path: Path, meta: dict) -> None:
    t = pa.Table.from_pandas(df[schema.names], schema=schema, preserve_index=False)
    t = t.replace_schema_metadata({"b1_meta": json.dumps(meta, ensure_ascii=False, default=str)})
    pq.write_table(t, path)


# --------------------------------------------------------------------------- resumen en texto
def texto_resumen(res: dict, tablas: dict, etiqueta: str, campo: str, con_referencia: bool, razones_piloto: list[str],
                  mismo_modelo: bool, unidad: str = "corrida") -> str:
    d: Datos = res["datos"]
    L = [f"B1 Dawid-Skene [{campo}] - {etiqueta}", f"items={d.n_items} anotadores={d.n_ann} observaciones={d.n_obs} "
         f"clases={d.clases} prior={res['prior']}"]
    if razones_piloto:
        L.append("ATENCION: PILOTO, NO RESULTADO (prueba de humo). Razones: " + "; ".join(razones_piloto))
    if con_referencia:
        L.append(f"Con referencia humana ({int(d.es_ref.sum())} anotador(es) humano(s); {int(d.item_con_ref.sum())} items). "
                 "Las medidas son exactitud estimada respecto de la referencia, que NO es verdad externa.")
    else:
        L.append("SIN referencia humana: los resultados son CONSISTENCIA ENTRE CORRIDAS, NO EXACTITUD.")
        L.append("ADVERTENCIA: corridas del mismo LLM/prompt no son independientes (012); el modelo las trata como independientes, "
                 "asi que los posteriores son falsamente precisos y el sesgo comun del anotador no se puede separar de la verdad.")
    if mismo_modelo and con_referencia and unidad == "corrida":
        L.append("ADVERTENCIA: todas las corridas LLM son del mismo modelo y se tratan como independientes; el sesgo comun NO se separa "
                 "de la verdad aunque haya referencia. Use --unidad modelo (una vista por modelo) para que la referencia lo identifique.")
    p = tablas["prevalencias"]
    L.append("Prevalencias (media [intervalo]): " + "; ".join(f"{r.clase}={r.media:.3f} [{r.lo:.3f}, {r.hi:.3f}]" for r in p.itertuples()))
    g = tablas["diagnosticos"]
    L.append(f"Convergencia: {'OK' if res['convergio'] else 'NO CONVERGIO'} (max R-hat={g.rhat.max():.3f} umbral "
             f"{res['cfg']['diagnosticos']['umbral_rhat']}; min ESS={g.ess.min():.0f} umbral {res['cfg']['diagnosticos']['umbral_ess']}).")
    if not res["convergio"]:
        L.append("ADVERTENCIA: no se cumplen los umbrales de diagnostico; no interpretar las salidas.")
    L.append("Estado: parametros PROVISIONALES (docs/issues/calibracion-2026-10-19-parametros-provisionales.md).")
    return "\n".join(L)


# --------------------------------------------------------------------------- orquestacion
def registrar_issue(mensaje: str, issues_dir: Path, hoy: Optional[dt.date] = None) -> Path:
    """Regla 5: entregable fuera de esquema -> issue en docs/issues/."""
    hoy = hoy or dt.date.today()
    p = Path(issues_dir) / f"calibracion-{hoy.isoformat()}-esquema-incumplido.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"# Issue: entrada de calibracion fuera de esquema ({hoy.isoformat()})\n\n- {mensaje}\n"
                "- Accion: calibrate se detuvo; corregir el entregable.\n\n")
    return p


def ejecutar(anot_rutas, salida_dir, campo: str = "exposure_class", referencia=None, ref_cols: Optional[dict] = None,
             permitir_piloto: bool = False, sobrescribir: bool = False, cfg: Optional[dict] = None,
             universo_path: Optional[Path] = None, unidad: str = "corrida", **kw) -> dict:
    """Ajusta B1, escribe Parquet + meta.json y devuelve {'rutas', 'resumen', ...}. kw: prior, semilla, n_cadenas, n_iter, descarte, adelgazamiento."""
    cfg = cfg or cargar_config()
    from src.score import exposicion as score
    largo, ann = cargar_anotaciones_llm(anot_rutas, campo, cfg)
    runs = sorted(largo["anotador"].unique())
    universo = None
    up = Path(universo_path) if universo_path else ROOT / cfg["entrada"]["universo_tareas"]
    if campo == "exposure_class" and up.exists() and "onet_soc" in ann.columns:
        universo = pd.read_parquet(up)
    razones = detectar_piloto(ann, universo, runs)
    if razones and not permitir_piloto:
        raise PilotoNoPermitido("; ".join(razones))
    etiqueta = cfg["salida"]["etiqueta_piloto"] if razones else cfg["salida"]["etiqueta_normal"]

    if unidad not in ("corrida", "modelo"):
        raise ValueError("unidad debe ser 'corrida' o 'modelo'")
    if unidad == "modelo":
        largo = colapsar_por_grupo(largo, dict(zip(ann["run_id"].astype(str), ann["model"].astype(str))) if "model" in ann.columns
                                   else {r: "modelo_desconocido" for r in runs})
    ref_n_fuera = 0
    con_ref = referencia is not None
    if con_ref:
        ref = cargar_referencia(referencia, campo, cfg, **(ref_cols or {}))
        en = ref["item"].isin(set(largo["item"]))
        ref_n_fuera = int((~en).sum()); ref = ref[en]
        if ref.empty:
            raise EsquemaIncumplido("la referencia humana no comparte ningun item con las anotaciones")
        largo = pd.concat([largo, ref], ignore_index=True)

    clases = list(cfg["campos"][campo]["clases"])
    res = ajustar(largo, clases, cfg, **kw)
    tablas = resumir(res, etiqueta, campo, con_ref)
    modelos = sorted(ann["model"].unique()) if "model" in ann.columns else []
    resumen = texto_resumen(res, tablas, etiqueta, campo, con_ref, razones, len(modelos) == 1, unidad)

    corridas = []
    for rid, g in ann.groupby("run_id"):
        corridas.append({"run_id": rid, **{c: (str(g[c].iloc[0]) if c in g else None) for c in
                         ("model", "prompt_version", "prompt_sha256", "run_date", "onet_version")}, "n_anotaciones": int(len(g))})
    entradas = [Path(p) for p in score._expandir(anot_rutas)] + ([Path(referencia)] if con_ref else [])
    cfg_s = res["cfg"]
    meta = {
        "etiqueta": etiqueta, "es_piloto": bool(razones), "razones_piloto": razones, "campo": campo,
        "unidad_anotador": unidad, "modo": "con_referencia_humana" if con_ref else "sin_referencia_humana",
        "lectura": cfg["salida"]["medida_con_humana"] if con_ref else cfg["salida"]["medida_sin_humana"],
        "advertencia": None if con_ref else "SIN muestra humana: consistencia entre corridas, NO exactitud; corridas del mismo LLM no son independientes (012).",
        "modelo": MODELO, "version_modelo": VERSION_MODELO, "clases": clases, "prior": res["prior"],
        "prior_parametros": {k: cfg["prior"][k] for k in ("prevalencia", res["prior"], "humano")},
        "muestreo": cfg_s["muestreo"], "diagnosticos_umbrales": cfg["diagnosticos"], "convergio": res["convergio"],
        "nivel_intervalo": cfg["salida"]["nivel_intervalo"], "semilla": res["semilla"],
        "tiempo_muestreo_s": round(res["tiempo_muestreo_s"], 3),
        "n_items": res["datos"].n_items, "n_anotadores": res["datos"].n_ann, "n_observaciones": res["datos"].n_obs,
        "anotadores": res["datos"].anotadores, "run_ids_entrada": runs, "corridas": corridas,
        "referencia_items_fuera_de_anotaciones": ref_n_fuera,
        "entradas_sha256": {str(p): _sha256(p) for p in entradas},
        "config_sha256": _sha256(CONFIG_PATH), "config": {k: cfg[k] for k in ("campos", "muestreo", "prior", "diagnosticos", "salida")},
        "versiones": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "pyarrow": pa.__version__},
        "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "resumen": resumen,
    }
    out = Path(salida_dir); out.mkdir(parents=True, exist_ok=True)
    stem = f"b1_{campo}" + ("_PILOTO" if razones else "")
    rutas = {n: out / f"{stem}_{n}.parquet" for n in ("items", "confusion", "prevalencias", "medidas", "diagnosticos", "traza_loglik")}
    rutas["meta"] = out / f"{stem}_meta.json"
    existentes = [p for p in rutas.values() if p.exists()]
    if existentes and not sobrescribir:
        raise FileExistsError(f"ya existen {[p.name for p in existentes]}; use --sobrescribir")
    esq = {**ESQUEMAS_BASE, "items": esquema_items(clases)}
    for n, df in tablas.items():
        escribir_tabla(df, esq[n], rutas[n], meta)
    rutas["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"rutas": rutas, "resumen": resumen, "meta": meta, "tablas": tablas, "resultado": res}


def main(argv=None) -> int:
    cfg = cargar_config()
    ap = argparse.ArgumentParser(description="B1 (decision 012): error de medicion tipo Dawid-Skene por Gibbs. Se niega a correr sobre el piloto.")
    ap.add_argument("--anotaciones", nargs="+", required=True,
                    help="archivos run_*.parquet o directorios con ellos")
    ap.add_argument("--campo", default="exposure_class", choices=list(cfg["campos"]))
    ap.add_argument("--referencia", default=None, help="parquet/CSV con etiquetas humanas de referencia (opcional)")
    ap.add_argument("--ref-item", default="task_id"); ap.add_argument("--ref-clase", default="clase_humana")
    ap.add_argument("--ref-revisor", default=None, help="columna con el revisor (cada uno es un anotador)")
    ap.add_argument("--unidad", choices=["corrida", "modelo"], default="corrida",
                    help="'modelo' colapsa las corridas de un mismo modelo en un anotador (moda; empate = ausente)")
    ap.add_argument("--prior", choices=["debil", "fuerte"], default=None)
    ap.add_argument("--semilla", type=int, default=None); ap.add_argument("--n-cadenas", type=int, default=None)
    ap.add_argument("--n-iter", type=int, default=None); ap.add_argument("--descarte", type=int, default=None)
    ap.add_argument("--adelgazamiento", type=int, default=None)
    ap.add_argument("--universo-tareas", default=None)
    ap.add_argument("--salida-dir", default=str(ROOT / cfg["salida"]["dir"]))
    ap.add_argument("--permitir-piloto", action="store_true",
                    help=f"prueba de humo sobre el piloto; salidas rotuladas '{cfg['salida']['etiqueta_piloto']}'")
    ap.add_argument("--sobrescribir", action="store_true")
    a = ap.parse_args(argv)
    kw = {k: v for k, v in dict(prior=a.prior, semilla=a.semilla, n_cadenas=a.n_cadenas, n_iter=a.n_iter,
                                descarte=a.descarte, adelgazamiento=a.adelgazamiento).items() if v is not None}
    try:
        r = ejecutar(a.anotaciones, a.salida_dir, a.campo, a.referencia,
                     dict(col_item=a.ref_item, col_clase=a.ref_clase, col_revisor=a.ref_revisor),
                     a.permitir_piloto, a.sobrescribir, cfg, universo_path=a.universo_tareas, unidad=a.unidad, **kw)
    except PilotoNoPermitido as e:
        print(f"RECHAZADO: las anotaciones son piloto ({e}). Use --permitir-piloto para una prueba de humo rotulada.", file=sys.stderr)
        return 2
    except EsquemaIncumplido as e:
        p = registrar_issue(str(e), ROOT / cfg["salida"]["issues_dir"])
        print(f"ENTRADA FUERA DE ESQUEMA: {e}\nIssue: {p}", file=sys.stderr)
        return 3
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        return 4
    except FileNotFoundError as e:
        print(f"NO ENCONTRADO: {e}", file=sys.stderr)
        return 5
    print(r["resumen"])
    for n, p in r["rutas"].items():
        print(f"  {n}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
