"""Scheduled job functions for the daily pipeline.

Each function is designed to be called by APScheduler. Sync functions run
in ThreadPoolExecutor; async functions run on the event loop directly.
"""
import logging

logger = logging.getLogger("scheduler.jobs")


# ── Phase 1: Trade data agents (sync, safe to run in parallel) ──────


def job_fetch_eurostat() -> dict:
    from app.agents.eurostat_agent import EurostatAgent
    from app.database import get_sync_db

    db = get_sync_db()
    agent = EurostatAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        logger.info(f"[scheduler] Eurostat: {count} records")
        return {"source": "eurostat", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("[scheduler] Eurostat failed")
        return {"source": "eurostat", "status": "error", "message": str(exc)}


def job_fetch_comtrade() -> dict:
    from app.agents.comtrade_agent import ComtradeAgent
    from app.database import get_sync_db

    db = get_sync_db()
    agent = ComtradeAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        logger.info(f"[scheduler] Comtrade: {count} records")
        return {"source": "comtrade", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("[scheduler] Comtrade failed")
        return {"source": "comtrade", "status": "error", "message": str(exc)}


def job_fetch_federal_register() -> dict:
    from app.agents.federal_register_agent import FederalRegisterAgent
    from app.database import get_sync_db

    db = get_sync_db()
    agent = FederalRegisterAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        logger.info(f"[scheduler] FederalRegister: {count} records")
        return {"source": "federal_register", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("[scheduler] FederalRegister failed")
        return {"source": "federal_register", "status": "error", "message": str(exc)}


def job_fetch_otexa() -> dict:
    from app.agents.otexa_agent import OtexaAgent
    from app.database import get_sync_db

    db = get_sync_db()
    agent = OtexaAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        logger.info(f"[scheduler] OTEXA: {count} records")
        return {"source": "otexa", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("[scheduler] OTEXA failed")
        return {"source": "otexa", "status": "error", "message": str(exc)}


# ── Phase 2: News agent (sync) ─────────────────────────────────────


def job_fetch_news() -> dict:
    from app.agents.general_watcher import GeneralWatcher
    from app.database import get_sync_db

    db = get_sync_db()
    agent = GeneralWatcher(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        logger.info(f"[scheduler] GeneralWatcher: {count} articles")
        return {"source": "openai_search", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("[scheduler] GeneralWatcher failed")
        return {"source": "openai_search", "status": "error", "message": str(exc)}


# ── Phase 3: Market research agent (sync) ──────────────────────────


def job_fetch_market_research() -> dict:
    from app.agents.market_research_agent import MarketResearchAgent
    from app.database import get_sync_db

    db = get_sync_db()
    agent = MarketResearchAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        logger.info(f"[scheduler] MarketResearch: {count} records")
        return {"source": "market_research_agent", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("[scheduler] MarketResearch failed")
        return {"source": "market_research_agent", "status": "error", "message": str(exc)}


# ── Phase 4: Derive market data (sync) ─────────────────────────────


def job_derive_market_data() -> dict:
    """Re-derive market_segments and market_size_series from trade_data."""
    from app.agents.constants import HS_CHAPTER_DESCRIPTIONS_FR, TEXTILE_HS_CHAPTERS
    from app.database import get_sync_db
    from app.models.market_research import new_market_size_doc, new_segment_doc

    db = get_sync_db()
    seg_count = 0
    size_count = 0

    # Seed segments for HS chapters
    for chapter in TEXTILE_HS_CHAPTERS:
        label_fr = HS_CHAPTER_DESCRIPTIONS_FR.get(chapter, f"Chapitre {chapter}")
        if not db.market_segments.find_one({"axis": "hs_chapter", "code": chapter}):
            doc = new_segment_doc(
                axis="hs_chapter", code=chapter,
                label_fr=label_fr, label_en=f"Chapter {chapter}",
                description_fr=f"Chapitre SH {chapter} — {label_fr}",
            )
            db.market_segments.insert_one(doc)
            seg_count += 1

    # Aggregate segments
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
        if not db.market_segments.find_one({"axis": axis, "code": code}):
            doc = new_segment_doc(axis=axis, code=code, label_fr=label_fr, label_en=label_en)
            db.market_segments.insert_one(doc)
            seg_count += 1

    # Derive market_size_series by year/chapter/flow
    pipeline = [
        {"$group": {
            "_id": {"year": {"$year": "$period_date"}, "chapter": {"$substr": ["$hs_code", 0, 2]}, "flow": "$flow"},
            "total_value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
        }},
        {"$sort": {"_id.year": 1, "_id.chapter": 1}},
    ]
    for r in db.trade_data.aggregate(pipeline):
        year = r["_id"]["year"]
        chapter = r["_id"]["chapter"]
        flow = r["_id"]["flow"] or "total"
        if not chapter or chapter in ("TO", "SI", ""):
            continue
        if not db.market_size_series.find_one(
            {"segment_code": chapter, "geography_code": "MA", "year": year, "flow": flow}
        ):
            doc = new_market_size_doc(
                segment_code=chapter, geography_code="MA",
                year=year, value_usd=r["total_value"],
                source="derived_from_trade_data", flow=flow,
            )
            try:
                db.market_size_series.insert_one(doc)
                size_count += 1
            except Exception:
                pass

    # Total market size per year
    total_pipeline = [
        {"$group": {
            "_id": {"year": {"$year": "$period_date"}, "flow": "$flow"},
            "total_value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
        }},
        {"$sort": {"_id.year": 1}},
    ]
    for r in db.trade_data.aggregate(total_pipeline):
        year = r["_id"]["year"]
        flow = r["_id"]["flow"] or "total"
        if not db.market_size_series.find_one(
            {"segment_code": "ALL", "geography_code": "MA", "year": year, "flow": flow}
        ):
            doc = new_market_size_doc(
                segment_code="ALL", geography_code="MA",
                year=year, value_usd=r["total_value"],
                source="derived_from_trade_data", flow=flow,
            )
            try:
                db.market_size_series.insert_one(doc)
                size_count += 1
            except Exception:
                pass

    logger.info(f"[scheduler] Derive: {seg_count} segments, {size_count} market size entries")
    return {"segments_created": seg_count, "size_entries_created": size_count, "status": "success"}


# ── Phase 5: Framework generation (ASYNC) ──────────────────────────


async def job_generate_frameworks() -> dict:
    """Generate all 3 frameworks, forcing cache refresh."""
    from app.database import get_async_db
    from app.services.market_research_service import generate_framework

    db = get_async_db()
    results = {}

    for fw_type in ("porter", "pestel", "tam_sam_som"):
        try:
            # Delete cached results to force regeneration
            await db.framework_results.delete_many({"framework_type": fw_type})
            result = await generate_framework(db, fw_type)
            results[fw_type] = "success"
            logger.info(f"[scheduler] Framework {fw_type}: generated successfully")
        except Exception as exc:
            results[fw_type] = f"error: {exc}"
            logger.exception(f"[scheduler] Framework {fw_type} failed")

    return results


# ── Phase 6: Reset daily counters (sync) ───────────────────────────


def job_reset_daily_counters() -> dict:
    from app.database import get_sync_db

    db = get_sync_db()
    db.data_source_status.update_many(
        {}, {"$set": {"records_fetched_today": 0, "api_calls_today": 0}}
    )
    logger.info("[scheduler] Daily counters reset")
    return {"status": "counters_reset"}
