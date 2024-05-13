import speech_recognition as sr
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence

r = sr.Recognizer()

# opens the file and converts it to text
def transcribe_audio(filename):
    with sr.AudioFile(filename) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
    return text

def chunk_audio(filename):
    sound = AudioSegment.from_file(filename)
    chunks = split_on_silence(sound, min_silence_len=1500, silence_thresh=sound.dBFS-14, keep_silence=500)
    folder = "audio-chunks"
    if not os.path.isdir(folder):
        os.mkdir(folder)
    final_text = ""
    for i, audio_chunk in enumerate(chunks, start=1):
        filename = os.path.join(folder, f"chunk{i}.wav")
        audio_chunk.export(filename, format="wav")
        try:
            text = transcribe_audio(filename)
        except sr.UnknownValueError as e:
            print("Error: ", str(e))    
        else:
            text = f"{text.capitalize()}. "
            print(filename, ":", text)
            final_text += text
    return final_text

def transcribe_microphone(duration):
    with sr.Microphone() as source:
        print("Recording...")
        audio_data = r.record(source, duration=duration)
        print("Transcribing...")
        text = r.recognize_google(audio_data)
        print(text)
transcribe_microphone(10)