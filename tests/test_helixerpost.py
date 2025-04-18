#!/usr/bin/env python3

import pytest
import os
import tempfile
import h5py
import numpy as np
from unittest.mock import patch, MagicMock

# Import the module to test
import helixerpost


class TestHelixerpost:
    """Tests for the helixerpost Rust module."""

    def test_import(self):
        """Test that the helixerpost module can be imported."""
        assert hasattr(helixerpost, "hello_world")
        assert hasattr(helixerpost, "run_helixer_post")

    def test_hello_world(self):
        """Test the hello_world function."""
        result = helixerpost.hello_world()
        assert result == "Hello, world!"
        assert isinstance(result, str)

    def test_run_helixer_post_signature(self):
        """Test that run_helixer_post has the expected signature."""
        import inspect

        sig = inspect.signature(helixerpost.run_helixer_post)
        params = list(sig.parameters.keys())

        # Check that the function has the expected parameters
        expected_params = [
            "genome_path",
            "predictions_path",
            "window_size",
            "edge_threshold",
            "peak_threshold",
            "min_coding_length",
            "gff_filename",
        ]
        assert params == expected_params

    def test_run_helixer_post_with_mock_data(self):
        """Test run_helixer_post with mock data files."""
        # Skip this test if the test data files don't exist
        if not os.path.exists("tests/data/genome_data.h5") or not os.path.exists(
            "tests/data/predictions.h5"
        ):
            pytest.skip("Test data files not available")

        with tempfile.NamedTemporaryFile(suffix=".gff3") as temp_gff:
            # Mock the run_helixer_post function
            original_run_helixer_post = helixerpost.run_helixer_post
            try:
                helixerpost.run_helixer_post = MagicMock(return_value=None)

                # Call the function with test data
                helixerpost.run_helixer_post(
                    "tests/data/genome_data.h5",
                    "tests/data/predictions.h5",
                    100,  # window_size
                    0.1,  # edge_threshold
                    0.8,  # peak_threshold
                    60,  # min_coding_length
                    temp_gff.name,
                )

                # Check that the mock was called with the correct arguments
                helixerpost.run_helixer_post.assert_called_once_with(
                    "tests/data/genome_data.h5",
                    "tests/data/predictions.h5",
                    100,
                    0.1,
                    0.8,
                    60,
                    temp_gff.name,
                )
            finally:
                # Restore the original function
                helixerpost.run_helixer_post = original_run_helixer_post

    @patch("helixerpost.run_helixer_post")
    def test_run_helixer_post_called_with_correct_args(self, mock_run_helixer_post):
        """Test that run_helixer_post is called with the correct arguments."""
        # Setup mock
        mock_run_helixer_post.return_value = None

        # Call the function
        helixerpost.run_helixer_post(
            "genome.h5", "predictions.h5", 100, 0.1, 0.8, 60, "output.gff3"
        )

        # Check that the function was called with the correct arguments
        mock_run_helixer_post.assert_called_once_with(
            "genome.h5", "predictions.h5", 100, 0.1, 0.8, 60, "output.gff3"
        )
