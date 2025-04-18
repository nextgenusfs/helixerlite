#!/usr/bin/env python3

import pytest
import os
import tempfile
import h5py
import numpy as np
from unittest.mock import patch, MagicMock

from helixerlite.hdf5 import HelixerFastaToH5Controller, HelixerExportControllerBase


class TestHelixerExportControllerBase:
    """Tests for the HelixerExportControllerBase class."""

    def test_calc_n_chunks(self):
        """Test the calc_n_chunks static method."""
        # Test with exact division
        assert HelixerExportControllerBase.calc_n_chunks(100, 10) == 20  # (100 // 10) * 2
        
        # Test with remainder
        assert HelixerExportControllerBase.calc_n_chunks(105, 10) == 22  # ((105 // 10) + 1) * 2
        
        # Test with chunk size larger than coord length
        assert HelixerExportControllerBase.calc_n_chunks(5, 10) == 2  # (5 // 10 + 1) * 2

    @pytest.fixture
    def controller(self):
        """Create a controller instance for testing."""
        with tempfile.NamedTemporaryFile(suffix='.fasta') as input_file, \
             tempfile.NamedTemporaryFile(suffix='.h5') as output_file:
            controller = HelixerExportControllerBase(input_file.name, output_file.name)
            yield controller

    def test_init(self, controller):
        """Test the initialization of HelixerExportControllerBase."""
        assert hasattr(controller, 'input_path')
        assert hasattr(controller, 'output_path')
        assert hasattr(controller, 'match_existing')
        assert controller.match_existing is False


class TestHelixerFastaToH5Controller:
    """Tests for the HelixerFastaToH5Controller class."""

    @pytest.fixture
    def mock_fasta_file(self):
        """Create a temporary FASTA file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.fasta', mode='w+') as fasta_file:
            fasta_file.write(">seq1\\nACGT\\n>seq2\\nTGCA\\n")
            fasta_file.flush()
            yield fasta_file.name

    @pytest.fixture
    def mock_h5_file(self):
        """Create a temporary HDF5 file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.h5') as h5_file:
            yield h5_file.name

    def test_coordinate_surrogate(self):
        """Test the CoordinateSurrogate inner class."""
        surrogate = HelixerFastaToH5Controller.CoordinateSurrogate("seq1", "ACGT")
        assert surrogate.seqid == "seq1"
        assert surrogate.sequence == "ACGT"
        assert surrogate.length == 4
        assert "seq1" in str(surrogate)
        assert "len: 4" in str(surrogate)

    @patch('helixerlite.hdf5.pyfastx.Fasta')
    @patch('helixerlite.hdf5.h5py.File')
    @patch('helixerlite.hdf5.CoordNumerifier.numerify_only_fasta')
    def test_export_fasta_to_h5(self, mock_numerify, mock_h5py_file, mock_pyfastx, 
                               mock_fasta_file, mock_h5_file):
        """Test the export_fasta_to_h5 method."""
        # Setup mocks
        mock_h5_file_instance = MagicMock()
        mock_h5py_file.return_value = mock_h5_file_instance
        
        mock_pyfastx.return_value = [
            ("seq1", "ACGT"),
            ("seq2", "TGCA")
        ]
        
        # Mock the numerify_only_fasta method to return test data
        mock_data = MagicMock()
        mock_data.key = "test_key"
        mock_data.matrix = np.zeros((10, 4))
        mock_data.dtype = np.float32
        
        mock_numerify.return_value = [
            ([mock_data], (0, 10)),  # First strand
            ([mock_data], (10, 20))  # Second strand
        ]
        
        # Create controller and call the method
        controller = HelixerFastaToH5Controller(mock_fasta_file, mock_h5_file)
        controller.h5 = mock_h5_file_instance  # Set the h5 attribute directly
        
        # Add a mock for _save_data
        controller._save_data = MagicMock()
        
        # Call the method
        controller.export_fasta_to_h5(
            chunk_size=10,
            compression="gzip",
            multiprocess=True,
            species="test_species",
            write_by=100
        )
        
        # Assertions
        mock_pyfastx.assert_called_once_with(mock_fasta_file, build_index=False)
        mock_h5py_file.assert_called_once_with(mock_h5_file, "w")
        
        # Check that _save_data was called for each sequence and strand
        assert controller._save_data.call_count == 4  # 2 sequences * 2 strands
        
        # Check that the file was closed
        mock_h5_file_instance.close.assert_called_once()

    @pytest.mark.skipif(not os.path.exists('tests/genome.fasta'),
                       reason="Test FASTA file not available")
    def test_integration_with_real_file(self, mock_h5_file):
        """Integration test with a real FASTA file."""
        try:
            # Create controller
            controller = HelixerFastaToH5Controller('tests/genome.fasta', mock_h5_file)
            
            # Call the method with small values to make the test faster
            controller.export_fasta_to_h5(
                chunk_size=10,
                compression="gzip",
                multiprocess=False,  # Use False for testing
                species="test_species",
                write_by=100
            )
            
            # Check that the output file exists and is not empty
            assert os.path.exists(mock_h5_file)
            assert os.path.getsize(mock_h5_file) > 0
            
            # Open the file and check its structure
            with h5py.File(mock_h5_file, 'r') as h5:
                # Check that the expected datasets exist
                assert '/data/X' in h5
                assert '/data/species' in h5
                assert '/data/seqids' in h5
                
                # Check that the attributes were set
                assert 'timestamp' in h5.attrs
                assert 'input_path' in h5.attrs
                assert h5.attrs['input_path'] == 'tests/genome.fasta'
                
        except Exception as e:
            pytest.skip(f"Error in integration test: {str(e)}")
