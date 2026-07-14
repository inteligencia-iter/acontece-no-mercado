"""
Engine de harmonização do Monitor de Notícias de Turismo.

Sequência por item (conforme pseudocódigo do projeto):
  1. Filtro in_scope  — é sobre turismo?
  2. Harmonização de categoria  — lookup_nativo OU classificador
  3. Filtro content_domain  — turismo_direto / geopolitica_relevante / excluir

Carrega o modelo (TF-IDF + SVC) uma única vez na importação do módulo.
"""

import re
import pickle
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .config import SourceConfig, SOURCES, PANROTAS_CROSSWALK, ME_CROSSWALK

logger = logging.getLogger(__name__)

# ── Caminhos dos artefatos do classificador ───────────────────────────────────
_BASE = Path(__file__).parent.parent   # diretório outputs/
_VEC_PATH   = _BASE / "tfidf_vectorizer.pkl"
_MODEL_PATH = _BASE / "svc_model.pkl"

_vectorizer = None
_classifier = None


def _load_models() -> None:
    global _vectorizer, _classifier
    if _vectorizer is None:
        with open(_VEC_PATH, "rb") as f:
            _vectorizer = pickle.load(f)
        logger.info("Vectorizer carregado: %s", _VEC_PATH)
    if _classifier is None:
        with open(_MODEL_PATH, "rb") as f:
            _classifier = pickle.load(f)
        logger.info("Classificador carregado: %s", _MODEL_PATH)


# ── 1. Filtro in_scope ────────────────────────────────────────────────────────
#
# Palavras-chave que sinalizam relevância turística.
# Fontes especializadas (Panrotas, M&E, Embratur) são in_scope por default.
# Fontes generalistas (G1, Agência Brasil) passam pelo filtro de keywords.

_TOURISM_KEYWORDS = re.compile(
    r"\b(turi[sz]mo|viagen?s?|hotel|hotelar|aero|aeroporto|voo|companhia aérea|"
    r"avião|aviação|destino|cruzeiro|agência de viagens|operadora|hospedag|"
    r"resort|pousada|hostel|temporada|férias|excursão|roteiro|passagem|"
    r"câmbio|dólar|euro|visto|fronteira|imigração|turista|visitante|"
    r"embratur|ministério do turismo|mtur|anac|iata)\b",
    re.IGNORECASE | re.UNICODE,
)

_SPECIALIZED_SOURCES = {"panrotas", "mercadoeeventos", "embratur"}


def check_in_scope(item: dict, cfg: SourceConfig) -> bool:
    """Retorna True se o item é relevante para o dataset de turismo."""
    if cfg.source_id in _SPECIALIZED_SOURCES:
        return True   # fontes especializadas: 100% in_scope por definição
    text = (item.get("title") or "") + " " + (item.get("description") or "")
    if cfg.keyword_filter:
        # Fonte com filtro explícito: ao menos uma keyword deve aparecer no texto
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(k) for k in cfg.keyword_filter) + r")\b",
            re.IGNORECASE | re.UNICODE,
        )
        return bool(pattern.search(text))
    return bool(_TOURISM_KEYWORDS.search(text))


# ── 2. Harmonização de categoria ──────────────────────────────────────────────

def _lookup_panrotas(cat_raw: Optional[str]) -> tuple[Optional[str], Optional[str], str, float]:
    """Aplica crosswalk do Panrotas. Retorna (l1, l2, method, confidence)."""
    if not cat_raw or cat_raw not in PANROTAS_CROSSWALK:
        return None, None, "sem_mapeamento", 0.0
    l1, l2_override = PANROTAS_CROSSWALK[cat_raw]
    if l1 is None:
        return None, None, "requires_disambiguation", 0.0
    # L2: subcategoria após " - " ou override explícito
    l2 = l2_override if l2_override else (cat_raw.split(" - ", 1)[1] if " - " in cat_raw else None)
    return l1, l2, "lookup_nativo", 1.0


def _lookup_me(cat_raw: Optional[str]) -> tuple[Optional[str], Optional[str], str, float]:
    """Aplica crosswalk do Mercado & Eventos."""
    if not cat_raw or cat_raw not in ME_CROSSWALK:
        return None, None, "sem_mapeamento", 0.0
    l1 = ME_CROSSWALK[cat_raw]
    if l1 is None:
        return None, None, "requires_disambiguation", 0.0
    return l1, None, "lookup_nativo", 1.0


def _classify(text: str) -> tuple[Optional[str], str, float]:
    """Classifica via TF-IDF + SVC calibrado. Retorna (l1, method, confidence)."""
    _load_models()
    vec = _vectorizer.transform([text])
    probas = _classifier.predict_proba(vec)[0]
    classes = _classifier.classes_
    idx = probas.argmax()
    confidence = float(probas[idx])
    l1 = classes[idx]
    return l1, "modelo_svc_tfidf", confidence


CONFIDENCE_THRESHOLD = 0.55   # abaixo disso → baixa confiança, encaminhar p/ revisão


def harmonize_category(item: dict, cfg: SourceConfig) -> dict:
    """
    Preenche canonical_category_l1/l2, category_mapping_method e confidence.
    Modifica item in-place e retorna.
    """
    cat_raw = item.get("source_category_raw")
    text = (item.get("title") or "") + " " + (item.get("description") or "")

    if cfg.source_id == "panrotas":
        l1, l2, method, conf = _lookup_panrotas(cat_raw)
        # Ambíguos do Panrotas também passam pelo classificador
        if method == "requires_disambiguation":
            l1, method, conf = _classify(text)
            l2 = None

    elif cfg.source_id == "mercadoeeventos":
        l1, l2, method, conf = _lookup_me(cat_raw)
        if method in ("sem_mapeamento", "requires_disambiguation"):
            l1, method, conf = _classify(text)
            l2 = None

    else:
        # Fontes sem taxonomia nativa confiável: classificador direto
        l1, method, conf = _classify(text)
        l2 = None

    item["canonical_category_l1"]       = l1
    item["canonical_category_l2"]       = l2
    item["category_mapping_method"]     = method
    item["category_mapping_confidence"] = round(conf, 4)

    # Sinalizar baixa confiança para revisão futura
    if conf < CONFIDENCE_THRESHOLD and method != "lookup_nativo":
        item["category_mapping_method"] = method + "_low_confidence"

    return item


# ── 3. Filtro content_domain ──────────────────────────────────────────────────
#
# Heurística por palavras-chave (fase 1).
# Fase 2: substituir a zona cinzenta por chamada ao LLM-árbitro.
#
# Regra: Camada B (geopolitica / partidaria) vence Camada A (turismo_direto).

_PARTISAN_PATTERN = re.compile(
    r"\b(eleição|eleições|candidato|candidatura|partido|partidos|campanha eleitoral|"
    r"senado|senador|deputado|vereador|governador|prefeito|presidente da república|"
    r"lula|bolsonaro|pt\b|pp\b|mdb\b|pl\b|psol\b|novo\b|união brasil|"
    r"escândalo|corrupção|impeachment|cpi\b|improbidade)\b",
    re.IGNORECASE | re.UNICODE,
)

_GEOPOLITICS_PATTERN = re.compile(
    r"\b(visto|vistos|fronteira|fronteiras|conflito|guerra|sanção|sanções|"
    r"câmbio|dólar|euro|libra|taxa de câmbio|inflação|juros|selic|"
    r"embargo|restrição de viagem|alerta de viagem|evacuação|"
    r"passaporte|imigração|refúgio|refugiado)\b",
    re.IGNORECASE | re.UNICODE,
)

_TOURISM_DIRECT_THRESHOLD = 0.3  # % mínimo de turismo-keywords para ser turismo_direto


def classify_content_domain(item: dict) -> dict:
    """
    Classifica content_domain e preenche content_domain_confidence.
    Regra: politica_partidaria_excluir vence geopolitica_relevante vence turismo_direto.
    Modifica item in-place e retorna.
    """
    text = (item.get("title") or "") + " " + (item.get("description") or "")

    has_partisan    = bool(_PARTISAN_PATTERN.search(text))
    has_geopolitics = bool(_GEOPOLITICS_PATTERN.search(text))
    has_tourism     = bool(_TOURISM_KEYWORDS.search(text))

    if has_partisan and not has_tourism:
        domain = "politica_partidaria_excluir"
        conf   = 0.80
    elif has_partisan and has_geopolitics and has_tourism:
        # Zona cinzenta: geopolítica com toque turístico — manter
        domain = "geopolitica_relevante"
        conf   = 0.60
    elif has_partisan and has_tourism:
        # Político mas com contexto turístico claro → manter com aviso
        domain = "turismo_direto"
        conf   = 0.55
    elif has_geopolitics:
        domain = "geopolitica_relevante"
        conf   = 0.75
    else:
        domain = "turismo_direto"
        conf   = 0.90

    item["content_domain"]            = domain
    item["content_domain_confidence"] = round(conf, 2)
    return item


# ── Pipeline completo por item ────────────────────────────────────────────────

def process_item(item: dict, cfg: SourceConfig) -> Optional[dict]:
    """
    Aplica pipeline completo a um item bruto.
    Retorna None se o item for descartado (out_of_scope, frescor, confiança ou politica_partidaria).
    """
    # Estágio 0: frescor — descartar itens mais antigos que max_age_days
    if cfg.max_age_days is not None:
        pub = item.get("pub_date") or ""
        if pub:
            try:
                pub_dt = datetime.fromisoformat(pub)
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                age = datetime.now(tz=timezone.utc) - pub_dt
                if age > timedelta(days=cfg.max_age_days):
                    logger.debug(
                        "Descartado por frescor (%d dias): %s",
                        age.days, (item.get("title") or "")[:60],
                    )
                    return None
            except Exception:
                pass  # data inválida → deixa passar para avaliação seguinte

    # Estágio 1: in_scope
    in_scope = check_in_scope(item, cfg)
    item["in_scope"] = in_scope
    if not in_scope:
        return None   # não persiste nem classifica

    # Estágio 2: harmonização de categoria
    harmonize_category(item, cfg)

    # Estágio 2b: confiança mínima — descartar classificações fracas (apenas para fontes sem lookup nativo)
    if cfg.min_classify_confidence > 0:
        method = item.get("category_mapping_method", "")
        conf   = item.get("category_mapping_confidence", 1.0)
        if "lookup_nativo" not in method and conf < cfg.min_classify_confidence:
            logger.debug(
                "Descartado por baixa confiança (%.2f < %.2f): %s",
                conf, cfg.min_classify_confidence, (item.get("title") or "")[:60],
            )
            return None

    # Estágio 3: content_domain
    classify_content_domain(item)
    if item["content_domain"] == "politica_partidaria_excluir":
        return None   # descarta

    return item
