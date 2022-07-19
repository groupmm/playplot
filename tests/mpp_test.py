import multiprocessing
import os
import shutil
import socketserver
import threading
import unittest
from time import sleep, perf_counter
from unittest.mock import patch
from urllib.error import URLError

import libfmp.b as lfb
import numpy as np
from RangeHTTPServer import RangeRequestHandler

from src.makeplotplayable import *

from examples.example_data import simple_audio_file, simple_annotations_file, long_audio_file

sr = 48000
annotations = np.genfromtxt(simple_annotations_file, delimiter=',')
audio, _ = lfb.read_audio(simple_audio_file, mono=True, Fs=sr)


class TestCaseHelper(unittest.TestCase):
    stopServer = False

    def setUp(self) -> None:
        self.stopServer = False
        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 0)
        self.addCleanup(self.cleanUp)

    def cleanUp(self) -> None:
        self.stopServer = True
        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 0)

        try:
            os.unlink('temp.wav')
        except OSError:
            pass

    @staticmethod
    def loadTemp():
        shutil.copy(long_audio_file, 'temp.wav')

    def runServer(self):
        with socketserver.TCPServer(("", 8088), RangeRequestHandler) as server:
            while not self.stopServer:
                try:
                    server.handle_request()
                except ConnectionResetError:
                    pass

    def timeout_assert(self, assertion, msg=None, timeout=1):
        start_time = perf_counter()
        while perf_counter() < start_time + timeout:
            if assertion():
                return
            sleep(0.01)
        self.assertTrue(False, msg)


class AudioPlaybackTestsForArray(TestCaseHelper):

    def test_invalid_shapes(self):
        with self.assertRaises(AssertionError):
            Session(np.zeros((0, 0, 0)), 48000)

        with self.assertRaises(AssertionError):
            Session(np.zeros((1, 0)), 48000)

        with self.assertRaises(AssertionError):
            Session(np.zeros((3, 0)), 48000)

    def test_short_array(self):
        arr = np.zeros((2, 0))

        session = Session(arr, 48000)
        session.paused = False

        sleep(1)

        session.check()

        session.stop()
        self.assertAlmostEqual(session.time, 0)


class ProcessCreationTests(TestCaseHelper):

    def test_process_count(self):
        session = Session(audio, sr)

        sleep(0.1)
        self.assertEqual(len(multiprocessing.active_children()), 0)

        @session
        def plot(audio_, sr_, name):
            import libfmp.b as lfb_

            fig, ax, _ = lfb_.plot_signal(audio_, sr_)
            return fig, ax, {'title': name}

        plot(audio, sr, "Fig 1")

        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 1)
        plot(audio, sr, "Fig 2")
        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 2)
        plot(audio, sr, "Fig 3")
        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 3)

        session.start()
        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 4)

        sleep(0.5)
        session.check()

        del session

    @patch('src.makeplotplayable._session._plot_process_start_helper')
    def test_process_creation(self, mocked):
        session = Session(audio, sr)

        @session
        def plot(audio_, sr_, name):
            import libfmp.b as lfb_
            fig, ax, _ = lfb_.plot_signal(audio_, sr_)
            return fig, ax, {'title': name}

        session.start()
        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 1)

        plot(audio, sr, "test_process_creation")
        sleep(1)
        self.timeout_assert(lambda: len(multiprocessing.active_children()) == 1)

        sleep(0.5)
        session.check()
        del session
        assert mocked.called


class AudioPlaybackTestsForFile(TestCaseHelper):

    def test_file_remove(self):
        self.loadTemp()

        session = Session.from_file('temp.wav')

        os.unlink('temp.wav')

        session.start()  # stack marker test_file_remove

        sleep(1)
        with self.assertRaises(AudioProcessException) as e:
            session.check()
        e = e.exception
        self.assertTrue(isinstance(e.original_exception, ValueError))
        self.assertTrue("stack marker test_file_remove" in e.origin_stack[-1])

        session.stop()

    def test_invalid_files(self):
        # invalid url
        with self.assertRaises(URLError):
            Session.from_file('http://localhost/not_existing.wav')

        # invalid url signature
        with self.assertRaises(URLError):
            Session.from_file('d:/d/not_existing.wav')

        # invalid file path
        with self.assertRaises(ValueError):
            Session.from_file('not_existing.wav')

        # file not audio file
        with self.assertRaises(RuntimeError):
            Session.from_file('mpp_test.py')

    def test_url_missing(self):
        print("ConnectionResetErrors are normal")
        self.loadTemp()
        threading.Thread(target=self.runServer).start()
        sleep(1)

        session = Session.from_file('http://localhost:8088/temp.wav')
        session.time = 200

        session.start()  # stack marker test_url_missing
        session.paused = False

        sleep(2)
        session.check()
        self.assertNotAlmostEqual(200, session.time)

        self.stopServer = True
        sleep(1)

        session.time = 200

        sleep(3)
        session.check()

        sleep(5)
        with self.assertRaises(AudioProcessException) as e:
            session.check()
        e = e.exception
        self.assertTrue(isinstance(e.original_exception, IOError))
        self.assertTrue("stack marker test_url_missing" in e.origin_stack[-1])

        sleep(3)
        session.stop()


class PlotTests(TestCaseHelper):
    def test_update_function(self):

        session = Session(audio, sr)
        session.start()

        @session
        def plot(annotations_):
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots()

            ax.plot(annotations_[:, 0])

            def update_func(time, pos, paused):
                new_paused = paused ^ (4.8 < time < 5.2)

                if time > 4:
                    time = pos

                return time, new_paused

            return fig, ax, {"title": "test_draw",
                             "overrider_update_function": update_func,
                             "custom_time_to_pos_function": lambda time: time / 2}

        plot(annotations)

        self.assertAlmostEqual(session.time, 0)
        self.assertTrue(session.paused)

        session.time = 1
        sleep(1)
        self.assertAlmostEqual(session.time, 1)
        self.assertTrue(session.paused)

        session.time = 6
        sleep(1)
        self.assertAlmostEqual(session.time, 3)
        self.assertTrue(session.paused)

        session.time = 1.5
        sleep(1)
        self.assertAlmostEqual(session.time, 1.5)
        self.assertTrue(session.paused)

        session.time = 5
        sleep(1)
        self.assertAlmostEqual(session.time, 3.5, delta=0.5)
        self.assertFalse(session.paused)

        session.time = 8.5
        sleep(1)
        self.assertAlmostEqual(session.time, 3.25, delta=0.5)
        self.assertFalse(session.paused)

        session.time = 5
        sleep(1)
        self.assertAlmostEqual(session.time, 2.5, delta=0.5)
        self.assertTrue(session.paused)

        session.check()
        session.stop()


if __name__ == '__main__':
    unittest.main()
