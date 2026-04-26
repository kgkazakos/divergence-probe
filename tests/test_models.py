"""Tests for data models."""
from divergence_probe.models import (
    DivergenceGap,
    DivergenceReport,
    GapType,
    Severity,
    Statement,
)


def _make_statement(text: str, stmt_type: str = "say", polarity: str = "positive") -> Statement:
    return Statement(
        text=text, statement_type=stmt_type, speaker="P1",
        sentence_idx=0, line_no=1, polarity=polarity,
        keywords=["email", "morning"],
    )


def _make_gap(gap_type: GapType = GapType.CONTRADICTION, severity: Severity = Severity.HIGH) -> DivergenceGap:
    say = _make_statement("I always check emails first thing.", "say", "positive")
    do = _make_statement("I didn't check emails until noon.", "do", "negative")
    return DivergenceGap(
        say_statement=say, do_statement=do,
        gap_type=gap_type, severity=severity,
        confidence=0.8, topic_overlap_score=0.4,
        explanation="Test divergence.",
        suggested_probe="Can you walk me through what happened?",
    )


class TestGapType:
    def test_values(self):
        assert GapType.CONTRADICTION.value == "contradiction"
        assert GapType.PARTIAL.value == "partial"
        assert GapType.UNCERTAIN.value == "uncertain"


class TestSeverity:
    def test_values(self):
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"


class TestStatement:
    def test_creation(self):
        stmt = _make_statement("I always do X.")
        assert stmt.text == "I always do X."
        assert stmt.statement_type == "say"
        assert stmt.speaker == "P1"

    def test_keywords_default(self):
        stmt = Statement(
            text="test", statement_type="say", speaker=None,
            sentence_idx=0, line_no=1, polarity="neutral",
        )
        assert stmt.keywords == []


class TestDivergenceGap:
    def test_creation(self):
        gap = _make_gap()
        assert gap.gap_type == GapType.CONTRADICTION
        assert gap.severity == Severity.HIGH
        assert gap.confidence == 0.8
        assert not gap.llm_enriched

    def test_llm_enriched_default_false(self):
        gap = _make_gap()
        assert gap.llm_enriched is False


class TestDivergenceReport:
    def _make_report(self, gaps=None):
        return DivergenceReport(
            source_file="test.txt", total_sentences=20,
            say_count=5, do_count=5, gaps=gaps or [],
        )

    def test_empty_report(self):
        r = self._make_report()
        assert r.contradiction_count == 0
        assert r.partial_count == 0
        assert r.high_severity_count == 0
        assert r.gap_rate == 0.0

    def test_counts(self):
        gaps = [
            _make_gap(GapType.CONTRADICTION, Severity.HIGH),
            _make_gap(GapType.CONTRADICTION, Severity.MEDIUM),
            _make_gap(GapType.PARTIAL, Severity.LOW),
        ]
        r = self._make_report(gaps=gaps)
        assert r.contradiction_count == 2
        assert r.partial_count == 1
        assert r.high_severity_count == 1

    def test_gap_rate(self):
        gaps = [_make_gap() for _ in range(2)]
        r = self._make_report(gaps=gaps)
        assert r.gap_rate == 2 / 5

    def test_gap_rate_zero_say(self):
        r = DivergenceReport(
            source_file="empty.txt", total_sentences=5, say_count=0, do_count=0,
        )
        assert r.gap_rate == 0.0
