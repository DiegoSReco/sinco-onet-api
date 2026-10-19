"""Interfaz abstracta de proveedor de LLM y cliente simulado (dry-run).

No hay ningun cliente real en este modulo: el usuario aun no indico modelo, proveedor ni presupuesto.
El cliente dry-run solo sirve para probar el pipeline y los esquemas; sus "anotaciones" son ruido
determinista sin valor sustantivo y nunca deben usarse como resultados.
"""
from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass


class TransientProviderError(Exception):
    """Fallo reintentable (red, limite de tasa, 5xx)."""


class PermanentProviderError(Exception):
    """Fallo no reintentable (autenticacion, solicitud invalida)."""


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def complete(self, system: str, user: str, *, temperature: float | None, seed: int | None,
                 max_tokens: int = 400) -> ProviderResponse:
        """Devuelve el texto crudo del modelo. Debe lanzar TransientProviderError o PermanentProviderError."""


class DryRunProvider(LLMProvider):
    """Simulador determinista. fail_rate: fraccion de tareas con error transitorio en el primer intento;
    invalid_rate: fraccion con formato invalido en el primer intento; marker: si aparece en el prompt,
    la respuesta es siempre invalida (para probar fallos definitivos)."""
    name = "dry-run"

    def __init__(self, fail_rate: float = 0.0, invalid_rate: float = 0.0, always_invalid_marker: str | None = None):
        self.fail_rate, self.invalid_rate, self.marker = fail_rate, invalid_rate, always_invalid_marker
        self._intentos: dict[str, int] = {}
        self.calls = 0

    @staticmethod
    def _u(*parts) -> float:
        h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
        return int.from_bytes(h[:8], "big") / 2**64

    def complete(self, system, user, *, temperature, seed, max_tokens=400):
        self.calls += 1
        n = self._intentos.get(user, 0)
        self._intentos[user] = n + 1
        ti = len(system + user) // 4
        if self.marker and self.marker in user:
            return ProviderResponse("no es json", ti, 3)
        if n == 0 and self._u("fail", user, seed) < self.fail_rate:
            raise TransientProviderError("fallo simulado")
        if n == 0 and self._u("inv", user, seed) < self.invalid_rate:
            return ProviderResponse('{"exposure_class": "E7", "score": 0.37}', ti, 8)
        u = self._u("cls", user, seed)
        out = {"exposure_class": "E0" if u < 1 / 3 else "E1" if u < 2 / 3 else "E2",
               "physical_bottleneck": self._u("phy", user, seed) < 0.3,
               "confidence": ["alta", "media", "baja"][int(self._u("conf", user, seed) * 3)],
               "rationale": "Salida simulada (dry-run) sin valor sustantivo."}
        return ProviderResponse(json.dumps(out), ti, 40)


def crear(nombre: str) -> LLMProvider:
    if nombre == "dry-run":
        return DryRunProvider()
    raise NotImplementedError(
        f"Proveedor '{nombre}' no implementado: falta que el usuario indique modelo, proveedor, clave y tope de gasto.")
