
import os
import librosa
import requests
import numpy as np
from pathlib import Path
from datetime import datetime
from pptx import Presentation
from pptx.util  import Pt,Inches
from moviepy import VideoFileClip
from multiprocessing import pool,cpu_count
from transformers import WhisperProcessor, WhisperForConditionalGeneration,pipeline,BartTokenizer,BartForConditionalGeneration,BartTokenizer, BartModel


def convert_audio_to_text(file_path,model_path):
    print(f'Converting audio to text for file: {file_path}')

    transcriptions=[]
    chunk_duration=60  # seconds
    sampling_rate_sr=16000
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        processor = WhisperProcessor.from_pretrained(model_path) # load model and processor
        model = WhisperForConditionalGeneration.from_pretrained(model_path)
        model.config.forced_decoder_ids = None
        
        audio,sampling_rate=librosa.load(file_path,sr=sampling_rate_sr)
        total_duration=librosa.get_duration(y=audio,sr=sampling_rate)
        print(f'Total audio duration-----------------: {total_duration:.2f} seconds')

        chunk_samples = int(chunk_duration * sampling_rate)
        for i in range(0, len(audio), chunk_samples):
            chunk = audio[i:i + chunk_samples]
            
            if len(chunk) == 0 or np.mean(np.abs(chunk)) < 0.01:
                print(f"Skipping silent chunk {i // chunk_samples + 1}/{len(audio) // chunk_samples + 1}-----------at",datetime.now().time())
                continue
            
            input_features = processor(np.array(chunk), sampling_rate=sampling_rate, return_tensors="pt").input_features
            predicted_ids = model.generate(input_features, num_beams=5, early_stopping=True)
            transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            transcriptions.append(transcription)
            
            print(f"Processed chunk {i // chunk_samples + 1}/{len(audio) // chunk_samples + 1}------------ at ",datetime.now().time())
        
        return " ".join(transcriptions)
    
    except Exception as e:
        print('error no text found in video :',e)


def get_convert_audio_to_text(transcription_file_path: str, output_audio_path: str, model_path: str) -> str:
    """Converts audio to text, caching the result in a file."""
    
    try:
        if os.path.exists(transcription_file_path):
            print(f'File already exists, reading from {transcription_file_path}')
            with open(transcription_file_path, "r") as file:
                return file.read()
        
        print(f'File does not exist, generating transcription for {transcription_file_path}')
        transcription = convert_audio_to_text(output_audio_path, model_path)
        
        with open(transcription_file_path, "w") as file:
            file.write(transcription)
        
        return transcription
    except Exception as e:
        print(f'Error processing audio to text: {e}')
        return ""
