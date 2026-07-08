"""
Ingestor RSS genérico.
Suporta feeds padrão e gzip. Stubs para fontes de scraping (fase 2).
"""

import re
import hashlib
import logging
from datetime import timezone
from typing import Iterator

import feedparser
from email.utils import parsedate_to_datetime

from .config import SourceConfig, SOURCES

logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (compatible; TurismoBR-Monitor/1.0)"


def _make_guid(link: str, title: str) -> str:
    """GUID determinístico para itens sem guid nativo."""
    raw = (link or "") + (title or "")
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_date(raw: str) -> str | None:
    """Converte data RFC 2822 para ISO 8601 UTC. Retorna None se falhar."""
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except Exception:
        return raw or None


def _clean_html(text: str) -> str:
    """Remove tags HTML e normaliza espaços."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


_IMG_TAG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


def _extract_image(entry, raw_html: str) -> str | None:
    """
    Tenta extrair URL de imagem de capa em ordem de preferência:
    1. media_content (tag <media:content>)
    2. media_thumbnail
    3. enclosure (tag <enclosure>)
    4. Primeiro <img> no HTML da description
    """
    # 1. media:content
    media = getattr(entry, "media_content", None) or []
    for m in media:
        url = m.get("url") or m.get("URL")
        if url and any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")):
            return url
    # fallback: pega qualquer media_content com url
    for m in media:
        url = m.get("url") or m.get("URL")
        if url:
            return url

    # 2. media:thumbnail
    thumb = getattr(entry, "media_thumbnail", None) or []
    for t in thumb:
        url = t.get("url")
        if url:
            return url

    # 3. enclosure
    enclosures = getattr(entry, "enclosures", None) or []
    for enc in enclosures:
        url = enc.get("url") or enc.get("href")
        ctype = enc.get("type", "")
        if url and "image" in ctype:
            return url

    # 4. primeiro <img> no HTML bruto
    if raw_html:
        m = _IMG_TAG_RE.search(raw_html)
        if m:
            return m.group(1)

    return None


def _fetch_rss(url: str, encoding: str | None = None) -> feedparser.FeedParserDict:
    """Faz o fetch de um feed RSS com User-Agent correto e suporte a gzip."""
    headers = {"User-Agent": UA}
    if encoding == "gzip":
        headers["Accept-Encoding"] = "gzip, deflate"
    return feedparser.parse(url, request_headers=headers)


def fetch_source(cfg: SourceConfig) -> Iterator[dict]:
    """
    Gera itens brutos de uma fonte configurada.
    Cada item tem o schema mínimo necessário para o harmonizador.
    """
    if cfg.rss_status in ("bloqueado_confirmed", "inexistente_confirmed"):
        yield from _fetch_scraping_stub(cfg)
        return

    seen_guids: set[str] = set()

    for url in cfg.feed_urls:
        logger.info("Fetching %s — %s", cfg.source_id, url)
        try:
            feed = _fetch_rss(url, cfg.feed_encoding)
        except Exception as exc:
            logger.error("Erro ao fazer fetch de %s: %s", url, exc)
            continue

        if feed.bozo and not feed.entries:
            logger.warning("Feed malformado ou vazio: %s", url)
            continue

        for entry in feed.entries:
            # ── Campos básicos ────────────────────────────────────────────────
            guid  = getattr(entry, "id", None) or _make_guid(
                getattr(entry, "link", ""), getattr(entry, "title", "")
            )
            if guid in seen_guids:
                continue
            seen_guids.add(guid)

            title   = _clean_html(getattr(entry, "title", "") or "")
            link    = getattr(entry, "link", "") or ""
            author  = getattr(entry, "author", "") or ""
            pub_raw = getattr(entry, "published", "") or ""
            pub_date = _parse_date(pub_raw)

            # ── Descrição / lide ──────────────────────────────────────────────
            # Preferência: summary (lide) > content[0] (corpo completo)
            summary = getattr(entry, "summary", "") or ""
            desc = _clean_html(summary)

            # Remove boilerplate (ex: Embratur)
            if cfg.boilerplate_regex and desc:
                desc = re.sub(cfg.boilerplate_regex, "", desc, flags=re.IGNORECASE).strip()

            # ── Imagem de capa ────────────────────────────────────────────────
            image_url = _extract_image(entry, summary)

            # ── Categoria nativa ──────────────────────────────────────────────
            tags = getattr(entry, "tags", []) or []
            categories = [t.term for t in tags if t.term] if tags else []

            # Filtrar categorias excluídas (ex: Embratur lixo)
            categories = [
                c for c in categories
                if c.lower() not in {e.lower() for e in cfg.exclude_categories}
            ]
            source_category_raw = categories[0] if categories else None

            yield {
                "source_id":           cfg.source_id,
                "guid":                guid,
                "title":               title,
                "link":                link,
                "description":         desc,
                "image_url":           image_url,
                "author":              author,
                "pub_date":            pub_date,
                "source_category_raw": source_category_raw,
                "all_categories":      categories,
                # campos a preencher pelo harmonizador
                "in_scope":                     None,
                "canonical_category_l1":        None,
                "canonical_category_l2":        None,
                "category_mapping_method":      None,
                "category_mapping_confidence":  None,
                "content_domain":               None,
                "content_domain_confidence":    None,
                "destaque_score":               None,
            }


def _fetch_scraping_stub(cfg: SourceConfig) -> Iterator[dict]:
    """
    Stub para fontes cujo RSS está bloqueado/inexistente.
    Fase 2: implementar scraping HTML aqui.
    """
    logger.warning(
        "Fonte '%s' requer scraping HTML (rss_status=%s). "
        "Stub ativo — nenhum item ingerido. Implementar em fase 2.",
        cfg.source_id, cfg.rss_status,
    )
    return
    yield  # torna a função um generator vazio


def fetch_all(source_ids: list[str] | None = None) -> Iterator[dict]:
    """
    Ingere todas as fontes configuradas (ou subset via source_ids).
    Gera itens brutos em ordem de chegada.
    """
    ids = source_ids or list(SOURCES.keys())
    for sid in ids:
        cfg = SOURCES.get(sid)
        if not cfg:
            logger.warning("source_id desconhecido: %s", sid)
            continue
        yield from fetch_source(cfg)
