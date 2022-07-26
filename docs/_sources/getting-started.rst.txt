Getting Started
===============

Make Plot Playable
==================

This module allows multiple interactive matplotlib plots to be created and synced to a
piece of audio.

Minimal Example
---------------

.. code:: python

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

For more examples see the examples directory.
More details are provided in the Readme.

How to wrap a plotting function
-------------------------------

A plotting function can be wrapped with a decorator as seen in
the minimal example, or we could wrap it manually. This is the option if the
original function should be preserved, or is already defined.

.. code:: python

   def plot(*args,**kwargs):
       ...

   session = Session(mono_audio_as_numpy_array, sampling_rate)

   plot_wrapped = session(plot)

It is done simply by calling the Session instance with the function

Multiprocessing limitations
---------------------------
To be able to plot efficiently (and in interactive session at all), we need
to use multiprocessing, to run each plot in its own process.
So we need to run our plotting functions in different processes.
The main process/thread does not block.

This is generally transparent to the user, but it complicates things like
exception handling.

It works well in interactive sessions like in a jupyter notebook.
(The plots will be opened on the machine the kernel runs on)

For more details about limitation look at the documentation of Multiprocessing and Dill.

Creating Sessions
-----------------

Multiple Sessions can be created. Each Session can have multiple plots
(theoretically non also). All plots can come from the same or different
plotting functions.

Sessions can either be created with a numpy array (mono or stereo)
(Session constructor) or from a file with the help of soundfile
(Session.from_file).
The file can ether be a file path or a http(s) url.
The file will get streamed.

For more details about the Session see the api documentation.

Stopping a session will close all associated interactive plots, deleting
a session stops the session on garbage collection.


User interaction
----------------

-  Navigation: Don't be in pan or zoom mode and simply click (or drag)
   while pressing the left or right mouse button

   Right mouse button will pause

   Left mouse button will play

-  Play/Pause: Space, Enter, middle mouse button

-  Hide/Show cursor: c