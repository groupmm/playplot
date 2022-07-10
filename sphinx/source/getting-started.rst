Getting Started
===============

Make Plot Playable
==================

This module allows multiple interactive matplotlib plots synced to a
piece of audio.

Simple Example
--------------

.. code:: python

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

For more examples see the examples directory.
All examples require libfmp. (``pip install libfmp``)

How to wrap a plotting function
-------------------------------

A plotting function can be wrapped with a decorator as seen in
example_1, or we could wrap it manually. This is the option if the
original function should be preserved, or is already defined.

.. code:: python

   def plot(*args,**kwargs):
       ...

   session = Session(mono_audio_as_numpy_array, sampling_rate)

   plot_wrapped = session(plot)

It is done simply by calling the Session instance with the function

Multiprocessing limitations
---------------------------

So we can plot efficiently (and in interactive session at all), we need
to use multiprocessing. With this comes, the need to run the plotting
function in another process witch knows nothing about our current
process.

So the plotting function needs to work in isolation. - First case: The
function is in the top level of a python file (basically all functions
which we could import from a file)

First the file gets imported, then the functions gets called. Some
implications: the functions seed different globals; imports can be at
the top of the file We always need to wrap souch function manually
(without decorator)

-  Second case: The function is anywhere else, (e.g. in a notebook a
   main function)

   The function will get called without any outer context. So we can’t
   use anything outside our function. We either need to pass it as an
   argument (e.g. other functions in our notebook), or we need to import
   it from inside the plotting function.

Creating Sessions
-----------------

Multiple Sessions can be created. Each Session can have multiple plots
(theoretically non also). All plots can come from the same or different
plotting functions.

Sessions can either be created with a numpy array (mono or stereo)
(Session constructor) or from a file with the help of soundfile
(Session.from_file). The file will be streamed in this case. (Low seek
times required for smooth playback)

For more details about the Session see the different docstrings.

Stopping a session will close all associated interactive plots, deleting
a session stops the session on garbage collection.

More about plot function return values
--------------------------------------

Plot functions can return three different kinds of output. (The return
value of the wrapped function is always None)

-  None:

   The plot won’t get a curser, it will be simply shown. It won’t
   interact with the session (besides stop events)n

-  Figure, Axes:

   The plot will be interactive. The curser will get added to the axes
   (axvline). Navigation will be enabled. The time of the audi clip will
   get mapped to the limits of the axes

-  Figure, Axes, Dict:

   To configer the plot, we can pass a dict with additional parameters.

Plot Parameters
---------------

Plot Parameters are passed via the return of the plotting function, in
the form of a string indexed dict. If a key is present it will override
the default value.

Parameters
~~~~~~~~~~

-  “title”: The Title of the Window

   -  Default: “Fig”

-  “axvline_kwargs”: The keyword arguments used to create the axvline

   -  Default: {“alpha”: 0.9, “ls”: ‘–’, “color”: ‘r’, “lw”: 1,
      “zorder”: 10}

-  “mapping”: Linear interpolated mapping between, time in the audio and
   x-axis position. A Numpy array in the shape (n,2). e.g. [[time_0,
   pos_0], [time_1, pos_1], …, [time_n-1, pos_n-1]] Out of bounds values
   will get clamped. Time and position are required to rise STRONGLY
   monotonic! There is an alternative mapping in case every feature
   border has a time: A tuple in the form (1d numpy array of all feature
   border times, position of first element, position of last element)

   -  Default: linear mapping from beginning to end

-  “window_pos”: the position, where the window should open. (array like
   with two integers)

   -  Default: None (matplotlib default)

-  “custom_time_to_pos_function”: Function to convert the time (point in
   the audio) into a position on the axes x-axis

   -  Default: function based on the mapping param

-  “custom_pos_to_time_function”: Function to convert the position (on
   the axes x-axis) into a time in the audio

   -  Default: function based on the mapping param

-  “artists”: list of matplotlib artists to animate. Requires the param
   “draw_function” to be set. Setting an element like a line here, will
   allow faster updates, if the element is interactive. See the
   matplotlib documentation for more information about artists.

-  “draw_function”: function that allows custom interactive elements.
   Requires the param “artists” to be set. This function will get called
   once per frame with (time:float,pos:float,paused:bool). Here you can
   modify all the artists you defined in “artists”, to animate them. The
   function expects a bool for the return type, stating if the artists
   should be redrawn.

-  “overrider_update_function”: setting this function disables the
   cursor and navigation. (the draw function still works) This function
   will get called once per frame (prior to draw_function) with
   (time:float,pos:float,paused:bool). It is ment to update time/pos and
   the paused state. The function is expected to return a tuple of the
   form (time/pos, paused). time/paused is the new value for ether time
   or pos depending on the param
   “overrider_update_function_returns_pos”. paused is bool describing
   the new paused state

-  “overrider_update_function_returns_pos”: does the
   “overrider_update_function” return a position. Only used if
   “overrider_update_function” is defined. True:
   “overrider_update_function” returns (pos, paused) False:
   “overrider_update_function” returns (time, paused)

   -  Default: False

User interaction
----------------

-  Navigation: Don’t be in pan or zoom mode and simply click (or drag)
   while pressing the left or right mouse button

   Right mouse button will pause

   Left mouse button will play

-  Play/Pause: Space, Enter, middle mouse button

-  Hide/Show cursor: c