"""Plantillas de texto versionadas (text_template_version) y truncamiento por campo (005 5.1, 4.5).

SINCO (consulta): titulo_ampliado + ocupaciones ejemplo + descripcion + funciones (variante A+F).
Los 'excluye' NO entran. O*NET (documento): titulo + descripcion. Sin tareas ni traduccion.
Truncamiento por tokens con prioridad: titulo, ocupaciones, descripcion, funciones; se registra.
"""
from __future__ import annotations

import pandas as pd

ETIQ = {"titulo": "", "ocupaciones": "Ocupaciones: ", "descripcion": "Descripcion: ", "funciones": "Funciones: "}
ETIQ_EN = {"titulo": "", "descripcion": "Description: "}


def _truncar(texto: str, tok, presupuesto: int) -> tuple[str, int, bool]:
    ids = tok.encode(texto, add_special_tokens=False)
    if len(ids) <= presupuesto:
        return texto, len(ids), False
    if presupuesto <= 0:
        return "", 0, True
    return tok.decode(ids[:presupuesto]).strip(), presupuesto, True


def construir_texto(campos: dict[str, str], tok, max_length: int, prefijo: str,
                    prioridad=("titulo", "ocupaciones", "descripcion", "funciones"), etiquetas=None) -> tuple[str, dict]:
    """campos: nombre -> texto ya unido (cadena vacia si no hay). Devuelve (texto con prefijo, info)."""
    etiquetas = etiquetas or ETIQ
    n_pref = len(tok.encode(prefijo, add_special_tokens=False)) if prefijo else 0
    restante = max_length - 2 - n_pref
    trozos, truncados, tokens = {}, [], 0
    for campo in prioridad:
        txt = (campos.get(campo) or "").strip()
        if not txt:
            continue
        txt_t, n, cortado = _truncar(etiquetas[campo] + txt, tok, restante)
        if cortado:
            truncados.append(campo)
        if txt_t:
            trozos[campo] = txt_t
        restante -= n
        tokens += n
    texto = prefijo + "\n".join(trozos[c] for c in prioridad if c in trozos)
    return texto, {"n_tokens": tokens + n_pref + 2, "truncado": bool(truncados), "campos_truncados": ",".join(truncados)}


def documentos_sinco(tablas: dict[str, pd.DataFrame], tok, max_length: int, prefijo: str, max_ocup: int,
                     prioridad) -> pd.DataFrame:
    """Un documento por grupo unitario SINCO, ordenado por codigo."""
    s = tablas["sinco"]
    gu = s[s["nivel"] == "grupo_unitario"][["sinco_code", "titulo"]]
    d = tablas["sinco_descripcion"].set_index("sinco_code")
    oc = tablas["sinco_ocupaciones_ejemplo"].sort_values(["sinco_code", "orden"]).groupby("sinco_code")["ocupacion"].apply(
        lambda x: " ".join(t.strip() for t in list(x)[:max_ocup]))
    fu = tablas["sinco_funciones"].sort_values(["sinco_code", "orden"]).groupby("sinco_code")["funcion"].apply(
        lambda x: " ".join(t.strip() for t in x))
    filas = []
    for code, titulo in sorted(zip(gu["sinco_code"], gu["titulo"])):
        campos = {
            "titulo": str(d["titulo_ampliado"].get(code) or titulo or ""),
            "ocupaciones": oc.get(code, ""),
            "descripcion": str(d["descripcion"].get(code) or ""),
            "funciones": fu.get(code, ""),
        }
        texto, info = construir_texto(campos, tok, max_length, prefijo, tuple(prioridad))
        filas.append({"sinco_code": code, "texto": texto, "tiene_funciones": bool(campos["funciones"]),
                      "tiene_ocupaciones": bool(campos["ocupaciones"]), **info})
    return pd.DataFrame(filas)


def documentos_onet(onet: pd.DataFrame, tok, max_length: int, prefijo: str) -> pd.DataFrame:
    """Un documento por ocupacion O*NET-SOC (titulo + descripcion), ordenado por codigo."""
    filas = []
    for code, t, dsc in sorted(zip(onet["onet_soc_code"], onet["titulo_en"], onet["descripcion_en"])):
        campos = {"titulo": str(t or ""), "descripcion": str(dsc or "")}
        texto, info = construir_texto(campos, tok, max_length, prefijo, ("titulo", "descripcion"), ETIQ_EN)
        filas.append({"onet_soc_code": code, "texto": texto, **info})
    return pd.DataFrame(filas)
