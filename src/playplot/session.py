import os
import queue
import threading
import traceback
from functools import wraps
from multiprocessing import Process
from time import sleep, monotonic
from typing import Optional, Union, List

import numpy as np
import soundfile as sf

from dill import dumps, HANDLE_FMODE
from ._audioProcess import audio_process_entrypoint
from ._plotProcess import plot_process_entrypoint
from ._util import SharedObject, UrlFile, runs_in_notebook, AudioProcessException, \
    PlotProcessException


def _plot_process_start_helper(func, so, stack, args, kwargs):
    # pickle with dill to increase compatibility (now works in ipy on Windows)
    dill = dumps((func, stack, args, kwargs), byref=False, recurse=True, protocol=-1, fmode=HANDLE_FMODE)

    p = Process(target=plot_process_entrypoint, args=(so, dill))
    p.daemon = True
    p.start()


class Session:
    __shared_object_storage: List[SharedObject] = list()

    @classmethod
    def from_file(cls, file: str, /, *,
                  close_with_last_plot: bool = True,
                  fps_target: float = 60,
                  plot_min_sleep: float = 0.001,
                  time: float = 0,
                  volume: float = 0.8,
                  looping: bool = False,
                  save_folder: str = ".",
                  show_msg_box_on_error_in_other_process: Optional[bool] = None) -> 'Session':
        """
        Construct a Session from an audio file.
        For more see the constructor of this class

        Parameters
        ----------
        file
            Audio file to be loaded (storage medium seek times should be fast) loaded via soundfile
        close_with_last_plot
            After last plot was closed no new plots can be created and audio playback will stop
        fps_target
            target frames per seconds for plots
        plot_min_sleep
            minimal time the plotting processes will yield for (default should suffice)
        time
            start time *see:* :attr:`~Session.time`
        volume
            audio volume as sample scalar (0-1)
        looping
            restart at the beginning after the end is reached
        save_folder
            existing folder where plot images get saved
        show_msg_box_on_error_in_other_process
            show a message box if an error occurs, useful if no explicit error handling is performed.
            on by default if running in an interactive context.
            (in jupyter notebooks the stderr is not shown)

        Raises
        ------
        URLError
            `file` was a 'url' and the connection failed

        ValueError
            `file` was not a `url` and not a valid file path

        RuntimeError
            the `file` was found but SoundFile was unable to read it

        Returns
        -------
        Session
            Session instance
        """
        return cls(file, 0, close_with_last_plot=close_with_last_plot, fps_target=fps_target,
                   plot_min_sleep=plot_min_sleep, time=time, volume=volume, looping=looping, save_folder=save_folder,
                   show_msg_box_on_error_in_other_process=show_msg_box_on_error_in_other_process)

    def __init__(self, x: Union[np.ndarray, str], /, sr: int, *,
                 close_with_last_plot: bool = True,
                 fps_target: float = 60,
                 plot_min_sleep: float = 0.001,
                 time: float = 0,
                 volume: float = 0.8,
                 looping: bool = False,
                 save_folder: str = ".",
                 show_msg_box_on_error_in_other_process: Optional[bool] = None):
        """
        A Session allows audio playback linked to multiple interactive matplotlib plots.
        These plots receive a curser and navigation functions,
        to visualize the point in the audio and allow for navigation.

        This Constructor allows the creation of a Session with a numpy array as basis.
        There is a nearly identical function see from_file(...),
        witch allows the same with a file location as audio source.

        After construction start the audio process via start().
        Wrap your plotting function(s) with this instance see __call__(...)
        and call these wrapped function with your parameters to create the plots.

        Parameters
        ----------
        x
            Audio data as one-dimensional (mono) or two-dimensional (stereo) (channels first) numpy float array
        sr
            sampling rate
        close_with_last_plot
            after last plot was closed no new plots can be created and audio playback will stop
        fps_target
            target frames per seconds for plots
        plot_min_sleep
            minimal time the plotting processes will yield for (default should suffice)
        time
            start time *see:* :attr:`~Session.time`
        volume
            audio volume as sample scalar (0-1)
        looping
            restart at the beginning after the end is reached
        save_folder
            existing folder where plot images get saved
        show_msg_box_on_error_in_other_process
            show a message box if an error occurs, useful if no explicit error handling is performed.
            on by default if running in an interactive context.
            (in jupyter notebooks the stderr is not shown)
        """
        if show_msg_box_on_error_in_other_process is None:
            show_msg_box_on_error_in_other_process = runs_in_notebook()

        # get metadata about the audio (file), in case a piece of audio is invalid an error should occur here
        if isinstance(x, str):
            if os.path.isfile(x):
                info = sf.info(x)
            else:
                source = UrlFile(x)
                info = sf.info(source)
                source.close()

            sr = info.samplerate
            duration = info.duration
        else:
            assert len(x.shape) == 1 or (len(x.shape) == 2 and x.shape[0] == 2), "Invalid signal shape"
            duration = x.shape[-1] / sr
            x = x.astype(dtype=np.float32).T

        self.__audio_process: Optional[Process] = None
        self.__x: Union[np.ndarray, str] = x
        self.__sr: int = sr
        # the shared object will be available on all processes and allows for ipc via Values
        self.__so: SharedObject = SharedObject(show_msg_box_on_error_in_other_process, duration, close_with_last_plot,
                                               fps_target, save_folder, plot_min_sleep, looping)
        # we need to keep the shared object alive, even after this instance is deconstructed,
        # so all processes can shut down properly
        self.__class__.__shared_object_storage.append(self.__so)
        self.__total_spawned_plots = 0
        self.time = time
        self.volume = volume

    def start(self) -> None:
        """
        Start the session.
        Required for Audio Playback.
        Only callable once.
        May be called before and after plots are opened.

        Raises
        ------
        RuntimeError
            In case the session is already started
        """
        if self.__audio_process is not None:
            raise RuntimeError("Session can only be started once")

        # record a stack trance, so in the case of an exception in another process, we can know where it originated
        # noinspection PyBroadException
        try:
            raise Exception("Future Exception (only used to capture a stack trace)")
        except Exception:
            stack = traceback.format_stack()[:-1]
        self.__audio_process = Process(target=audio_process_entrypoint, args=(self.__so, self.__x, self.__sr, stack))
        self.__audio_process.daemon = True
        self.__audio_process.start()

    def stop(self) -> None:
        """
        Stop the session.
        This closes all interactive plots, no new plots can be opened.
        The Session can not be restarted.
        Calling multiple times is allowed.
        """
        try:
            with self.__so.lock:
                self.__so.stop.value = True
        except AttributeError:
            pass

    def __del__(self):
        self.stop()

    def save_plot_images(self, frame_number: int) -> None:
        """
        Saves images of all currently open plots,
        in the folder ``save_folder`` provided to the constructor.
        The files are named title_frame_number.png.
        If multiple plots are saved the titles must differ.
        Don't interact with the plots while this function runs.

        Can be used to help creat a video::

            start = 0
            end = session.duration
            fps = 30

            for i in range(int((end-start)*fps)):
                session.time = i/fps+start
                session.save_plot_images(i)

        It is not fast.

        Parameters
        ----------
        frame_number
            part of the output file names
        """
        was_paused = self.paused
        self.paused = True
        # signal plot processes
        with self.__so.lock:
            self.__so.plots_wrote_current_frame.value = 0
            self.__so.save_as_frame_number.value = frame_number

        # wait until all plots have written there file
        while True:
            with self.__so.lock:
                if self.__so.plots_wrote_current_frame.value >= self.__so.open_plots.value:
                    break
            sleep(0.001)

        if not was_paused:
            self.paused = False

    def join(self, timeout=None, force_close_with_last_plot=True) -> None:
        """
        Block until all Plots are closed

        Parameters
        ----------
        timeout
            raises TimeoutError if reached (default: blocks forever)
        force_close_with_last_plot
            close session even if the Session was constructed with close_with_last_plot=False

        Raises
        ------
        TimeoutError
            Timeout reached
        """
        start_time = monotonic()
        while True:
            if timeout is not None and monotonic() > start_time + timeout:
                raise TimeoutError()
            if self.__so.close_with_last_plot:
                if not self.is_running:
                    return
            else:
                with self.__so.lock:
                    if self.__so.open_plots.value == 0:
                        if force_close_with_last_plot:
                            self.stop()
                        return
            sleep(0.01)

    def wait_for_plots_opening(self, number_of_plots=None, timeout=10, supress_timeout_error=True):
        """
        Block until at least `number_of_plots` are open.

        Parameters
        ----------
        number_of_plots
            Wait until `number of plots` are open (>=0).
            Defaults to total number of plots spawned by this session.
        timeout
            Raises TimeoutError if reached (default: blocks forever) and supress_timeout_error is not set.
        supress_timeout_error
            Simply return when the timeout is reached.

        Raises
        ------
        TimeoutError
            Timeout reached
        """
        start_time = monotonic()

        if number_of_plots is None:
            number_of_plots = self.total_spawned_plots

        if number_of_plots < 0:
            raise ValueError("number_of_plots is negative")

        while True:
            if timeout is not None and monotonic() > start_time + timeout:
                if supress_timeout_error:
                    return
                raise TimeoutError()
            with self.__so.lock:
                if self.__so.open_plots.value >= number_of_plots:
                    return
            sleep(0.01)

    def retrieve_errors(self) -> List[Union[AudioProcessException, PlotProcessException]]:
        """
        Check if something went wrong in the other processes and get the errors as a list.

        Returns
        -------
        list
            List of all errors that occurred in other processes associated with this session since the last check/retrieve_errors.
            Empty if no errors were raised.

        """
        error_list = list()
        with self.__so.lock:
            if self.__so.error_queue_size.value > 0:
                while True:
                    try:
                        error_list.append(self.__so.error_queue.get(block=False))
                    except queue.Empty:
                        break
                self.__so.error_queue_size.value = 0
        return error_list

    def check(self) -> None:
        """
        Check if something went wrong in another process.

        Raises
        ----------
        AudioProcessException
            Raised in case some error occurred in the audio process associated with this session since the last check/retrieve_errors
            instance of :class:`~playplot.ForeignProcessException`
        PlotProcessException
            Raised in case some error occurred in a plot process associated with this session since the last check/retrieve_errors
            instance of :class:`~playplot.ForeignProcessException`
        """
        error_list = list(self.retrieve_errors())
        if len(error_list) == 0:
            return

        raise error_list[0]

    @property
    def show_msg_box_on_error_in_other_process(self) -> bool:
        """
        Show msg box on error in other process.
        Can be used to decide if main process should check for exceptions.
        """
        return self.__so.show_msg_box_on_error_in_other_process

    @property
    def paused(self) -> bool:
        """
        Audio playback control.
        (may stay false after session has stopped running)
        """
        with self.__so.lock:
            return self.__so.paused.value

    @paused.setter
    def paused(self, val: bool) -> None:
        with self.__so.lock:
            self.__so.paused.value = val

    @property
    def looping(self) -> bool:
        """
        Restart after end is reached.
        (argument in constructor)
        """
        with self.__so.lock:
            return self.__so.looping.value

    @looping.setter
    def looping(self, val: bool) -> None:
        with self.__so.lock:
            self.__so.looping.value = val

    @property
    def time(self) -> float:
        """
        Current cursor time will be clamped between 0-duration.
        (argument in constructor)
        """
        with self.__so.lock:
            return self.__so.time.value

    @time.setter
    def time(self, val: float) -> None:
        with self.__so.lock:
            if val != self.__so.time.value:
                self.__so.time.value = max(0, min(self.__so.duration, val))
                self.__so.time_skip.value = True

    @property
    def volume(self) -> float:
        """
        Current volume will be clamped between 0-1.
        (argument in constructor)
        """
        with self.__so.lock:
            return self.__so.volume.value

    @volume.setter
    def volume(self, val: float) -> None:
        with self.__so.lock:
            self.__so.volume.value = max(0.0, min(1.0, val))

    @property
    def is_running(self) -> bool:
        """
        Check if the Session is (still) running.
        """
        with self.__so.lock:
            return not self.__so.stop.value and self.__audio_process is not None

    @property
    def duration(self) -> float:
        """
        Get the duration of the associated audio (in seconds).
        """
        return self.__so.duration

    @property
    def total_spawned_plots(self) -> int:
        """
        Get the total amount of plots spawned by this session.
        This value get immediately incremented after calling the plot function
        """
        return self.__total_spawned_plots

    def __call__(self, func):
        """
        Function to wrap plotting function to use with Session.

        Possible use cases::

            def plotFunc(args,kwargs):
                import matplotlib.pyplot as plt
                import numpy as np
                ...
                return fig, ax

            wrapped_func = session(plotFunc)

        or::

            @session
            def plotFunc(*args,**kwargs):
                import matplotlib.pyplot as plt
                import numpy as np
                ...
                return fig, ax


        For more details and templates see :ref:`plotting details <plotting_details>`.

        Parameters
        ----------
        func
            function to wrap

        Returns
        -------
        Callable
            wrapped function same parameters as input, calling this function will plot in new process

        Raises
        ------
        RuntimeError
            in case the session is already stopped
        """

        so = self.__so

        # create wrapper function transfer metadata
        @wraps(func)
        def wrapper(*args, **kwargs):
            with so.lock:
                if so.stop.value:
                    raise RuntimeError("Session already stopped")

            # record a stack trance, so in the case of an exception in another process, we can know where it originated
            # noinspection PyBroadException
            try:
                raise Exception("Future Exception (only used to capture a stack trace)")
            except Exception:
                stack = traceback.format_stack()[:-1]

            # Creating a new process on Windows is slow -> use multithreading to create process
            if os.name == 'nt':
                t = threading.Thread(target=_plot_process_start_helper, args=(func, so, stack, args, kwargs))
                t.daemon = True
                t.start()
            else:
                _plot_process_start_helper(func, so, stack, args, kwargs)

            self.__total_spawned_plots += 1

        return wrapper
