"""
Persistência mensal dos itens harmonizados.

Estrutura de arquivos:
  dados/
    {aaaa-mm}.json          — lista de itens do mês (append/upsert por guid)
    indice-meses.json       — índice com metadados de cada mês

Política de upsert:
  - Chave primária: guid
  - Se o guid já existe no arquivo mensal, substitui (atualiza) o item
  - Se não existe, acrescenta ao final
  Isso permite re-executar o pipeline sem duplicatas.
"""

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DADOS_DIR = Path(__file__).parent.parent / "dados"


def _month_key(pub_date_iso: Optional[str]) -> str:
    """
    Extrai AAAA-MM de um timestamp ISO 8601.
    Se ausente ou inválido, usa o mês corrente.
    """
    if pub_date_iso:
        try:
            return pub_date_iso[:7]   # "2026-07"
        except Exception:
            pass
    return datetime.now(tz=timezone.utc).strftime("%Y-%m")


def _load_month(month_key: str) -> dict[str, dict]:
    """
    Carrega o arquivo mensal como dict {guid: item}.
    Retorna dict vazio se o arquivo não existir.
    """
    path = _DADOS_DIR / f"{month_key}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    return {item["guid"]: item for item in items}


def _save_month(month_key: str, items_by_guid: dict[str, dict]) -> Path:
    """Persiste o dicionário como lista ordenada por pub_date desc."""
    _DADOS_DIR.mkdir(parents=True, exist_ok=True)
    path = _DADOS_DIR / f"{month_key}.json"
    items = sorted(
        items_by_guid.values(),
        key=lambda x: x.get("pub_date") or "",
        reverse=True,
    )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return path


def _update_index(month_key: str, n_items: int) -> None:
    """Mantém indice-meses.json atualizado."""
    index_path = _DADOS_DIR / "indice-meses.json"
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {}

    index[month_key] = {
        "mes": month_key,
        "total_itens": n_items,
        "atualizado_em": datetime.now(tz=timezone.utc).isoformat(),
    }

    # Ordena por mês descendente
    ordered = dict(sorted(index.items(), reverse=True))
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)


def upsert_items(items: list[dict], dry_run: bool = False) -> dict:
    """
    Insere ou atualiza uma lista de itens harmonizados nos arquivos mensais.

    Retorna resumo:
      {
        "meses_afetados": [...],
        "novos": int,
        "atualizados": int,
        "total_upsert": int,
      }
    """
    # Agrupa por mês
    by_month: dict[str, list[dict]] = {}
    for item in items:
        mk = _month_key(item.get("pub_date"))
        by_month.setdefault(mk, []).append(item)

    stats = {"meses_afetados": [], "novos": 0, "atualizados": 0, "total_upsert": 0}

    for month_key, month_items in sorted(by_month.items()):
        existing = _load_month(month_key)
        n_before = len(existing)

        new_count = 0
        upd_count = 0
        for item in month_items:
            guid = item["guid"]
            if guid in existing:
                upd_count += 1
            else:
                new_count += 1
            existing[guid] = item

        if not dry_run:
            path = _save_month(month_key, existing)
            _update_index(month_key, len(existing))
            logger.info(
                "Mês %s → %s (+%d novos, %d atualizados) — %s",
                month_key, len(existing), new_count, upd_count, path.name,
            )
        else:
            logger.info(
                "[dry-run] Mês %s → %d existentes + %d novos + %d atualizados",
                month_key, n_before, new_count, upd_count,
            )

        stats["meses_afetados"].append(month_key)
        stats["novos"]          += new_count
        stats["atualizados"]    += upd_count
        stats["total_upsert"]   += new_count + upd_count

    return stats


def load_month(month_key: str) -> list[dict]:
    """Carrega todos os itens de um mês como lista (para consulta/front-end)."""
    return list(_load_month(month_key).values())


def list_months() -> list[str]:
    """Retorna a lista de meses disponíveis (AAAA-MM) em ordem descendente."""
    index_path = _DADOS_DIR / "indice-meses.json"
    if not index_path.exists():
        return []
    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)
    return sorted(index.keys(), reverse=True)
