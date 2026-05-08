from __future__ import annotations

import json
import os
import re
import sqlite3

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_DB_PATH = os.getenv("PERSUASION_DB_PATH", "persuasion_feedback.db")

TRUST_TERMS = [
    "risk", "intelligence", "explainable", "institutional", "diligence",
    "integrity", "delivery", "issuance", "portfolio", "capital", "evidence",
]
HYPE_TERMS = [
    "revolutionary", "guaranteed", "best", "100%", "massive", "instant",
    "unbeatable", "secret", "easy money", "no risk",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def extract_terms(text: str) -> List[str]:
    clean = normalise_text(text)
    terms: List[str] = []

    for term in TRUST_TERMS + HYPE_TERMS:
        if term in clean:
            terms.append(term)

    phrase_patterns = [
        r"delivery risk",
        r"integrity risk",
        r"capital exposure",
        r"risk intelligence",
        r"carbon project",
        r"project risk",
        r"explainable ai",
        r"investment committee",
        r"hidden risk",
        r"before investment",
        r"before capital",
    ]

    for pattern in phrase_patterns:
        if re.search(pattern, clean):
            terms.append(pattern)

    return sorted(set(terms))


@dataclass
class PerformanceScore:
    score: float
    components: Dict[str, float]
    interpretation: str


def score_performance(metrics: Dict[str, Any]) -> PerformanceScore:
    impressions = max(float(metrics.get("impressions") or 0), 0)
    clicks = max(float(metrics.get("clicks") or 0), 0)
    conversions = max(float(metrics.get("conversions") or 0), 0)
    signups = max(float(metrics.get("signups") or 0), 0)
    demo_bookings = max(float(metrics.get("demo_bookings") or 0), 0)
    bounce_rate = float(metrics.get("bounce_rate") or 0)
    engagement_rate = float(metrics.get("engagement_rate") or 0)

    lead_quality_raw = metrics.get("lead_quality")
    lead_quality = float(lead_quality_raw) / 10 if lead_quality_raw is not None else 0

    ctr = float(metrics.get("ctr") or (clicks / impressions if impressions else 0))
    conversion_rate = float(metrics.get("conversion_rate") or (conversions / clicks if clicks else 0))
    signup_rate = float(signups / clicks) if clicks else 0
    demo_rate = float(demo_bookings / clicks) if clicks else 0

    raw = (
        min(ctr, 0.15) / 0.15 * 20
        + min(conversion_rate, 0.20) / 0.20 * 30
        + min(demo_rate, 0.10) / 0.10 * 20
        + min(signup_rate, 0.20) / 0.20 * 10
        + min(engagement_rate, 1.0) * 10
        + min(lead_quality, 1.0) * 15
        - min(bounce_rate, 1.0) * 10
    )

    score = round(max(0, min(100, raw)), 2)

    if score >= 70:
        interpretation = "winner"
    elif score >= 45:
        interpretation = "promising"
    elif score >= 25:
        interpretation = "weak"
    else:
        interpretation = "loser"

    return PerformanceScore(
        score=score,
        components={
            "ctr": round(ctr, 4),
            "conversion_rate": round(conversion_rate, 4),
            "signup_rate": round(signup_rate, 4),
            "demo_rate": round(demo_rate, 4),
            "engagement_rate": round(engagement_rate, 4),
            "lead_quality_normalised": round(lead_quality, 4),
            "bounce_rate": round(bounce_rate, 4),
        },
        interpretation=interpretation,
    )


class FeedbackStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ad_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    campaign_id TEXT,
                    ad_id TEXT,
                    audience TEXT,
                    angle TEXT,
                    headline TEXT,
                    description TEXT,
                    cta TEXT,
                    landing_page_url TEXT,
                    metrics_json TEXT NOT NULL,
                    score REAL NOT NULL,
                    score_components_json TEXT NOT NULL,
                    interpretation TEXT NOT NULL,
                    terms_json TEXT NOT NULL,
                    notes TEXT
                )
                """
            )
            conn.commit()

    def log_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        metrics = payload.get("metrics") or {}
        scored = score_performance(metrics)

        headline = payload.get("headline", "")
        description = payload.get("description", "")
        terms = extract_terms(
            " ".join([
                headline,
                description,
                payload.get("angle", ""),
                payload.get("cta", ""),
            ])
        )

        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO ad_feedback (
                    created_at, campaign_id, ad_id, audience, angle,
                    headline, description, cta, landing_page_url,
                    metrics_json, score, score_components_json,
                    interpretation, terms_json, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utc_now(),
                    payload.get("campaign_id"),
                    payload.get("ad_id"),
                    payload.get("audience"),
                    payload.get("angle"),
                    headline,
                    description,
                    payload.get("cta"),
                    payload.get("landing_page_url"),
                    json.dumps(metrics),
                    scored.score,
                    json.dumps(scored.components),
                    scored.interpretation,
                    json.dumps(terms),
                    payload.get("notes"),
                ),
            )
            conn.commit()
            row_id = cur.lastrowid

        return {
            "id": row_id,
            "score": scored.score,
            "interpretation": scored.interpretation,
            "score_components": scored.components,
            "terms_detected": terms,
        }

    def list_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ad_feedback ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def analyse(self, audience: Optional[str] = None) -> Dict[str, Any]:
        rows = self.list_results(500)

        if audience:
            audience_clean = normalise_text(audience)
            rows = [
                row for row in rows
                if audience_clean in normalise_text(row.get("audience", ""))
            ]

        if not rows:
            return {
                "status": "no_data_yet",
                "message": "Log campaign performance first, then the learning loop can identify winning wording.",
                "recommended_next_test": [
                    "risk intelligence vs AI-powered platform",
                    "delivery risk vs ESG analytics",
                    "capital exposure vs sustainability insights",
                ],
            }

        winners = [r for r in rows if r["score"] >= 70]
        losers = [r for r in rows if r["score"] < 25]
        promising = [r for r in rows if 45 <= r["score"] < 70]

        term_scores: Dict[str, List[float]] = {}
        angle_scores: Dict[str, List[float]] = {}

        for row in rows:
            for term in row.get("terms", []):
                term_scores.setdefault(term, []).append(row["score"])
            if row.get("angle"):
                angle_scores.setdefault(row["angle"], []).append(row["score"])

        def average(items: Iterable[float]) -> float:
            vals = list(items)
            return round(sum(vals) / len(vals), 2) if vals else 0

        winning_terms = sorted(
            [{"term": k, "avg_score": average(v), "samples": len(v)} for k, v in term_scores.items()],
            key=lambda x: (x["avg_score"], x["samples"]),
            reverse=True,
        )[:10]

        weak_terms = sorted(
            [{"term": k, "avg_score": average(v), "samples": len(v)} for k, v in term_scores.items()],
            key=lambda x: (x["avg_score"], -x["samples"]),
        )[:10]

        winning_angles = sorted(
            [{"angle": k, "avg_score": average(v), "samples": len(v)} for k, v in angle_scores.items()],
            key=lambda x: (x["avg_score"], x["samples"]),
            reverse=True,
        )[:5]

        return {
            "status": "ok",
            "sample_count": len(rows),
            "winner_count": len(winners),
            "promising_count": len(promising),
            "loser_count": len(losers),
            "average_score": average([r["score"] for r in rows]),
            "winning_terms": winning_terms,
            "weak_terms": weak_terms,
            "winning_angles": winning_angles,
            "best_ads": rows_sorted(rows, reverse=True)[:5],
            "worst_ads": rows_sorted(rows, reverse=False)[:5],
            "next_generation_guidance": build_generation_guidance(winning_terms, weak_terms, winning_angles),
        }

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "campaign_id": row["campaign_id"],
            "ad_id": row["ad_id"],
            "audience": row["audience"],
            "angle": row["angle"],
            "headline": row["headline"],
            "description": row["description"],
            "cta": row["cta"],
            "landing_page_url": row["landing_page_url"],
            "metrics": json.loads(row["metrics_json"]),
            "score": row["score"],
            "score_components": json.loads(row["score_components_json"]),
            "interpretation": row["interpretation"],
            "terms": json.loads(row["terms_json"]),
            "notes": row["notes"],
        }


def rows_sorted(rows: List[Dict[str, Any]], reverse: bool) -> List[Dict[str, Any]]:
    compact = []

    for row in rows:
        compact.append({
            "score": row["score"],
            "interpretation": row["interpretation"],
            "audience": row.get("audience"),
            "angle": row.get("angle"),
            "headline": row.get("headline"),
            "description": row.get("description"),
            "metrics": row.get("metrics"),
            "terms": row.get("terms"),
        })

    return sorted(compact, key=lambda x: x["score"], reverse=reverse)


def build_generation_guidance(
    winning_terms: List[Dict[str, Any]],
    weak_terms: List[Dict[str, Any]],
    winning_angles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    use_more = [x["term"] for x in winning_terms[:5] if x["avg_score"] >= 45]
    use_less = [x["term"] for x in weak_terms[:5] if x["avg_score"] < 35]
    angles = [x["angle"] for x in winning_angles[:3]]

    return {
        "use_more_of": use_more or ["risk intelligence", "delivery risk", "institutional diligence"],
        "use_less_of": use_less or ["generic AI claims", "hype language", "guarantees"],
        "prioritise_angles": angles or ["capital protection", "delivery risk", "integrity risk"],
        "prompt_instruction": (
            "Generate the next ads using proven terms and angles. Avoid weak terms, hype, "
            "guarantees, and generic AI positioning. Prefer institutional, risk-led wording."
        ),
    }


def build_learning_prompt_context(audience: Optional[str] = None) -> Dict[str, Any]:
    analysis = FeedbackStore().analyse(audience)

    if analysis.get("status") != "ok":
        return {
            "status": "no_feedback_yet",
            "guidance": [
                "Prefer institutional trust language.",
                "Avoid hype claims.",
                "Lead with financial risk and delivery risk.",
            ],
        }

    return {
        "status": "feedback_available",
        "winning_terms": analysis.get("winning_terms", []),
        "weak_terms": analysis.get("weak_terms", []),
        "winning_angles": analysis.get("winning_angles", []),
        "next_generation_guidance": analysis.get("next_generation_guidance", {}),
    }
