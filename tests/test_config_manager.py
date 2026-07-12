"""Tests for ui/gen/config_manager.py — ConfigManager."""
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from ui.gen.config_manager import ConfigManager, SchemaError, _format_toml_value, _serialize_toml


# ═══════════════════════════════════════════════════════════════
#  Unit: _format_toml_value / _serialize_toml
# ═══════════════════════════════════════════════════════════════

class TestFormatTomlValue:

    def test_bool(self):
        assert _format_toml_value(True) == "true"
        assert _format_toml_value(False) == "false"

    def test_string(self):
        result = _format_toml_value('hello world')
        assert result == '"hello world"'

    def test_string_with_escapes(self):
        result = _format_toml_value('line1\nline2')
        assert '\\n' in result

    def test_int(self):
        assert _format_toml_value(42) == "42"

    def test_float(self):
        assert _format_toml_value(3.14) == "3.14"

    def test_none(self):
        assert _format_toml_value(None) == '""'

    def test_dict(self):
        result = _format_toml_value({"key": "val"})
        assert 'key' in result
        assert '"val"' in result

    def test_list(self):
        result = _format_toml_value([1, 2, 3])
        assert '1' in result
        assert '3' in result


class TestSerializeToml:

    def test_basic(self):
        data = {"section1": {"key1": "val1", "key2": 42}}
        result = _serialize_toml(data)
        assert "[section1]" in result
        assert "key1" in result
        assert "key2" in result


# ═══════════════════════════════════════════════════════════════
#  ConfigManager
# ═══════════════════════════════════════════════════════════════

class TestConfigManager:

    @pytest.fixture
    def cm(self, tmp_data_dir, config_schema) -> ConfigManager:
        """Create a ConfigManager with a temp file path (not yet saved)."""
        path = tmp_data_dir / "test_config.toml"
        return ConfigManager(str(path), config_schema)

    def test_create_and_save(self, cm):
        """Create a new config, save it → file exists."""
        cm.load()
        assert cm.filepath.exists()
        assert cm.active_section == "default"
        assert cm.get("string_key") == "hello"
        assert cm.get("int_key") == 42

    def test_load_existing(self, cm, config_schema):
        """Save, then load again — values persist."""
        cm.load()
        cm.set("string_key", "world")
        cm.set("int_key", 100)
        cm.save()

        # New manager on same file
        cm2 = ConfigManager(str(cm.filepath), config_schema)
        cm2.load()
        assert cm2.get("string_key") == "world"
        assert cm2.get("int_key") == 100

    def test_switch_section(self, cm):
        """Switch between sections."""
        cm.load()
        cm.add_section("alt")
        cm.activate("alt")
        assert cm.active_section == "alt"
        cm.set("string_key", "alt_value")
        assert cm.get("string_key") == "alt_value"

        # Switch back
        cm.activate("default")
        assert cm.get("string_key") == "hello"

    def test_activate_nonexistent(self, cm):
        """Activating a non-existent section returns False."""
        cm.load()
        result = cm.activate("nonexistent")
        assert result is False

    def test_add_duplicate_section(self, cm):
        """Adding a duplicate section returns False."""
        cm.load()
        result = cm.add_section("default")
        assert result is False

    def test_delete_section(self, cm):
        """Delete a non-default section."""
        cm.load()
        cm.add_section("alt")
        cm.activate("alt")
        result = cm.delete_section("alt")
        assert result is True
        assert "alt" not in cm.sections
        # Should revert to default
        assert cm.active_section == "default"

    def test_delete_default_section(self, cm):
        """Cannot delete the default section."""
        cm.load()
        result = cm.delete_section("default")
        assert result is False

    def test_sections_property(self, cm):
        """sections property returns non-meta section names."""
        cm.load()
        assert "default" in cm.sections
        assert "meta" not in cm.sections

    def test_active_property(self, cm):
        """active returns current section config dict."""
        cm.load()
        active = cm.active
        assert isinstance(active, dict)
        assert active.get("string_key") == "hello"

    def test_as_dict(self, cm):
        """as_dict includes _name."""
        cm.load()
        d = cm.as_dict()
        assert d["_name"] == "default"

    def test_is_dirty(self, cm):
        """is_dirty tracks unsaved changes."""
        cm.load()
        assert cm.is_dirty() is False
        cm.set("string_key", "changed")
        assert cm.is_dirty() is True
        cm.save()
        assert cm.is_dirty() is False

    def test_get_with_default(self, cm):
        """get returns default for missing key."""
        cm.load()
        val = cm.get("nonexistent_key", "fallback")
        assert val == "fallback"

    def test_set_different_section(self, cm):
        """set can target a different section via parameter."""
        cm.load()
        cm.add_section("alt")
        cm.set("string_key", "alt_val", section="alt")
        assert cm.get("string_key") == "hello"  # default still has original
        cm.activate("alt")
        assert cm.get("string_key") == "alt_val"

    def test_get_section(self, cm):
        """get_section returns dict for a named section."""
        cm.load()
        sec = cm.get_section("default")
        assert sec.get("string_key") == "hello"
        assert cm.get_section("nonexistent") == {}

    # ── Edge: missing file ──

    def test_load_nonexistent_file(self, tmp_data_dir, config_schema):
        """Non-existent file → automagically created with defaults."""
        path = tmp_data_dir / "new_config.toml"
        assert not path.exists()
        cm = ConfigManager(str(path), config_schema)
        cm.load()
        assert path.exists()
        assert cm.get("string_key") == "hello"

    # ── Edge: corrupt TOML ──

    def test_load_corrupt_toml(self, tmp_data_dir, config_schema):
        """Corrupt TOML file → backup created and file recreated."""
        path = tmp_data_dir / "corrupt.toml"
        path.write_text("[[[invalid toml content]]]\n", encoding="utf-8")
        cm = ConfigManager(str(path), config_schema)
        cm.load()
        # Backup should exist
        backup = path.with_suffix(".toml.bak")
        assert backup.exists()
        # File should be recreated with valid defaults
        assert cm.get("string_key") == "hello"

    # ── Schema key auto-fill ──

    def test_missing_schema_keys_filled(self, cm, config_schema):
        """Missing keys in existing sections are auto-filled on load."""
        cm.load()
        # Manually remove a key from data
        del cm._data["default"]["float_key"]
        cm._data["default"]["int_key"] = 999
        cm._ensure_schema()
        assert "float_key" in cm._data["default"]
        assert cm._data["default"]["float_key"] == 3.14  # default value
        assert cm._data["default"]["int_key"] == 999  # preserved

    # ── Edge: invalid schema (not used, but SchemaError class exists) ──

    def test_schema_error_class(self):
        """SchemaError can be raised and caught."""
        from ui.gen.config_manager import SchemaError
        with pytest.raises(SchemaError):
            raise SchemaError("test error")

    # ── Edge: add_section with copy_from ──

    def test_add_section_copy(self, cm):
        """Add section by copying existing section values."""
        cm.load()
        cm.set("string_key", "custom_val")
        cm.add_section("alt", copy_from="default")
        assert cm.get_section("alt")["string_key"] == "custom_val"

    # ── Edge: add_section with non-existent copy source ──

    def test_add_section_copy_nonexistent(self, cm, config_schema):
        """If copy_from section doesn't exist, use schema defaults."""
        cm.load()
        cm.add_section("alt", copy_from="nonexistent")
        assert cm.get_section("alt")["string_key"] == config_schema["string_key"]["default"]
