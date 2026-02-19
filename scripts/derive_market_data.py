"""
Derive market research data from existing trade_data collection.

Populates:
  - market_segments (HS chapters 50-63)
  - market_size_series (annual totals by HS chapter)

Usage:
    cd backend && python ../scripts/derive_market_data.py
"""
import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure the backend package is importable
_here = os.path.dirname(os.path.abspath(__file__))
_backend = os.path.join(os.path.dirname(_here), "backend")
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.agents.constants import HS_CHAPTER_DESCRIPTIONS_FR, TEXTILE_HS_CHAPTERS
from app.database import get_sync_db
from app.models.market_research import new_market_size_doc, new_segment_doc


def derive():
    db = get_sync_db()

    # ── 1. Seed market segments for HS chapters ──────────
    print("\n[1/3] Seeding market segments for HS chapters 50-63...")
    seg_count = 0
    for chapter in TEXTILE_HS_CHAPTERS:
        label_fr = HS_CHAPTER_DESCRIPTIONS_FR.get(chapter, f"Chapitre {chapter}")
        label_en = f"Chapter {chapter}"

        existing = db.market_segments.find_one({"axis": "hs_chapter", "code": chapter})
        if not existing:
            doc = new_segment_doc(
                axis="hs_chapter",
                code=chapter,
                label_fr=label_fr,
                label_en=label_en,
                description_fr=f"Chapitre SH {chapter} — {label_fr}",
            )
            db.market_segments.insert_one(doc)
            seg_count += 1
            print(f"  [OK] Segment: Ch. {chapter} — {label_fr}")
        else:
            print(f"  [SKIP] Segment exists: Ch. {chapter}")

    # Also add aggregate segments
    aggregate_segments = [
        ("product_category", "apparel", "Vetements et habillement", "Apparel & Clothing"),
        ("product_category", "home_textiles", "Textiles de maison", "Home Textiles"),
        ("product_category", "technical_textiles", "Textiles techniques", "Technical Textiles"),
        ("product_category", "raw_materials", "Matieres premieres textiles", "Raw Textile Materials"),
        ("fiber_type", "cotton", "Coton", "Cotton"),
        ("fiber_type", "synthetic", "Fibres synthetiques", "Synthetic Fibers"),
        ("fiber_type", "wool", "Laine", "Wool"),
        ("fiber_type", "silk", "Soie", "Silk"),
    ]
    for axis, code, label_fr, label_en in aggregate_segments:
        existing = db.market_segments.find_one({"axis": axis, "code": code})
        if not existing:
            doc = new_segment_doc(axis=axis, code=code, label_fr=label_fr, label_en=label_en)
            db.market_segments.insert_one(doc)
            seg_count += 1
            print(f"  [OK] Segment: {axis}/{code} — {label_fr}")
        else:
            print(f"  [SKIP] Segment exists: {axis}/{code}")

    print(f"\n  => {seg_count} new segments created")

    # ── 2. Derive market_size_series from trade_data ─────
    print("\n[2/3] Deriving market size series from trade_data...")
    size_count = 0

    # Aggregate by year, HS chapter (2-digit), flow
    pipeline = [
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$period_date"},
                    "chapter": {"$substr": ["$hs_code", 0, 2]},
                    "flow": "$flow",
                },
                "total_value": {
                    "$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}
                },
            }
        },
        {"$sort": {"_id.year": 1, "_id.chapter": 1}},
    ]

    results = list(db.trade_data.aggregate(pipeline))
    print(f"  Found {len(results)} aggregation results")

    for r in results:
        year = r["_id"]["year"]
        chapter = r["_id"]["chapter"]
        flow = r["_id"]["flow"] or "total"
        value = r["total_value"]

        if not chapter or chapter in ("TO", "SI", ""):
            continue

        # Dedup
        existing = db.market_size_series.find_one({
            "segment_code": chapter,
            "geography_code": "MA",
            "year": year,
            "flow": flow,
        })
        if not existing:
            doc = new_market_size_doc(
                segment_code=chapter,
                geography_code="MA",
                year=year,
                value_usd=value,
                unit="USD",
                source="derived_from_trade_data",
                flow=flow,
            )
            try:
                db.market_size_series.insert_one(doc)
                size_count += 1
            except Exception:
                pass

    # Also create total market size per year (all chapters combined)
    total_pipeline = [
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$period_date"},
                    "flow": "$flow",
                },
                "total_value": {
                    "$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}
                },
            }
        },
        {"$sort": {"_id.year": 1}},
    ]

    for r in db.trade_data.aggregate(total_pipeline):
        year = r["_id"]["year"]
        flow = r["_id"]["flow"] or "total"
        value = r["total_value"]

        existing = db.market_size_series.find_one({
            "segment_code": "ALL",
            "geography_code": "MA",
            "year": year,
            "flow": flow,
        })
        if not existing:
            doc = new_market_size_doc(
                segment_code="ALL",
                geography_code="MA",
                year=year,
                value_usd=value,
                source="derived_from_trade_data",
                flow=flow,
            )
            try:
                db.market_size_series.insert_one(doc)
                size_count += 1
            except Exception:
                pass

    print(f"  => {size_count} new market size entries created")

    # ── 3. Summary ───────────────────────────────────────
    print("\n[3/3] Summary:")
    print(f"  Segments:        {db.market_segments.count_documents({})}")
    print(f"  Market Size:     {db.market_size_series.count_documents({})}")
    print(f"  Companies:       {db.companies.count_documents({})}")
    print(f"  Market Share:    {db.market_share_series.count_documents({})}")
    print(f"  Events:          {db.competitive_events.count_documents({})}")
    print(f"  Insights:        {db.insights.count_documents({})}")
    print(f"  Frameworks:      {db.framework_results.count_documents({})}")
    print("\nDerivation complete!")


if __name__ == "__main__":
    derive()
