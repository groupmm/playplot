import os
import numpy as np
__base_path = os.path.abspath(os.path.dirname(__file__))

simple_audio_file = os.path.join(__base_path, "simple_audio.wav")
simple_annotations_file = os.path.join(__base_path, "simple_annotations.csv")  # two columns of data

long_audio_file = os.path.join(__base_path, "long_audio.wav")  # time > 30 min for streaming examples

video_file = os.path.join(__base_path, "video.mp4")
audio_to_video_file = os.path.join(__base_path, "video.wav")  # same length as video

url_audio_example = "https://bigsoundbank.com/UPLOAD/wav/0100.wav"  # url to an audio file

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
