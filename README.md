# Audio -> Video Generator

This program takes an inputted audio file, and plays it over a video of the audios waveform with generated subtitles/ This application would mainly serve for content creation, for example those clips they show on the news of police calls with the waveform and some random background image. Additionally the application will take in an optional background.png image to put behind the waveform. 

In order to use this program, you will need ffmpeg and IMageMagick installed on your machine, in addition to all the pip requirements. You will also need a free assemblyai api key from their website assemblyai.com, add a config.py file to your src/ directory and add the line API_KEY="YOUR_KEY"
