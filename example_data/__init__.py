import os
__base_path = os.path.abspath(os.path.dirname(__file__))

simple_audio_file = os.path.join(__base_path, "simple_audio.wav")
simple_annotations_file = os.path.join(__base_path, "simple_annotations.csv")  # two columns of data

long_audio_file = os.path.join(__base_path, "long_audio.wav")  # time > 30 min for streaming examples

video_file = os.path.join(__base_path, "video.mp4")
audio_to_video_file = os.path.join(__base_path, "video.wav")  # same length as video

url_audio_example = "https://bigsoundbank.com/UPLOAD/wav/0100.wav"  # url to an audio file