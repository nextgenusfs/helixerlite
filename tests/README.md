# Tests for helixerlite

This directory contains tests for the helixerlite package.

## Running Tests

You can run the tests using pytest:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=helixerlite

# Run specific test file
pytest tests/test_helixerpost.py
```

## Test Structure

- `test_helixerpost.py`: Tests for the Rust bindings
- `test_hdf5.py`: Tests for the HDF5 handling functionality
- `test_utilities.py`: Tests for utility functions
- `test_integration.py`: Integration tests for the full pipeline
- `test_fasta_to_hdf5.py`: Tests for the fasta2hdf5 function

## Test Data

The tests use the following data files:

- `genome.fasta`: A sample genome FASTA file for testing
- `genome_data.h5`: A sample HDF5 file containing genome data
- `predictions.h5`: A sample HDF5 file containing predictions

## Adding New Tests

When adding new functionality, please also add corresponding tests. Follow the existing test structure and naming conventions.