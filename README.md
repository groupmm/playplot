# Make Plot Playable
This module allows multiple interactive matplotlib plots synced to a piece of audio.
Created by Daniel Keitel under the MIT licence.

This repository is in its early stages and should not be public yet.


## Simple Example

```python
# example 1:
# very simple example plotting function plots
# audio is a numpy array containing audio at the sampling rate sr

from makeplotplayable import Session

# crate a Session from the audio data
session = Session(audio, sr)


#decorate the plot function with the session
# noinspection PyShadowingNames
@session
def plot(audio, sr, name):
    # define a plot function, which does not use any global (not even imports)
    # this is a limitation from multiprocessing
    # everything the function needs should be parsed as an argument/key-word-argument
    # simple datatypes definitely work, we can even pass other functions (stay away from lambdas)
    # if there are issues check the limitations of dill
    import libfmp.b as lfb

    fig, ax, _ = lfb.plot_signal(audio, sr)

    # return the figure, the axis and an optional config dict for the cursor as a tuple
    return fig, ax, {'title': name}


#call the plot function, it will create the plot in another process
plot(audio, sr, "Fig 1")

#we can create multiple plots in on session (all plots in a session will be linked)
plot(audio, sr, "Fig 2")

#start the session to enable audio playback
session.start()
```

For more examples see the examples directory.
All examples require libfmp, (```pip install libfmp```)
some more (use requirements.txt).
For the advanced examples additional files are necessary look in `__init__.py` in the example_data folder.


For the documentation see the docs folder.

The requirements.txt contains all development dependencies.

To build a wheel and install it run ```make install```.

For a development installation run ```pip install -e .```

