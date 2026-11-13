# divergence-probe

**Detect habitual-claim vs episodic-report divergence in UX research transcripts.**  
No graph database. No pipeline setup. Runs on any transcript file in seconds.

Part of the [CPR Orbital series](https://github.com/kgkazakos) — 40 open-source AI-native product research tools, shipped every Friday.

---

## The problem

When participants say *"I always check my emails first thing"* and thirty seconds later reveal they didn't look at email until noon, that's a behavioural divergence — and one of the most analytically valuable signals in qualitative research.

Heavy-duty solutions exist for deep longitudinal analysis. But not every research programme needs a graph database to catch the obvious contradictions in a single session transcript.

`divergence-probe` is the 80% solution: a fast, offline, dependency-light tool that flags habitual claims against episodic reports — then generates follow-up probe questions the researcher can use in real time or during debrief.

---

## Features

- **Habitual-claim detection** — tags "I always / usually / try to / never" statements
- **Episodic-report detection** — tags "I actually / forgot / ended up / last week I" reports
- **Divergence classification** — CONTRADICTION (direct conflict), PARTIAL (shared topic, inconsistent framing), UNCERTAIN (weak signal)
- **Confidence scoring** — ranked by topic overlap and polarity conflict
- **Probe generation** — natural follow-up questions ready to paste into a debrief guide
- **Fully offline** — zero API calls required; rule-based engine runs with no credentials
- **Optional LLM enrichment** — add `--llm-backend openai|anthropic|gemini` for refined probes
- **Batch mode** — scan an entire session directory in one command
- **JSON output** — pipe results into your own tooling

---

## Installation

```bash
pip install divergence-probe
```

With LLM enrichment (pick your backend):

```bash
pip install "divergence-probe[openai]"
pip install "divergence-probe[anthropic]"
pip install "divergence-probe[gemini]"
pip install "divergence-probe[llm]"   # all three
```

---

## Quick start

```bash
# Scan a single transcript
dp scan interview_p01.txt

# JSON output
dp scan interview_p01.txt --json-output

# With LLM-enriched probes
dp scan interview_p01.txt --llm-backend anthropic

# Batch — scan a whole session folder
dp batch ./sessions/

# Tighten the confidence threshold
dp scan interview_p01.txt --min-confidence 0.5
```

---

## CLI reference

### `dp scan`

```
dp scan TRANSCRIPT [OPTIONS]

Arguments:
  TRANSCRIPT            Path to a transcript file (.txt)

Options:
  --min-overlap FLOAT   Minimum Jaccard keyword overlap (default: 0.05)
  --min-confidence FLT  Minimum confidence to include a divergence (default: 0.30)
  --max-window INT      Max sentence distance for claim/report pairs (default: 60)
  --llm-backend TEXT    openai | anthropic | gemini
  --top-n INT           Divergences to enrich with LLM (default: 5)
  --json-output         Emit results as JSON
```

### `dp batch`

```
dp batch DIRECTORY [OPTIONS]

Arguments:
  DIRECTORY             Directory containing transcript files

Options:
  --pattern TEXT        Glob pattern for files (default: *.txt)
  --min-overlap FLOAT
  --min-confidence FLT
  --max-window INT
  --json-output
```

---

## Transcript format

`divergence-probe` handles the most common transcript formats out of the box:

```
# Colon-separated speakers
Moderator: Walk me through your morning routine.
Participant: I always check emails before anything else.

# Bracket-prefixed speakers
[M] How did that go last week?
[P1] I actually didn't check emails until noon.

# Plain text (no speaker labels)
I always write meeting notes right after the session.
I skipped notes for two meetings this week.
```

---

## Python API

```python
from divergence_probe import detect_gaps, detect_gaps_from_file
from divergence_probe.models import GapType

# From a string
report = detect_gaps(transcript_text, source_file="p01")

# From a file
from pathlib import Path
report = detect_gaps_from_file(Path("sessions/p01.txt"))

print(f"{len(report.gaps)} divergences · {report.contradiction_count} contradictions")

for gap in report.gaps:
    print(gap.gap_type.value, gap.severity.value, gap.confidence)
    print("CLAIM: ", gap.say_statement.text)
    print("REPORT:", gap.do_statement.text)
    print("Probe: ", gap.suggested_probe)
```

---

## JSON output schema

```json
{
  "source_file": "p01.txt",
  "total_sentences": 42,
  "say_count": 8,
  "do_count": 12,
  "gap_count": 4,
  "contradiction_count": 3,
  "partial_count": 1,
  "high_severity_count": 2,
  "gap_rate": 0.5,
  "gaps": [
    {
      "gap_type": "contradiction",
      "severity": "high",
      "confidence": 0.84,
      "topic_overlap_score": 0.33,
      "llm_enriched": false,
      "say": { "text": "...", "speaker": "P1", "line_no": 5, "polarity": "positive" },
      "do":  { "text": "...", "speaker": "P1", "line_no": 9, "polarity": "negative" },
      "explanation": "...",
      "suggested_probe": "..."
    }
  ]
}
```

---

## LLM enrichment

The LLM layer is reference scaffolding — excluded from CI and never required for the tool to run. When you pass `--llm-backend`, the top-N divergences (by confidence) are sent to the model for refined explanations, severity calibration, and richer probe questions.

| Backend   | Default model       | Install extra                          |
|-----------|---------------------|----------------------------------------|
| OpenAI    | `gpt-4o-mini`       | `pip install divergence-probe[openai]`    |
| Anthropic | `claude-sonnet-4-6` | `pip install divergence-probe[anthropic]` |
| Gemini    | `gemini-3.6-flash`  | `pip install divergence-probe[gemini]`    |

Set your API key in the environment before use:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
```

---

## Design principles

**Rule-based core, always.** Works fully offline with zero dependencies beyond `click` and `rich`. LLM enrichment is always additive and opt-in.

**No graph database.** Deep longitudinal divergence analysis with multimodal signal belongs to heavier tooling. `divergence-probe` is for the 80% case: a single session, a quick scan, a debrief the same afternoon.

**Probe-first output.** The primary deliverable is not a score — it is a question the researcher can actually ask.

---

## Part of the CPR Ecosystem

`divergence-probe` is Tool 13 in the [CPR Orbital series](https://github.com/kgkazakos) — 40 open-source Python tools for AI-native product research infrastructure, shipping every Friday from March to December 2026.

Related tools in this series:

| Tool | What it does |
|------|-------------|
| [`transcript-cleaner`](https://github.com/kgkazakos/transcript-cleaner) | Fix diarization errors and speaker gaps before analysis |
| [`qual-sniffer`](https://github.com/kgkazakos/qual-sniffer) | Detect methodological weaknesses in discussion guides |
| [`saturation-meter`](https://github.com/kgkazakos/saturation-meter) | Estimate thematic saturation — know when to stop |
| [`bias-audit`](https://github.com/kgkazakos/bias-audit) | Detect interviewer bias patterns across a corpus |
| [`recall-probe`](https://github.com/kgkazakos/recall-probe) | Longitudinal divergence across study waves |

---

## License

MIT © Kostas Kazakos
