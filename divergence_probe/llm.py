"""
Optional LLM enrichment for divergence-probe.

Excluded from CI — the rule-based engine in core.py is the shipped product.

Install extras before use:
    pip install "divergence-probe[openai]"
    pip install "divergence-probe[anthropic]"
    pip install "divergence-probe[gemini]"

Trigger via CLI:
    dp scan transcript.txt --llm-backend openai
"""
from __future__ import annotations

import json
from typing import Optional

from .models import DivergenceGap, DivergenceReport, GapType, Severity

_ENRICH_PROMPT = """\
You are an expert UX researcher specialising in behavioural divergence analysis.

A "divergence" occurs when a participant's habitual self-report ("I always do X")
contradicts their account of actual behaviour ("I didn't do X last Tuesday").

Analyse this candidate divergence from a user research transcript:

HABITUAL CLAIM: {say}
EPISODIC REPORT: {do}

Rule-based classification: {gap_type} ({severity} severity)
Rule-based explanation:    {explanation}

Respond ONLY with a valid JSON object — no preamble, no markdown fences:
{{
  "is_genuine_gap": true,
  "refined_explanation": "...",
  "severity": "high | medium | low",
  "probe": "A natural follow-up question the researcher could ask",
  "context_note": "Any contextual nuance that might explain the divergence legitimately"
}}
"""


def _enrich_openai(gap: DivergenceGap, client, model: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": _ENRICH_PROMPT.format(
            say=gap.say_statement.text, do=gap.do_statement.text,
            gap_type=gap.gap_type.value, severity=gap.severity.value,
            explanation=gap.explanation,
        )}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content)


def _enrich_anthropic(gap: DivergenceGap, client, model: str) -> dict:
    response = client.messages.create(
        model=model, max_tokens=512, temperature=0.2,
        messages=[{"role": "user", "content": _ENRICH_PROMPT.format(
            say=gap.say_statement.text, do=gap.do_statement.text,
            gap_type=gap.gap_type.value, severity=gap.severity.value,
            explanation=gap.explanation,
        )}],
    )
    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def _enrich_gemini(gap: DivergenceGap, client, model: str) -> dict:
    response = client.models.generate_content(
        model=model,
        contents=_ENRICH_PROMPT.format(
            say=gap.say_statement.text, do=gap.do_statement.text,
            gap_type=gap.gap_type.value, severity=gap.severity.value,
            explanation=gap.explanation,
        ),
    )
    raw = response.text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def enrich_report(
    report: DivergenceReport,
    backend: str = "openai",
    top_n: int = 5,
    model: Optional[str] = None,
) -> DivergenceReport:
    """
    Enrich the top-N high-confidence divergences with LLM analysis.

    Args:
        report:   Output from detect_gaps / detect_gaps_from_file.
        backend:  One of "openai", "anthropic", "gemini".
        top_n:    Maximum gaps to enrich (most confident first).
        model:    Override the default model string.

    Returns:
        The same DivergenceReport with enriched fields (mutated in-place).
    """
    _DEFAULTS = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-6",
        "gemini": "gemini-3.6-flash",
    }

    if backend not in _DEFAULTS:
        raise ValueError(
            f"Unknown backend: '{backend}'. Choose: openai, anthropic, gemini"
        )

    effective_model = model or _DEFAULTS[backend]
    candidates = [
        g for g in report.gaps
        if g.gap_type in (GapType.CONTRADICTION, GapType.PARTIAL)
    ][:top_n]

    if not candidates:
        return report

    if backend == "openai":
        from openai import OpenAI
        client = OpenAI()
        enrich_fn = lambda gap: _enrich_openai(gap, client, effective_model)
    elif backend == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        enrich_fn = lambda gap: _enrich_anthropic(gap, client, effective_model)
    else:
        from google import genai
        client = genai.Client()
        enrich_fn = lambda gap: _enrich_gemini(gap, client, effective_model)

    for gap in candidates:
        try:
            result = enrich_fn(gap)
            if result.get("refined_explanation"):
                gap.explanation = result["refined_explanation"]
            if result.get("probe"):
                gap.suggested_probe = result["probe"]
            llm_sev = result.get("severity", "").lower()
            if llm_sev in ("high", "medium", "low"):
                gap.severity = Severity(llm_sev)
            gap.llm_enriched = True
        except Exception as exc:  # noqa: BLE001
            gap.explanation += f" [LLM enrichment skipped: {exc}]"

    return report
