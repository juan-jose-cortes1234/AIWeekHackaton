"""Perfiles explícitos: evitan que perillas viejas de Colab contaminen la prueba."""
from dataclasses import replace

BASE = dict(puestos_pregunta=4, pasajes_por_opcion=2,
            mc_rerank_candidatos_pregunta=20, rerank_candidatos_opcion=8,
            mc_reparto_equilibrado=False, mc_contexto_cobertura=False,
            mc_marcas_evidencia=True, mc_prompt_preciso=False,
            mc_citas_visibles=False, mc_rerank_consenso=False,
            mc_incluir_area=False, mc_gemma_pensamiento_tokens=0, mc_revision_evidencia=False,
            mc_verificacion_independiente=False,
            mc_modo="directo", mc_analisis_previo=False,
            mc_razonamiento_tokens=0, mc_consulta_opcion="clave", mc_palabras_clave=10)
PERFILES = {
    "v12": {},
    "consenso": {"mc_rerank_consenso": True},
    "pensamiento": {"mc_gemma_pensamiento_tokens": 512},
    "area": {"mc_incluir_area": True},
    "revision": {"mc_revision_evidencia": True},
    "verificacion": {"mc_verificacion_independiente": True},
    "pregunta40": {"mc_rerank_candidatos_pregunta": 40},
    "opciones20": {"rerank_candidatos_opcion": 20},
    "prompt_preciso": {"mc_prompt_preciso": True},
    "marcas_off": {"mc_marcas_evidencia": False},
    "contexto_cobertura": {"mc_contexto_cobertura": True},
    "citas_visibles": {"mc_citas_visibles": True},
    "c21": dict(puestos_pregunta=2, mc_rerank_candidatos_pregunta=40,
                rerank_candidatos_opcion=20, mc_reparto_equilibrado=True,
                mc_contexto_cobertura=True, mc_marcas_evidencia=False,
                mc_prompt_preciso=True, mc_citas_visibles=True),
}


def configurar(cfg, nombre):
    return replace(cfg, **(BASE | PERFILES[nombre]))
