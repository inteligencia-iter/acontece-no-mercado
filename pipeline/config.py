"""
Configuração de fontes e crosswalks do Monitor de Notícias de Turismo.
Baseado em: taxonomia-canonica-fontes.md + resultados-validacao-tecnica.md
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Taxonomia canônica L1 ─────────────────────────────────────────────────────
L1_CLASSES = [
    "Aviação",
    "Hotelaria",
    "Destinos",
    "Atrativos e Parques",
    "Cruzeiros",
    "Distribuição e Trade",
    "Corporativo",
    "Eventos e Feiras",
    "Câmbio e Economia do Turismo",
    "Política e Regulação Setorial",
]

# ── Crosswalk Panrotas ────────────────────────────────────────────────────────
PANROTAS_CROSSWALK: dict[str, tuple[Optional[str], Optional[str]]] = {
    # 100x Brasil
    "100x Brasil - Concessões":           ("Política e Regulação Setorial",  None),
    "100x Brasil - Crédito":              ("Câmbio e Economia do Turismo",   None),
    "100x Brasil - Destinos":             ("Destinos",                       None),
    "100x Brasil - Empreendedorismo":     ("Câmbio e Economia do Turismo",   None),
    "100x Brasil - Empresas":             ("Corporativo",                    None),
    "100x Brasil - Eventos":              ("Eventos e Feiras",               None),
    "100x Brasil - Financiamentos":       ("Câmbio e Economia do Turismo",   None),
    "100x Brasil - Hotelaria":            ("Hotelaria",                      None),
    "100x Brasil - Infraestrutura":       ("Política e Regulação Setorial",  None),
    "100x Brasil - Investimentos":        ("Câmbio e Economia do Turismo",   None),
    "100x Brasil - Mercado":              ("Câmbio e Economia do Turismo",   None),
    "100x Brasil - Mercado de capitais":  ("Câmbio e Economia do Turismo",   None),
    "100x Brasil - Pesquisas e Estatísticas": ("Câmbio e Economia do Turismo", None),
    "100x Brasil - Política":             ("Política e Regulação Setorial",  None),
    "100x Brasil - Política monetária":   ("Câmbio e Economia do Turismo",   None),
    "100x Brasil - Sustentabilidade":     ("Câmbio e Economia do Turismo",   None),
    # Agências de Viagens
    "Agências de Viagens - Eventos":      ("Eventos e Feiras",               None),
    "Agências de Viagens - Mercado":      ("Distribuição e Trade",           None),
    "Agências de Viagens - Movimentação": ("Distribuição e Trade",           None),
    "Agências de Viagens - Nichos":       ("Distribuição e Trade",           None),
    "Agências de Viagens - Remuneração":  ("Distribuição e Trade",           None),
    "Agências de Viagens - Treinamento":  ("Distribuição e Trade",           None),
    "Agências de Viagens - Vendas":       ("Distribuição e Trade",           None),
    # Aviação
    "Aviação - Aeroportos":               ("Aviação", None),
    "Aviação - Distribuição":             ("Aviação", None),
    "Aviação - Empresas":                 ("Aviação", None),
    "Aviação - Eventos":                  ("Aviação", None),
    "Aviação - Investimentos":            ("Aviação", None),
    "Aviação - Novas rotas":              ("Aviação", None),
    "Aviação - Parcerias":                ("Aviação", None),
    "Aviação - Pesquisas e Estatísticas": ("Aviação", None),
    "Aviação - Tecnologia":               ("Aviação", None),
    # Corporativo
    "Corporativo - Aviação":              ("Corporativo", None),
    "Corporativo - Cases":                ("Corporativo", None),
    "Corporativo - Destinos":             ("Corporativo", None),
    "Corporativo - Empresas":             ("Corporativo", None),
    "Corporativo - Estudos":              ("Corporativo", None),
    "Corporativo - Eventos":              ("Corporativo", None),
    "Corporativo - Gente":                ("Corporativo", None),
    "Corporativo - Gestão de viagens":    ("Corporativo", None),
    "Corporativo - Hotelaria":            ("Corporativo", None),
    "Corporativo - Mercado":              ("Corporativo", None),
    "Corporativo - Mice":                 ("Eventos e Feiras",               None),
    "Corporativo - Mobilidade":           ("Corporativo", None),
    "Corporativo - Pesquisas e Estatísticas": ("Corporativo",               None),
    "Corporativo - Política":             ("Corporativo", None),
    "Corporativo - Política de viagens":  ("Corporativo", None),
    "Corporativo - TMCs":                 ("Corporativo", None),
    "Corporativo - Tecnologia":           ("Corporativo", None),
    # Destinos
    "Destinos - Alternativo":             ("Destinos",           None),
    "Destinos - Comer e beber":           ("Destinos",           None),
    "Destinos - Entretenimento":          ("Destinos",           None),
    "Destinos - Eventos":                 ("Eventos e Feiras",   None),
    "Destinos - Luxo":                    ("Destinos",           None),
    "Destinos - Parques temáticos":       ("Atrativos e Parques", None),
    "Destinos - Pesquisas e Estatísticas":("Destinos",           None),
    "Destinos - Romântico":               ("Destinos",           None),
    # Hotelaria
    "Hotelaria - Alimentos e bebidas":    ("Hotelaria", None),
    "Hotelaria - Distribuição":           ("Hotelaria", None),
    "Hotelaria - Eventos":                ("Hotelaria", None),
    "Hotelaria - Inaugurações":           ("Hotelaria", None),
    "Hotelaria - Investimentos":          ("Hotelaria", None),
    "Hotelaria - Mercado":                ("Hotelaria", None),
    "Hotelaria - Parcerias":              ("Hotelaria", None),
    "Hotelaria - Tecnologia":             ("Hotelaria", None),
    # Mercado
    "Mercado - Cartões de assistência":   ("Distribuição e Trade",           None),
    "Mercado - Consolidadoras":           ("Distribuição e Trade",           None),
    "Mercado - Cruzeiros":                ("Cruzeiros",                      None),
    "Mercado - Destinos":                 ("Destinos",                       None),
    "Mercado - Distribuição":             ("Distribuição e Trade",           None),
    "Mercado - Diversidade":              ("Corporativo",                    None),
    "Mercado - Economia e Política":      (None,                             None),  # ambíguo → classificador
    "Mercado - Encontros":                ("Eventos e Feiras",               None),
    "Mercado - Feiras":                   ("Eventos e Feiras",               None),
    "Mercado - Locadoras de veículos":    ("Distribuição e Trade",           None),
    "Mercado - Operadoras":               ("Distribuição e Trade",           None),
    "Mercado - Opinião":                  (None,                             None),  # ambíguo → classificador
    "Mercado - Pesquisas e Estatísticas": ("Câmbio e Economia do Turismo",   None),
    "Mercado - Receptivos":               ("Distribuição e Trade",           None),
    "Mercado - Sustentabilidade":         ("Câmbio e Economia do Turismo",   None),
    "Mercado - Tecnologia":               ("Corporativo",                    None),
    "Mercado - Transporte":               ("Distribuição e Trade",           None),
    # Operadoras
    "Operadoras - Agências de viagens":   ("Distribuição e Trade", None),
    "Operadoras - Aviação":               ("Distribuição e Trade", None),
    "Operadoras - Destinos":              ("Distribuição e Trade", None),
    "Operadoras - Distribuição":          ("Distribuição e Trade", None),
    "Operadoras - Empregos":              ("Distribuição e Trade", None),
    "Operadoras - Entretenimento":        ("Distribuição e Trade", None),
    "Operadoras - Eventos":               ("Distribuição e Trade", None),
    "Operadoras - Investimentos":         ("Distribuição e Trade", None),
    "Operadoras - Mercado":               ("Distribuição e Trade", None),
    "Operadoras - Parques temáticos":     ("Atrativos e Parques",  None),
    "Operadoras - Política de viagens":   ("Distribuição e Trade", None),
    "Operadoras - Segurança":             ("Distribuição e Trade", None),
    "Operadoras - Tecnologia":            ("Distribuição e Trade", None),
}

# ── Crosswalk Mercado & Eventos ───────────────────────────────────────────────
ME_CROSSWALK: dict[str, Optional[str]] = {
    "Aviação":                  "Aviação",
    "Agências e Operadoras":    "Distribuição e Trade",
    "Cruzeiros":                "Cruzeiros",
    "Feiras e Eventos":         "Eventos e Feiras",
    "Tecnologia e Inovação":    "Corporativo",
    "Brasil":                   None,   # geográfico — classificador
    "Notícias":                 None,   # genérico — classificador
    "Seguro Viagem":            "Distribuição e Trade",
    "Hotelaria":                "Hotelaria",
    "Destinos":                 "Destinos",
}

# ── Configuração das fontes ───────────────────────────────────────────────────
@dataclass
class SourceConfig:
    source_id: str
    source_type: str
    native_taxonomy_trusted: bool
    needs_full_text_scrape: bool
    rss_status: str                       # confirmado | bloqueado_confirmed | inexistente_confirmed
    feed_urls: list[str] = field(default_factory=list)
    crosswalk: Optional[dict] = None
    category_field: Optional[str] = None
    boilerplate_regex: Optional[str] = None
    exclude_categories: list[str] = field(default_factory=list)
    feed_encoding: Optional[str] = None  # ex: "gzip"
    fallback_url: Optional[str] = None
    max_age_days: Optional[int] = None          # descartar itens mais antigos que N dias
    min_classify_confidence: float = 0.0        # descartar classificações abaixo desse score
    title_cleanup_regex: Optional[str] = None   # remover sufixo/prefixo do título (ex: "- Fonte")


SOURCES: dict[str, SourceConfig] = {

    "panrotas": SourceConfig(
        source_id="panrotas",
        source_type="especializada_com_taxonomia_nativa",
        native_taxonomy_trusted=True,
        needs_full_text_scrape=False,
        rss_status="confirmado",
        category_field="category",
        crosswalk=PANROTAS_CROSSWALK,
        feed_urls=[
            "https://www.panrotas.com.br/feed/destinos",
            "https://www.panrotas.com.br/feed/mercado",
            "https://www.panrotas.com.br/feed/aviacao",
            "https://www.panrotas.com.br/feed/hotelaria",
            "https://www.panrotas.com.br/feed/operadoras",
            "https://www.panrotas.com.br/feed/agencias-de-viagens",
            "https://www.panrotas.com.br/feed/corporativo",
            "https://www.panrotas.com.br/feed/100x-brasil",
            # /feed/gente deliberadamente omitido
        ],
    ),

    "mercadoeeventos": SourceConfig(
        source_id="mercadoeeventos",
        source_type="especializada_trade",
        native_taxonomy_trusted=True,
        needs_full_text_scrape=False,
        rss_status="confirmado",
        category_field="category",
        crosswalk=ME_CROSSWALK,
        feed_urls=["https://www.mercadoeeventos.com.br/feed/"],
    ),

    "embratur": SourceConfig(
        source_id="embratur",
        source_type="institucional_promocional_internacional",
        native_taxonomy_trusted=False,
        needs_full_text_scrape=True,
        rss_status="confirmado",
        category_field="category",
        boilerplate_regex=r"O post .* apareceu primeiro em Embratur\.?",
        exclude_categories=["modelo_noticia", "uncategorized"],
        feed_urls=["https://embratur.com.br/feed/"],
    ),

    "g1_turismo": SourceConfig(
        source_id="g1_turismo",
        source_type="generalista",
        native_taxonomy_trusted=False,
        needs_full_text_scrape=True,
        rss_status="confirmado",
        category_field=None,   # retorna apenas "G1" — inútil
        feed_encoding="gzip",
        feed_urls=["https://g1.globo.com/rss/g1/turismo-e-viagem/"],
    ),

    "agenciabrasil": SourceConfig(
        source_id="agenciabrasil",
        source_type="institucional_publico_editorial",
        native_taxonomy_trusted=False,
        needs_full_text_scrape=True,
        rss_status="confirmado",
        category_field=None,
        feed_urls=[
            "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml",
            "https://agenciabrasil.ebc.com.br/rss/geral/feed.xml",
            "https://agenciabrasil.ebc.com.br/rss/internacional/feed.xml",
            # rss/politica deliberadamente omitido
        ],
    ),

    "valor_economico": SourceConfig(
        source_id="valor_economico",
        source_type="generalista",
        native_taxonomy_trusted=False,
        needs_full_text_scrape=False,
        rss_status="confirmado",
        category_field=None,
        max_age_days=30,
        min_classify_confidence=0.0,   # keyword do Google News já filtra; score não aplicado
        title_cleanup_regex=r"\s*[-–]\s*Valor Econ[oô]mico\.?\s*$",
        feed_urls=[
            "https://news.google.com/rss/search?q=turismo+OR+turistas+site:valor.globo.com&hl=pt-BR&gl=BR&ceid=BR:pt-419",
        ],
    ),

    # ── Fontes com fallback de scraping (stubs — implementar em fase 2) ────────
    "diariodoturismo": SourceConfig(
        source_id="diariodoturismo",
        source_type="especializada_trade",
        native_taxonomy_trusted=False,
        needs_full_text_scrape=True,
        rss_status="bloqueado_confirmed",
        fallback_url="https://diariodoturismo.com.br/",
        feed_urls=[],   # RSS desativado — usar scraping HTML
    ),

    "mtur_govbr": SourceConfig(
        source_id="mtur_govbr",
        source_type="institucional_domestico",
        native_taxonomy_trusted=False,
        needs_full_text_scrape=True,
        rss_status="inexistente_confirmed",
        fallback_url="https://www.gov.br/turismo/pt-br/assuntos/noticias",
        feed_urls=[],   # RSS inexistente — usar scraping + sitemap
    ),
}

# ── Categorias de alto impacto para destaque_score ───────────────────────────
HIGH_IMPACT_CATEGORIES = {"Câmbio e Economia do Turismo", "Aviação"}
