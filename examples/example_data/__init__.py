import os
import numpy as np
__base_path = os.path.abspath(os.path.dirname(__file__))

simple_audio_file = os.path.join(__base_path, "simple_audio.wav")
# any wave file

simple_annotations_file = os.path.join(__base_path, "simple_annotations.csv")
# annotations to said wave file
# two columns (strongly monotonic rising)
# first column: time in audio file
# second column: mapped position (arbitrary)
# example for an audio file of 60s:
# 0.0,0
# 60.0,1

long_audio_file = os.path.join(__base_path, "long_audio.wav")
# long wav file for streaming example (only for advanced)

video_file = os.path.join(__base_path, "video.mp4")
# a (monochrome video file, audio will be ignored) (only for advanced)
audio_to_video_file = os.path.join(__base_path, "video.wav")
# audio file to the video (only for advanced)
# the file should have the same length as the video


# automatic caching
_example_a_file = os.path.join(__base_path, "example_a.npz")

example_a_sr = 48000

if not os.path.exists(_example_a_file):
    import libfmp.b as lfb

    example_a_time_feature_mapping: np.ndarray = np.genfromtxt(simple_annotations_file, delimiter=',')[:, 0]
    example_a_audio: np.ndarray = lfb.read_audio(simple_audio_file, mono=True, Fs=example_a_sr)[0]

    np.savez(_example_a_file, time_feature_mapping=example_a_time_feature_mapping, audio=example_a_audio)

else:
    data = np.load(_example_a_file)
    example_a_time_feature_mapping: np.ndarray = data['time_feature_mapping']
    example_a_audio: np.ndarray = data['audio']
