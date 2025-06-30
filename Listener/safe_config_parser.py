"""

"""

from typing import Dict, Any, Optional, Union, Callable
from pathlib import Path
import tomllib
import logging
from dataclasses import dataclass
from enum import Enum


class ConfigError(Exception):
    """Custom exception for configuration-related errors."""


class ConfigValidationError(ConfigError):
    """Exception raised when configuration validation fails."""


class ConfigParseError(ConfigError):
    """Exception raised when configuration parsing fails."""


class ConfigSource(Enum):
    """Enum to identify the source type of configuration."""

    FILE_PATH = "file_path"
    STRING_CONTENT = "string_content"
    DICT_OBJECT = "dict_object"


@dataclass
class ParsedConfig:
    """Container for parsed configuration with metadata."""

    data: Dict[str, Any]
    source: ConfigSource
    source_info: str
    is_valid: bool = True
    validation_errors: Optional[list] = None


class SafeConfigParser:
    """
    A safe configuration parser that handles TOML files and strings
    with proper validation and error handling.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.validators: list[Callable[[Dict[str, Any]], tuple[bool, list[str]]]] = []

    def add_validator(
        self, validator: Callable[[Dict[str, Any]], tuple[bool, list[str]]]
    ):
        """
        Add a custom validator function.

        Args:
            validator: A function that takes a config dict and returns (is_valid, errors_list)
        """
        self.validators.append(validator)

    def _validate_config(self, config_data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Run all registered validators on the configuration data.

        Args:
            config_data: The configuration dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        all_errors = []

        for validator in self.validators:
            try:
                is_valid, errors = validator(config_data)
                if not is_valid:
                    all_errors.extend(errors)
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                all_errors.append(f"Validator error: {str(e)}")

        return len(all_errors) == 0, all_errors

    def _sanitize_path(self, path_input: Union[str, Path]) -> Path:
        """
        Safely convert and validate a path input.

        Args:
            path_input: The path as string or Path object

        Returns:
            Path object

        Raises:
            ConfigParseError: If path is invalid or unsafe
        """
        try:
            path = Path(path_input).resolve()

            # Basic security checks
            if not path.exists():
                raise ConfigParseError(f"Configuration file does not exist: {path}")

            if not path.is_file():
                raise ConfigParseError(f"Path is not a file: {path}")

            # Check file size (prevent loading extremely large files)
            file_size = path.stat().st_size
            max_size = 10 * 1024 * 1024  # 10MB limit
            if file_size > max_size:
                raise ConfigParseError(
                    f"Configuration file too large: {file_size} bytes (max: {max_size})"
                )

            return path

        except (OSError, IOError) as e:
            raise ConfigParseError(f"Invalid path: {str(e)}") from e

    def _parse_toml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Safely parse a TOML file.

        Args:
            file_path: Path to the TOML file

        Returns:
            Parsed configuration dictionary

        Raises:
            ConfigParseError: If parsing fails
        """
        try:
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigParseError(
                f"Invalid TOML syntax in file {file_path}: {str(e)}"
            ) from e
        except PermissionError as exc:
            raise ConfigParseError(
                f"Permission denied reading file: {file_path}"
            ) from exc
        except (OSError, IOError) as e:
            raise ConfigParseError(
                f"Unexpected error reading file {file_path}: {str(e)}"
            ) from e

    def _parse_toml_string(self, toml_string: str) -> Dict[str, Any]:
        """
        Safely parse a TOML string.

        Args:
            toml_string: TOML content as string

        Returns:
            Parsed configuration dictionary

        Raises:
            ConfigParseError: If parsing fails
        """
        try:
            # Limit string size to prevent memory issues
            max_size = 1024 * 1024  # 1MB limit
            if len(toml_string) > max_size:
                raise ConfigParseError(
                    f"TOML string too large: {len(toml_string)} characters (max: {max_size})"
                )

            return tomllib.loads(toml_string)
        except tomllib.TOMLDecodeError as e:
            raise ConfigParseError(f"Invalid TOML syntax in string: {str(e)}") from e
        except (ValueError, TypeError, MemoryError) as e:
            raise ConfigParseError(
                f"Unexpected error parsing TOML string: {str(e)}"
            ) from e

    def parse_config(
        self, input_data: Union[str, Path, Dict[str, Any]]
    ) -> ParsedConfig:
        """
        Safely parse configuration from various input types.

        Args:
            input_data: Can be a file path, TOML string, or dictionary

        Returns:
            ParsedConfig object with parsed data and metadata
        """
        try:
            # Determine input type and parse accordingly
            if isinstance(input_data, dict):
                config_data = input_data.copy()
                source = ConfigSource.DICT_OBJECT
                source_info = "Dictionary object"
                self.logger.info("Parsing configuration from dictionary object")

            elif isinstance(input_data, (str, Path)):
                # Check if it's a file path or TOML string
                try:
                    path = Path(input_data)
                    if path.exists() and path.is_file():
                        # It's a file path
                        safe_path = self._sanitize_path(path)
                        config_data = self._parse_toml_file(safe_path)
                        source = ConfigSource.FILE_PATH
                        source_info = str(safe_path)
                        self.logger.info(
                            "Parsing configuration from file: %s", safe_path
                        )
                    else:
                        # It's a TOML string
                        config_data = self._parse_toml_string(str(input_data))
                        source = ConfigSource.STRING_CONTENT
                        source_info = (
                            f"String content ({len(str(input_data))} characters)"
                        )
                        self.logger.info("Parsing configuration from TOML string")
                except (OSError, ValueError, TypeError):
                    # If path checking fails, treat as TOML string
                    config_data = self._parse_toml_string(str(input_data))
                    source = ConfigSource.STRING_CONTENT
                    source_info = f"String content ({len(str(input_data))} characters)"
                    self.logger.info("Parsing configuration from TOML string")
            else:
                raise ConfigParseError(f"Unsupported input type: {type(input_data)}")

            # Validate the parsed configuration
            is_valid, validation_errors = self._validate_config(config_data)

            if not is_valid:
                self.logger.warning(
                    "Configuration validation failed: %s", validation_errors
                )

            result = ParsedConfig(
                data=config_data,
                source=source,
                source_info=source_info,
                is_valid=is_valid,
                validation_errors=validation_errors if not is_valid else None,
            )

            self.logger.info("Successfully parsed configuration from %s", source_info)
            return result

        except (ValueError, TypeError, OSError) as e:
            # Catch any unexpected errors
            self.logger.error("Unexpected error parsing configuration: %s", str(e))
            raise ConfigParseError(f"Unexpected error: {str(e)}") from e

    def safe_get_config(
        self,
        input_data: Union[str, Path, Dict[str, Any]],
        default: Optional[Dict[str, Any]] = None,
        raise_on_invalid: bool = False,
    ) -> Dict[str, Any]:
        """
        Safely get configuration dictionary with fallback options.

        Args:
            input_data: Configuration input (file path, TOML string, or dict)
            default: Default configuration to return if parsing fails
            raise_on_invalid: Whether to raise exception on validation failure

        Returns:
            Configuration dictionary

        Raises:
            ConfigError: If parsing fails and no default is provided
        """
        try:
            parsed_config = self.parse_config(input_data)

            if not parsed_config.is_valid and raise_on_invalid:
                raise ConfigValidationError(
                    f"Configuration validation failed: {parsed_config.validation_errors}"
                )

            return parsed_config.data

        except ConfigError as e:
            self.logger.error("Configuration parsing failed: %s", str(e))
            if default is not None:
                self.logger.info("Using default configuration")
                return default
            raise
        except (ValueError, TypeError, OSError) as e:
            self.logger.error("Unexpected error in safe_get_config: %s", str(e))
            if default is not None:
                self.logger.info("Using default configuration due to unexpected error")
                return default
            raise ConfigError(f"Unexpected error: {str(e)}") from e


# Example validator functions
def validate_required_fields(
    required_fields: list[str],
) -> Callable[[Dict[str, Any]], tuple[bool, list[str]]]:
    """
    Create a validator that checks for required fields.

    Args:
        required_fields: List of field names that must be present

    Returns:
        Validator function
    """

    def validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
        errors = []
        for field in required_fields:
            if field not in config:
                errors.append(f"Required field missing: {field}")
        return len(errors) == 0, errors

    return validator


def validate_field_types(
    field_types: Dict[str, type]
) -> Callable[[Dict[str, Any]], tuple[bool, list[str]]]:
    """
    Create a validator that checks field types.

    Args:
        field_types: Dictionary mapping field names to expected types

    Returns:
        Validator function
    """

    def validator(config: Dict[str, Any]) -> tuple[bool, list[str]]:
        errors = []
        for field, expected_type in field_types.items():
            if field in config and not isinstance(config[field], expected_type):
                errors.append(
                    f"Field '{field}' should be {expected_type.__name__}, got {type(config[field]).__name__}"
                )
        return len(errors) == 0, errors

    return validator
