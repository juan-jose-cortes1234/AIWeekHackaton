"""Decoder abierto en proceso, con pesos de Hugging Face (ARQUITECTURA §5).

Backends (sin APIs ni servidores):
- `llamacpp`: llama-cpp-python + GGUF oficial (`Qwen/Qwen3-8B-GGUF`). CPU o GPU.
  La salida JSON se fuerza con una gramática derivada del JSON schema.
- `transformers`: `Qwen/Qwen3-8B` con transformers (GPU). Decodificación voraz
  y parser tolerante con un reintento.

Siempre: temperatura 0 (decodificación voraz), semilla fija, Qwen3 sin modo de
razonamiento, y lista blanca de modelos abiertos verificada antes de cargar.
Las generaciones se guardan en caché por hash de (modelo, mensajes, parámetros);
`usar_cache=False` fuerza la regeneración (verificación en vivo).
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from src.config import RAIZ, Config, config

DIR_CACHE = RAIZ / "build" / "cache" / "gen"
SIN_RAZONAMIENTO = " /no_think"


@dataclass
class Generacion:
    texto: str
    datos: dict | None
    segundos: float
    tokens_prompt: int | None = None
    tokens_salida: int | None = None
    desde_cache: bool = False


# --------------------------------------------------------------------------- JSON

def extraer_json(texto: str) -> dict | None:
    """Primer objeto JSON válido del texto (tolera ```json, <think> y texto alrededor)."""
    t = re.sub(r"<think>.*?</think>", "", texto or "", flags=re.DOTALL)
    t = re.sub(r"```(?:json)?", "", t)
    inicio = t.find("{")
    while inicio != -1:
        nivel, en_cadena, escape = 0, False, False
        for i in range(inicio, len(t)):
            c = t[i]
            if en_cadena:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    en_cadena = False
            elif c == '"':
                en_cadena = True
            elif c == "{":
                nivel += 1
            elif c == "}":
                nivel -= 1
                if nivel == 0:
                    try:
                        obj = json.loads(t[inicio:i + 1])
                        return obj if isinstance(obj, dict) else None
                    except json.JSONDecodeError:
                        break
        inicio = t.find("{", inicio + 1)
    return None


# --------------------------------------------------------------------------- cliente

class LLM:
    def __init__(self, cfg: Config = config):
        cfg.validar_final()
        self.cfg = cfg
        self.backend = cfg.decoder_backend
        if self.backend == "llamacpp":
            self.id_modelo = f"{cfg.decoder_gguf_repo}/{cfg.decoder_gguf_file}"
            self._cargar_llamacpp()
        else:
            self.id_modelo = cfg.decoder_model
            self._cargar_transformers()

    # ---- carga
    def _cargar_llamacpp(self) -> None:
        from huggingface_hub import hf_hub_download
        from llama_cpp import Llama

        ruta = hf_hub_download(self.cfg.decoder_gguf_repo, self.cfg.decoder_gguf_file,
                               token=self.cfg.hf_token or None)
        self.modelo = Llama(
            model_path=ruta, n_ctx=self.cfg.decoder_num_ctx, seed=self.cfg.decoder_seed,
            n_threads=self.cfg.decoder_threads or None,
            n_gpu_layers=-1 if self.cfg.decoder_device == "cuda" else 0,
            verbose=False)

    def _cargar_transformers(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        torch.manual_seed(self.cfg.decoder_seed)
        self.tokenizer = AutoTokenizer.from_pretrained(self.cfg.decoder_model,
                                                       token=self.cfg.hf_token or None)
        self.modelo = AutoModelForCausalLM.from_pretrained(
            self.cfg.decoder_model, torch_dtype=torch.bfloat16,
            device_map=self.cfg.decoder_device, token=self.cfg.hf_token or None)
        self.modelo.eval()

    # ---- caché
    def _clave(self, mensajes: list[dict], esquema: dict | None, max_tokens: int) -> str:
        cuerpo = json.dumps({"backend": self.backend, "modelo": self.id_modelo,
                             "mensajes": mensajes, "esquema": esquema, "max_tokens": max_tokens,
                             "temperatura": 0, "semilla": self.cfg.decoder_seed,
                             "ctx": self.cfg.decoder_num_ctx},
                            ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()

    # ---- generación
    def generar(self, mensajes: list[dict], esquema: dict | None = None, max_tokens: int = 700,
                usar_cache: bool = True, dir_cache: Path | None = None) -> Generacion:
        """Genera con temperatura 0. Si `esquema` se da, la salida es un objeto JSON."""
        mensajes = [dict(m) for m in mensajes]
        if mensajes and mensajes[-1]["role"] == "user" and SIN_RAZONAMIENTO not in mensajes[-1]["content"]:
            mensajes[-1]["content"] += SIN_RAZONAMIENTO
        directorio = dir_cache or DIR_CACHE
        ruta = directorio / f"{self._clave(mensajes, esquema, max_tokens)}.json"
        if usar_cache and ruta.is_file():
            d = json.loads(ruta.read_text(encoding="utf-8"))
            return Generacion(d["texto"], d["datos"], 0.0, d.get("tokens_prompt"),
                              d.get("tokens_salida"), desde_cache=True)

        t0 = time.perf_counter()
        if self.backend == "llamacpp":
            texto, tp, ts = self._generar_llamacpp(mensajes, esquema, max_tokens)
        else:
            texto, tp, ts = self._generar_transformers(mensajes, max_tokens)
        datos = extraer_json(texto) if esquema is not None else None
        if esquema is not None and datos is None:
            # Un reintento con instrucción explícita de corrección.
            correccion = mensajes + [{"role": "assistant", "content": texto},
                                     {"role": "user", "content": "Responde únicamente con el "
                                      "objeto JSON pedido, sin texto adicional." + SIN_RAZONAMIENTO}]
            if self.backend == "llamacpp":
                texto, tp2, ts2 = self._generar_llamacpp(correccion, esquema, max_tokens)
            else:
                texto, tp2, ts2 = self._generar_transformers(correccion, max_tokens)
            tp, ts = (tp or 0) + (tp2 or 0), (ts or 0) + (ts2 or 0)
            datos = extraer_json(texto)
        seg = time.perf_counter() - t0

        directorio.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({"texto": texto, "datos": datos, "tokens_prompt": tp,
                                    "tokens_salida": ts, "modelo": self.id_modelo},
                                   ensure_ascii=False), encoding="utf-8")
        return Generacion(texto, datos, seg, tp, ts)

    def _generar_llamacpp(self, mensajes, esquema, max_tokens):
        kwargs = dict(messages=mensajes, temperature=0.0, top_p=1.0, top_k=1, min_p=0.0,
                      repeat_penalty=1.0, seed=self.cfg.decoder_seed, max_tokens=max_tokens)
        if esquema is not None:
            kwargs["response_format"] = {"type": "json_object", "schema": esquema}
        r = self.modelo.create_chat_completion(**kwargs)
        uso = r.get("usage") or {}
        return (r["choices"][0]["message"]["content"] or "", uso.get("prompt_tokens"),
                uso.get("completion_tokens"))

    def _generar_transformers(self, mensajes, max_tokens):
        import torch

        entrada = self.tokenizer.apply_chat_template(
            mensajes, add_generation_prompt=True, enable_thinking=False,
            return_tensors="pt").to(self.modelo.device)
        with torch.no_grad():
            salida = self.modelo.generate(entrada, max_new_tokens=max_tokens, do_sample=False,
                                          pad_token_id=self.tokenizer.eos_token_id)
        nuevos = salida[0][entrada.shape[-1]:]
        return (self.tokenizer.decode(nuevos, skip_special_tokens=True), int(entrada.shape[-1]),
                int(nuevos.shape[-1]))
