# Playplot

This repository contains a Python package called Playplot, 
which provides the ability to create and sync multiple interactive matplotlib plots to a piece of audio.
Each plot is handled in its own process, allowing smooth animations without a blocking main thread/process.
This package works great inside interactive notebooks, with the limitations, that plots are shown on the machine
where the kernel runs.


## References

Daniel Keitel, Meinard Müller, Christof Weiß and Sebastian Rosenzweig.
Playplot: A Python Package to Sync Matplotlib Plots to Audio.
To be submitted to the Journal of Open Source Software (JOSS).

## Installing

To use the library just install it via pip.
```pip install playplot```

To run the examples locally and for development this repository is necessary.

```git clone https://github.com/groupmm/playplot.git```

For a development installation run ```python -m pip install -e .```

All additional dependencies can be installed via ```python -m pip --r requirements.txt```

## Usage

### Examples

For examples see the `examples` folder of this repository.
These examples need some local data to function properly (except ``minimal``)

Those files are provided for all examples except for ``advanced``.
See ``examples/example_data/__init__.py`` for which files are additionally required. 
Members of the Audiolabs can find the missing files on lin2 under ``/GroupMM/Students/Work_DK/example_data/``

The ``minimal`` and ``basic`` examples don't have additional dependencies.
``intermediate`` requires ``libfmp`` (can be installed via ``python -m pip install libfmp``)
``advanced`` has the most dependencies. I recommend installing from the requirements.txt files. (``python -m pip install -r requirements.txt``) 

#### Minimal Example

```python
import matplotlib.pyplot as plt
from playplot import Session

# create a Session from the audio data (url not final)
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

The documentation is built with sphinx.
It is hosted on GitHub Pages.

## Contributing
I am happy for suggestions and contributions.
I would be grateful for creating an issue in this GitHub repository.
Please do not submit a pull request without prior consultation with me.

## Licence

The code for this package is published under an MIT licence.
This does not apply to the data files in ``examples/example_data``.

## Acknowledgements
This library was initially created for a project in my master's degree in computer science.
Under the suppervision of Prof. Dr. Meinard Müller, Dr. Christof Weiß and (Dr.) Sebastian Rosenzweig at 
the International Audio Laboratories Erlangen, which are a joint institution of the Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU) and Fraunhofer Institute for Integrated Circuits IIS. 
We also thank the German Research Foundation (DFG) for various research grants that allowed us for conducting fundamental research in music processing.