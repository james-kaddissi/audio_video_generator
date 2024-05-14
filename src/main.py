import speech_recognition as sr
import os
import subprocess

import time
from faster_whisper import WhisperModel

from pydub import AudioSegment
from pydub.silence import split_on_silence
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import assemblyai as aai

from config import API_KEY

aai.settings.api_key = API_KEY
r = sr.Recognizer()

def generate_waveform_video(audio_path, output_video_path, rate=60, bars=50, width=800, height=600, white_background=False):
    command = [
        'seewav',
        '--rate', str(rate),
        '--bars', str(bars),
        '--width', str(width),
        '--height', str(height),
        audio_path,
        output_video_path
    ]

    if white_background:
        command.append('--white')

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error generating waveform video:")
        print(result.stderr)
    else:
        print("Waveform video generated successfully!")
        print(result.stdout)

def create_subtitled_video(input_video, subtitle_file, output_video):
    video = VideoFileClip(input_video)

    with open(subtitle_file, "r") as f:
        subtitles = f.read().split("\n\n")

    subtitle_clips = []
    for subtitle in subtitles:
        if not subtitle.strip():
            continue

        parts = subtitle.split("\n")
        if len(parts) >= 3:
            times = parts[1].split(" --> ")
            start_time = parse_srt_time(times[0])
            end_time = parse_srt_time(times[1])
            text = "\n".join(parts[2:])

            subtitle_clip = (TextClip(text, fontsize=24, color='white', bg_color='black')
                             .set_position(('center', 'bottom'))
                             .set_duration(end_time - start_time)
                             .set_start(start_time))
            subtitle_clips.append(subtitle_clip)

    final_video = CompositeVideoClip([video, *subtitle_clips])
    final_video.write_videofile(output_video, codec="libx264")

def parse_srt_time(srt_time):
    h, m, s = srt_time.split(":")
    s, ms = s.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def step(input_video):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(input_video)
    subtitles = transcript.export_subtitles_srt()
    with open("subtitles.srt", "w") as f:
        f.write(subtitles)

def main_process(audio):
    audio_file = audio
    output_video = "output_video.mp4"
    generate_waveform_video(audio_file, output_video, rate=60, bars=1000, width=800, height=600, white_background=True)
    time.sleep(5)
    input_video = output_video
    step(input_video)
    create_subtitled_video(input_video, "subtitles.srt", "final_output_video.mp4")

    os.remove("subtitles.srt")
    os.remove("output_video.mp4")

def record_microphone(duration, temp_audio_file="temp_audio.wav"):
    with sr.Microphone() as source:
        print("Recording...")
        audio_data = r.record(source, duration=duration)
        with open(temp_audio_file, "wb") as f:
            f.write(audio_data.get_wav_data())
        print("Recording finished.")
    return temp_audio_file

def run_with_recording(duration):
    temp_audio_file = "temp_audio.wav"
    try:
        record_microphone(duration, temp_audio_file)
        main_process(temp_audio_file)
    finally:
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)


def run():
    run_with_recording(15)

run()
