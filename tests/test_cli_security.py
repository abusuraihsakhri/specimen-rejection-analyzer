"""
Security and input validation tests for CLI.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import csv

from cli import _resolve_safe_path, _safe_float, main


class TestResolveSafePath:
    """Tests for path traversal protection."""

    def test_valid_path_within_cwd(self):
        """Paths within cwd should resolve successfully."""
        p = _resolve_safe_path("data.csv", must_exist=False)
        assert p is not None

    def test_path_traversal_denied(self):
        """Paths outside cwd should be denied."""
        with pytest.raises(ValueError, match="outside the working directory"):
            _resolve_safe_path("../etc/passwd", must_exist=False)

    def test_nested_traversal_denied(self):
        """Nested traversal attempts should be denied."""
        with pytest.raises(ValueError, match="outside the working directory"):
            _resolve_safe_path("subdir/../../../etc/passwd", must_exist=False)

    def test_nonexistent_input_file_raises(self):
        """Non-existent input files should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            _resolve_safe_path("nonexistent_file_12345.csv", must_exist=True)


class TestSafeFloat:
    """Tests for safe float parsing."""

    def test_valid_float(self):
        assert _safe_float("3.14", "test") == 3.14

    def test_integer_string(self):
        assert _safe_float("42", "test") == 42.0

    def test_empty_string_returns_default(self):
        assert _safe_float("", "test", 1.5) == 1.5

    def test_none_returns_default(self):
        assert _safe_float(None, "test", 2.5) == 2.5

    def test_invalid_string_returns_default(self):
        assert _safe_float("not-a-number", "test", 0.0) == 0.0

    def test_whitespace_returns_default(self):
        assert _safe_float("   ", "test", 1.0) == 1.0


class TestBatchCLI:
    """Tests for batch CSV processing with validation."""

    def _create_test_csv(self, rows, fieldnames=None):
        """Helper to create a temporary CSV file."""
        if fieldnames is None:
            fieldnames = ["task_id", "target_identifier", "primary_metric", "secondary_metric", "status_descriptor", "is_critical_flag"]
        fd, path = tempfile.mkstemp(suffix=".csv", dir=".")
        with os.fdopen(fd, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return path

    def test_batch_with_valid_data(self):
        """Batch processing with valid data should succeed."""
        csv_path = self._create_test_csv([
            {"task_id": "T1", "target_identifier": "K1", "primary_metric": "10.5",
             "secondary_metric": "3.2", "status_descriptor": "NOMINAL", "is_critical_flag": "false"},
        ])
        out_path = "test_batch_out.csv"
        try:
            result = main(["batch", "-i", csv_path, "-o", out_path])
            assert result == 0
            assert os.path.exists(out_path)
        finally:
            os.unlink(csv_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_batch_with_invalid_float(self):
        """Batch processing should handle invalid float values gracefully."""
        csv_path = self._create_test_csv([
            {"task_id": "T1", "target_identifier": "K1", "primary_metric": "invalid",
             "secondary_metric": "3.2", "status_descriptor": "NOMINAL", "is_critical_flag": "false"},
        ])
        out_path = "test_batch_invalid_out.csv"
        try:
            result = main(["batch", "-i", csv_path, "-o", out_path])
            assert result == 0
            assert os.path.exists(out_path)
        finally:
            os.unlink(csv_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_batch_traversal_denied(self):
        """Batch processing should deny path traversal attempts."""
        with pytest.raises(ValueError, match="outside the working directory"):
            main(["batch", "-i", "../etc/passwd", "-o", "out.csv"])

    def test_batch_output_traversal_denied(self):
        """Batch processing should deny output path traversal."""
        csv_path = self._create_test_csv([
            {"task_id": "T1", "target_identifier": "K1", "primary_metric": "10.5",
             "secondary_metric": "3.2", "status_descriptor": "NOMINAL", "is_critical_flag": "false"},
        ])
        try:
            with pytest.raises(ValueError, match="outside the working directory"):
                main(["batch", "-i", csv_path, "-o", "../etc/out.csv"])
        finally:
            os.unlink(csv_path)
