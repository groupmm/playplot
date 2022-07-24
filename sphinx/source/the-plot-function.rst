The Plotting Function
=====================

.. _plotting_details:

plotting details

The Parameter Dict
------------------

Simple Parameters
~~~~~~~~~~~~~~~~~

-  ``title``: The Title of the Window

    -  Default: "Fig"

-  ``axvline_kwargs``: The keyword arguments used to create the axvline

    -  Default: ``{"alpha": 0.9, "ls": '-', "color": 'r', "lw": 1, "zorder": 10}``

-  ``window_pos``: the position, where the window should open. (array like
    with two integers)

    -  Default: None (matplotlib default)

-  ``mapping``: Linear interpolated mapping between, time in the audio playback and
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

