"""Tests for logger utility."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.utils.logger import setup_logger


class TestSetupLogger:
    """Test the setup_logger function."""

    def test_setup_logger_default_params(self):
        """Test setup_logger with default parameters."""
        logger = setup_logger("unique_test_logger_1")

        assert logger.name == "unique_test_logger_1"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 2  # console and file handlers

        # Check console handler
        console_handler = logger.handlers[0]
        assert isinstance(console_handler, logging.StreamHandler)
        assert console_handler.level == logging.INFO

        # Check file handler
        file_handler = logger.handlers[1]
        assert isinstance(file_handler, logging.handlers.RotatingFileHandler)
        assert file_handler.level == logging.DEBUG

    def test_setup_logger_custom_name(self):
        """Test setup_logger with custom name."""
        logger = setup_logger("custom_logger")

        assert logger.name == "custom_logger"
        assert logger.level == logging.INFO

    def test_setup_logger_custom_level(self):
        """Test setup_logger with custom level."""
        logger = setup_logger("test", "DEBUG")

        assert logger.name == "test"
        assert logger.level == logging.DEBUG

    def test_setup_logger_invalid_level(self):
        """Test setup_logger with invalid level defaults to INFO."""
        with pytest.raises(AttributeError):
            setup_logger("test", "INVALID")

    @patch('pathlib.Path.mkdir')
    def test_setup_logger_creates_log_directory(self, mock_mkdir):
        """Test that setup_logger creates the log directory."""
        with patch('logging.handlers.RotatingFileHandler'):
            setup_logger()

            # Verify directory creation was called
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_setup_logger_file_handler_configuration(self):
        """Test file handler configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            with patch('src.utils.logger.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.mkdir = MagicMock()
                mock_path_instance.__truediv__ = MagicMock(return_value=log_dir / "kiotviet.log")
                mock_path_instance.parent = MagicMock()
                mock_path_instance.parent.parent = MagicMock()
                mock_path_instance.parent.parent.__truediv__ = MagicMock(return_value=log_dir)

                mock_path.return_value = mock_path_instance

                logger = setup_logger("unique_test_logger_3")

                file_handler = logger.handlers[1]
                assert isinstance(file_handler, logging.handlers.RotatingFileHandler)

                # Check maxBytes and backupCount
                assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
                assert file_handler.backupCount == 5

    def test_setup_logger_formatter_configuration(self):
        """Test that formatters are properly configured."""
        logger = setup_logger()

        console_handler = logger.handlers[0]
        file_handler = logger.handlers[1]

        # Check console formatter
        console_formatter = console_handler.formatter
        assert "%(asctime)s" in console_formatter._fmt
        assert "%(name)s" in console_formatter._fmt
        assert "%(levelname)s" in console_formatter._fmt
        assert "%(message)s" in console_formatter._fmt

        # Check file formatter
        file_formatter = file_handler.formatter
        assert "%(asctime)s" in file_formatter._fmt
        assert "%(name)s" in file_formatter._fmt
        assert "%(levelname)s" in file_formatter._fmt
        assert "%(filename)s" in file_formatter._fmt
        assert "%(lineno)d" in file_formatter._fmt
        assert "%(message)s" in file_formatter._fmt

    def test_setup_logger_returns_same_instance(self):
        """Test that setup_logger returns the same logger instance for same name."""
        logger1 = setup_logger("test_logger")
        logger2 = setup_logger("test_logger")

        assert logger1 is logger2

    def test_setup_logger_different_instances(self):
        """Test that setup_logger returns different instances for different names."""
        logger1 = setup_logger("logger1")
        logger2 = setup_logger("logger2")

        assert logger1 is not logger2