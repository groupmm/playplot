import numpy as np
import matplotlib.pyplot as plt
from makeplotplayable import Session

from example_data import example_a_time_feature_mapping as time_feature_mapping, example_a_audio as audio, example_a_sr as sr


def main01():
    # crate a Session from the audio data
    session01 = Session(audio, sr)

    # decorate the plot function with the session
    # noinspection PyShadowingNames
    @session01
    def plot(name):
        # define a plot function
        # the function must be serializable by dill (shouldn't be a practical limitation)
        # if there are issues check the documentation and the limitations of dill and multiprocessing

        # create figure and axis
        fig = plt.figure(figsize=(6, 2), dpi=72)
        ax = plt.subplot(1, 1, 1)

        # plot waveform into the figure -----------------------------------------------
        T_coef = np.arange(audio.shape[0]) / sr
        ax.plot(T_coef, audio, color='gray')
        ax.set_xlim([T_coef[0], T_coef[-1]])
        ylim_x = audio[np.isfinite(audio)]
        x_min, x_max = ylim_x.min(), ylim_x.max()
        if x_max == x_min:
            x_max = x_max + 1
        ax.set_ylim([min(1.1 * x_min, 0.9 * x_min), max(1.1 * x_max, 0.9 * x_max)])
        ax.set_xlabel('Time (seconds)')
        plt.tight_layout()
        # -----------------------------------------------------------------------------

        # return the figure, the axis and an optional config dict for the cursor as a tuple
        return fig, ax, {'title': name}

    # call the plot function, it will create the plot in another process
    plot("A01 Fig 1")

    # we can create multiple plots in on session (all plots in a session will be linked)
    plot("A01 Fig 2")

    # start the session to enable audio playback
    session01.start()

    # block until all plots are closed
    session01.join()
    # check for exceptions from the other processes
    session01.check()


def plot_waveform():
    # create figure and axis
    fig = plt.figure(figsize=(6, 2), dpi=72)
    ax = plt.subplot(1, 1, 1)

    # plot into the axis
    T_coef = np.arange(audio.shape[0]) / sr
    ax.plot(T_coef, audio, color='gray')
    ax.set_xlim([T_coef[0], T_coef[-1]])
    ylim_x = audio[np.isfinite(audio)]
    x_min, x_max = ylim_x.min(), ylim_x.max()
    if x_max == x_min:
        x_max = x_max + 1
    ax.set_ylim([min(1.1 * x_min, 0.9 * x_min), max(1.1 * x_max, 0.9 * x_max)])
    ax.set_xlabel('Time (seconds)')
    plt.tight_layout()

    return fig, ax


def main02():
    session02 = Session(audio, sr,show_msg_box_on_error_in_other_process=True)

    # start the session to enable audio playback
    session02.start()

    # set initial volume
    session02.volume = 0.5

    # begin playback at the 10s mark
    session02.time = 10

    # create a wrapped version of the plot function with the help os the session
    plot_wraped = session02(plot_waveform)

    # wrap with decorator and add functionality
    @session02
    def plot_decorated(**kwargs):
        return *plot_waveform(), kwargs

    # call the original version
    plot_waveform()

    # call the wrapped function
    plot_wraped()

    # call the new decorated function with extra kwargs
    plot_decorated(title="A02 Decorated", window_pos=(64, 64), axvline_kwargs={"alpha": 0.5, "ls": "--", "color": "c", "lw": 2, "zorder": 10})

    # block until all plots are closed
    session02.join()
    # check for exceptions from the other processes
    session02.check()


def main03():
    session03 = Session(audio, sr)

    # start the session to enable audio playback
    session03.start()
    # session03.volume = 0

    @session03
    def plot():
        fig, ax = plt.subplots()
        ax.plot(time_feature_mapping)
        ax.set_xlabel('Time (measures)')
        ax.set_ylabel('Time (seconds)')

        mapping = time_feature_mapping, 0, time_feature_mapping.size - 1

        return fig, ax, {"mapping": mapping,
                         "title": "A03 Dense Mapping"}

    plot()
    # block until all plots are closed
    session03.join()
    # check for exceptions from the other processes
    session03.check()


if __name__ == "__main__":
    print("main01")
    main01()
    print("main02")
    main02()
    print("main03")
    main03()
