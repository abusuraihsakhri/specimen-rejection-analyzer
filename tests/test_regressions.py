"""Regression coverage for audit integrity, input validation, and privacy controls."""
import math

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import rejection_analyzer
from cli import _safe_float, main
from agents.api import api_audit_logs
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def test_unmatched_lookup_reports_no_hit():
    result = rejection_analyzer.lookup("creatinine")
    assert result["score"] == 0
    assert result["top_hit"] == "No match"
    assert result["all"] == []


def test_csv_reason_priority_and_unknown(tmp_path):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "query,rejection_reason\nQ1,Hemolyzed sample\nQ2,unknown terminology\n",
        encoding="utf-8",
    )
    rows = rejection_analyzer.process_csv(input_file, output_file)
    assert [row["top_hit"] for row in rows] == ["Hemolyzed Sample", "No match"]
    assert output_file.is_file()


@pytest.mark.parametrize("csv_content", ["", "hello\n", "reason,reason\nx,y\n", "reason\nx,y\n"])
def test_analyzer_rejects_malformed_csv(tmp_path, csv_content):
    source = tmp_path / "invalid.csv"
    source.write_text(csv_content, encoding="utf-8")
    with pytest.raises(ValueError):
        rejection_analyzer.process_csv(source, tmp_path / "output.csv")


@pytest.mark.parametrize("value", ["nan", "inf", "-Infinity", "not-a-number"])
def test_cli_rejects_nonfinite_metrics(value):
    assert _safe_float(value, "primary", 7.5) == 7.5


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_api_schema_rejects_nonfinite_metrics(bad):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T1", target_identifier="S1", primary_metric=bad)


def test_batch_input_output_cannot_match(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "data.csv"
    source.write_text("task_id,target_identifier,primary_metric\nT1,S1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="different"):
        main(["batch", "--input", "data.csv", "--output", "data.csv"])
    assert source.read_text(encoding="utf-8").startswith("task_id")


def test_audit_verifies_signatures_not_only_links():
    audit = AuditTrail(secret_key="unit-test-secret")
    audit.log("tester", "supervisor", "EVENT", {"count": 1})
    audit.log("tester", "supervisor", "EVENT", {"count": 2})
    assert audit.verify_integrity()
    audit.logs[1]["event_type"] = "TAMPERED"
    assert not audit.verify_integrity()


def test_audit_returns_defensive_snapshot():
    audit = AuditTrail(secret_key="unit-test-secret")
    audit.log("tester", "supervisor", "EVENT", {"count": 1})
    exposed = audit.get_trail()
    exposed[0]["event_type"] = "TAMPERED"
    assert audit.verify_integrity()


def test_audit_missing_fields_fail_closed():
    audit = AuditTrail(secret_key="unit-test-secret")
    audit.log("tester", "supervisor", "EVENT", {"count": 1})
    del audit.logs[0]["timestamp"]
    assert not audit.verify_integrity()


def test_reject_phi_inside_attributes():
    payload = SystemTaskPayload(
        task_id="TEST-01", target_identifier="S-01", primary_metric=1,
        attributes={"notes": "Patient MRN-123456"},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_audit_endpoint_requires_configured_token(monkeypatch):
    monkeypatch.delenv("API_AUDIT_TOKEN", raising=False)
    with pytest.raises(HTTPException) as err:
        api_audit_logs()
    assert err.value.status_code == 503
    monkeypatch.setenv("API_AUDIT_TOKEN", "test-only-key")
    with pytest.raises(HTTPException) as err:
        api_audit_logs(x_audit_token="incorrect")
    assert err.value.status_code == 403
    assert api_audit_logs(x_audit_token="test-only-key")["verified"] is True
