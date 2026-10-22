"""Jason Stys: independent evidence extraction and truncation oracles. Function/variable lines: docs/SOURCE_MAP.md."""

import io
import sys
from types import SimpleNamespace

import pytest

from assurance.report import load_report, synthetic_report
from tools.extract_report import extract, main


def test_extract_plain_and_timestamped_records():
    """Timestamp stripping must preserve actual JSON spaces, values and the synthetic label."""
    report = synthetic_report()
    plain = "REPORT_BEGIN\n" + report.model_dump_json(indent=2) + "\nREPORT_END"
    assert extract(plain) == report
    stamped = "\n".join("2026-10-22T00:00:00.0000000Z " + line for line in plain.splitlines())
    assert extract(stamped) == report


@pytest.mark.parametrize(
    "text",
    [
        "",
        "REPORT_BEGIN\n{}",
        "REPORT_END",
        "REPORT_BEGIN\nREPORT_BEGIN",
        "REPORT_BEGIN\n{}\nREPORT_END\nREPORT_BEGIN",
    ],
)
def test_incomplete_or_ambiguous_records_rejected(text):
    """A truncated or multiple record log must not become apparently complete evidence."""
    with pytest.raises(ValueError):
        extract(text)


@pytest.mark.parametrize("piped", [True, False])
def test_cli_recovers_real_file_or_stdin_without_overwriting(tmp_path, monkeypatch, piped):
    """The documented CLI consumes text only and creates a validated separate evidence file."""
    report = synthetic_report()
    content = ("REPORT_BEGIN\n" + report.model_dump_json(indent=2) + "\nREPORT_END").encode()
    source = tmp_path / "job.log"
    source.write_bytes(content)
    destination = tmp_path / "recovered.json"
    monkeypatch.setattr(
        sys, "argv", ["extract_report.py", "-" if piped else str(source), str(destination)]
    )
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(content)))
    main()
    assert load_report(destination) == report
