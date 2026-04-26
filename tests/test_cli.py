"""Tests for the Click CLI."""
import json
from pathlib import Path

from click.testing import CliRunner

from divergence_probe.cli import cli

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURE_DIR / "sample_transcript.txt"
BATCH_DIR = FIXTURE_DIR / "batch"


class TestScanCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_scan_rich_output(self):
        result = self.runner.invoke(cli, ["scan", str(SAMPLE)])
        assert result.exit_code == 0
        assert "divergence-probe" in result.output

    def test_scan_json_output(self):
        result = self.runner.invoke(cli, ["scan", str(SAMPLE), "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "source_file" in data
        assert "gaps" in data
        assert isinstance(data["gaps"], list)

    def test_scan_json_gap_structure(self):
        result = self.runner.invoke(cli, ["scan", str(SAMPLE), "--json-output"])
        data = json.loads(result.output)
        for gap in data["gaps"]:
            assert "gap_type" in gap
            assert "severity" in gap
            assert "confidence" in gap
            assert "say" in gap
            assert "do" in gap
            assert "explanation" in gap
            assert "suggested_probe" in gap

    def test_scan_summary_counts(self):
        result = self.runner.invoke(cli, ["scan", str(SAMPLE), "--json-output"])
        data = json.loads(result.output)
        assert data["total_sentences"] > 0
        assert data["say_count"] >= 0
        assert data["do_count"] >= 0

    def test_scan_strict_confidence(self):
        result = self.runner.invoke(
            cli, ["scan", str(SAMPLE), "--min-confidence", "0.99", "--json-output"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        for g in data["gaps"]:
            assert g["confidence"] >= 0.99

    def test_scan_missing_file(self):
        result = self.runner.invoke(cli, ["scan", "nonexistent.txt"])
        assert result.exit_code != 0

    def test_scan_no_gaps_message(self, tmp_path):
        plain = tmp_path / "plain.txt"
        plain.write_text("The meeting was at three.\nWe discussed the roadmap.\n")
        result = self.runner.invoke(cli, ["scan", str(plain)])
        assert result.exit_code == 0

    def test_scan_gap_rate_in_json(self):
        result = self.runner.invoke(cli, ["scan", str(SAMPLE), "--json-output"])
        data = json.loads(result.output)
        assert "gap_rate" in data
        assert 0.0 <= data["gap_rate"] <= 1.0


class TestBatchCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_batch_rich_output(self):
        result = self.runner.invoke(cli, ["batch", str(BATCH_DIR)])
        assert result.exit_code == 0

    def test_batch_json_output(self):
        result = self.runner.invoke(cli, ["batch", str(BATCH_DIR), "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_files" in data
        assert "reports" in data
        assert data["total_files"] == 2

    def test_batch_json_structure(self):
        result = self.runner.invoke(cli, ["batch", str(BATCH_DIR), "--json-output"])
        data = json.loads(result.output)
        for report in data["reports"]:
            assert "source_file" in report
            assert "gaps" in report

    def test_batch_no_match(self, tmp_path):
        result = self.runner.invoke(cli, ["batch", str(tmp_path), "--pattern", "*.xyz"])
        assert result.exit_code != 0

    def test_batch_custom_pattern(self, tmp_path):
        f = tmp_path / "session.txt"
        f.write_text("P: I always check my emails.\nP: I actually forgot yesterday.\n")
        result = self.runner.invoke(
            cli, ["batch", str(tmp_path), "--pattern", "session.txt", "--json-output"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_files"] == 1


class TestCLIVersion:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
