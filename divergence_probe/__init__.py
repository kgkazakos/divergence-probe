"""divergence-probe — Detect habitual-claim vs episodic-report divergence in UX research transcripts."""

from .core import detect_gaps, detect_gaps_from_file
from .models import DivergenceGap, DivergenceReport, GapType, Severity, Statement

__version__ = "0.1.0"
__all__ = [
    "detect_gaps",
    "detect_gaps_from_file",
    "GapType",
    "Severity",
    "Statement",
    "DivergenceGap",
    "DivergenceReport",
]
