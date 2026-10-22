"""Jason Stys: independent evidence extraction and truncation oracles. Function/variable lines: docs/SOURCE_MAP.md."""

import pytest

from assurance.report import synthetic_report
from tools.extract_report import extract


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
