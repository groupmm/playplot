import os
import time
import traceback
from time import sleep
from typing import Union

import miniaudio
import numpy as np

from ._util import SharedObject, UrlFile, show_error_box, AudioProcessException

import soundfile
import threading
import sys

TIMEOUT = 5.0


class AudioFileReaderThread(threading.Thread):
    def __init__(self, purl):
        super().__init__(target=self.run, daemon=True)
        buffer_duration = 5

        self.chunk_size = 40000

        self.lock = threading.Lock()

        source = purl if os.path.isfile(purl) else UrlFile(purl)
        self._sf: soundfile.SoundFile = soundfile.SoundFile(source)
        self.length = len(self._sf)
        self.buffer = np.zeros((self._sf.samplerate*buffer_duration, 2), dtype='float32')

        self.start_frame = 0
        self.number_of_frames = 0

        self.next_requested_frame = 0

        self.stop = False
        self.thread_exception = None

        self.start()

    def close(self):
        self.stop = True

    def read(self, start, stop):
        start_time = time.monotonic()
        while True:
            if start_time + TIMEOUT < time.monotonic():
                if self.thread_exception:
                    raise self.thread_exception
                raise TimeoutError("SoundFile was unable to read the audio stream")

            self.lock.acquire(timeout=TIMEOUT)
            if self.thread_exception:
                raise self.thread_exception

            start_index = start - self.start_frame
            stop_index = stop - self.start_frame
            if 0 <= start_index and stop_index <= self.number_of_frames:
                self.next_requested_frame = stop
                self.lock.release()
                return self.buffer[start_index: stop_index]
            self.lock.release()

            self.next_requested_frame = start
            time.sleep(0.001)

    def run(self):
        try:
            while True:
                if self.stop:
                    self._sf.close()
                    return
                if self.next_requested_frame != self.start_frame:
                    with self.lock:
                        # new position is inside of buffer -> move buffer
                        if self.start_frame < self.next_requested_frame < self.start_frame + self.number_of_frames:
                            to_keep = self.buffer[self.next_requested_frame-self.start_frame:self.number_of_frames]
                            self.buffer = np.concatenate((to_keep, np.zeros((self.buffer.shape[0] - to_keep.shape[0], 2))),
                                                         dtype='float32')
                            self.start_frame = self.next_requested_frame
                            self.number_of_frames = to_keep.shape[0]
                        # new position is outside buffer -> reset
                        elif self.start_frame != self.next_requested_frame:
                            self.start_frame = self.next_requested_frame
                            self.number_of_frames = 0

                elif self.buffer.shape[0] - self.number_of_frames > self.chunk_size and \
                        self.length - self.start_frame - self.number_of_frames > 0:
                    insert_position = self.start_frame + self.number_of_frames
                    self._sf.seek(insert_position)
                    limited_chunk_size = min(self.chunk_size, self.length - insert_position)
                    data = self._sf.read(limited_chunk_size, dtype='float32', always_2d=True)
                    if data.shape[0] == 0:
                        raise IOError("SoundFile was unable to read the audio stream")
                    with self.lock:
                        if insert_position == self.start_frame + self.number_of_frames:
                            self.buffer[self.number_of_frames:self.number_of_frames+limited_chunk_size] = data
                            self.number_of_frames += limited_chunk_size

                else:
                    time.sleep(0.01)
        except Exception as e:
            self.thread_exception = e

        # f.seek(start)
        # f.read(stop - start, dtype='float32', always_2d=True)


class Playback:
    def __init__(self, so: SharedObject, x: Union[str, np.ndarray], sr):
        self.so = so

        self.duration = so.duration
        self.sr = sr
        self.x = x
        self.new_time_used = False
        self.playback_stopped = False

        with so.lock:
            self.time = so.time.value
            self.volume = so.volume.value
            self.override_time = self.time
            self.paused = so.paused.value
            self.looping = so.looping.value

        channel_count = 2 if isinstance(x, str) else (len(x.shape))

        self.device = miniaudio.PlaybackDevice(sample_rate=sr,
                                               nchannels=channel_count,
                                               output_format=miniaudio.SampleFormat.FLOAT32,
                                               buffersize_msec=30)

        # choose generator for audio signal deepening on how the Session was started
        self.gen_exception = None
        self.gen_instance = self.gen_file() if isinstance(x, str) else self.gen()
        # prime generator
        next(self.gen_instance)

        if self.gen_exception:
            raise self.gen_exception

        # let miniaudio do its job in its own thread
        self.device.start(self.gen_instance)

        if self.gen_exception:
            raise self.gen_exception

    # generator function based on ndarray
    def gen(self):
        try:
            x: np.ndarray = self.x
            required_frames = yield b""

            head = 0

            while True:
                # in paused state play silence
                if self.paused or self.playback_stopped:
                    required_frames = yield np.zeros((required_frames, 1), dtype=np.float32)
                    continue

                # check if time skip occurred
                if self.override_time is not None:
                    self.new_time_used = False
                    ot = self.override_time
                    self.override_time = None

                    head = int(ot * self.sr)

                start = head
                head += required_frames
                stop = head

                # reached end of clip
                if stop > x.shape[0]:
                    stop = x.shape[0]
                    head = 0
                    if not self.looping:
                        self.playback_stopped = True

                self.time = head / self.sr
                self.new_time_used = True

                ret = x[start:stop, None]
                required_frames = yield ret * self.volume
        except Exception as e:
            if threading.current_thread() is threading.main_thread():
                raise e
            self.gen_exception = e

    # generator function based on ndarray
    def gen_file(self):
        try:
            x: str = self.x

            frt = AudioFileReaderThread(x)

            required_frames = yield b""

            head = 0

            # in paused state play silence
            while True:
                # in paused state play silence
                if self.paused or self.playback_stopped:
                    required_frames = yield np.zeros((required_frames, 1), dtype=np.float32)
                    continue

                # check if time skip occurred
                if self.override_time is not None:
                    self.new_time_used = False
                    ot = self.override_time
                    self.override_time = None

                    head = int(ot * self.sr)

                start = head
                head += required_frames
                stop = head

                # reached end of clip
                if stop > frt.length:
                    stop = frt.length
                    head = 0
                    if not self.looping:
                        self.playback_stopped = True

                self.time = head / self.sr
                self.new_time_used = True

                # get required frames directly from the file
                ret = frt.read(start, stop)
                # ret = ret.sum(axis=1) / ret.shape[1]
                required_frames = yield ret * self.volume

        except Exception as e:
            if threading.current_thread() is threading.main_thread():
                raise e
            self.gen_exception = e

    def loop(self):
        so = self.so

        while True:
            if self.gen_exception:
                raise self.gen_exception

            with so.lock:
                if so.stop.value or (so.close_with_last_plot and so.openPlots.value == 0):
                    break

                time = so.time.value
                time_skip = so.time_skip.value
                so.time_skip.value = False

                self.looping = so.looping.value
                self.volume = so.volume.value

                if self.playback_stopped:
                    so.paused.value = True
                    self.paused = True
                    self.playback_stopped = False
                else:
                    self.paused = so.paused.value

                if time_skip:
                    self.override_time = time

                # prevent old time to be propagated
                if self.new_time_used and self.override_time is None:
                    so.time.value = self.time

            sleep(0.001)

    def close(self):
        self.device.close()
        with self.so.lock:
            self.so.stop.value = True


# audioProcess entry point
def audio_process_entrypoint(so: SharedObject, x, sr, stack):

    def handle_exception(exc_type, exc_value, exc_traceback):
        sys.excepthook = sys.__excepthook__
        traceback.format_exc()
        exc = AudioProcessException(exc_value,
                                    "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                                    stack)
        print(f"Audio Process {'-'*(100-14)}\n{exc}{'-'*100}", file=sys.stderr)

        if so.show_msg_box_on_error_in_other_process:
            # noinspection PyBroadException
            try:
                show_error_box(str(exc))
            except Exception:
                pass

        with so.lock:
            so.stop.value = True
            if not issubclass(exc_type, KeyboardInterrupt):
                so.error_queue_size.value += 1
                so.total_error_count.value += 1
                so.error_queue.put(exc)

        exit(0 if issubclass(exc_type, KeyboardInterrupt) else 1)

    sys.excepthook = handle_exception

    # noinspection PyBroadException
    try:
        pb = Playback(so, x, sr)
        pb.loop()
        pb.close()
    except Exception:
        handle_exception(*sys.exc_info())


