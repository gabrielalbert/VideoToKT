
import os
import re
import json
import librosa
import requests
from pathlib import Path
from datetime import datetime
from pptx import Presentation
from pptx.util  import Pt,Inches
from moviepy import VideoFileClip
from multiprocessing import pool,cpu_count
from langchain_community.llms import Ollama
from langchain.schema import (AIMessage,HumanMessage,SystemMessage)
from transformers import WhisperProcessor, WhisperForConditionalGeneration,pipeline,BartTokenizer,BartForConditionalGeneration,BartTokenizer, BartModel
from Library.settings import *
from fastapi import FastAPI,HTTPException,Response
from pydantic import BaseModel

def convert_text_to_textSummary_ollama(content):
    print(f"convert_text_to_textSummary_ollama start ------------------ at ",datetime.now().time())
    try:
        # prompt = f"""
            # content={content}
            # Please generate a structured JSON output based on the following instructions. 
            # 1.Directly explains the concept instead of summarizing a discussion.
            # 2.Avoids phrases like ""The speakers discusses ...." or "They explain..."
            # 3.Presents information as on educational breakdown,making it clear for reader.
            # The JSON should have these fields:
            # Make sure the output is valid JSON, structured as follows:
            # [{{
            #     "topic": "Extract main topic of the discussion from the beginning of contenet",
            #     "topic_summary": "summarize the key discussion points of topic",
            #     "chapters": [
            #         {{
            #             "timecode": "The time span for the chapter (in the format HH:MM:SS)",
            #             "chapterSummary": "summarize the key discussion in this chapter",
            #             "chapterDescription": {{
            #                 "Overview": "A detailed step by step explanation of the concept and Describe what it is,why it is,why it is important,how it works,and its use cases.
            #                 Ensure it is self-contained and does not reference a discussion or presenter give that detail in paragraph.
            #             }}
            #         }}
            #     ]
            # }}]
            # 1.chapters are based on different conceppts discussed in the content.
            # 2.The overview field provides a detailed explanation of how the process works (not just a summary).
     
            # Return strictly the output as valid JSON object only, ensuring proper indentation and format no extra information except json in output.
            # ensure all field of json have data as per instructions and 
            # ensure no json related error like 'Expecting property name enclosed in double quotes'
            # and must be response is only "valid json object"
            # """

        # chat_message=[SystemMessage(content=prompt), HumanMessage(content=prompt), ]
        # llm=Ollama(model=OLLAMA_MODEL)
        # summary_text=llm.invoke(input=chat_message,max_token=2048) 
        prompt = f"""
            content={content}
            Please generate a structured JSON output based on the following instructions. 
            1.Directly explains the concept instead of summarizing a discussion.
            2.Avoids phrases like ""The speakers discusses ...." or "They explain..."
            3.Presents information as on educational breakdown,making it clear for reader.
            
            The JSON should have these fields:
            Make sure the output is valid JSON, structured as follows:
            [{{
                "topic": "Extract main topic of the discussion from the beginning of content",
                "topic_summary": "summarize the key discussion points of topic",
                "chapters": [
                    {{
                        "timecode": "The time span for the chapter (in the format HH:MM:SS)",
                        "chapterSummary": "summarize the key discussion in this chapter",
                        "chapterDescription": {{
                            "Overview": "A detailed step by step explanation of the concept and Describe what it is,why it is,why it is important,how it works,and its use cases.
                            Ensure it is self-contained and does not reference a discussion or presenter give that detail in paragraph.please dont add extra json property
                        }}
                    }}
                ]
            }}]
            
            1.please analyze and then extract all data from given content.
            2.chapters are based on different concepts discussed in the content.
            3.The overview field provides a detailed explanation of how the process works (not just a summary).
            please does not add code in response add only text in json object,
            Return strictly the output as valid JSON object only, 
            ensuring proper indentation and format no extra information except json in output.
            ensure all field of json have data as per instructions and 
            ensure no json related error and no json validation errors 
            and must be response is only "valid json object" make sure without json format errors.
            """
        res = requests.post(OLLAMA_MODEL_API, json={
                "prompt": prompt,
                "stream" : False,
                "model" : OLLAMA_MODEL
            })
        # print('res.text=',res.text)
        res_dict=json.loads(res.text)
        # print('res_dict=',res_dict)
        summary_text=res_dict.get("response")  
        print('summary_text=',summary_text) 
        return summary_text
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []

    except Exception as e:
        print('error convert_text_to_textSummary_ollama:',{e})
        return []
    
def get_convert_text_to_textSummary_ollama(summary_text_file_path,transcription):
    try:
        data=[]
        summary_text=''
        if os.path.exists( summary_text_file_path):
            print('file already exist reading filepath=',summary_text_file_path)
            with open(summary_text_file_path,"r") as file:
                summary_text=file.read()
            if summary_text and isinstance(summary_text, str) and summary_text.strip():  
                data= ExtractJson(summary_text) 
            else:
                data = "[]"  # Default to an empty JSON array
            return data
        else :
            print('file not exist filepath=',summary_text_file_path)
            summary_text=convert_text_to_textSummary_ollama(transcription)
            
            with open(summary_text_file_path,"w") as file:
                if isinstance(summary_text,list):
                    summary_text="\n".join(summary_text)
                file.write(summary_text)
            if summary_text and isinstance(summary_text, str) and summary_text.strip():  
                data= ExtractJson(summary_text) 
            else:
                data = "[]"  # Default to an empty JSON array
       
        return data
    except Exception as e:
        print('error get_convert_text_to_textSummary_ollama:',{e})
        return summary_text
 
def ExtractJson(summary_text)   :
    try:
        if summary_text.strip().startswith('{'):
            summary_text = f'[{summary_text}]'
        # Extract JSON using regex to get content between the square brackets
        print('summary_json before extract=',summary_text)
        json_pattern = r'\[.*\]'
        json_match = re.search(json_pattern, summary_text, re.DOTALL)

        # Extract and clean up the JSON string
        if json_match:
            json_str = json_match.group(0).strip()  # Remove unnecessary whitespaces around the JSON
            try:
                # Load the JSON data into a Python object
                extracted_json = json.loads(json_str)
                print('extracted_json=',extracted_json)
                return extracted_json
                # print('extracted_json=',extracted_json)  # Print the extracted JSON object
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        else:
            print("No JSON found")
    except Exception as e:
        print('error in ExtractJson-------------------------:',{e})
        return extracted_json
 