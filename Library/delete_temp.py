import os
import sys
import glob
from Library.settings import *
import shutil


def delete_existing_data(folder_list):
    print('folder_list',folder_list)
    """Deletes existing data in the specified folders under MEDIA_ROOT."""
    for folder in folder_list:
        print('foler=',folder)
        folder_path = Path(MEDIA_ROOT) / folder
        if folder_path.exists() and folder_path.is_dir():
            # for file_ext in ["*.mp3","*.txt","*.JPG"]:
            for file_ext in ["*.mp3","*_summary_text.txt","*.JPG"]:
                for file in folder_path.glob(file_ext):
                    file.unlink()    
            # shutil.rmtree(folder_path)  # Deletes the folder and its contents
                    print('.mp3 or .txt files deleted',file)
        # folder_path.mkdir(parents=True, exist_ok=True)  # Recreates the folder




