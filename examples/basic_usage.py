"""
Basic usage example for divergence-probe.

Install: pip install divergence-probe
Run:     python examples/basic_usage.py
"""

from divergence_probe import detect_gaps
from divergence_probe.models import GapType

TRANSCRIPT = """
Moderator: How do you handle email during the workday?
Participant: I always check emails first thing in the morning. I make it a habit.
Moderator: And how did that actually play out last week?
Participant: I actually didn't check emails until noon on Monday. I got distracted by Slack.
Moderator: What about meeting documentation?
Participant: I always write meeting notes straight after sessions. I never let it slip.
Moderator: Any examples from this week?
Participant: I skipped notes for two meetings this week. I kept telling myself I'd do it later.
"""

if __name__ == "__main__":
    report = detect_gaps(TRANSCRIPT, source_file="example")

    print(f"\ndivergence-probe  ·  {report.source_file}")
    print(f"{'─' * 50}")
    print(f"Sentences:         {report.total_sentences}")
    print(f"Habitual claims:   {report.say_count}")
    print(f"Episodic reports:  {report.do_count}")
    print(f"Divergences:       {len(report.gaps)}")
    print(f"Contradictions:    {report.contradiction_count}")
    print(f"High severity:     {report.high_severity_count}")
    print()

    for i, gap in enumerate(report.gaps, 1):
        icon = "⚡" if gap.gap_type == GapType.CONTRADICTION else "⚠"
        print(f"{i}. {icon} {gap.gap_type.value.upper()} [{gap.severity.value}]")
        print(f"   CLAIM:  {gap.say_statement.text}")
        print(f"   REPORT: {gap.do_statement.text}")
        print(f"   {gap.explanation}")
        if gap.suggested_probe:
            print(f"   → Probe: {gap.suggested_probe}")
        print()

    print("─" * 50)
    print("Add --llm-backend openai|anthropic|gemini for enriched probes.")
    print("Try: dp scan my_transcript.txt --llm-backend anthropic")
