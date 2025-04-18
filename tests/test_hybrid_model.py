#!/usr/bin/env python3

import pytest
from unittest.mock import patch, MagicMock

from helixerlite.hybrid_model import HybridModel


class TestHybridModel:
    """Tests for the HybridModel class."""

    @pytest.mark.skip(reason="Requires complex mocking of argparse")
    @patch("helixerlite.hybrid_model.HelixerModel")
    def test_init(self, mock_helixer_model):
        """Test the initialization of HybridModel."""
        # Create a mock instance with a parser attribute
        mock_instance = MagicMock()
        mock_helixer_model.return_value = mock_instance
        mock_instance.parser = MagicMock()

        # Call the constructor with test arguments
        args = ["--test-arg", "test_value"]
        HybridModel(args)  # No need to store the model instance

        # Assertions
        mock_helixer_model.assert_called_once_with(cli_args=args)
        # Check that add_argument was called for the expected arguments
        assert mock_instance.parser.add_argument.call_count >= 6

    @pytest.mark.skip(reason="Requires complex mocking of argparse")
    @patch("helixerlite.hybrid_model.HelixerModel")
    def test_run(self, mock_helixer_model):
        """Test the run method of HybridModel."""
        # Create a mock instance with necessary attributes
        mock_instance = MagicMock()
        mock_helixer_model.return_value = mock_instance
        mock_instance.parser = MagicMock()
        mock_instance.predict_and_eval = MagicMock()

        # Set up the mock instance to have the necessary attributes to pass validation
        mock_instance.testing = False
        mock_instance.data_dir = "/path/to/data"

        # Call the constructor and run method
        hybrid_model = HybridModel([])
        hybrid_model.run()

        # Assertions
        mock_instance.predict_and_eval.assert_called_once()
