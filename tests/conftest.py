#!/usr/bin/env python3

import pytest
import os
import tempfile
import h5py
import numpy as np


@pytest.fixture
def temp_fasta_file():
    """Create a temporary FASTA file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.fasta', mode='w+') as fasta_file:
        fasta_file.write(">seq1\nACGT\n>seq2\nTGCA\n")
        fasta_file.flush()
        yield fasta_file.name


@pytest.fixture
def temp_h5_file():
    """Create a temporary HDF5 file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.h5') as h5_file:
        yield h5_file.name


@pytest.fixture
def temp_gff_file():
    """Create a temporary GFF3 file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.gff3') as gff_file:
        yield gff_file.name


@pytest.fixture
def mock_h5_data():
    """Create mock HDF5 data for testing."""
    with tempfile.NamedTemporaryFile(suffix='.h5') as h5_file:
        with h5py.File(h5_file.name, 'w') as f:
            # Create datasets
            f.create_dataset('/data/X', data=np.zeros((10, 4)))
            f.create_dataset('/data/species', data=np.array(['test_species'] * 10, dtype='S20'))
            f.create_dataset('/data/seqids', data=np.array(['seq1'] * 10, dtype='S20'))
            f.create_dataset('/data/start_ends', data=np.zeros((10, 2), dtype=np.int32))
            
            # Set attributes
            f.attrs['timestamp'] = 'test_timestamp'
            f.attrs['input_path'] = 'test_input_path'
        
        yield h5_file.name
