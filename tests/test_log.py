#!/usr/bin/env python3

# No need for pytest or os imports
import tempfile
from unittest.mock import patch, MagicMock

from helixerlite.log import startLogging, system_info, finishLogging


class TestLog:
    """Tests for the log module."""

    def test_start_logging(self):
        """Test the startLogging function."""
        # Mock tracemalloc to avoid starting it
        with (
            patch("helixerlite.log.tracemalloc") as mock_tracemalloc,
            patch("helixerlite.log.logging") as mock_logging,
            patch("helixerlite.log.os.path.isfile") as mock_isfile,
            patch("helixerlite.log.os.remove") as mock_remove,
        ):
            # Setup mocks
            mock_logger = MagicMock()
            mock_logging.getLogger.return_value = mock_logger
            mock_formatter = MagicMock()
            mock_logging.Formatter.return_value = mock_formatter
            mock_handler = MagicMock()
            mock_logging.FileHandler.return_value = mock_handler
            mock_console_handler = MagicMock()
            mock_logging.StreamHandler.return_value = mock_console_handler
            mock_isfile.return_value = True  # Simulate file exists

            # Call the function
            with tempfile.NamedTemporaryFile(suffix=".log") as temp_log:
                startLogging(logfile=temp_log.name)  # No need to store the logger

                # Assertions
                mock_tracemalloc.start.assert_called_once()
                mock_logging.getLogger.assert_called_once()
                mock_isfile.assert_called_once_with(temp_log.name)
                mock_remove.assert_called_once_with(temp_log.name)
                mock_logging.FileHandler.assert_called_once_with(temp_log.name)
                assert (
                    mock_logger.addHandler.call_count >= 2
                )  # At least 2 handlers added

    def test_system_info(self):
        """Test the system_info function."""
        # Mock all the imported modules
        with (
            patch("platform.python_version") as mock_python_version,
            patch("helixerlite.log.__version__", "0.1.0"),
            patch("helixerlite.log.tf.__version__", "2.10.0"),
            patch("helixerlite.log.h5py.__version__", "3.7.0"),
            patch("helixerlite.log.pyfastx.__version__", "0.8.4"),
            patch("helixerlite.log.gfftk.__version__", "0.2.0"),
            patch("helixerlite.log.numpy.__version__", "1.23.5"),
        ):
            # Setup mocks
            mock_python_version.return_value = "3.10.0"

            # Create a mock logger function
            mock_logger_func = MagicMock()

            # Call the function
            system_info(mock_logger_func)

            # Assertions
            mock_logger_func.assert_called_once()
            mock_python_version.assert_called_once()

            # Check that the log message contains the version information
            log_message = mock_logger_func.call_args[0][0]
            assert "Python v3.10.0" in log_message
            assert "helixerlite v0.1.0" in log_message
            assert "tensorflow v2.10.0" in log_message
            assert "h5py v3.7.0" in log_message
            assert "pyfastx v0.8.4" in log_message
            assert "gfftk v0.2.0" in log_message
            assert "numpy v1.23.5" in log_message

    def test_finish_logging(self):
        """Test the finishLogging function."""
        # Mock tracemalloc
        with (
            patch("helixerlite.log.tracemalloc") as mock_tracemalloc,
            patch("helixerlite.log.human_readable_size") as mock_human_readable_size,
        ):
            # Setup mocks
            mock_tracemalloc.get_traced_memory.return_value = (
                1000,
                5000,
            )  # current, peak
            mock_human_readable_size.return_value = "5.0 KB"

            # Create a mock logger function
            mock_logger_func = MagicMock()

            # Call the function
            finishLogging(mock_logger_func, "test_module")

            # Assertions
            mock_tracemalloc.get_traced_memory.assert_called_once()
            mock_tracemalloc.stop.assert_called_once()
            mock_human_readable_size.assert_called_once_with(5000)
            mock_logger_func.assert_called_once()

            # Check the log message
            log_message = mock_logger_func.call_args[0][0]
            assert "test_module" in log_message
            assert "finished" in log_message
            assert "peak memory usage=5.0 KB" in log_message
