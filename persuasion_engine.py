from typing import Any, Dict


def build_psychology_map(payload: Dict[str, Any]) -> Dict[str, Any]:
    audience = payload.get("audience") or "institutional carbon buyers"

    return {
        "audience": audience,
        "primary_fears": [
            "hidden project delivery failure",
            "capital committed to weak carbon projects",
            "greenwashing or reputational exposure",
            "poor diligence evidence",
            "issuance delays and under-delivery",
        ],
        "trust_drivers": [
            "explainable scoring",
            "institutional tone",
            "risk-led evidence",
            "clear drivers behind outputs",
            "measured claims rather than hype",
        ],
        "persuasion_strategy": [
            "lead with expensive risk",
            "frame cost of inaction",
            "show diligence value",
            "avoid guaranteed outcomes",
            "make next step low friction",
        ],
    }


def build_institutional_assets(payload: Dict[str, Any]) -> Dict[str, Any]:
    audience = payload.get("audience") or "institutional carbon investors"
    offer = payload.get("offer") or "carbon risk intelligence"

    return {
        "headlines": [
            "Detect Carbon Project Risk",
            "Assess Delivery Risk",
            "Carbon Risk Intelligence",
            "Explainable ESG Scoring",
            "Know Risk Before Capital",
            "Evaluate Carbon Integrity",
            "Model Issuance Risk",
            "Institutional ESG Insight",
            "Climate Project Diligence",
            "Carbon Buyer Intelligence",
            "Reduce Diligence Blind Spots",
            "Analyse One Project",
            "Project Risk Before Invest",
            "Carbon Integrity Signals",
            "Risk-Led ESG Messaging",
        ],
        "descriptions": [
            "Assess delivery, issuance and integrity risk before committing capital.",
            "Explainable carbon project intelligence for investors and ESG teams.",
            "Identify hidden project risks and improve institutional diligence.",
            "Generate risk-led messaging for carbon buyers and climate finance teams.",
            "Avoid hype. Use direct, credible, institutional carbon-risk language.",
            "Turn ESG positioning into clear Google Ads and landing-page messaging.",
            "Learn which wording earns trust, clicks and demo interest over time.",
            "Use buyer psychology to frame carbon risk clearly and professionally.",
        ],
        "keywords": [
            "carbon project risk",
            "carbon credit risk",
            "carbon due diligence",
            "carbon investment risk",
            "carbon credit integrity",
            "carbon project analysis",
            "carbon credit issuance risk",
            "carbon offset risk",
            "voluntary carbon market risk",
            "ESG investment risk",
            "climate investment due diligence",
            "carbon project delivery",
            "carbon risk intelligence",
            "ESG risk platform",
            "climate finance risk",
        ],
        "negative_keywords": [
            "free",
            "jobs",
            "course",
            "training",
            "definition",
            "calculator",
            "cheap",
            "carbon monoxide",
            "credit card",
            "personal loan",
        ],
        "cta_options": [
            "Analyse One Project",
            "Book a Risk Demo",
            "Review Portfolio Risk",
            "See Risk Drivers",
            "Generate Ads",
        ],
        "ad_angles": [
            f"Financial risk framing for {audience}",
            "Delivery and issuance risk before capital exposure",
            "Integrity and greenwashing risk protection",
            "Explainable diligence and institutional trust",
            f"Offer-led positioning around {offer}",
        ],
        "landing_page_hero_headlines": [
            "Know if carbon projects can deliver before capital is committed.",
            "Explainable carbon risk intelligence for serious institutional buyers.",
            "Turn carbon project uncertainty into decision-ready risk insight.",
        ],
        "psychology_map": build_psychology_map(payload),
        "compliance_notes": [
            "Do not claim guaranteed returns.",
            "Do not claim guaranteed project delivery.",
            "Avoid saying the platform certifies carbon credits.",
            "Use assess, model, analyse and identify rather than prove or guarantee.",
            "Make clear outputs support diligence and marketing judgement.",
        ],
    }
