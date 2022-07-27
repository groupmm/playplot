The Plotting Function
=====================
.. _plotting_details:

The plot function is the callable which gets wrapped by a Session instance.

Any args and kwargs are allowed, and variables from outer scopes can be used,
which can be transferred to the plotting process.

This limitation effects few objects we may on to use (dont use file descriptors or whole application instances).
Notable is the Session instance itself, which is not usable inside the plotting function.

Plot function return values
--------------------------------------

Plot functions can return three different kinds of output.
(The return value of the wrapped function is always None)

-  None:

   The plot won't get a curser, it will be simply shown. It won't
   interact with the session (no real reason to use it).

-  Figure, Axes:

   The plot will be interactive. The curser will get added to the axes
   (axvline). Navigation will be enabled. The time of the audi clip will
   get mapped to the limits of the axes.

-  Figure, Axes, Dict:

   To configer the plot, we can pass a dict with additional parameters.

Plot Parameters
---------------

Plot Parameters are passed via the return of the plotting function, in
the form of a string indexed dict. If a key is present it will override
the default value.

Simple Parameters
~~~~~~~~~~~~~~~~~

-  ``title``:
    The Title of the Window

    -  Default: "Fig"

-  ``axvline_kwargs``:
    The keyword arguments used to create the axvline

    -  Default: ``{"alpha": 0.9, "ls": '-', "color": 'r', "lw": 1, "zorder": 10}``

-  ``window_pos``:
    the position, where the window should open. (array like
    with two integers)

    -  Default: None (matplotlib default)

-  ``mapping``:
    Linear interpolated mapping between, time in the audio playback and
    the x-axis position.

    Two mapping types are available, a sparce mapping, containing pairs of times and corresponding positions
    and a dense mapping giving a time to each feature.

    - Sparce mapping:
        This mapping neads to be passed as a numpy array in the shape (n,2).
        Time and position values

    A Numpy array in the shape (n,2). e.g. [[time_0,
    pos_0], [time_1, pos_1], …, [time_n-1, pos_n-1]] Out of bounds values
    will get clamped. Time and position are required to rise STRONGLY
    monotonic! There is an alternative mapping in case every feature
    border has a time: A tuple in the form (1d numpy array of all feature
    border times, position of first element, position of last element)

    -  Default: linear mapping from beginning to end

Advanced Parameters
~~~~~~~~~~~~~~~~~~~~~~~
-  ``custom_time_to_pos_function``:
    Function to convert the time (point in
    the audio) into a position (on the axes x-axis)

    -  Default: function based on the mapping param

-  ``custom_pos_to_time_function``:
    Function to convert the position (on
    the axes x-axis) into a time in the audio

    -  Default: function based on the mapping param

-  ``artists``:
    List of matplotlib artists to animate. Requires the param
    ``draw_function`` to be set. Setting an element like a line here, will
    allow faster updates, if the element is interactive. See the
    matplotlib documentation for more information about artists.

-  ``draw_function``:
    Function that allows custom interactive elements.
    Requires the param "artists" to be set. This function will get called
    once per frame with (time:float,pos:float,paused:bool). Here you can
    modify all the artists you defined in "artists", to animate them. The
    function expects a bool for the return type, signaling if the artists
    should be redrawn.

-  ``override_update_function``:
    Setting this function disables the
    cursor and navigation. (the draw function still works) This function
    will get called once per frame (prior to draw_function) with
    (time:float,pos:float,paused:bool). It is ment to update time/pos and
    the paused state. The function is expected to return a tuple of the
    form (time/pos, paused). time/paused is the new value for ether time
    or pos depending on the param
    "override_update_function_returns_pos". paused is a bool describing
    the new paused state.

-  ``override_update_function_returns_pos``:
    does the "override_update_function" return a position.
    Only used if "override_update_function" is defined.

    True: "override_update_function" returns (pos, paused)

    False: "override_update_function" returns (time, paused)

    -  Default: False

See the examples (advanced) for use cases.