"""API de solo lectura SINCO 2019 / O*NET con FastAPI (decision 004, opcion B).

Reutiliza src/api/service.py sin cambios de logica. Solo GET/HEAD (otro metodo -> 405). Sin scores, exposicion ni
probabilidades. Documentacion OpenAPI automatica en /docs y /openapi.json.

Uso local (solo loopback):  python -m src.api.app --port 8001
Variables de entorno (opcionales):
  SINCO_CORS_ORIGINS   origenes permitidos para CORS, separados por coma (vacio = sin CORS)
  SINCO_ALLOWED_HOSTS  cabeceras Host permitidas, separadas por coma (por defecto: loopback)
  SINCO_ALLOW_PUBLIC_BIND=1  permite que "python -m src.api.app" escuche fuera de 127.0.0.1 (no usar sin decision)
"""
from __future__ import annotations

import argparse
import mimetypes
import os
import re
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import service as S

STATIC = Path(__file__).resolve().parent / "static"
METODOS = ["GET", "HEAD"]
MAX_Q = 100            # largo maximo de texto de busqueda
MAX_OFFSET = 100_000
LIMITE_BUSQUEDA_SINCO = 100
RE_SINCO = re.compile(r"[1-9][0-9]{0,3}")
RE_SOC = re.compile(r"[0-9]{2}-[0-9]{4}\.[0-9]{2}")
HOSTS_POR_DEFECTO = ["127.0.0.1", "localhost", "[::1]", "::1"]

CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
# Swagger UI (/docs) se carga de cdn.jsdelivr.net; solo esa ruta relaja la CSP.
CSP_DOCS = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def _lista_env(nombre: str, defecto: list[str]) -> list[str]:
    v = os.environ.get(nombre)
    return [x.strip() for x in v.split(",") if x.strip()] if v is not None else list(defecto)


def _err(status: int, msg: str) -> JSONResponse:
    return JSONResponse({"error": msg}, status_code=status)


def create_app(cors_origins: list[str] | None = None, allowed_hosts: list[str] | None = None) -> FastAPI:
    cors_origins = _lista_env("SINCO_CORS_ORIGINS", []) if cors_origins is None else cors_origins
    allowed_hosts = _lista_env("SINCO_ALLOWED_HOSTS", HOSTS_POR_DEFECTO) if allowed_hosts is None else allowed_hosts

    app = FastAPI(
        title="API SINCO 2019 / O*NET (solo lectura)",
        version="0.2",
        description=("Catalogo SINCO 2019 (INEGI) y ocupaciones/tareas O*NET (USDOL/ETA, CC BY 4.0) y coincidencias SINCO-O*NET. "
                     "Solo GET/HEAD. No devuelve scores, exposicion ni probabilidades. Las coincidencias automaticas (Metodo A1, "
                     "embeddings) estan **sin validar**."),
        docs_url="/docs", redoc_url=None, openapi_url="/openapi.json",
    )

    # ---- middlewares (el ultimo agregado es el mas externo)
    @app.middleware("http")
    async def solo_lectura_y_cabeceras(request: Request, call_next):
        if request.method not in METODOS:   # incluye OPTIONS no atendido por CORS
            resp = _err(405, "API de solo lectura: solo GET/HEAD")
            resp.headers["Allow"] = "GET, HEAD"
        else:
            resp = await call_next(request)
        h = resp.headers
        h["X-Content-Type-Options"] = "nosniff"
        h["X-Frame-Options"] = "DENY"
        h["Referrer-Policy"] = "no-referrer"
        h["Cross-Origin-Resource-Policy"] = "same-origin" if not cors_origins else "cross-origin"
        h["Cache-Control"] = "no-store"
        h["Content-Security-Policy"] = CSP_DOCS if request.url.path == "/docs" else CSP
        return resp

    if cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_methods=METODOS, allow_headers=[], allow_credentials=False)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # ---- errores con el mismo formato {"error": ...} de la API anterior
    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return _err(exc.status_code, {404: "no encontrado", 405: "API de solo lectura: solo GET/HEAD"}.get(exc.status_code, str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def _val(request: Request, exc: RequestValidationError):
        return JSONResponse({"error": "parametros invalidos", "detalle": [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()]},
                            status_code=422)

    @app.exception_handler(Exception)
    async def _500(request: Request, exc: Exception):  # sin detalles internos
        return JSONResponse({"error": "error interno", "tipo": type(exc).__name__}, status_code=500)

    def ro(path: str, **kw):
        """GET (documentado en OpenAPI) + HEAD (oculto) sobre la misma funcion."""
        def deco(fn):
            app.api_route(path, methods=["HEAD"], **{**kw, "include_in_schema": False})(fn)
            return app.api_route(path, methods=["GET"], **kw)(fn)
        return deco

    # ---- rutas /api (cada una delega en service.py)
    @ro("/api/health", tags=["sistema"], summary="Estado del servicio")
    def health():
        return S.health()

    @ro("/api/meta", tags=["sistema"], summary="Fuentes (hash, version), tablas y estado del crosswalk")
    def meta():
        return S.meta()

    @ro("/api/sinco/tree", tags=["sinco"], summary="Arbol completo SINCO 2019 (714 nodos)")
    def sinco_tree():
        return S.sinco_tree()

    @ro("/api/sinco/search", tags=["sinco"], summary="Busqueda sin acentos por codigo, titulo u ocupacion ejemplo")
    def sinco_search(q: str = Query("", max_length=MAX_Q), limit: int = Query(30, description=f"1 a {LIMITE_BUSQUEDA_SINCO}; se recorta")):
        return S.sinco_search(q, max(1, min(limit, LIMITE_BUSQUEDA_SINCO)))

    @ro("/api/sinco/{codigo}", tags=["sinco"], summary="Detalle de un nodo SINCO (1 a 4 digitos)")
    def sinco_detail(codigo: str):
        d = S.sinco_detail(codigo) if RE_SINCO.fullmatch(codigo) else None
        return d if d else _err(404, "codigo SINCO no encontrado")

    @ro("/api/onet/occupations", tags=["onet"], summary="Lista paginada de ocupaciones O*NET")
    def onet_list(q: str = Query("", max_length=MAX_Q), limit: int = Query(50, description="1 a 200; se recorta"),
                  offset: int = Query(0, ge=0, le=MAX_OFFSET)):
        return S.onet_list(q, limit, offset)

    @ro("/api/onet/occupations/{soc}", tags=["onet"], summary="Detalle y tareas de una ocupacion O*NET (sin valoraciones)")
    def onet_detail(soc: str):
        d = S.onet_detail(soc) if RE_SOC.fullmatch(soc) else None
        return d if d else _err(404, "ocupacion O*NET no encontrada")

    @ro("/api/crosswalk", tags=["crosswalk"], summary="Coincidencias SINCO-O*NET (automaticas, sin validar, salvo que diga otra cosa)")
    def crosswalk(sinco_code: str | None = Query(None, max_length=4), onet_soc_code: str | None = Query(None, max_length=10)):
        return S.crosswalk(sinco_code, onet_soc_code)

    @ro("/api/crosswalk/schema", tags=["crosswalk"], summary="Esquema declarado de crosswalk.parquet")
    def crosswalk_schema():
        return S.crosswalk_schema()

    @ro("/api/{resto:path}", include_in_schema=False)
    def api_404(resto: str):
        return _err(404, "ruta no encontrada")

    # ---- pagina estatica (lista blanca: solo archivos bajo src/api/static/)
    @ro("/{ruta:path}", include_in_schema=False)
    def estatico(ruta: str):
        rel = "index.html" if ruta in ("", "/") else ruta
        partes = rel.replace("\\", "/").split("/")
        if "\x00" in rel or "\\" in rel or any(p in ("..", "") or p.startswith(".") for p in partes):
            return _err(404, "no encontrado")
        f = (STATIC / rel).resolve()
        if STATIC.resolve() not in f.parents or not f.is_file():
            return _err(404, "no encontrado")
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("javascript"):
            ctype += "; charset=utf-8"
        return Response(f.read_bytes(), media_type=ctype)

    return app


app = create_app()


def main():
    import uvicorn
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8001)
    a = ap.parse_args()
    if a.host not in ("127.0.0.1", "localhost", "::1") and os.environ.get("SINCO_ALLOW_PUBLIC_BIND") != "1":
        raise SystemExit("Rechazado: solo se permite escuchar en loopback (127.0.0.1). Ver src/api/README.md.")
    print(f"API FastAPI de solo lectura en http://{a.host}:{a.port}/  (docs: /docs; Ctrl+C para salir)")
    uvicorn.run("src.api.app:app", host=a.host, port=a.port, log_level="info", server_header=False)


if __name__ == "__main__":
    main()
