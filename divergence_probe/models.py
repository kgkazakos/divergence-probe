"""Core data models for divergence-probe."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GapType(Enum):
    CONTRADICTION = "contradiction"
    PARTIAL = "partial"
    UNCERTAIN = "uncertain"


class Severity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Statement:
    """A single sentence tagged as a habitual claim ('say') or episodic report ('do')."""

    text: str
    statement_type: str
    speaker: Optional[str]
    sentence_idx: int
    line_no: int
    polarity: str
    keywords: list = field(default_factory=list)


@dataclass
class DivergenceGap:
    """A detected divergence between a habitual claim and a reported behaviour."""

    say_statement: Statement
    do_statement: Statement
    gap_type: GapType
    severity: Severity
    confidence: float
    topic_overlap_score: float
    explanation: str
    suggested_probe: Optional[str] = None
    llm_enriched: bool = False


@dataclass
class DivergenceReport:
    """Full analysis output for one transcript."""

    source_file: str
    total_sentences: int
    say_count: int
    do_count: int
    gaps: list = field(default_factory=list)

    @property
    def contradiction_count(self) -> int:
        return sum(1 for g in self.gaps if g.gap_type == GapType.CONTRADICTION)

    @property
    def partial_count(self) -> int:
        return sum(1 for g in self.gaps if g.gap_type == GapType.PARTIAL)

    @property
    def high_severity_count(self) -> int:
        return sum(1 for g in self.gaps if g.severity == Severity.HIGH)

    @property
    def gap_rate(self) -> float:
        if self.say_count == 0:
            return 0.0
        return len(self.gaps) / self.say_count
