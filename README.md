# Playplot

This repository contains a Python package called _playplot_, 
which provides an __interactive audio playback for matplotlib plots including the creation, navigation, and synchronization of such plots.__
Each plot is handled in its own process, allowing smooth animations without a blocking main thread/process.
Plots can be started from a Python __script__ or an __interactive notebook__, with plots being shown in separate windows on the machine
where the kernel is running.


## References

Daniel Keitel, Meinard Müller, Christof Weiß, and Sebastian Rosenzweig.  
_Playplot: A Python Package to Sync Matplotlib Plots to Audio._  
To be submitted to the Journal of Open Source Software (JOSS).

## Installing

To use the library just install it via pip.
```pip install playplot```

To run the examples locally and for development this repository is necessary.

```git clone https://github.com/groupmm/playplot.git```

For a development installation run ```python -m pip install -e .```

All additional dependencies can be installed via ```python -m pip -r requirements.txt```

## Usage

### Examples

For examples see the `examples` folder of this repository.
These examples need some local data to work properly (except ``minimal``)

Those files are provided for all examples except for ``advanced``.
See ``examples/example_data/__init__.py`` for which files are additionally required. 
Members of GroupMM can find the missing files on lin2 under ``/GroupMM/Students/Work_DK/example_data/``

The ``minimal`` and ``basic`` examples don't have additional dependencies.
``intermediate`` requires ``libfmp`` (can be installed via ``python -m pip install libfmp``)
``advanced`` has the most dependencies. We recommend installing from the requirements.txt files. (``python -m pip install -r requirements.txt``) 

#### Minimal Example

```python
import matplotlib.pyplot as plt
from playplot import Session

# create a Session from the audio data (url not final)
session = Session.from_file("https://github.com/groupmm/playplot/blob/main/examples/example_data/bach_bwv245_no22_vokalensemble_ilmenau.wav?raw=true")

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
There are some test script in the `tests` folder, mostly focussing on process management and error handling.

### Docs
The documentation is built with sphinx and hosted on __GitHub Pages__.

## Contributing
We welcome any suggestions and contributions.
For contributing, please create an issue within this GitHub repository.
Please do not submit a pull request without prior consultation to us.

## Licence
The code for this package is published under an __MIT licence__.
This does not apply to the data files in ``examples/example_data``.
Example file ``bach_bwv245_no22_vokalensemble_ilmenau.wav`` is a recording of Choral No. 22 "Durch Dein Gefängnis" from J.S. Bachs _Johannespassion_, performed by Vokalensemble Ilmenau (conductor: Hans-Jürgen Freitag) at Jakobuskirche Ilmenau, 24.3.2013. Permission granted by the conductor to be used for demo and research purposes only.

## Acknowledgements
The initial version of this library was created during a research internship of Daniel Keitel within a computer science master's program, under the supervision of Prof. Dr. Meinard Müller, Dr. Christof Weiß and Dr. des. Sebastian Rosenzweig at 
the International Audio Laboratories Erlangen, which are a joint institution of the Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU) and Fraunhofer Institute for Integrated Circuits IIS. 
This Python library is closely inspired by the MATLAB tool ``MakePlotPlayable``, implemented by Harald Grohganz and colleagues and part of the MATLAB SM Toolbox [1].
We also thank the German Research Foundation (DFG) for various research grants that allowed us for conducting fundamental research in music processing.

[1] Meinard Müller, Nanzhu Jiang, and Harald G. Grohganz  
_SM Toolbox: MATLAB Implementations for Computing and Enhancing Similarity Matrices_  
Proceedings of 53rd Audio Engineering Society (AES) Conference on Semantic Audio  
London, UK, 2014.  
https://www.audiolabs-erlangen.de/resources/MIR/SMtoolbox
