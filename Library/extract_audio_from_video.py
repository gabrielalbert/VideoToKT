import os
import sys
import requests
from pathlib import Path
from datetime import datetime
import librosa
from moviepy import VideoFileClip
from pptx import Presentation
from pptx.util import Pt, Inches
from transformers import (WhisperProcessor, WhisperForConditionalGeneration, pipeline,
                          BartTokenizer, BartForConditionalGeneration, BartModel)


def extract_audio_from_video(video_path: str, output_audio_path: str) -> str:
    """ Extracts audio from a given video file and saves it as an audio file.   """
    
    print('Starting audio extraction from video...')
    try:
        with VideoFileClip(video_path) as video:
            if video.audio is None:
                raise ValueError("No audio stream found in the video.")
            video.audio.write_audiofile(output_audio_path)
        print('Audio extraction completed successfully.')
    except Exception as e:
        print(f'Error extracting audio from video: {e}')
    
    return output_audio_path