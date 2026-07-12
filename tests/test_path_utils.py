"""Tests for core/path_utils.py — Windows path-length warnings."""

import sys
from pathlib import Path

import pytest

from core.path_utils import check_path_length, warn_on_long_path


class TestCheckPathLength:
    """Unit tests for ``check_path_length()``."""

    def test_short_path_returns_no_warnings(self):
        """Paths under the threshold should return an empty list."""
        result = check_path_length("/a/short/path/file.txt")
        assert result == []

    def test_long_path_returns_warning_when_win32(self, monkeypatch: pytest.MonkeyPatch):
        """On win32 a path > 250 chars should produce exactly one warning."""
        monkeypatch.setattr(sys, "platform", "win32")
        long_path = "/" + "a" * 260
        result = check_path_length(long_path)
        assert len(result) == 1
        assert "路径过长" in result[0]
        assert str(len(long_path)) in result[0]

    def test_long_path_on_linux_returns_empty(self, monkeypatch: pytest.MonkeyPatch):
        """On non-Windows, even very long paths produce no warnings."""
        monkeypatch.setattr(sys, "platform", "linux")
        long_path = "/" + "a" * 300
        result = check_path_length(long_path)
        assert result == []

    def test_accepts_path_object(self, monkeypatch: pytest.MonkeyPatch):
        """``Path`` objects should be accepted just like strings."""
        monkeypatch.setattr(sys, "platform", "win32")
        long_path = Path("/" + "b" * 260)
        result = check_path_length(long_path)
        assert len(result) == 1
        assert "路径过长" in result[0]

    def test_exactly_at_threshold_no_warning(self, monkeypatch: pytest.MonkeyPatch):
        """A path exactly 250 characters should NOT trigger a warning."""
        monkeypatch.setattr(sys, "platform", "win32")
        path = "/" + "c" * 249  # 1 + 249 = 250
        result = check_path_length(path)
        assert result == []


class TestWarnOnLongPath:
    """Lightweight smoke tests for ``warn_on_long_path()``."""

    def test_short_path_does_not_raise(self):
        """Calling with a short path should never raise an exception."""
        warn_on_long_path("/a/short/path.txt")  # must not raise

    def test_long_path_on_win32_does_not_raise(self, monkeypatch: pytest.MonkeyPatch):
        """Even with a long path on win32, the function should not raise."""
        monkeypatch.setattr(sys, "platform", "win32")
        warn_on_long_path("/" + "d" * 260)  # must not raise
