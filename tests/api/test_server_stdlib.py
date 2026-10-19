"""Prueba minima del servidor stdlib anterior (src/api/server.py), que se conserva funcional."""
import json
import threading
import urllib.error
import urllib.request

import pytest

from src.api import server as SRV


@pytest.fixture(scope="module")
def base():
    srv = SRV.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown(); srv.server_close()


def test_stdlib_health_arbol_405_y_traversal(base):
    assert json.load(urllib.request.urlopen(base + "/api/health")) == {"ok": True}
    assert json.load(urllib.request.urlopen(base + "/api/sinco/tree"))["n_nodos"] == 714
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(urllib.request.Request(base + "/api/crosswalk", data=b"{}", method="POST"))
    assert e.value.code == 405
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(base + "/..%2f..%2fdata/raw/manifest.json")
    assert e.value.code == 404
