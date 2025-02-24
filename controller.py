import os
import sys
import shutil
import asyncpg
import asyncio
import logging
import requests
from datetime import datetime
from pathlib import Path
from Library.settings import *
from Library.delete_temp import *
from Library.convert_json_to_ppt import *
from Library.convert_audio_to_text import *
from Library.extract_image_from_video import *
from Library.extract_audio_from_video import *
from Library.convert_text_to_textSummary_ollama import *
from Library.postgressql import get_postgres
from fastapi import FastAPI, File, UploadFile,Depends,APIRouter,Response

router=APIRouter()

# logging.basicConfig(level=logging.DEBUG)
 # print('TESSERACT_PATH=',TESSERACT_PATH)

@router.get('/test')
def test():
     return {'message': 'Test API called successfully'}

@router.post('/testapi')
def test(prompt:str):
    res = requests.post('http://10.63.34.245:11435/api/generate', json={
                "prompt": prompt,
                "stream" : False,
                "model" : "llama3.2:1b"
            })
    # print('res.text=',res.text)
    res_dict=json.loads(res.text)
    # print('res_dict=',res_dict)
    res_value=res_dict.get("response")
    print('res_value=',res_value)
    # return Response(content=res_value, media_type="application/json")
    return {'message': res_value}
   

@router.post("/addstatus")
async def add_status(request: Request, file: UploadFile, user_name :str,db_pool: asyncpg.Pool = Depends(get_postgres)):
    """Handles file upload and inserts metadata into the database."""
    try:
        async with db_pool.acquire() as con:
            result = await con.fetchval(
                "INSERT INTO videotoppt (file_path, status,file_name,start_time,user_name) VALUES ($1, $2,$3,NOW(),$4) RETURNING id;", '', 'created',file.filename,user_name)
            if result:
                file_path, file_name, output_audio_path = save_uploaded_file(file, str(result))
                return {"statusMessage": "success", "status":"created" ,"id": str(result),
                        "file_path": file_path, "file_name": file.filename, "audio_path": output_audio_path}
        raise ValueError("Database insertion failed")
    except Exception as e:
        print('error=',str(e))
        return {"statusMessage": "error", "error": str(e)}


@router.post("/updatestatus")
async def update_status(status: str, statusMessage: str ,file_name: str, id: str, db_pool: asyncpg.Pool = Depends(get_postgres)):
    """Updates the status and file path of an existing entry."""
    try:
        async with db_pool.acquire() as con:
            # result = await con.fetchval("UPDATE videotoppt SET status = $1, file_path = $2 WHERE id = $3 RETURNING id;", status, file_name, id)
            strQuery="""
                UPDATE videotoppt 
                SET 
                    status = $1::VARCHAR, 
                    file_path = $2, 
                    uploaded_time = CASE WHEN $1 = 'inprogress' THEN NOW() ELSE uploaded_time END,
                    completed_time = CASE WHEN $1 != 'inprogress' THEN NOW() ELSE completed_time END
                WHERE id = $3 
                RETURNING id;
            """
            # print('strQuery=',strQuery)
            result = await con.fetchval(strQuery, status, file_name, id)
            if result:
                return {"statusMessage": statusMessage, "status": status, "id": str(result)}
        raise ValueError("Update failed")
    except Exception as e:
        print('error=',str(e))
        return {"statusMessage": "error", "error": str(e)}
 

@router.post("/downloadfile")
async def download_file(id: str):
    """Handles the download of a PowerPoint file."""
    try:
        file_path = Path(MEDIA_ROOT) / 'ppt_data' / f"{id}.pptx"
       
        if file_path.exists():
            headers = {"Content-Disposition": f'attachment; filename="{id}.pptx"'}
            print(f"Presentation downloaded successfully at {datetime.now().time()}")
            return FileResponse(
                path=file_path,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                headers=headers
            )
        raise FileNotFoundError("File not found")
    except Exception as e:
        return {"statusMessage": "error", "error": str(e)}
 
@router.post("/processfile")
async def processfile(request: Request, id: str, db_pool: asyncpg.Pool = Depends(get_postgres)):
    """Processes a video file, extracts audio, transcribes, summarizes, and generates a PowerPoint presentation."""
    try:
        # delete_existing_data('images','ppt_data')
        await update_status('inprogress',"inprogress status updated successfully" ,id, id, db_pool)
        temp_file_path = Path(MEDIA_ROOT) / 'files'
        files = [f for f in temp_file_path.glob(f"{id}.*") if f.suffix not in {".txt", ".mp3"}]
        print(files)
        if not files:
            raise ValueError("No valid file found")
        
        file_name = files[0].name
        file_ext = Path(file_name).suffix.lower()
        file_path = temp_file_path / file_name
        
        output_audio_path = Path(str(file_path).replace(file_ext, '.mp3'))
        if not output_audio_path.exists():
            extract_audio_from_video(file_path, output_audio_path)
        
        transcription = process_transcription(id, output_audio_path)
        summary_text = process_summary(id, transcription)
        image_filenames = get_extract_image_from_video(file_path, id)
        try:
            ppt_name = convert_json_to_ppt(request, summary_text, Path(MEDIA_ROOT) / 'ppt_data', id, image_filenames)
        
        except RuntimeError as e:
            delete_existing_data(['files','images'])
            raise RuntimeError(f"Error in json formate response from ollama model:{e}")
    
        print('completed-------------')
        print('before delete')
        delete_existing_data(['files','images'])
        print('after delete')

        return await update_status('completed',"completed status updated successfully", id, id, db_pool)
        # return status_response
        # return 0
    except Exception as e:
        return {"statusMessage": "error", "error": str(e)}

def save_uploaded_file(inputfile: UploadFile, id: str):
    """Saves the uploaded file and retrieves its details."""
    save_path = Path(MEDIA_ROOT) / 'files'
    save_path.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(inputfile.filename).suffix.lower()
    file_name = f"{id}{file_ext}"
    file_path = save_path / file_name
    
    with open(file_path, 'wb') as dest:
        shutil.copyfileobj(inputfile.file, dest)
    
    return file_path, *get_file_details(file_name, file_path)

def get_file_details(file_name: str, file_path: Path):
    
    """Validates the file format and generates file details."""
    
    supported_formats = {'.wmv', '.mp4', '.mkv'}
    
    file_ext = Path(file_name).suffix.lower()
    if file_ext not in supported_formats:
        raise ValueError(f"Unsupported file format: {file_ext}. Only {supported_formats} are supported.")
    
    return file_name.replace(file_ext, ''), str(file_path).replace(file_ext, '.mp3')

def process_transcription(file_name, output_audio_path):

    transcription_file_path = Path(MEDIA_ROOT) / 'files' / f"{file_name}_text.txt"
    return get_convert_audio_to_text(transcription_file_path, output_audio_path, WHISPER_MODEL_PATH)

def process_summary(file_name, transcription):

    summary_text_file_path = Path(MEDIA_ROOT) / 'files' / f"{file_name}_summary_text.txt"
    return get_convert_text_to_textSummary_ollama(summary_text_file_path, transcription)

