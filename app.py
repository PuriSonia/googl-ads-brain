import os
import json
from typing import Dict, Any

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

from persuasion_engine import build_institutional_assets, build_psychology_map
from feedback_loop import FeedbackStore, build_learning_prompt_context

load_dotenv()

app = Flask(__name__)


POSITIONING = {
    "platform": "Carbon Risk Intelligence Platform",
    "core_line": "We don’t rate carbon credits — we model whether they will actually deliver.",
    "problem": "Investors and corporates deploy capital into carbon projects without a reliable way to assess delivery, issuance and integrity risk.",
    "solution": "Explainable AI messaging that frames carbon risk clearly for institutional buyers.",
    "pain_points": [
        "Projects that never issue credits",
        "Issuance delays",
        "Integrity failure",
        "Greenwashing exposure",
        "Difficulty pricing risk",
        "Poor project transparency",
    ],
}


def build_prompt(payload: Dict[str, Any]) -> str:
    psychology = build_psychology_map(payload)
    learning = build_learning_prompt_context(payload.get("audience"))

    return f"""
You are an expert B2B Google Ads strategist for an institutional Carbon Risk Intelligence Platform.

Positioning:
{json.dumps(POSITIONING, indent=2)}

Buyer psychology:
{json.dumps(psychology, indent=2)}

Feedback-loop learning context:
{json.dumps(learning, indent=2)}

Campaign brief:
{json.dumps(payload, indent=2)}

Return strict JSON only with this structure:
{{
  "headlines": [],
  "descriptions": [],
  "keywords": [],
  "negative_keywords": [],
  "cta_options": [],
  "ad_angles": [],
  "landing_page_hero_headlines": [],
  "psychology_map": {{}},
  "compliance_notes": []
}}

Rules:
- Headlines should be concise and Google Ads friendly.
- Descriptions should be direct and institutional.
- Avoid guarantees, hype, exaggerated claims, financial promises, or certification claims.
- Prefer language around delivery risk, integrity risk, institutional diligence, explainability and capital exposure.
""".strip()


def generate_with_openai(payload: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "Return valid JSON only. No markdown."},
            {"role": "user", "content": build_prompt(payload)},
        ],
        temperature=0.7,
    )

    text = response.choices[0].message.content.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "raw_output": text,
            "warning": "OpenAI returned text that was not valid JSON."
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "status": "ok",
        "message": "Google Ads Brain full app running",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "endpoints": [
            "/api/generate",
            "/api/generate-improved",
            "/api/psychology",
            "/api/persuasion-assets",
            "/api/feedback/log",
            "/api/feedback/analyse",
        ],
    })


@app.route("/api/generate", methods=["POST"])
def api_generate():
    payload = request.get_json(silent=True) or {}

    try:
        result = generate_with_openai(payload)
        result["source"] = "openai"
    except Exception as exc:
        result = build_institutional_assets(payload)
        result["source"] = "fallback_rules"
        result["openai_error"] = str(exc)

    return jsonify(result)


@app.route("/api/generate-improved", methods=["POST"])
def api_generate_improved():
    payload = request.get_json(silent=True) or {}
    payload["feedback_loop_guidance"] = build_learning_prompt_context(payload.get("audience"))

    try:
        result = generate_with_openai(payload)
        result["source"] = "openai_with_feedback_loop"
    except Exception as exc:
        result = build_institutional_assets(payload)
        result["source"] = "fallback_rules_with_feedback"
        result["openai_error"] = str(exc)

    return jsonify(result)


@app.route("/api/psychology", methods=["POST"])
def api_psychology():
    payload = request.get_json(silent=True) or {}
    return jsonify(build_psychology_map(payload))


@app.route("/api/persuasion-assets", methods=["POST"])
def api_persuasion_assets():
    payload = request.get_json(silent=True) or {}
    return jsonify(build_institutional_assets(payload))


@app.route("/api/feedback/log", methods=["POST"])
def api_feedback_log():
    payload = request.get_json(silent=True) or {}
    return jsonify(FeedbackStore().log_result(payload))


@app.route("/api/feedback/analyse", methods=["GET", "POST"])
def api_feedback_analyse():
    payload = request.get_json(silent=True) or {} if request.method == "POST" else {}
    audience = payload.get("audience") or request.args.get("audience")
    return jsonify(FeedbackStore().analyse(audience=audience))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True,
    )
