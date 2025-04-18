#!/usr/bin/env python3

import pytest
import os
from unittest.mock import patch, MagicMock

from helixerlite.utilities import (
    download,
    runprocess,
    preds2gff3,
    prediction2gff3,
    check_inputs,
    is_file,
    which2,
)


class TestUtilities:
    """Tests for the utilities module."""

    def test_download(self):
        """Test the download function."""
        with (
            patch("helixerlite.utilities.urlopen") as mock_urlopen,
            patch("builtins.open", create=True) as mock_open,
        ):
            # Setup mocks
            mock_response = MagicMock()
            # First call returns data, second call returns empty to exit the loop
            mock_response.read.side_effect = [b"test data", b""]
            mock_urlopen.return_value = mock_response

            mock_file = MagicMock()
            mock_open.return_value = mock_file

            # Call the function
            download("http://example.com/file.txt", "output.txt")

            # Assertions
            mock_urlopen.assert_called_once_with("http://example.com/file.txt")
            mock_open.assert_called_once_with("output.txt", "wb")
            mock_file.write.assert_called_once_with(b"test data")
            assert mock_response.read.call_count == 2

    @patch("helixerlite.utilities.subprocess.Popen")
    def test_runprocess_with_stdout_stderr(self, mock_popen):
        """Test runprocess with stdout and stderr capture."""
        # Setup mock
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"stdout output", b"stderr output")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Create temporary files for stdout and stderr
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            # Call the function
            runprocess(
                ["echo", "test"], stdout="stdout.txt", stderr="stderr.txt"
            )  # No need to store the result

            # Assertions
            mock_popen.assert_called_once()
            # Check that open was called with the correct arguments
            mock_open.assert_any_call("stdout.txt", "w")
            mock_open.assert_any_call("stderr.txt", "w")

    @patch("helixerlite.utilities.subprocess.Popen")
    def test_runprocess_without_stdout_stderr(self, mock_popen):
        """Test runprocess without stdout and stderr capture."""
        # Setup mock
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Call the function
        result = runprocess(["echo", "test"])

        # Assertions
        mock_popen.assert_called_once()
        assert result is None

    @patch("helixerlite.utilities.helixerpost.run_helixer_post")
    def test_preds2gff3(self, mock_run_helixer_post):
        """Test the preds2gff3 function."""
        # Call the function with default parameters
        preds2gff3("genome.h5", "predictions.h5", "output.gff3")

        # Check that run_helixer_post was called with the correct arguments
        mock_run_helixer_post.assert_called_once_with(
            "genome.h5",
            "predictions.h5",
            100,  # default window_size
            0.1,  # default edge_threshold
            0.8,  # default peak_threshold
            60,  # default min_coding_length
            "output.gff3",
        )

        # Reset mock
        mock_run_helixer_post.reset_mock()

        # Call the function with custom parameters
        preds2gff3(
            "genome.h5",
            "predictions.h5",
            "output.gff3",
            window_size=200,
            edge_threshold=0.2,
            peak_threshold=0.9,
            min_coding_length=100,
        )

        # Check that run_helixer_post was called with the custom arguments
        mock_run_helixer_post.assert_called_once_with(
            "genome.h5", "predictions.h5", 200, 0.2, 0.9, 100, "output.gff3"
        )

    @patch("helixerlite.utilities.runprocess")
    def test_prediction2gff3(self, mock_runprocess):
        """Test the prediction2gff3 function."""
        # Call the function
        prediction2gff3("genome.h5", "predictions.h5", "output.gff3")

        # Check that runprocess was called with the correct arguments
        mock_runprocess.assert_called_once_with(
            [
                "helixer_post_bin",
                "genome.h5",
                "predictions.h5",
                "100",
                "0.1",
                "0.8",
                "60",
                "output.gff3",
            ]
        )

        # Reset mock
        mock_runprocess.reset_mock()

        # Call the function with custom parameters
        prediction2gff3(
            "genome.h5",
            "predictions.h5",
            "output.gff3",
            window_size=200,
            edge_threshold=0.2,
            peak_threshold=0.9,
            min_coding_length=100,
        )

        # Check that runprocess was called with the custom arguments
        mock_runprocess.assert_called_once_with(
            [
                "helixer_post_bin",
                "genome.h5",
                "predictions.h5",
                "200",
                "0.2",
                "0.9",
                "100",
                "output.gff3",
            ]
        )

    @patch("helixerlite.utilities.is_file")
    def test_check_inputs(self, mock_is_file):
        """Test the check_inputs function."""
        # Setup mock
        mock_is_file.return_value = True

        # Call the function with valid inputs
        check_inputs(["file1.txt", "file2.txt"])

        # Assertions
        assert mock_is_file.call_count == 2
        mock_is_file.assert_any_call("file1.txt")
        mock_is_file.assert_any_call("file2.txt")

        # Reset mock
        mock_is_file.reset_mock()

        # Setup mock for invalid input
        mock_is_file.return_value = False

        # Call the function with invalid inputs
        with pytest.raises(FileNotFoundError):
            check_inputs(["file1.txt"])

        # Assertions
        mock_is_file.assert_called_once_with("file1.txt")

    @patch("os.path.isfile")
    def test_is_file(self, mock_isfile):
        """Test the is_file function."""
        # Setup mock for existing file
        mock_isfile.return_value = True

        # Call the function with existing file
        result = is_file("existing_file.txt")

        # Assertions
        assert result is True
        mock_isfile.assert_called_once_with("existing_file.txt")

        # Reset mock
        mock_isfile.reset_mock()

        # Setup mock for non-existing file
        mock_isfile.return_value = False

        # Call the function with non-existing file
        result = is_file("non_existing_file.txt")

        # Assertions
        assert result is False
        mock_isfile.assert_called_once_with("non_existing_file.txt")

    @patch("os.path.isfile")
    @patch("os.access")
    def test_which2(self, mock_access, mock_isfile):
        """Test the which2 function."""
        # Setup mocks for existing command
        mock_isfile.return_value = True
        mock_access.return_value = True

        # Mock the PATH environment variable
        with patch.dict("os.environ", {"PATH": "/usr/bin:/usr/local/bin"}):
            # Call the function with existing command
            result = which2("python")

            # Assertions
            assert result == "/usr/bin/python"
            mock_isfile.assert_any_call("/usr/bin/python")
            mock_access.assert_any_call("/usr/bin/python", os.X_OK)

            # Reset mocks
            mock_isfile.reset_mock()
            mock_access.reset_mock()

            # Setup mocks for non-existing command
            mock_isfile.return_value = False

            # Call the function with non-existing command
            result = which2("non_existing_command")

            # Assertions
            assert result is None
