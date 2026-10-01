"""Recuperador híbrido determinista (ARQUITECTURA §4).

Por pregunta:
1. **Router de citas explícitas**: si la pregunta nombra un artículo concreto
   (“artículo 1820 del Código Civil”), ese artículo entra primero, por metadatos.
2. **Denso + BM25** para cada consulta (la pregunta y, opcionalmente, consultas
   extra como las opciones de una MC), fusionados con RRF ponderado.
3. **Boosts** pequeños: fragmentos del área de la pregunta y de las normas que
   la pregunta menciona sin artículo.
4. **Diversidad**: como máximo `max_por_articulo` fragmentos del mismo artículo
   (o de la misma sección de una sentencia).
5. Desempates por id del fragmento ⇒ misma entrada, mismos pasajes, siempre.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from src.config import Config, config
from src.index.lexico import IndiceBM25
from src.oficial import citations


@dataclass
class Pasaje:
    id: int
    chunk_id: str
    doc_id: str
    inicio: int
    fin: int
    texto: str
    score: float
    score_denso: float | None = None
    score_bm25: float | None = None
    score_rerank: float | None = None
    origen: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def a_entrega(self) -> dict:
        """Forma exigida por schema/submission.schema.json."""
        return {"doc_id": self.doc_id, "inicio": self.inicio, "fin": self.fin,
                "texto": self.texto, "score": round(float(self.score), 4)}


def _cuerpos(texto: str) -> set[tuple]:
    return citations.bodies(citations.extract(texto))



def leer_complementarios(ruta: Path | None) -> frozenset[str]:
    """doc_id de los documentos complementarios (C-10): uno por línea, `#` para comentarios.

    Sin archivo, ninguno (todos los documentos son principales).
    """
    if not ruta or not Path(ruta).is_file():
        return frozenset()
    lineas = Path(ruta).read_text(encoding="utf-8").splitlines()
    return frozenset(l.strip() for l in lineas if l.strip() and not l.lstrip().startswith("#"))

class Recuperador:
    def __init__(self, chunks: list[dict], indice_denso, bm25: IndiceBM25, encoder,
                 cfg: Config = config, reranker=None):
        self.chunks = chunks
        self.reranker = reranker
        self.denso = indice_denso
        self.bm25 = bm25
        self.encoder = encoder
        self.cfg = cfg
        # Cuerpo normativo del documento de cada fragmento (por su nombre canónico).
        cache_doc: dict[str, frozenset] = {}
        self.complementarios = leer_complementarios(cfg.documentos_complementarios)
        self.cuerpo_doc: list[frozenset] = []
        self.por_articulo: dict[tuple, list[int]] = defaultdict(list)
        self.por_cuerpo: dict[tuple, set[int]] = defaultdict(set)
        for i, c in enumerate(chunks):
            if c["doc_id"] not in cache_doc:
                cache_doc[c["doc_id"]] = frozenset(_cuerpos(c.get("nombre_canonico") or ""))
            cuerpos = cache_doc[c["doc_id"]]
            self.cuerpo_doc.append(cuerpos)
            for b in cuerpos:
                self.por_cuerpo[b].add(i)
                if c.get("articulo") and c.get("tipo_fragmento") == "articulo":
                    self.por_articulo[(b, str(c["articulo"]).lower())].append(i)

    # ------------------------------------------------------------------ carga
    @classmethod
    def cargar(cls, dir_indice: Path | None = None, encoder=None,
               cfg: Config = config, reranker=None) -> "Recuperador":
        import faiss

        d = dir_indice or cfg.index_dir
        with (d / "chunks.jsonl").open(encoding="utf-8") as fh:
            chunks = [json.loads(l) for l in fh if l.strip()]
        man = json.loads((d / "index_manifest.json").read_text(encoding="utf-8"))
        if encoder is None:
            from src.index.encoder import EncoderST

            encoder = EncoderST(man["modelo"])
        elif man["modelo"] != getattr(encoder, "nombre", man["modelo"]):
            raise ValueError(f"El índice se construyó con {man['modelo']} y se pasó "
                             f"{encoder.nombre}.")
        if reranker is None and cfg.use_reranker:
            from src.retrieval.reranker import Reranker

            reranker = Reranker(cfg.reranker_model)
        return cls(chunks, faiss.read_index(str(d / "index.faiss")),
                   IndiceBM25.cargar(d / "bm25"), encoder, cfg, reranker)

    # ------------------------------------------------------------------ piezas
    def router(self, pregunta: str) -> tuple[list[int], set[tuple]]:
        """Fragmentos de artículos citados explícitamente y cuerpos mencionados."""
        citas = citations.extract(pregunta)
        directos: list[int] = []
        for cuerpo_art in sorted(citas, key=lambda c: tuple(str(x) for x in c)):
            b, art = cuerpo_art[:3], cuerpo_art[3]
            if art is None:
                continue
            for i in self.por_articulo.get((b, str(art).lower()), []):
                if i not in directos:
                    directos.append(i)
        return directos, citations.bodies(citas)

    def _ranking_denso(self, consulta: str, k: int) -> list[tuple[int, float]]:
        if self.denso.ntotal == 0:
            return []
        q = self.encoder.codificar([consulta], es_consulta=True)
        sims, ids = self.denso.search(np.asarray(q, dtype=np.float32), min(k, self.denso.ntotal))
        pares = [(int(i), float(s)) for i, s in zip(ids[0], sims[0]) if i >= 0]
        # Redondeo + desempate por id: evita que diferencias de 1e-7 cambien el orden.
        return sorted(pares, key=lambda p: (-round(p[1], 5), p[0]))

    # ------------------------------------------------------------------ búsqueda
    def buscar(self, pregunta: str, area: str | None = None,
               consultas_extra: list[str] | None = None, k: int | None = None,
               n_rerank: int | None = None) -> list[Pasaje]:
        cfg = self.cfg
        k = k or cfg.top_k_pasajes
        consultas = [pregunta] + [c for c in (consultas_extra or []) if c.strip()]

        rrf: dict[int, float] = defaultdict(float)
        s_denso: dict[int, float] = {}
        s_bm25: dict[int, float] = {}
        origen: dict[int, set[str]] = defaultdict(set)
        for q in consultas:
            for r, (i, s) in enumerate(self._ranking_denso(q, cfg.candidatos)):
                rrf[i] += cfg.peso_denso / (cfg.rrf_k + r + 1)
                s_denso[i] = max(s_denso.get(i, -1.0), s)
                origen[i].add("denso")
            for r, (i, s) in enumerate(self.bm25.buscar(q, cfg.candidatos)):
                rrf[i] += cfg.peso_bm25 / (cfg.rrf_k + r + 1)
                s_bm25[i] = max(s_bm25.get(i, 0.0), s)
                origen[i].add("bm25")

        directos, mencionados = self.router(pregunta)
        for i in rrf:
            if area and area in (self.chunks[i].get("areas") or []):
                rrf[i] += cfg.boost_area
            if mencionados & self.cuerpo_doc[i]:
                rrf[i] += cfg.boost_cuerpo

        orden = [i for i in sorted(rrf, key=lambda i: (-round(rrf[i], 8), i))
                 if i not in set(directos)]
        s_rerank: dict[int, float] = {}
        if self.reranker is not None and cfg.use_reranker:
            # Reordena con el cross-encoder los mejores candidatos de la fusión.
            n = n_rerank or cfg.rerank_candidatos
            cabeza, cola = orden[:n], orden[n:]
            ids = directos + cabeza
            puntos = self.reranker.puntuar(pregunta, [self.chunks[i]["texto"] for i in ids])
            s_rerank = {i: round(float(p), 5) for i, p in zip(ids, puntos)}
            cabeza = sorted(cabeza, key=lambda i: (-s_rerank[i], i))
            candidatos = [(i, 1.0 + s_rerank[i], "router") for i in directos] + \
                         [(i, s_rerank[i], "rerank") for i in cabeza] + \
                         [(i, rrf[i] * 1e-3, None) for i in cola]
        else:
            maximo = max(rrf.values(), default=0.0)
            candidatos = [(i, maximo + 1.0, "router") for i in directos] + \
                         [(i, rrf[i], None) for i in orden]

        res: list[Pasaje] = []
        por_unidad: dict[tuple, int] = defaultdict(int)
        por_documento: dict[str, int] = defaultdict(int)
        n_complementarios = 0
        for i, puntaje, etiqueta in candidatos:
            c = self.chunks[i]
            unidad = (c["doc_id"], c.get("articulo") or c.get("seccion") or c["chunk_id"])
            if por_unidad[unidad] >= cfg.max_por_articulo:
                continue
            # Tope por documento, salvo si la pregunta lo menciona (p. ej. "según la
            # Sentencia SU-455 de 2020…"): ahí conviene ver varias partes del mismo documento.
            mencionado = etiqueta == "router" or bool(mencionados & self.cuerpo_doc[i])
            if (cfg.max_por_documento and not mencionado
                    and por_documento[c["doc_id"]] >= cfg.max_por_documento):
                continue
            # Documentos complementarios (C-10): pocos pasajes entre los 10, salvo si se mencionan.
            complementario = c["doc_id"] in self.complementarios and not mencionado
            if complementario and cfg.max_complementarios and n_complementarios >= cfg.max_complementarios:
                continue
            n_complementarios += complementario
            por_unidad[unidad] += 1
            por_documento[c["doc_id"]] += 1
            orig = sorted(origen.get(i, set()) | ({etiqueta} if etiqueta else set()))
            res.append(Pasaje(
                id=i, chunk_id=c["chunk_id"], doc_id=c["doc_id"], inicio=c["inicio"],
                fin=c["fin"], texto=c["texto"], score=puntaje, score_denso=s_denso.get(i),
                score_bm25=s_bm25.get(i), score_rerank=s_rerank.get(i), origen=orig,
                meta={k2: c.get(k2) for k2 in ("articulo", "seccion", "tipo_fragmento",
                                               "nombre_canonico", "areas", "url")}))
            if len(res) >= k:
                break
        return res
