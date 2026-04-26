"""Tests for the core detection engine."""
from pathlib import Path

from divergence_probe.core import (
    _detect_polarity,
    _extract_keywords,
    _is_do,
    _is_say,
    _parse_transcript,
    _topic_overlap,
    detect_gaps,
    detect_gaps_from_file,
)
from divergence_probe.models import GapType

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class TestPatternTagging:
    """_is_say / _is_do pattern detection."""

    import pytest

    @__import__("pytest").mark.parametrize("text", [
        "I always check my emails first thing.",
        "I usually try to respond within an hour.",
        "I tend to write notes straight after meetings.",
        "I never let meetings pile up back to back.",
        "I make sure to review PRs within 24 hours.",
        "I'm good about blocking focus time.",
        "I typically turn off notifications during deep work.",
    ])
    def test_say_patterns(self, text):
        assert _is_say(text), f"Expected SAY match: {text!r}"

    @__import__("pytest").mark.parametrize("text", [
        "I actually didn't check emails until noon.",
        "I found myself checking Slack every ten minutes.",
        "I forgot to write up the notes.",
        "Last week I had seven back-to-back meetings.",
        "Yesterday I skipped the standup entirely.",
        "I ended up going over budget again.",
    ])
    def test_do_patterns(self, text):
        assert _is_do(text), f"Expected DO match: {text!r}"

    def test_plain_sentence_not_say(self):
        assert not _is_say("The meeting was on Thursday.")

    def test_plain_sentence_not_do(self):
        assert not _is_do("The product has three main features.")


class TestPolarity:
    def test_positive(self):
        assert _detect_polarity("I always make sure to complete my tasks.") == "positive"

    def test_negative(self):
        assert _detect_polarity("I didn't check emails and forgot the meeting.") == "negative"

    def test_neutral(self):
        result = _detect_polarity("The session lasted about an hour.")
        assert result in ("neutral", "positive", "negative")


class TestKeywords:
    def test_extracts_content_words(self):
        kw = _extract_keywords("I always check my emails every morning.")
        assert "check" in kw
        assert "emails" in kw
        assert "morning" in kw

    def test_excludes_stopwords(self):
        kw = _extract_keywords("I did this and that today.")
        assert "the" not in kw
        assert "and" not in kw
        assert "i" not in kw

    def test_short_words_excluded(self):
        kw = _extract_keywords("I go to the gym.")
        assert "go" not in kw
        assert "gym" in kw


class TestTopicOverlap:
    def test_identical(self):
        kw = ["email", "morning", "check"]
        assert _topic_overlap(kw, kw) == 1.0

    def test_disjoint(self):
        assert _topic_overlap(["email"], ["gym"]) == 0.0

    def test_partial(self):
        score = _topic_overlap(["email", "morning"], ["email", "afternoon"])
        assert 0.0 < score < 1.0

    def test_empty(self):
        assert _topic_overlap([], ["email"]) == 0.0


class TestParseTranscript:
    def test_speaker_colon_format(self):
        text = "Moderator: Hello there.\nParticipant: I always do X."
        parsed = _parse_transcript(text)
        assert any(s == "Moderator" for s, _, _ in parsed)
        assert any(s == "Participant" for s, _, _ in parsed)

    def test_bracket_format(self):
        text = "[M] How are you?\n[P1] I usually check emails first."
        parsed = _parse_transcript(text)
        speakers = [s for s, _, _ in parsed]
        assert "M" in speakers or "P1" in speakers

    def test_no_speaker(self):
        text = "I always check my email. I forgot yesterday."
        parsed = _parse_transcript(text)
        assert len(parsed) >= 2
        assert all(s is None for s, _, _ in parsed)

    def test_multisentence_line(self):
        text = "P: I always check email first. But I forgot yesterday. It happens."
        parsed = _parse_transcript(text)
        assert len(parsed) == 3


class TestDetectGaps:
    def test_detects_clear_contradiction(self):
        transcript = (
            "Participant: I always check my emails first thing in the morning.\n"
            "Participant: I actually didn't check emails until noon on Monday.\n"
        )
        report = detect_gaps(transcript)
        assert len(report.gaps) >= 1
        types = [g.gap_type for g in report.gaps]
        assert GapType.CONTRADICTION in types or GapType.PARTIAL in types

    def test_no_gaps_neutral_text(self):
        transcript = (
            "Moderator: Tell me about the product.\n"
            "Participant: The dashboard has three panels.\n"
            "Participant: The export function worked fine.\n"
        )
        report = detect_gaps(transcript)
        assert report.contradiction_count == 0

    def test_report_metadata(self):
        transcript = "P: I always write notes. I forgot to write notes yesterday.\n"
        report = detect_gaps(transcript, source_file="test.txt")
        assert report.source_file == "test.txt"
        assert report.total_sentences >= 1
        assert report.say_count >= 1
        assert report.do_count >= 1

    def test_gaps_sorted_by_confidence(self):
        transcript = (
            "P: I always check email first thing.\n"
            "P: I actually didn't check emails until noon.\n"
            "P: I usually write meeting notes right away.\n"
            "P: I skipped notes for three meetings last week.\n"
        )
        report = detect_gaps(transcript)
        confidences = [g.confidence for g in report.gaps]
        assert confidences == sorted(confidences, reverse=True)

    def test_min_confidence_filter(self):
        transcript = (
            "P: I always exercise regularly.\n"
            "P: I went to the gym yesterday.\n"
        )
        report_strict = detect_gaps(transcript, min_confidence=0.9)
        report_loose = detect_gaps(transcript, min_confidence=0.1)
        assert len(report_strict.gaps) <= len(report_loose.gaps)

    def test_fixture_file(self):
        report = detect_gaps_from_file(FIXTURE_DIR / "sample_transcript.txt")
        assert report.total_sentences > 5
        assert report.say_count > 0
        assert report.do_count > 0
        assert len(report.gaps) >= 2

    def test_probe_generated(self):
        transcript = (
            "P: I always check email every morning.\n"
            "P: I actually didn't check emails until noon.\n"
        )
        report = detect_gaps(transcript)
        for g in report.gaps:
            assert g.suggested_probe is not None
            assert len(g.suggested_probe) > 10

    def test_max_window_limits_pairs(self):
        lines = ["P: I always check emails.\n"] + ["P: Some unrelated line.\n"] * 100
        lines.append("P: I actually didn't check emails.\n")
        transcript = "".join(lines)
        report_tight = detect_gaps(transcript, max_window=5)
        report_wide = detect_gaps(transcript, max_window=200)
        assert len(report_tight.gaps) <= len(report_wide.gaps)


class TestDetectGapsFromFile:
    def test_loads_and_detects(self):
        report = detect_gaps_from_file(FIXTURE_DIR / "sample_transcript.txt")
        assert report.source_file == "sample_transcript.txt"
        assert report.total_sentences > 0
