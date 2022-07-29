import math
import os.path
import sys
import traceback
from time import perf_counter, sleep
from typing import Dict, Any, Optional, Tuple, Callable, List
import matplotlib
import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np
from dill import loads

from ._util import SharedObject, show_error_box, PlotProcessException


# builds a piecewise linear function mapping from X to Y
def build_mapping_function(X, Y):
    def func(x):
        if x <= X[0]:
            return Y[0]
        if x >= X[-1]:
            return Y[-1]

        b_i = np.argmax(x < X)
        a_i = b_i - 1

        a, b = X[a_i], X[b_i]

        alpha = (x - a) / (b - a)

        ret = (1 - alpha) * Y[a_i] + alpha * Y[b_i]
        return ret

    return func


def build_mapping_function_dense_pos_to_time(ticks, first_tick, last_tick):
    def func(x):
        index_float = (x - first_tick) / (last_tick - first_tick) * (ticks.shape[0]-1)
        index_float = max(0, min(ticks.shape[0]-1, index_float))
        a_index = math.floor(index_float)
        b_index = math.ceil(index_float)
        alpha = index_float % 1
        a = ticks[a_index]
        b = ticks[b_index]
        time = b * alpha + a * (1 - alpha)
        return time

    return func


def build_mapping_function_dense_time_to_pos(ticks, first_tick, last_tick):
    def func(x):
        i = np.searchsorted(ticks, x, side='left')

        if i == ticks.shape[0]:
            raw_pos = ticks.shape[0] - 1
        elif i == 0:
            raw_pos = 0
        else:
            a = ticks[i - 1]
            b = ticks[i]
            alpha = (x - a) / (b - a)
            raw_pos = (i - 1) * (1 - alpha) + i * alpha

        pos = (raw_pos / (ticks.shape[0]-1)) * (last_tick - first_tick) + first_tick

        return pos

    return func


# Main plot class
class MPP:
    def pos_to_time(self, p: float) -> float:
        time = self.map_pos_to_time(p)
        return max(0, min(self.so.duration, time))

    def time_to_pos(self, time: float) -> float:
        # a, b = self.ax.dataLim.x0, self.ax.dataLim.x1
        p = self.map_time_to_pos(time)
        return p  # max(a, min(b, p))

    def on_click(self, event):
        so = self.so

        self.pressed_buttons[event.button] = True

        # prevent mouse input when in pan/zoom mode
        if self.fig.canvas.cursor().shape() != 0:
            return

        # middle click -> play/pause
        if event.button == 2:
            with so.lock:
                so.paused.value = not so.paused.value
            return

        if event.inaxes != self.ax:
            return

        time = self.pos_to_time(event.xdata)

        with so.lock:
            so.paused.value = True
            if time != so.time.value:
                so.time.value = time
                so.time_skip.value = True

    def on_move(self, event):
        so = self.so

        if self.fig.canvas.cursor().shape() != 0 or not (
                self.pressed_buttons[1] or self.pressed_buttons[3]) or event.inaxes != self.ax:
            return

        time = self.pos_to_time(event.xdata)

        with so.lock:
            so.paused.value = True
            if time != so.time.value:
                so.time.value = time
                so.time_skip.value = True

    def on_release(self, event):
        so = self.so

        self.pressed_buttons[event.button] = False

        if self.fig.canvas.cursor().shape() != 0 or event.button != 1 or event.inaxes != self.ax:
            return

        time = self.pos_to_time(event.xdata)

        with so.lock:
            so.paused.value = self.pressed_buttons[3]
            if time != so.time.value:
                so.time.value = time
                so.time_skip.value = True

    def on_key(self, event):
        so = self.so
        if event.key == "c":
            self.hidden = not self.hidden
        if event.key in [" ", "enter"]:
            with so.lock:
                so.paused.value = not so.paused.value

    # load the default parameter if parameter is not specified from plot function
    def load_default_params(self):
        so = self.so
        params = self.params
        if "mapping" in params:
            arr = params["mapping"]
        else:
            arr = np.array([[0, self.ax.dataLim.x0], [so.duration, self.ax.dataLim.x1]])

        assert (isinstance(arr, tuple) and len(arr) == 3) or \
               (len(arr.shape) == 2 and arr.shape[1] == 2 and arr.dtype == float), \
               "invalid mapping"

        if "custom_time_to_pos_function" in params:
            self.map_time_to_pos = params["custom_time_to_pos_function"]
        else:
            if isinstance(arr, np.ndarray):
                self.map_time_to_pos = build_mapping_function(arr[:, 0], arr[:, 1])
            else:
                self.map_time_to_pos = build_mapping_function_dense_time_to_pos(*arr)

        if "custom_pos_to_time_function" in params:
            self.map_pos_to_time = params["custom_pos_to_time_function"]
        else:
            if isinstance(arr, np.ndarray):
                self.map_pos_to_time = build_mapping_function(arr[:, 1], arr[:, 0])
            else:
                self.map_pos_to_time = build_mapping_function_dense_pos_to_time(*arr)

        if "title" not in params:
            params["title"] = "Fig"

        if "axvline_kwargs" not in params:
            params["axvline_kwargs"] = {"alpha": 0.9, "ls": '--', "color": 'r', "lw": 1, "zorder": 10}

        if "artists" not in params or "draw_function" not in params:
            params["artists"] = []
            params["draw_function"] = lambda *args, **kwargs: False

        if "override_update_function" not in params:
            params["override_update_function"] = None

        if "override_update_function_returns_pos" not in params:
            params["override_update_function_returns_pos"] = False

        if "window_pos" not in params:
            params["window_pos"] = None

    def __init__(self, fig: plt.Figure, ax: matplotlib.axes.Axes, params: Dict[str, Any], so: SharedObject):
        self.fig: plt.Figure = fig
        self.ax: matplotlib.axes.Axes = ax
        self.params: Dict[str, Any] = params
        self.so: SharedObject = so

        self.map_time_to_pos: Optional[Callable] = None
        self.map_pos_to_time: Optional[Callable] = None

        self.load_default_params()

        # keep track of pressed mouse buttons (maybe more than 4?)
        self.pressed_buttons: List[bool] = [False for _ in range(10)]
        self.hidden = False
        self.artists = []

        with so.lock:
            self.start_time = so.time.value

        self.fig.canvas.manager.set_window_title(self.params["title"])
        if params["window_pos"] is not None:
            self.fig.canvas.manager.window.move(params["window_pos"][0], params["window_pos"][1])

        if params["override_update_function"] is None:
            fig.canvas.mpl_connect('key_press_event', self.on_key)
            fig.canvas.mpl_connect('button_release_event', self.on_release)
            fig.canvas.mpl_connect('button_press_event', self.on_click)
            fig.canvas.mpl_connect('motion_notify_event', self.on_move)

            v_line = self.ax.axvline(self.time_to_pos(self.start_time), **self.params["axvline_kwargs"])
            self.artists.append(v_line)

        self.artists.extend(params["artists"])

        # BlitManager allows for efficient animations without redrawing everything
        self.blit_manager = BlitManager(self.fig.canvas, self.artists)

        # Initial plot show + time for gui loop to render
        plt.show(block=False)
        plt.pause(0.1)

    def loop(self):
        so = self.so
        fig_num = self.fig.number

        last_time = self.start_time
        last_hidden = False

        last_frame = perf_counter()

        last_save_index = -1

        # detect when window is closed
        while plt.fignum_exists(fig_num):
            with so.lock:
                if so.stop.value:
                    break
                save_index = so.save_as_frame_number.value
                fps_target = so.fps_target.value
                min_delay = so.plot_min_sleep.value
                time = so.time.value
                paused = so.paused.value

            gui_update_necessary = False
            pos = self.time_to_pos(time)

            if self.params["override_update_function"] is None:
                if last_time != time or self.hidden != last_hidden:
                    self.artists[0].set_xdata([pos, pos])
                    self.artists[0].set(visible=not self.hidden)
                    last_time = time
                    last_hidden = self.hidden
                    gui_update_necessary = True

            else:
                new_time_or_pos, new_paused = self.params["override_update_function"](time, pos, bool(paused))
                assert isinstance(new_time_or_pos, float), "the new time must be a float"
                assert isinstance(new_paused, bool), "the new paused must be a bool"
                time_or_pos_changed = new_time_or_pos != time
                if self.params["override_update_function_returns_pos"]:
                    time_or_pos_changed = new_time_or_pos != pos
                    new_time_or_pos = self.map_pos_to_time(new_time_or_pos)

                new_time_or_pos = max(0, min(so.duration, new_time_or_pos))
                if time_or_pos_changed or new_paused != paused:
                    time = new_time_or_pos
                    paused = new_paused
                    with so.lock:
                        so.paused.value = paused
                        if time != so.time.value:
                            so.time.value = time
                            so.time_skip.value = True

            gui_update_necessary |= self.params["draw_function"](time, pos, bool(paused))

            if gui_update_necessary:
                self.blit_manager.update()
            else:
                # gui needs time to process internal updates
                self.fig.canvas.flush_events()

            # save plot as png
            if save_index != -1 and save_index != last_save_index:
                _save_fig_as_png(self.fig, os.path.join(so.save_folder, f"{self.params['title']}_{save_index:06d}.png"))
                with so.lock:
                    so.plots_wrote_current_frame.value += 1
            last_save_index = save_index

            # sleep to give processor time for other tasks
            now = perf_counter()
            delay = (1 / fps_target) - (now - last_frame)
            delay = max(min_delay, delay)
            last_frame = now
            if delay > 0:
                sleep(delay)


def call_func(func, args, kwargs) -> Optional[
              Tuple[plt.Figure, matplotlib.axes.Axes, Dict[str, Any]]]:
    # set backend; Important if we don't set it explicitly we could get anything; this overrides wats in the env
    # Qt is well-supported and generally great, Cairo is way more efficient than Agg
    matplotlib.use("Qt5Cairo")
    plt.ion()

    # call user defined function passed from other processes
    ret = func(*args, **kwargs)

    # Determine return type of func or fallback to "static" plot
    # with mapping (Figure, Axes, ndarray)
    if isinstance(ret, tuple) and len(ret) == 3 and isinstance(ret[0], plt.Figure) and \
            isinstance(ret[1], matplotlib.axes.Axes) and isinstance(ret[2], dict):
        fig, ax, params = ret
        return fig, ax, params

    # without mapping (Figure, Axes)
    elif isinstance(ret, tuple) and len(ret) == 2 and isinstance(ret[0], plt.Figure) and \
            isinstance(ret[1], matplotlib.axes.Axes):
        fig, ax = ret
        return fig, ax, dict()

    elif ret is None:
        return None

    else:
        raise ValueError("Invalid return value from plotting function")


# entry point for process
def plot_process_entrypoint(so: SharedObject, dill):
    # keep count of open plots and close on ctrl-c
    try:
        func, stack, args, kwargs = loads(dill)
        with so.lock:
            so.open_plots.value = so.open_plots.value + (2 if so.open_plots.value < 0 else 1)

    except KeyboardInterrupt:
        return

    def handle_exception(exc_type, exc_value, exc_traceback):
        sys.excepthook = sys.__excepthook__
        traceback.format_exc()
        exc = PlotProcessException(exc_value,
                                   "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                                   stack)
        print(f"Plot Process {'-' * (100 - 13)}\n{exc}{'-' * 100}", file=sys.stderr)

        if so.show_msg_box_on_error_in_other_process:
            # noinspection PyBroadException
            try:
                show_error_box(str(exc))
            except Exception:
                pass

        with so.lock:
            so.open_plots.value -= 1
            if not issubclass(exc_type, KeyboardInterrupt):
                so.error_queue_size.value += 1
                so.total_error_count.value += 1
                so.error_queue.put(exc)

        exit(0 if issubclass(exc_type, KeyboardInterrupt) else 1)

    sys.excepthook = handle_exception

    # noinspection PyBroadException
    try:
        func_ret = call_func(func, args, kwargs)
        if func_ret is None:
            plt.show(block=True)
        else:
            mpp = MPP(*func_ret, so=so)
            mpp.loop()

        with so.lock:
            so.open_plots.value -= 1
    except Exception:
        handle_exception(*sys.exc_info())


def _save_fig_as_png(fig, file):
    # No idea how to do it any other way
    # noinspection PyProtectedMember
    surface = fig.canvas._renderer.gc.ctx.get_target()
    surface.write_to_png(file)


class BlitManager:
    """
    From: https://matplotlib.org/stable/tutorials/advanced/blitting.html
    """
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for subclasses of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all the animated artists."""
        fig = self.canvas.figure
        sorted_artists = sorted(self._artists, key=lambda x: x.zorder)
        for a in sorted_artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()
