"""
Rule-based divergence detection engine for divergence-probe.

Zero external dependencies. Runs fully offline with no API calls required.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .models import DivergenceGap, DivergenceReport, GapType, Severity, Statement
from .patterns import DO_PATTERNS, NEGATIVE_MARKERS, POSITIVE_MARKERS, SAY_PATTERNS, STOPWORDS


def _detect_polarity(text: str) -> str:
    lower = text.lower()
    neg = sum(1 for m in NEGATIVE_MARKERS if m in lower)
    pos = sum(1 for m in POSITIVE_MARKERS if m in lower)
    if neg > pos:
        return "negative"
    if pos > neg:
        return "positive"
    return "neutral"


def _extract_keywords(text: str) -> list:
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    return [w for w in words if w not in STOPWORDS]


def _is_say(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in SAY_PATTERNS)


def _is_do(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in DO_PATTERNS)


def _topic_overlap(kw1: list, kw2: list) -> float:
    if not kw1 or not kw2:
        return 0.0
    s1, s2 = set(kw1), set(kw2)
    union = s1 | s2
    return len(s1 & s2) / len(union) if union else 0.0


def _classify_gap(say_stmt: Statement, do_stmt: Statement, overlap: float) -> tuple:
    say_pol, do_pol = say_stmt.polarity, do_stmt.polarity

    if (say_pol == "positive" and do_pol == "negative") or (
        say_pol == "negative" and do_pol == "positive"
    ):
        gap_type = GapType.CONTRADICTION
        severity = Severity.HIGH if overlap > 0.25 else Severity.MEDIUM
        confidence = min(0.92, 0.55 + overlap)
        say_exc = say_stmt.text[:70]
        do_exc = do_stmt.text[:70]
        if say_pol == "positive":
            explanation = (
                "Participant claims to regularly perform this behaviour "
                f'("{say_exc}") but their reported episode contradicts this ("{do_exc}").'
            )
        else:
            explanation = (
                "Participant claims to avoid this behaviour "
                f'("{say_exc}") but a reported episode suggests otherwise ("{do_exc}").'
            )
    elif overlap > 0.12:
        gap_type = GapType.PARTIAL
        severity = Severity.MEDIUM if overlap > 0.25 else Severity.LOW
        confidence = 0.30 + overlap
        explanation = (
            "Possible divergence — the stated intent and the reported "
            "behaviour share a common topic but differ in framing."
        )
    else:
        gap_type = GapType.UNCERTAIN
        severity = Severity.LOW
        confidence = 0.18
        explanation = (
            "Weak topical overlap. May not represent a genuine divergence; "
            "worth a light probe to clarify."
        )

    return gap_type, severity, min(confidence, 1.0), explanation


def _generate_probe(gap: DivergenceGap) -> str:
    say_exc = gap.say_statement.text[:55].rstrip(".").strip()
    do_exc = gap.do_statement.text[:55].rstrip(".").strip()
    if gap.gap_type == GapType.CONTRADICTION:
        return (
            f'You mentioned earlier that you "{say_exc.lower()}" — '
            f'but you also said "{do_exc.lower()}". '
            "Can you help me understand what typically happens in practice?"
        )
    return (
        f'I noticed you said "{say_exc}" and also "{do_exc}". '
        "Could you walk me through a recent example of how that plays out?"
    )


def _parse_transcript(text: str) -> list:
    lines = text.strip().splitlines()
    results = []
    current_speaker: Optional[str] = None
    speaker_re = re.compile(
        r"^(?:\[([^\]]+)\]|([A-Za-z][A-Za-z0-9 _\-]{0,30}?):\s*)(.+)$"
    )
    for line_no, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        m = speaker_re.match(line)
        if m:
            current_speaker = (m.group(1) or m.group(2) or "").strip() or None
            text_part = m.group(3).strip()
        else:
            text_part = line
        for sent in re.split(r"(?<=[.!?])\s+", text_part):
            sent = sent.strip()
            if len(sent) > 8:
                results.append((current_speaker, sent, line_no))
    return results


def detect_gaps(
    transcript_text: str,
    source_file: str = "transcript",
    min_overlap: float = 0.05,
    min_confidence: float = 0.30,
    max_window: int = 60,
) -> DivergenceReport:
    """
    Detect habitual-claim vs episodic-report divergences in a transcript string.

    Fully rule-based — no API calls required.
    """
    parsed = _parse_transcript(transcript_text)
    say_stmts: list = []
    do_stmts: list = []

    for idx, (speaker, text, line_no) in enumerate(parsed):
        kw = _extract_keywords(text)
        pol = _detect_polarity(text)
        is_s = _is_say(text)
        is_d = _is_do(text)
        stmt = Statement(
            text=text,
            statement_type="say" if is_s else "do",
            speaker=speaker,
            sentence_idx=idx,
            line_no=line_no,
            polarity=pol,
            keywords=kw,
        )
        if is_s:
            say_stmts.append(stmt)
        if is_d:
            do_stmts.append(stmt)

    raw_gaps: list = []
    seen_pairs: set = set()

    for say in say_stmts:
        for do in do_stmts:
            pair_key = (say.sentence_idx, do.sentence_idx)
            if pair_key in seen_pairs:
                continue
            if abs(say.sentence_idx - do.sentence_idx) > max_window:
                continue
            overlap = _topic_overlap(say.keywords, do.keywords)
            if overlap < min_overlap:
                continue
            gap_type, severity, confidence, explanation = _classify_gap(say, do, overlap)
            if confidence < min_confidence:
                continue
            gap = DivergenceGap(
                say_statement=say,
                do_statement=do,
                gap_type=gap_type,
                severity=severity,
                confidence=confidence,
                topic_overlap_score=overlap,
                explanation=explanation,
            )
            gap.suggested_probe = _generate_probe(gap)
            raw_gaps.append(gap)
            seen_pairs.add(pair_key)

    raw_gaps.sort(key=lambda g: g.confidence, reverse=True)

    deduped: list = []
    seen_say_idx: set = set()
    for g in raw_gaps:
        if g.say_statement.sentence_idx not in seen_say_idx:
            deduped.append(g)
            seen_say_idx.add(g.say_statement.sentence_idx)

    return DivergenceReport(
        source_file=source_file,
        total_sentences=len(parsed),
        say_count=len(say_stmts),
        do_count=len(do_stmts),
        gaps=deduped,
    )


def detect_gaps_from_file(path: Path, **kwargs) -> DivergenceReport:
    """Convenience wrapper — reads a transcript file and calls detect_gaps."""
    return detect_gaps(path.read_text(encoding="utf-8"), source_file=path.name, **kwargs)
