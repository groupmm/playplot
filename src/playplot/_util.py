import urllib.request
from multiprocessing import Value, Lock, Queue


class SharedObject:
    """One instance per session handles all ipc"""
    def __init__(self, show_msg_box_on_error_in_other_process, duration, close_with_last_plot, fps_target,
                 save_folder, plot_min_sleep, looping):
        self.show_msg_box_on_error_in_other_process = show_msg_box_on_error_in_other_process
        self.duration = duration
        self.save_folder = save_folder
        self.lock = Lock()
        self.close_with_last_plot: bool = close_with_last_plot
        self.fps_target = Value('d', fps_target, lock=False)
        self.plot_min_sleep = Value('d', plot_min_sleep, lock=False)
        self.time = Value('d', 0, lock=False)
        self.volume = Value('d', 0, lock=False)
        self.paused = Value('i', True, lock=False)
        self.looping = Value('i', looping, lock=False)
        self.stop = Value('i', False, lock=False)
        self.open_plots: Value = Value('i', -1, lock=False)
        self.time_skip = Value('i', False, lock=False)
        self.save_as_frame_number = Value('i', -1, lock=False)
        self.plots_wrote_current_frame = Value('i', 0, lock=False)
        self.total_error_count = Value('i', 0, lock=False)
        self.error_queue_size = Value('i', 0, lock=False)
        self.error_queue = Queue()


class UrlFile:
    """Provide a file like object from a (http) url, with seek capabilities"""
    def __init__(self, url):
        self.url = url
        self.sock = urllib.request.urlopen(url, timeout=2)
        self.length = self.sock.length
        self.pos = 0
        self.last_pos = 0

    def read(self, n):
        if self.pos != self.last_pos:
            req = urllib.request.Request(self.url)
            req.add_header('Range', f'bytes={self.pos}-')
            self.sock.close()
            self.sock = urllib.request.urlopen(req)
        self.pos += n
        self.last_pos = self.pos
        return self.sock.read(n)

    def seek(self, offset, whence=0):
        if whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.length - offset
        else:
            self.pos = offset

    def readinto(self, buf):
        data = self.read(len(buf))
        buf[:len(data)] = data
        return len(data)

    def tell(self):
        return self.pos

    def close(self):
        self.sock.close()


def show_error_box(text: str):
    """Show an errorbox, if no Qt application is running create one"""
    from PyQt5.QtWidgets import QMessageBox, QApplication
    if not QApplication.instance():
        _ = QApplication([])
    QMessageBox.critical(None, "Plotting Error", text)


def runs_in_notebook() -> bool:
    """Check if it is executed in an interactive environment"""
    try:
        # noinspection PyUnresolvedReferences
        return __IPYTHON__
    except NameError:
        return False


class ForeignProcessException(Exception):
    """
    This Exception contains all attributes to capture important information coming from another process.

    Attributes
    ----------
    original_exception
        exception raised in other process

    formatted_traceback
        traceback of exception raised in other process

    origin_stack
        stack of process creation (main process)

    """

    def __init__(self, original_exception, formatted_traceback, origin_stack):
        super().__init__()
        self.original_exception = original_exception
        self.formatted_traceback = formatted_traceback
        self.origin_stack = origin_stack

    def __reduce__(self):
        return self.__class__, (self.original_exception, self.formatted_traceback, self.origin_stack)

    def __str__(self):
        process_type = 'the audio playback process' if isinstance(self, AudioProcessException) else \
            'a plotting playback process' if isinstance(self, PlotProcessException) else \
            'a foreign process'
        ret = f"An {type(self.original_exception).__name__} occurred inside {process_type}:\n"
        ret += self.formatted_traceback
        ret += "\nThis Process was started from:\n"
        ret += '\n'.join(self.origin_stack)
        return ret

    def __repr__(self):
        return str(self)


class PlotProcessException(ForeignProcessException):
    """
    ForeignProcessException raised by plot process
    :class:`ForeignProcessException`
    """
    pass


class AudioProcessException(ForeignProcessException):
    """
    ForeignProcessException raised by audio process
    :class:`ForeignProcessException`
    """
    pass
