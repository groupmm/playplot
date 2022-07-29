import matplotlib.pyplot as plt
from playplot import Session

if __name__ == "__main__":

    # create a Session from the audio data (url not final) (also accepts local paths)
    session = Session.from_file("https://github.com/groupmm/playplot/blob/main/examples/example_data/bach_bwv245_no22_vokalensemble_ilmenau.wav?raw=true")

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

    # Wait until all plots are closed
    session.join()
    # Check for potential exceptions in the other processes
    session.check()
