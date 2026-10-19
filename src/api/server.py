"""Servidor HTTP de solo lectura (biblioteca estandar). Uso: python -m src.api.server [--host 127.0.0.1] [--port 8000]

Solo GET/HEAD. Cualquier otro metodo -> 405. Sirve /api/* (JSON) y la pagina estatica de src/api/static/.
No escribe en data/raw ni data/processed. Sin scores ni exposicion.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import service as S

STATIC = Path(__file__).resolve().parent / "static"


def _int(q: dict, k: str, d: int) -> int:
    try:
        return int(q.get(k, [d])[0])
    except ValueError:
        return d


def route(path: str, q: dict):
    """Devuelve (status, payload). payload None -> 404."""
    p = path.rstrip("/") or "/"
    if p == "/api/health":
        return 200, S.health()
    if p == "/api/meta":
        return 200, S.meta()
    if p == "/api/sinco/tree":
        return 200, S.sinco_tree()
    if p == "/api/sinco/search":
        return 200, S.sinco_search(q.get("q", [""])[0], _int(q, "limit", 30))
    m = re.fullmatch(r"/api/sinco/([1-9][0-9]{0,3})", p)
    if m:
        d = S.sinco_detail(m.group(1))
        return (200, d) if d else (404, {"error": "codigo SINCO no encontrado"})
    if p == "/api/onet/occupations":
        return 200, S.onet_list(q.get("q", [""])[0], _int(q, "limit", 50), _int(q, "offset", 0))
    m = re.fullmatch(r"/api/onet/occupations/([0-9]{2}-[0-9]{4}\.[0-9]{2})", p)
    if m:
        d = S.onet_detail(m.group(1))
        return (200, d) if d else (404, {"error": "ocupacion O*NET no encontrada"})
    if p == "/api/crosswalk":
        return 200, S.crosswalk(q.get("sinco_code", [None])[0], q.get("onet_soc_code", [None])[0])
    if p == "/api/crosswalk/schema":
        return 200, S.crosswalk_schema()
    if p.startswith("/api/"):
        return 404, {"error": "ruta no encontrada"}
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "sinco-api/0.1"

    def _send(self, status: int, body: bytes, ctype: str, head_only: bool = False):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _handle(self, head_only: bool = False):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            r = route(unquote(u.path), q)
        except Exception as e:  # error inesperado: 500 sin detalles internos
            return self._send(500, json.dumps({"error": "error interno", "tipo": type(e).__name__}).encode(), "application/json; charset=utf-8", head_only)
        if r is not None:
            status, payload = r
            return self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", head_only)
        rel = "index.html" if u.path in ("", "/") else unquote(u.path).lstrip("/")
        f = (STATIC / rel).resolve()
        if STATIC.resolve() not in f.parents or not f.is_file():
            return self._send(404, b'{"error": "no encontrado"}', "application/json; charset=utf-8", head_only)
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        self._send(200, f.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith("text/") or ctype.endswith("javascript") else ""), head_only)

    def do_GET(self):
        self._handle()

    def do_HEAD(self):
        self._handle(head_only=True)

    def _no_permitido(self):
        self.send_response(405)
        self.send_header("Allow", "GET, HEAD")
        body = b'{"error": "API de solo lectura: solo GET/HEAD"}'
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _no_permitido

    def log_message(self, fmt, *args):  # registro breve
        print("%s %s" % (self.address_string(), fmt % args))


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    srv = make_server(a.host, a.port)
    print(f"API de solo lectura en http://{a.host}:{a.port}/  (Ctrl+C para salir)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
