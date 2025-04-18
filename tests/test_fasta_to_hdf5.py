#!/usr/bin/env python3

from helixerlite.__main__ import fasta2hdf5

import pytest


class TestFasta2hdf5:
    """Tests for the fasta2hdf5 function in __main__.py."""

    def test_convert_valid_fasta_to_hdf5(self, mocker):
        """Test that fasta2hdf5 calls HelixerFastaToH5Controller with the correct parameters."""
        # Mock the HelixerFastaToH5Controller to avoid actual file operations
        mock_controller = mocker.patch(
            "helixerlite.__main__.HelixerFastaToH5Controller", autospec=True
        )
        mock_instance = mock_controller.return_value

        # Call the function
        fasta = "tests/genome.fasta"
        hdout = "tests/output.h5"
        fasta2hdf5(fasta, hdout)

        # Assert that the controller was created with the correct parameters
        mock_controller.assert_called_once_with(fasta, hdout)

        # Assert that the export_fasta_to_h5 method was called with the correct parameters
        mock_instance.export_fasta_to_h5.assert_called_once_with(
            chunk_size=21384,
            compression="gzip",
            multiprocess=True,
            species=mocker.ANY,
            write_by=20_000_000,
        )

    def test_convert_with_custom_parameters(self, mocker):
        """Test fasta2hdf5 with custom parameters."""
        # Mock the HelixerFastaToH5Controller
        mock_controller = mocker.patch(
            "helixerlite.__main__.HelixerFastaToH5Controller", autospec=True
        )
        mock_instance = mock_controller.return_value

        # Call the function with custom parameters
        fasta = "tests/genome.fasta"
        hdout = "tests/output.h5"
        subseqlen = 1000
        species = "test_species"
        fasta2hdf5(fasta, hdout, subseqlen=subseqlen, species=species)

        # Assert that the controller was created with the correct parameters
        mock_controller.assert_called_once_with(fasta, hdout)

        # Assert that the export_fasta_to_h5 method was called with the correct parameters
        mock_instance.export_fasta_to_h5.assert_called_once_with(
            chunk_size=subseqlen,
            compression="gzip",
            multiprocess=True,
            species=species,
            write_by=20_000_000,
        )
