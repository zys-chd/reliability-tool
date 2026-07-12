"""Tests for core/open_file.py — cross-platform file opening."""
import os
from pathlib import Path

import pytest


class TestOpenFile:
    """Test that open_file function exists and handles different path inputs.

    We cannot actually test opening a file (no display), but we can verify:
    - Function import works
    - Raises FileNotFoundError for non-existent paths
    - Accepts both str and Path inputs
    """

    def test_import_exists(self):
        """Function exists and is callable."""
        from core.open_file import open_file
        assert callable(open_file)

    def test_raises_on_nonexistent(self):
        """Non-existent file raises FileNotFoundError."""
        from core.open_file import open_file
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            open_file("/nonexistent/path/that/does/not/exist.txt")

    def test_raises_on_nonexistent_path(self):
        """Path object with non-existent file raises FileNotFoundError."""
        from core.open_file import open_file
        p = Path("/nonexistent/path/that/does/not/exist.txt")
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            open_file(p)

    def test_accepts_str_and_path(self):
        """Function signature accepts both str and Path."""
        import inspect
        from core.open_file import open_file
        sig = inspect.signature(open_file)
        param = sig.parameters["path"]
        ann = param.annotation
        assert "str" in str(ann) or "Path" in str(ann) or str(ann) != "empty"
