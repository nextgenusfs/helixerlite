# Helixerlite: Simplified Gene Prediction using Helixer and HelixerPost

This is a lightweight "predict-only" version of [Helixer](https://github.com/weberlab-hhu/Helixer) and [HelixerPost](https://github.com/TonyBolger/HelixerPost). Helixer is written in Python and contains many utilities for training models that aren't needed for end users who just want to predict genes in a genome. For smaller eukaryotic genomes, a GPU is not necessary for prediction. On average Ascomycete fungal genomes (~30 Mb), `helixerlite` should take less than 20 minutes to run.

HelixerPost is written in Rust and is in a separate repository, which makes installing a single tool cumbersome. By using `maturin` and `pyO3`, we wrap the Rust code into Python and run it as a single command-line tool.

## Features

- Convert FASTA files to HDF5 format for Helixer
- Run gene prediction using a pre-trained Helixer model
- Convert predictions to GFF3 format
- Lightweight and easy to install
- No GPU required for smaller genomes

## Installation

Installation can be done with `pip` or other tools able to install from PyPI, such as `uv`:

```bash
python -m pip install helixerlite
```

## Usage

### Command-line Interface

HelixerLite provides a simple command-line interface:

```bash

# Run prediction
helixerlite --fasta genome.fasta --lineage fungi --out output.gff3 
```

### Python API

You can also use HelixerLite as a Python library:

```python
from helixerlite import fasta2hdf5, preds2gff3
from helixerlite.hybrid_model import HybridModel

# Convert FASTA to HDF5
fasta2hdf5("genome.fasta", "genome.h5")

# Run prediction
model = HybridModel(["--load-model-path", "path/to/model",
                     "--test-data", "genome.h5",
                     "--prediction-output-path", "predictions.h5"])
model.run()

# Convert predictions to GFF3
preds2gff3("genome.h5", "predictions.h5", "output.gff3")
```

## Requirements

- Python 3.8 or higher
- TensorFlow 2.10 or higher
- h5py
- pyfastx
- gfftk

## Development

### Setting up a development environment

```bash
# Clone the repository
git clone https://github.com/nextgenusfs/helixerlite.git
cd helixerlite

# Create a conda environment
conda create -n helixerlite python=3.10
conda activate helixerlite

# Install development dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
python -m pytest
```

## Citation

Anybody using this repo should cite the original Helixer authors, manuscript, code, etc.

Felix Holst, Anthony Bolger, Christopher Günther, Janina Maß, Sebastian Triesch, Felicitas Kindel, Niklas Kiel, Nima Saadat, Oliver Ebenhöh, Björn Usadel, Rainer Schwacke, Marie Bolger, Andreas P.M. Weber, Alisandra K. Denton. Helixer—de novo Prediction of Primary Eukaryotic Gene Models Combining Deep Learning and a Hidden Markov Model. bioRxiv 2023.02.06.527280; doi: https://doi.org/10.1101/2023.02.06.527280