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

from flask import Flask, request, jsonify, send_file
app = Flask(__name__)


def generate_waveform_video(audio_path, output_video_path, rate=60, bars=50, width=800, height=600, white_background=False):
    command = [
        'seewav',
        '--rate', str(rate),
        '--bars', str(bars),
        '--width', str(width),
        '--height', str(height),
        '--color', '1,1,1',
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

    if subtitle_file and os.path.exists(subtitle_file):
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
                subtitle_clip = (TextClip(text, fontsize=24, color='black', bg_color='white')
                                 .set_position(('center', 'bottom'))
                                 .set_duration(end_time - start_time)
                                 .set_start(start_time))
                subtitle_clips.append(subtitle_clip)
        
        final_video = CompositeVideoClip([video, *subtitle_clips])
    else:
        final_video = video

    final_video.write_videofile(output_video, codec="libx264")


def parse_srt_time(srt_time):
    h, m, s = srt_time.split(":")
    s, ms = s.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def step(input_video):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(input_video)

    if not transcript or not transcript.text.strip():
        print("No transcribable audio found; skipping subtitle generation.")
        return 

    subtitles = transcript.export_subtitles_srt()
    with open("subtitles.srt", "w") as f:
        f.write(subtitles)

def main_process(audio):
    audio_file = audio
    output_video = os.path.join(os.path.dirname(__file__), "output_video.mp4")
    final_output_video = os.path.join(os.path.dirname(__file__), "final_output_video.mp4")

    print(f"Generating waveform video at: {output_video}")
    generate_waveform_video(audio_file, output_video, rate=60, bars=100, width=800, height=600, white_background=False)

    if not os.path.exists(output_video):
        print("Output video was not created.")
        return

    time.sleep(5)
    input_video = output_video
    
    step(input_video)
    
    subtitle_file = "subtitles.srt"
    if os.path.exists(subtitle_file):
        print("Subtitles file exists. Creating subtitled video.")
        create_subtitled_video(input_video, subtitle_file, final_output_video)
    else:
        print("Subtitles file does not exist. Creating video without subtitles.")
        create_subtitled_video(input_video, None, final_output_video)

    if os.path.exists(final_output_video):
        print("Final output video created successfully.")
    else:
        print("Final output video was not created.")

    os.remove(subtitle_file) if os.path.exists(subtitle_file) else None
    os.remove(output_video) if os.path.exists(output_video) else None


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

@app.route("/generate_video", methods=["POST"])
def upload_and_generate():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    file.save("temp_audio.wav")
    main_process("temp_audio.wav")
    return send_file("final_output_video.mp4", as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)