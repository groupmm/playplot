# Make Plot Playable

This repository contains a Python package called Make Plot Playable, 
which provides the ability to create and sync multiple interactive matplotlib plots to a piece of audio.
Each plot is handled in its one process, allowing smooth animations without a blocking main thread/process.
This package works great inside interactive notebooks, with the limitations, that plots are shown on the machine
where the kernel runs.


## References

Daniel Keitel, Meinard Müller, Christof Weiß and Sebastian Rosenzweig.
Make Plot Playable: A Python Package to Sync Matplotlib Plots to Audio.
To be submitted to the Journal of Open Source Software (JOSS).

## Installing

To use the library just install it via pip.
```pip install make-plot-playable```

To run the examples locally and for development this repository is necessary.

```git clone https://github.com/daniel-keitel/make-plot-playable.git```

All additional dependencies can be found in `requirements.txt`

For a development installation run ```pip install -e .```

## Usage

### Examples

For examples see the `examples` folder of this repository.
These examples need some data to function properly (except ``minimal``)

These files are not provided.
See ``examples/example_data/__init__.py`` for which files are required for specific examples. 
Members of the Audiolabs can find the missing files on lin2 under ``/GroupMM/Students/Work_DK/example_data/``

All examples are currently work in progress and my change drastically.
The ``minimal`` and ``basic`` examples don't have additional dependencies.
``minimal`` doesnt require any extra files.
All files necessary for ``basic`` will be part of the repo.
``intermediate`` and ``advanced`` are WIP (working but suboptimal)

#### Minimal Example

```python
import matplotlib.pyplot as plt
from makeplotplayable import Session

# crate a Session from the audio data (url not final)
session = Session.from_file("https://github.com/meinardmueller/synctoolbox/blob/master/data_music/Schubert_D911-01_HU33.wav?raw=true")

# decorate the plot function with the session
@session
def plot(duration):
    fig, ax = plt.subplots()
    ax.plot([0, duration])
    ax.set_xlabel("number of files played")
    ax.set_ylabel("time in seconds")
    return fig, ax

# call the plot function, it will create the plot in another process
plot(session.duration)

# start the session to enable audio playback
session.start()

# Wait until all plots are closed (not necessary when running interactive)
session.join()
# Check for potential exceptions in the other processes (not necessary when running interactive, an error msg will be displayed)
session.check()
```

### Tests

There are some tests in the `tests` folder.
They mostly focus the process managing and error handling.

### Docs

The documentation is build with sphinx. 
And is hosted on GitHub Pages.

## Contributing
I am happy for suggestions and contributions.
I would be grateful for creating an issue in this Github repository.
Please do not submit a pull request without prior consultation with me.

## Licence

The code for this package is published under an MIT licence.
This does not apply to the data files in ``examples/example_data``.

## Acknowledgements
The International Audio Laboratories Erlangen, which are a joint institution of the Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU) and Fraunhofer Institute for Integrated Circuits IIS. 
We also thank the German Research Foundation (DFG) for various research grants that allowed us for conducting fundamental research in music processing.