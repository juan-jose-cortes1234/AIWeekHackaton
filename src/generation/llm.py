"""Decoder abierto en proceso, con pesos de Hugging Face (ARQUITECTURA §5).

Backends (sin APIs ni servidores):
- `llamacpp`: llama-cpp-python + GGUF (por defecto `ggml-org/gemma-4-E4B-it-GGUF`, Q8_0;
  antes `Qwen/Qwen3-8B-GGUF`). CPU o GPU. El formato de chat sale del propio GGUF.
  La salida JSON se fuerza con una gramática derivada del JSON schema.
- `transformers`: el modelo original con transformers (GPU; probado solo con Qwen3). Decodificación voraz
  y parser tolerante con un reintento.

Siempre: temperatura 0 (decodificación voraz), semilla fija y lista blanca de modelos
abiertos verificada antes de cargar. Qwen3 va sin modo de razonamiento, salvo cuando se pide
con `razonamiento_tokens` (selección múltiple, C-09): primero razona libremente dentro de
`<think>…</think>` con un tope de tokens y luego escribe el JSON con la gramática.
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
    truncada: bool = False
    razonamiento: str | None = None
    razonamiento_truncado: bool = False


def prefijo_pensamiento_gemma(prompt: str) -> str:
    """Abre el canal nativo sobre la plantilla del propio GGUF, nunca sobre ChatML."""
    if "<|turn>system\n<|think|>" not in prompt:
        raise ValueError("La plantilla de Gemma no activó enable_thinking=True.")
    if not prompt.endswith("<|turn>model\n"):
        raise ValueError("La plantilla de Gemma no abrió el turno del modelo esperado.")
    return prompt + "<|channel>thought\n"


# --------------------------------------------------------------------------- JSON

def reparar_json_truncado(texto: str) -> dict | None:
    """Rescata los campos completos de un objeto JSON cortado por el límite de tokens.

    Recorre el texto llevando la cuenta de cadenas y corchetes; descarta el último
    par clave-valor si quedó a medias y cierra lo que siga abierto. Devuelve None si
    no hay al menos un campo completo.
    """
    t = re.sub(r"<think>.*?</think>", "", texto or "", flags=re.DOTALL)
    inicio = t.find("{")
    if inicio == -1:
        return None
    t = t[inicio:]
    pila: list[str] = []
    en_cadena = escape = False
    ultimo_corte = None          # posición tras el último valor completo de nivel 1
    for i, c in enumerate(t):
        if en_cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                en_cadena = False
                if len(pila) == 1:
                    ultimo_corte = i + 1 if _cierra_valor(t, i) else ultimo_corte
            continue
        if c == '"':
            en_cadena = True
        elif c in "{[":
            pila.append("}" if c == "{" else "]")
        elif c in "}]":
            if pila:
                pila.pop()
            if len(pila) == 1:
                ultimo_corte = i + 1
            if not pila:
                return extraer_json(t[:i + 1])
    if ultimo_corte is None:
        return None
    candidato = t[:ultimo_corte].rstrip().rstrip(",") + "}"
    try:
        obj = json.loads(candidato)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) and obj else None


def _cierra_valor(t: str, i: int) -> bool:
    """¿La comilla en `i` cierra un valor (y no una clave)? Una clave va seguida de ':'."""
    resto = t[i + 1:].lstrip()
    return not resto.startswith(":")

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
        # "/no_think" y el modo de razonamiento con <think> son propios de Qwen3: con otro
        # decoder de la lista blanca no se usan (se le pide el JSON sin más).
        self.es_qwen3 = "qwen3" in self.id_modelo.lower()
        self.sufijo = SIN_RAZONAMIENTO if self.es_qwen3 else ""

    # ---- carga
    def _cargar_llamacpp(self) -> None:
        from huggingface_hub import hf_hub_download
        from llama_cpp import Llama

        ruta = hf_hub_download(self.cfg.decoder_gguf_repo, self.cfg.decoder_gguf_file,
                               token=self.cfg.hf_token or None)
        try:
            self.modelo = Llama(
                model_path=ruta, n_ctx=self.cfg.decoder_num_ctx, seed=self.cfg.decoder_seed,
                n_threads=self.cfg.decoder_threads or None,
                n_gpu_layers=-1 if self.cfg.decoder_device == "cuda" else 0,
                verbose=False)
        except ValueError as exc:
            pista = (" En GPU, la causa habitual es falta de VRAM: revise con nvidia-smi qué "
                     "proceso ocupa la memoria (JAX/TensorFlow reservan el 75 % al importarse) "
                     "o baje DECODER_NUM_CTX.") if self.cfg.decoder_device == "cuda" else ""
            raise RuntimeError(f"No se pudo cargar {self.id_modelo}.{pista}") from exc
        if self.modelo.metadata.get("general.architecture") == "gemma4":
            self._formato_gemma4()

    def _formato_gemma4(self) -> None:
        """Plantilla de chat propia de Gemma 4 con el razonamiento apagado (C-18, aporte de Pablo).

        Gemma 4 usa sus propios turnos y canales, no ChatML; el formateador genérico de
        llama-cpp-python no le aplica `enable_thinking=False`, y con el canal de razonamiento
        abierto la gramática JSON choca con lo que el modelo quiere escribir. Se arma el
        formateador con la plantilla Jinja del propio GGUF, sus tokens de inicio/fin y el fin de
        turno `<turn|>` como parada.
        """
        from functools import partial

        from llama_cpp.llama_chat_format import (
            Jinja2ChatFormatter, chat_formatter_to_chat_completion_handler,
        )

        plantilla = self.modelo.metadata.get("tokenizer.chat_template")
        if not plantilla:
            raise RuntimeError("El GGUF de Gemma 4 no trae su plantilla de chat.")
        bos = self.modelo.detokenize([self.modelo.token_bos()], special=True).decode("utf-8")
        eos = self.modelo.detokenize([self.modelo.token_eos()], special=True).decode("utf-8")
        fin_turno = self.modelo.tokenize(b"<turn|>", add_bos=False, special=True)
        if len(fin_turno) != 1:
            raise RuntimeError("El tokenizer del GGUF no reconoce el fin de turno de Gemma 4.")
        formateador = Jinja2ChatFormatter(template=plantilla, bos_token=bos, eos_token=eos,
                                          stop_token_ids=[self.modelo.token_eos(), fin_turno[0]])
        self._gemma_formateador = partial(formateador, enable_thinking=False)
        self._gemma_formateador_pensando = partial(formateador, enable_thinking=True)
        self.modelo.chat_handler = chat_formatter_to_chat_completion_handler(self._gemma_formateador)
        self.formato_chat = "gemma4-sin-razonamiento"

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

    # ---- tamaño
    @property
    def n_ctx(self) -> int:
        return self.cfg.decoder_num_ctx

    def contar_tokens(self, mensajes: list[dict], gemma_pensamiento_tokens: int = 0) -> int:
        """Tokens del prompt con la plantilla de chat (margen de 16 por mensaje en llamacpp)."""
        if self.backend == "llamacpp":
            if gemma_pensamiento_tokens:
                prompt = prefijo_pensamiento_gemma(
                    self._gemma_formateador_pensando(messages=mensajes).prompt)
                return len(self.modelo.tokenize(prompt.encode("utf-8"), add_bos=False, special=True))
            if getattr(self, "_gemma_formateador", None) is not None:   # conteo exacto (C-18)
                prompt = self._gemma_formateador(messages=mensajes).prompt
                return len(self.modelo.tokenize(prompt.encode("utf-8"), add_bos=False, special=True))
            texto = "\n".join(m["content"] for m in mensajes) + self.sufijo
            return len(self.modelo.tokenize(texto.encode("utf-8"), add_bos=False)) + 16 * len(mensajes)
        ids = self.tokenizer.apply_chat_template(mensajes, add_generation_prompt=True,
                                                 enable_thinking=False, tokenize=True)
        return len(ids)

    # ---- caché
    def _clave(self, mensajes: list[dict], esquema: dict | None, max_tokens: int,
              razonamiento_tokens: int = 0, gemma_pensamiento_tokens: int = 0) -> str:
        cuerpo = json.dumps({"backend": self.backend, "modelo": self.id_modelo,
                             "mensajes": mensajes, "esquema": esquema, "max_tokens": max_tokens,
                             "formato_chat": getattr(self, "formato_chat", None),
                             **({"razonamiento_tokens": razonamiento_tokens}
                                if razonamiento_tokens else {}),
                             **({"gemma_pensamiento_tokens": gemma_pensamiento_tokens,
                                 "canal_gemma": "thought-json-v1"}
                                if gemma_pensamiento_tokens else {}),
                             "temperatura": 0, "semilla": self.cfg.decoder_seed,
                             "ctx": self.cfg.decoder_num_ctx},
                            ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()

    # ---- generación
    def generar(self, mensajes: list[dict], esquema: dict | None = None, max_tokens: int = 700,
                usar_cache: bool = True, dir_cache: Path | None = None,
                razonamiento_tokens: int = 0, gemma_pensamiento_tokens: int = 0) -> Generacion:
        """Genera con temperatura 0. Si `esquema` se da, la salida es un objeto JSON.

        `razonamiento_tokens` > 0 activa el modo de razonamiento de Qwen3 con ese tope (C-09).
        """
        mensajes = [dict(m) for m in mensajes]
        if gemma_pensamiento_tokens and (
                self.backend != "llamacpp" or not hasattr(self, "_gemma_formateador_pensando")):
            raise ValueError("El pensamiento nativo requiere un GGUF de arquitectura gemma4.")
        if not self.es_qwen3:
            razonamiento_tokens = 0
        if (self.sufijo and not razonamiento_tokens and mensajes and mensajes[-1]["role"] == "user"
                and self.sufijo not in mensajes[-1]["content"]):
            mensajes[-1]["content"] += self.sufijo
        directorio = dir_cache or DIR_CACHE
        ruta = directorio / f"{self._clave(mensajes, esquema, max_tokens, razonamiento_tokens, gemma_pensamiento_tokens)}.json"
        if usar_cache and ruta.is_file():
            d = json.loads(ruta.read_text(encoding="utf-8"))
            return Generacion(d["texto"], d["datos"], 0.0, d.get("tokens_prompt"),
                              d.get("tokens_salida"), desde_cache=True,
                              truncada=d.get("truncada", False),
                              razonamiento=d.get("razonamiento"),
                              razonamiento_truncado=d.get("razonamiento_truncado", False))

        t0 = time.perf_counter()
        razonamiento = None
        pensamiento_cortado = False
        if gemma_pensamiento_tokens:
            razonamiento, texto, tp, ts, cortada, pensamiento_cortado = self._generar_gemma_razonando(
                mensajes, esquema, max_tokens, gemma_pensamiento_tokens)
        elif razonamiento_tokens:
            razonamiento, texto, tp, ts, cortada = self._generar_razonando(
                mensajes, esquema, max_tokens, razonamiento_tokens)
        else:
            texto, tp, ts, cortada = self._generar(mensajes, esquema, max_tokens)
        datos = extraer_json(texto) if esquema is not None else None
        if esquema is not None and datos is None:
            if cortada:
                # Cortada por el límite de tokens: con temperatura 0 un reintento repetiría
                # exactamente lo mismo. Se rescatan los campos que alcanzaron a completarse.
                datos = reparar_json_truncado(texto)
            else:
                # JSON mal formado sin corte: un reintento con instrucción de corrección.
                correccion = mensajes + [{"role": "assistant", "content": texto},
                                         {"role": "user", "content": "Responde únicamente con el "
                                          "objeto JSON pedido, sin texto adicional." + self.sufijo}]
                texto, tp2, ts2, cortada = self._generar(correccion, esquema, max_tokens)
                tp, ts = (tp or 0) + (tp2 or 0), (ts or 0) + (ts2 or 0)
                datos = extraer_json(texto) or (reparar_json_truncado(texto) if cortada else None)
        seg = time.perf_counter() - t0

        directorio.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({"texto": texto, "datos": datos, "tokens_prompt": tp,
                                    "tokens_salida": ts, "truncada": cortada,
                                    "razonamiento": razonamiento, "modelo": self.id_modelo,
                                    "razonamiento_truncado": pensamiento_cortado},
                                   ensure_ascii=False), encoding="utf-8")
        return Generacion(texto, datos, seg, tp, ts, truncada=cortada, razonamiento=razonamiento,
                          razonamiento_truncado=pensamiento_cortado)

    def _generar_gemma_razonando(self, mensajes, esquema, max_tokens, presupuesto):
        """Pensamiento libre acotado; después, JSON forzado en el canal de respuesta.

        Tokens y plantilla nativos del GGUF. Se conserva el texto EXACTO del primer
        tramo al continuar; la gramática solo rige tras cerrar <channel|>.
        El tope reserva siempre espacio para el JSON y se registra si corta el pensamiento.
        """
        from llama_cpp import LlamaGrammar

        prefijo = prefijo_pensamiento_gemma(
            self._gemma_formateador_pensando(messages=mensajes).prompt)
        tokenizar = lambda t: self.modelo.tokenize(t.encode("utf-8"), add_bos=False, special=True)
        entrada = tokenizar(prefijo)
        if len(entrada) + presupuesto + max_tokens + 16 > self.n_ctx:
            raise ValueError("El prompt no deja espacio para pensamiento y respuesta de Gemma.")
        comunes = dict(temperature=0.0, top_p=1.0, top_k=1, min_p=0.0,
                       repeat_penalty=1.0, seed=self.cfg.decoder_seed)
        cierres = [tokenizar(t) for t in ("<channel|>", "<turn|>")]
        if any(len(ids) != 1 for ids in cierres):
            raise ValueError("Gemma no reconoce los tokens nativos de cierre de canal y turno.")
        fin = {ids[0] for ids in cierres} | {self.modelo.token_eos()}
        generados, cerrado = [], False
        self.modelo.set_seed(self.cfg.decoder_seed)
        # Parar por IDs: create_completion puede ocultar los tokens especiales al
        # decodificar texto, por lo que un stop de cadena no basta para <channel|>.
        for token in self.modelo.generate(entrada, temp=0.0, top_p=1.0, top_k=1,
                                           min_p=0.0, repeat_penalty=1.0, reset=True):
            if token in fin:
                cerrado = True
                break
            generados.append(int(token))
            if len(generados) >= presupuesto:
                break
        pensamiento = self.modelo.detokenize(generados, prev_tokens=entrada,
                                             special=True).decode("utf-8", errors="replace")
        gramatica = (LlamaGrammar.from_json_schema(json.dumps(esquema), verbose=False)
                     if esquema is not None else None)
        final = entrada + generados + cierres[0]
        if len(final) + max_tokens > self.n_ctx:
            raise ValueError("La continuación de Gemma excede la ventana reservada.")
        r2 = self.modelo.create_completion(prompt=final, max_tokens=max_tokens,
                                           stop=["<turn|>"], grammar=gramatica, **comunes)
        u2 = r2.get("usage") or {}
        return (pensamiento, r2["choices"][0]["text"] or "",
                len(entrada) + (u2.get("prompt_tokens") or 0),
                len(generados) + (u2.get("completion_tokens") or 0),
                r2["choices"][0].get("finish_reason") == "length",
                not cerrado)

    def _generar_razonando(self, mensajes, esquema, max_tokens, razonamiento_tokens):
        """Modo de razonamiento (C-09): (razonamiento, texto, tokens_prompt, tokens_salida, cortada).

        llamacpp: la gramática JSON regiría desde el primer token e impediría el `<think>`, así
        que son dos tramos sobre el mismo prompt en formato ChatML (el de Qwen3): (1) sin
        gramática, desde `<think>` hasta `</think>` o el tope; (2) el mismo prefijo con el
        razonamiento cerrado y la gramática del esquema. llama.cpp reutiliza el prefijo ya
        evaluado, así que el tramo 2 no relee la evidencia. Si el tope corta el razonamiento,
        se cierra ahí. transformers: plantilla con `enable_thinking=True` y parser tolerante.
        """
        if self.backend != "llamacpp":
            texto, tp, ts, cortada = self._generar_transformers(
                mensajes, max_tokens + razonamiento_tokens, pensar=True)
            m = re.search(r"<think>(.*?)(?:</think>|$)", texto, flags=re.DOTALL)
            return (m.group(1).strip() if m else None), texto, tp, ts, cortada

        from llama_cpp import LlamaGrammar

        chatml = "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in mensajes)
        prefijo = f"{chatml}<|im_start|>assistant\n<think>\n"
        comunes = dict(temperature=0.0, top_p=1.0, top_k=1, min_p=0.0, repeat_penalty=1.0,
                       seed=self.cfg.decoder_seed)
        r1 = self.modelo.create_completion(prompt=prefijo, max_tokens=razonamiento_tokens,
                                           stop=["</think>"], **comunes)
        razonamiento = (r1["choices"][0]["text"] or "").strip()
        gramatica = (LlamaGrammar.from_json_schema(json.dumps(esquema), verbose=False)
                     if esquema is not None else None)
        r2 = self.modelo.create_completion(
            prompt=f"{prefijo}{razonamiento}\n</think>\n\n", max_tokens=max_tokens,
            stop=["<|im_end|>"], grammar=gramatica, **comunes)
        u1, u2 = r1.get("usage") or {}, r2.get("usage") or {}
        return (razonamiento, r2["choices"][0]["text"] or "", u1.get("prompt_tokens"),
                (u1.get("completion_tokens") or 0) + (u2.get("completion_tokens") or 0),
                r2["choices"][0].get("finish_reason") == "length")

    def _generar(self, mensajes, esquema, max_tokens):
        """(texto, tokens_prompt, tokens_salida, cortada_por_longitud)."""
        if self.backend == "llamacpp":
            return self._generar_llamacpp(mensajes, esquema, max_tokens)
        return self._generar_transformers(mensajes, max_tokens)

    def _generar_llamacpp(self, mensajes, esquema, max_tokens):
        kwargs = dict(messages=mensajes, temperature=0.0, top_p=1.0, top_k=1, min_p=0.0,
                      repeat_penalty=1.0, seed=self.cfg.decoder_seed, max_tokens=max_tokens)
        if esquema is not None:
            kwargs["response_format"] = {"type": "json_object", "schema": esquema}
        r = self.modelo.create_chat_completion(**kwargs)
        uso = r.get("usage") or {}
        eleccion = r["choices"][0]
        return (eleccion["message"]["content"] or "", uso.get("prompt_tokens"),
                uso.get("completion_tokens"), eleccion.get("finish_reason") == "length")

    def _generar_transformers(self, mensajes, max_tokens, pensar: bool = False):
        import torch

        entrada = self.tokenizer.apply_chat_template(
            mensajes, add_generation_prompt=True, enable_thinking=pensar,
            return_tensors="pt").to(self.modelo.device)
        with torch.no_grad():
            salida = self.modelo.generate(entrada, max_new_tokens=max_tokens, do_sample=False,
                                          pad_token_id=self.tokenizer.eos_token_id)
        nuevos = salida[0][entrada.shape[-1]:]
        return (self.tokenizer.decode(nuevos, skip_special_tokens=True), int(entrada.shape[-1]),
                int(nuevos.shape[-1]), int(nuevos.shape[-1]) >= max_tokens)
