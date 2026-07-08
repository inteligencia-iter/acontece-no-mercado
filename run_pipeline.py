#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ponto de entrada do Monitor de Noticias de Turismo.

Uso:
  python run_pipeline.py                        # executa todas as fontes
  python run_pipeline.py --sources panrotas g1  # fontes especificas
  python run_pipeline.py --dry-run              # nao persiste; imprime resumo
  python run_pipeline.py --dry-run --sources g1_turismo

Saida padrao em modo normal: dados/{aaaa-mm}.json + dados/indice-meses.json

Janela temporal: jan/2025 em diante (MIN_DATE).
Itens mais antigos sao ignorados na persistencia, mas o pipeline
nunca apaga dados ja gravados - acumulativo.
"""

# Mes minimo para persistencia (inclusive). Formato "AAAA-MM".
MIN_DATE = "2025-01"

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone

from pipeline.fetcher import fetch_all
from pipeline.harmonizer import process_item
from pipeline.scorer import score_item
from pipeline.storage import upsert_items
from pipeline.config import SOURCES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_pipeline")


def _print_report(all_items, discarded, stats):
    total_fetched = len(all_items) + discarded

    print("\n" + "=" * 60)
    print("  Monitor de Noticias de Turismo - " + datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 60)
    print("  Itens recuperados (bruto):   %5d" % total_fetched)
    print("  Descartados (fora de scope): %5d" % discarded)
    print("  Itens persistidos/dry-run:   %5d" % len(all_items))
    print()

    cat_counts = Counter(
        item.get("canonical_category_l1") or "sem_categoria"
        for item in all_items
    )
    print("  Distribuicao por categoria L1:")
    for cat, n in cat_counts.most_common():
        bar = "#" * min(n // 5, 40)
        print("    %-35s %4d  %s" % (cat, n, bar))
    print()

    method_counts = Counter(
        item.get("category_mapping_method") or "unknown"
        for item in all_items
    )
    print("  Metodo de mapeamento:")
    for method, n in method_counts.most_common():
        print("    %-40s %4d" % (method, n))
    print()

    domain_counts = Counter(
        item.get("content_domain") or "unknown"
        for item in all_items
    )
    print("  Content domain:")
    for domain, n in domain_counts.most_common():
        print("    %-40s %4d" % (domain, n))
    print()

    source_counts = Counter(item.get("source_id") for item in all_items)
    print("  Por fonte:")
    for src, n in source_counts.most_common():
        print("    %-30s %4d" % (src, n))
    print()

    tier_counts = Counter(item.get("layout_tier") for item in all_items)
    print("  Layout tiers (destaque_score):")
    for tier in ["manchete", "grade", "condensado"]:
        print("    %-15s %4d" % (tier, tier_counts.get(tier, 0)))
    print()

    low_conf = sum(
        1 for item in all_items
        if "low_confidence" in (item.get("category_mapping_method") or "")
    )
    print("  Baixa confianca (< 0.55):    %5d  -> candidatos a LLM-arbitro" % low_conf)

    if not stats.get("dry_run"):
        print()
        print("  Arquivos atualizados:")
        for mk in stats.get("meses_afetados", []):
            print("    dados/%s.json" % mk)
        print("    dados/indice-meses.json")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Monitor de Noticias de Turismo")
    parser.add_argument(
        "--sources", nargs="+", metavar="SOURCE_ID",
        help="IDs das fontes a ingerir (padrao: todas)",
        choices=list(SOURCES.keys()),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Executa o pipeline completo mas nao grava arquivos",
    )
    args = parser.parse_args()

    dry_run = args.dry_run
    source_ids = args.sources or None

    if dry_run:
        logger.info("Modo DRY-RUN ativo - nenhum arquivo sera gravado")

    # Fase 1: Ingestion
    logger.info("Iniciando ingestao de fontes: %s", source_ids or "todas")
    raw_items = list(fetch_all(source_ids))
    logger.info("Itens brutos recuperados: %d", len(raw_items))

    # Fase 2: Harmonizacao
    harmonized = []
    discarded = 0

    for item in raw_items:
        cfg = SOURCES.get(item["source_id"])
        if cfg is None:
            logger.warning("Source sem config: %s", item.get("source_id"))
            discarded += 1
            continue
        result = process_item(item, cfg)
        if result is None:
            discarded += 1
        else:
            harmonized.append(result)

    logger.info("Apos harmonizacao: %d validos, %d descartados", len(harmonized), discarded)

    # Fase 3: Scoring
    for item in harmonized:
        score_item(item)

    # Fase 4: Filtro de janela temporal
    before_filter = len(harmonized)
    harmonized = [
        item for item in harmonized
        if (item.get("pub_date") or "")[:7] >= MIN_DATE
    ]
    filtered_out = before_filter - len(harmonized)
    if filtered_out:
        logger.info("Descartados por janela temporal (< %s): %d", MIN_DATE, filtered_out)

    # Fase 5: Persistencia
    storage_stats = upsert_items(harmonized, dry_run=dry_run)
    storage_stats["dry_run"] = dry_run

    # Relatorio
    _print_report(harmonized, discarded, storage_stats)

    # Em dry-run, exibe amostra top-5
    if dry_run and harmonized:
        top5 = sorted(harmonized, key=lambda x: x.get("destaque_score") or 0, reverse=True)[:5]
        print("  Top-5 por destaque_score (amostra):")
        for item in top5:
            cat = (item.get("canonical_category_l1") or "")[:30]
            title = (item.get("title") or "")[:65]
            print("    [%.3f] %-10s %-30s %s" % (
                item.get("destaque_score", 0),
                item.get("layout_tier", ""),
                cat,
                title,
            ))
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
