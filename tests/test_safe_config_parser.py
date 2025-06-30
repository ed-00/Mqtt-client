"""
Unit tests for the SafeConfigParser module.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import logging
from typing import Dict, Any

from Listener.safe_config_parser import (
    SafeConfigParser,
    ConfigError,
    ConfigValidationError,
    ConfigParseError,
    ConfigSource,
    ParsedConfig,
    validate_required_fields,
    validate_field_types
)


@pytest.mark.unit
class TestConfigExceptions:
    """Test custom configuration exceptions."""

    def test_config_error_inheritance(self):
        """Test that ConfigError inherits from Exception."""
        error = ConfigError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_config_validation_error_inheritance(self):
        """Test that ConfigValidationError inherits from ConfigError."""
        error = ConfigValidationError("validation failed")
        assert isinstance(error, ConfigError)
        assert isinstance(error, Exception)

    def test_config_parse_error_inheritance(self):
        """Test that ConfigParseError inherits from ConfigError."""
        error = ConfigParseError("parse failed")
        assert isinstance(error, ConfigError)
        assert isinstance(error, Exception)


@pytest.mark.unit
class TestParsedConfig:
    """Test ParsedConfig dataclass."""

    def test_parsed_config_creation(self):
        """Test creating a ParsedConfig instance."""
        data = {"key": "value"}
        config = ParsedConfig(
            data=data,
            source=ConfigSource.DICT_OBJECT,
            source_info="test dict"
        )

        assert config.data == data
        assert config.source == ConfigSource.DICT_OBJECT
        assert config.source_info == "test dict"
        assert config.is_valid is True
        assert config.validation_errors is None

    def test_parsed_config_with_validation_errors(self):
        """Test ParsedConfig with validation errors."""
        config = ParsedConfig(
            data={},
            source=ConfigSource.STRING_CONTENT,
            source_info="test string",
            is_valid=False,
            validation_errors=["error1", "error2"]
        )

        assert config.is_valid is False
        assert config.validation_errors == ["error1", "error2"]


@pytest.mark.unit
class TestSafeConfigParser:
    """Test SafeConfigParser class."""

    def test_init_with_logger(self):
        """Test initialization with custom logger."""
        logger = logging.getLogger("test")
        parser = SafeConfigParser(logger)
        assert parser.logger == logger

    def test_init_without_logger(self):
        """Test initialization without custom logger."""
        parser = SafeConfigParser()
        assert parser.logger is not None
        assert isinstance(parser.logger, logging.Logger)

    def test_add_validator(self):
        """Test adding a custom validator."""
        parser = SafeConfigParser()

        def dummy_validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
            return True, []

        parser.add_validator(dummy_validator)
        assert len(parser.validators) == 1
        assert parser.validators[0] == dummy_validator

    def test_validate_config_no_validators(self, safe_config_parser):
        """Test validation with no validators returns True."""
        config_data = {"key": "value"}
        is_valid, errors = safe_config_parser._validate_config(config_data)  # pylint: disable=protected-access

        assert is_valid is True
        assert errors == []

    def test_validate_config_with_passing_validator(self, safe_config_parser):
        """Test validation with passing validator."""
        def passing_validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
            return True, []

        safe_config_parser.add_validator(passing_validator)
        config_data = {"key": "value"}
        is_valid, errors = safe_config_parser._validate_config(config_data)  # pylint: disable=protected-access

        assert is_valid is True
        assert errors == []

    def test_validate_config_with_failing_validator(self, safe_config_parser):
        """Test validation with failing validator."""
        def failing_validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
            return False, ["validation error"]

        safe_config_parser.add_validator(failing_validator)
        config_data = {"key": "value"}
        is_valid, errors = safe_config_parser._validate_config(config_data)  # pylint: disable=protected-access

        assert is_valid is False
        assert errors == ["validation error"]

    def test_validate_config_with_exception_in_validator(self, safe_config_parser):
        """Test validation when validator raises exception."""
        def exception_validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
            raise ValueError("validator crashed")

        safe_config_parser.add_validator(exception_validator)
        config_data = {"key": "value"}
        is_valid, errors = safe_config_parser._validate_config(config_data)  # pylint: disable=protected-access

        assert is_valid is False
        assert len(errors) == 1
        assert "Validator error: validator crashed" in errors[0]


@pytest.mark.unit
class TestSanitizePath:
    """Test path sanitization functionality."""

    def test_sanitize_path_valid_file(self, safe_config_parser, temp_toml_file):
        """Test sanitizing a valid file path."""
        result = safe_config_parser._sanitize_path(temp_toml_file)  # pylint: disable=protected-access
        assert isinstance(result, Path)
        assert result.exists()
        assert result.is_file()

    def test_sanitize_path_string_input(self, safe_config_parser, temp_toml_file):
        """Test sanitizing a string path."""
        result = safe_config_parser._sanitize_path(str(temp_toml_file))  # pylint: disable=protected-access
        assert isinstance(result, Path)
        assert result.exists()

    def test_sanitize_path_nonexistent_file(self, safe_config_parser):
        """Test sanitizing path to nonexistent file."""
        with pytest.raises(ConfigParseError, match="does not exist"):
            safe_config_parser._sanitize_path("/nonexistent/file.toml")  # pylint: disable=protected-access

    def test_sanitize_path_directory(self, safe_config_parser):
        """Test sanitizing path to directory instead of file."""
        with pytest.raises(ConfigParseError, match="not a file"):
            safe_config_parser._sanitize_path("/tmp")  # pylint: disable=protected-access

    def test_sanitize_path_large_file(self, safe_config_parser):
        """Test sanitizing path to overly large file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Create a large file (exceed 10MB limit)
            large_content = "x" * (11 * 1024 * 1024)  # 11MB
            f.write(large_content.encode())
            temp_path = f.name

        try:
            with pytest.raises(ConfigParseError, match="too large"):
                safe_config_parser._sanitize_path(temp_path)  # pylint: disable=protected-access
        finally:
            os.unlink(temp_path)


@pytest.mark.unit
class TestParseTomlFile:
    """Test TOML file parsing functionality."""

    def test_parse_toml_file_valid(self, safe_config_parser, temp_toml_file, sample_toml_config):
        """Test parsing a valid TOML file."""
        result = safe_config_parser._parse_toml_file(temp_toml_file)  # pylint: disable=protected-access
        assert result == sample_toml_config

    def test_parse_toml_file_invalid_syntax(self, safe_config_parser, invalid_toml_file):
        """Test parsing file with invalid TOML syntax."""
        with pytest.raises(ConfigParseError, match="Invalid TOML syntax"):
            safe_config_parser._parse_toml_file(invalid_toml_file)  # pylint: disable=protected-access

    def test_parse_toml_file_permission_denied(self, safe_config_parser):
        """Test parsing file with permission denied."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(ConfigParseError, match="Permission denied"):
                safe_config_parser._parse_toml_file(Path("/test/file.toml"))  # pylint: disable=protected-access

    def test_parse_toml_file_unexpected_error(self, safe_config_parser, temp_toml_file):
        """Test handling unexpected errors during file parsing."""
        with patch("builtins.open", side_effect=OSError("Unexpected error")):
            with pytest.raises(ConfigParseError, match="Unexpected error"):
                safe_config_parser._parse_toml_file(temp_toml_file)  # pylint: disable=protected-access


@pytest.mark.unit
class TestParseTomlString:
    """Test TOML string parsing functionality."""

    def test_parse_toml_string_valid(self, safe_config_parser):
        """Test parsing a valid TOML string."""
        toml_string = '''
        [section]
        key = "value"
        number = 42
        '''
        result = safe_config_parser._parse_toml_string(toml_string)  # pylint: disable=protected-access
        assert result == {"section": {"key": "value", "number": 42}}

    def test_parse_toml_string_invalid_syntax(self, safe_config_parser):
        """Test parsing string with invalid TOML syntax."""
        invalid_toml = "invalid = toml ["
        with pytest.raises(ConfigParseError, match="Invalid TOML syntax"):
            safe_config_parser._parse_toml_string(invalid_toml)  # pylint: disable=protected-access

    def test_parse_toml_string_too_large(self, safe_config_parser):
        """Test parsing overly large TOML string."""
        large_string = "key = 'value'\n" * (1024 * 200)  # Exceed 1MB limit
        with pytest.raises(ConfigParseError, match="too large"):
            safe_config_parser._parse_toml_string(large_string)  # pylint: disable=protected-access


@pytest.mark.unit
class TestParseConfig:
    """Test main parse_config functionality."""

    def test_parse_config_from_dict(self, safe_config_parser, sample_toml_config):
        """Test parsing configuration from dictionary."""
        result = safe_config_parser.parse_config(sample_toml_config)

        assert isinstance(result, ParsedConfig)
        assert result.data == sample_toml_config
        assert result.source == ConfigSource.DICT_OBJECT
        assert result.source_info == "Dictionary object"
        assert result.is_valid is True

    def test_parse_config_from_file(self, safe_config_parser, temp_toml_file, sample_toml_config):
        """Test parsing configuration from file."""
        result = safe_config_parser.parse_config(temp_toml_file)

        assert isinstance(result, ParsedConfig)
        assert result.data == sample_toml_config
        assert result.source == ConfigSource.FILE_PATH
        assert str(temp_toml_file) in result.source_info
        assert result.is_valid is True

    def test_parse_config_from_string(self, safe_config_parser):
        """Test parsing configuration from TOML string."""
        toml_string = '[section]\nkey = "value"'
        result = safe_config_parser.parse_config(toml_string)

        assert isinstance(result, ParsedConfig)
        assert result.data == {"section": {"key": "value"}}
        assert result.source == ConfigSource.STRING_CONTENT
        assert "String content" in result.source_info
        assert result.is_valid is True

    def test_parse_config_with_validation_errors(self, safe_config_parser):
        """Test parsing with validation errors."""
        def failing_validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
            return False, ["test error"]

        safe_config_parser.add_validator(failing_validator)
        result = safe_config_parser.parse_config({"key": "value"})

        assert result.is_valid is False
        assert result.validation_errors == ["test error"]

    def test_parse_config_invalid_input_type(self, safe_config_parser):
        """Test parsing with invalid input type."""
        with pytest.raises(ConfigParseError, match="Unsupported input type"):
            safe_config_parser.parse_config(123)  # Invalid type


@pytest.mark.unit
class TestSafeGetConfig:
    """Test safe_get_config functionality."""

    def test_safe_get_config_success(self, safe_config_parser, sample_toml_config):
        """Test successful configuration retrieval."""
        result = safe_config_parser.safe_get_config(sample_toml_config)
        assert result == sample_toml_config

    def test_safe_get_config_with_default(self, safe_config_parser):
        """Test configuration retrieval with default fallback."""
        with patch.object(safe_config_parser, 'parse_config', side_effect=ConfigParseError("test")):
            default_config = {"default": "value"}
            result = safe_config_parser.safe_get_config("invalid", default=default_config)
            assert result == default_config

    def test_safe_get_config_raise_on_invalid(self, safe_config_parser):
        """Test configuration retrieval with raise_on_invalid=True."""
        def failing_validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
            return False, ["validation failed"]

        safe_config_parser.add_validator(failing_validator)

        with pytest.raises(ConfigValidationError):
            safe_config_parser.safe_get_config(
                {"key": "value"},
                raise_on_invalid=True
            )

    def test_safe_get_config_no_default_on_error(self, safe_config_parser):
        """Test configuration retrieval without default on error."""
        # Test with invalid TOML string that will cause parsing error
        invalid_toml = "invalid = toml ["  # Invalid TOML syntax

        # Without default, should raise exception
        with pytest.raises(ConfigParseError):
            safe_config_parser.safe_get_config(invalid_toml)

        # With default, should return the default
        default_config = {"fallback": True}
        result = safe_config_parser.safe_get_config(invalid_toml, default=default_config)
        assert result == default_config


@pytest.mark.unit
class TestValidators:
    """Test validation helper functions."""

    def test_validate_required_fields_success(self):
        """Test required fields validation with all fields present."""
        validator = validate_required_fields(["field1", "field2"])
        config = {"field1": "value1", "field2": "value2", "extra": "value3"}

        is_valid, errors = validator(config)
        assert is_valid is True
        assert errors == []

    def test_validate_required_fields_missing(self):
        """Test required fields validation with missing fields."""
        validator = validate_required_fields(["field1", "field2", "field3"])
        config = {"field1": "value1"}

        is_valid, errors = validator(config)
        assert is_valid is False
        assert len(errors) == 2
        assert "Required field missing: field2" in errors
        assert "Required field missing: field3" in errors

    def test_validate_field_types_success(self):
        """Test field type validation with correct types."""
        validator = validate_field_types({"name": str, "age": int, "active": bool})
        config = {"name": "John", "age": 30, "active": True}

        is_valid, errors = validator(config)
        assert is_valid is True
        assert errors == []

    def test_validate_field_types_wrong_types(self):
        """Test field type validation with incorrect types."""
        validator = validate_field_types({"name": str, "age": int})
        config = {"name": 123, "age": "thirty"}

        is_valid, errors = validator(config)
        assert is_valid is False
        assert len(errors) == 2
        assert "Field 'name' should be str, got int" in errors
        assert "Field 'age' should be int, got str" in errors

    def test_validate_field_types_missing_fields(self):
        """Test field type validation with missing fields (should pass)."""
        validator = validate_field_types({"name": str, "age": int})
        config = {"name": "John"}  # age is missing but validation should pass

        is_valid, errors = validator(config)
        assert is_valid is True
        assert errors == []
