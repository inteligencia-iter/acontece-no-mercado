"""
Cálculo do destaque_score para cada item harmonizado.

destaque_score ∈ [0.0, 1.0]
Determina o layout no front-end:
  ≥ 0.70  → manchete (card grande, topo da aba)
  0.40–0.69 → grade padrão
  < 0.40  → rodapé / condensado

Fatores ponderados (soma dos pesos = 1.0):
  A. Confiança de classificação      (0.25) — sinal de qualidade do dado
  B. Categoria de alto impacto       (0.20) — Aviação, Câmbio e Economia
  C. Fonte especializada             (0.20) — Panrotas e M&E > demais
  D. Presença em múltiplas fontes    (0.20) — cross-source dedup (fase 2: placeholder)
  E. Recência                        (0.15) — decai com a idade em horas
"""

import re
import math
from datetime import datetime, timezone
from typing import Optional

from .config import HIGH_IMPACT_CATEGORIES

# Fontes por nível de autoridade editorial
_SPECIALIZED_SOURCES = {"panrotas", "mercadoeeventos"}
_INSTITUTIONAL_SOURCES = {"embratur", "agenciabrasil", "mtur_govbr"}
# g1_turismo e diariodoturismo ficam no nível base


def _source_weight(source_id: str) -> float:
    """Peso de autoridade da fonte (0.0 – 1.0)."""
    if source_id in _SPECIALIZED_SOURCES:
        return 1.0
    if source_id in _INSTITUTIONAL_SOURCES:
        return 0.6
    return 0.4   # generalista / trade não-verificado


def _recency_score(pub_date_iso: Optional[str]) -> float:
    """
    Score de recência baseado em decaimento exponencial.
    Meia-vida: 24 horas.
    Sem data → 0.5 (neutro).
    """
    if not pub_date_iso:
        return 0.5
    try:
        pub = datetime.fromisoformat(pub_date_iso)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        hours_old = (now - pub).total_seconds() / 3600
        hours_old = max(0.0, hours_old)
        # decaimento: score = e^(-lambda * t), lambda = ln(2)/24
        lam = math.log(2) / 24.0
        return math.exp(-lam * hours_old)
    except Exception:
        return 0.5


def compute_destaque_score(item: dict) -> float:
    """
    Calcula o destaque_score de um item harmonizado.
    Retorna valor em [0.0, 1.0], arredondado em 3 casas.
    """
    # A. Confiança da classificação
    conf = item.get("category_mapping_confidence") or 0.0
    score_a = min(float(conf), 1.0)

    # B. Categoria de alto impacto
    l1 = item.get("canonical_category_l1") or ""
    score_b = 1.0 if l1 in HIGH_IMPACT_CATEGORIES else 0.0

    # C. Autoridade da fonte
    source_id = item.get("source_id") or ""
    score_c = _source_weight(source_id)

    # D. Cross-source (fase 2 — placeholder neutro)
    score_d = 0.5

    # E. Recência
    score_e = _recency_score(item.get("pub_date"))

    destaque = (
        0.25 * score_a +
        0.20 * score_b +
        0.20 * score_c +
        0.20 * score_d +
        0.15 * score_e
    )
    return round(min(max(destaque, 0.0), 1.0), 3)


def annotate_layout_tier(item: dict) -> dict:
    """
    Adiciona 'layout_tier' ao item com base no destaque_score.
    Modifica in-place e retorna.
    """
    score = item.get("destaque_score") or 0.0
    if score >= 0.70:
        tier = "manchete"
    elif score >= 0.40:
        tier = "grade"
    else:
        tier = "condensado"
    item["layout_tier"] = tier
    return item


def score_item(item: dict) -> dict:
    """
    Preenche destaque_score e layout_tier.
    Modifica item in-place e retorna.
    """
    item["destaque_score"] = compute_destaque_score(item)
    annotate_layout_tier(item)
    return item
