## Helixerlite: simplified gene prediction using Helixer and HelixerPost

This is an attempt to create a "predict-only" version of [Helixer](https://github.com/weberlab-hhu/Helixer) and [HelixerPost](https://github.com/TonyBolger/HelixerPost). Helixer is written in python and has a whole bunch of extra utilities/code used for training the models, etc --> however, this is not needed for end user just trying to use the model to do gene prediction in a genome.  Also, for smaller eukaryotic genomes, GPU is not necessary for prediction.  On somewhat average Ascomycete fungal genomes (~ 30 Mb), `helixerlite` should take less than 20 minutes to run.  HelixerPost is written in rust and is in a separate repository, which makes installing a single tool a little bit cumbersome. By using `maturin` and `pyO3` we can wrap the rust code into Python and run it as a single command-line-tool. 

My hope is that Helixer developers can re-vamp their codebase to make a "helixer-predict" based on what I've done here so that future updates to the codebase can be incorporated. 

#### Installation

Installation can be done with `pip` or other tools able to install from PyPi, ie `uv`. 

```
python -m pip install helixerlite
```

#### Anybody using this repo should cite the original Helixer authors, manuscript, code, etc.

Felix Holst, Anthony Bolger, Christopher Günther, Janina Maß, Sebastian Triesch, Felicitas Kindel, Niklas Kiel, Nima Saadat, Oliver Ebenhöh, Björn Usadel, Rainer Schwacke, Marie Bolger, Andreas P.M. Weber, Alisandra K. Denton. Helixer—de novo Prediction of Primary Eukaryotic Gene Models Combining Deep Learning and a Hidden Markov Model. bioRxiv 2023.02.06.527280; doi: https://doi.org/10.1101/2023.02.06.527280