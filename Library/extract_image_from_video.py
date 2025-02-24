import os
import re
import cv2
import pptx
import cv2.data
import pytesseract
import numpy as np
from pathlib import Path
from pptx.util import Inches
from Library.settings import *
from fastapi import FastAPI, File, UploadFile, Request
import traceback

pytesseract.pytesseract.tesseract_cmd=TESSERACT_PATH 

def crop_faces(image_path,frame,frame_counter):
    # print('crop start--------------')
    cropped_image_path = ''
    try:
        print('crop_faces start')
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        
        _,binary_dark=cv2.threshold(gray,30,255,cv2.THRESH_BINARY_INV)
       
        dark_pixels=cv2.countNonZero(binary_dark)
        
        total_pixels=gray.shape[0]*gray.shape[1]
        
        dark_ratio=dark_pixels/total_pixels
        
        # print(f"{round(dark_ratio,2) }-------------skipped due to dark ration/background {dark_ratio:.2f} and frame_counter={frame_counter}")         
        image = cv2.imread(image_path)
       
        if round(dark_ratio,2) ==0.00  :
            return cropped_image_path
        elif image is not None:
            height, width, _ = image.shape
            crop_width = 1676  # Defined crop width
            # Check if cropping is valid
            if crop_width < width:
                left_cropped = image[:, :crop_width]  # Crop the left side of the image
                print('image_path=',image_path)
                cropped_image_path =image_path.replace('.jpg', f'_cropped.jpg')
                cv2.imwrite(cropped_image_path, left_cropped)
                # print('cropped_image_path=',cropped_image_path)
                return cropped_image_path
                # cropped_images.append(cropped_image_path)
                # return cropped_images
    except Exception as e:
        print('error crop_faces:',{e})
        return ''
    
def extract_image_from_video(video_path,file_name):
    print('TESSERACT_PATH=',TESSERACT_PATH)
    image_filenames=[]
    image_folder=os.path.join(MEDIA_ROOT,'images')
    os.makedirs(image_folder, exist_ok=True)  # Ensure directory exists        
    if not os.path.exists(TESSERACT_PATH):
        raise FileNotFoundError(f"Tesseract not found at {TESSERACT_PATH}")
    try:       
        interval=2000
        frame_count=-1
        frame_counter=0
        filename_format=file_name+"_frame_{:05d}.jpg"    
        def motion(frame,frame_counter,threshold=5000):
          
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            text=pytesseract.image_to_string(gray)     
           
            name_pattern=re.findall(r'\b[a-zA-Z]{3,} [a-zA-Z]{3,}\b',text.lower().strip())
            unique_names=set(name_pattern)
            _,binary_dark=cv2.threshold(gray,30,255,cv2.THRESH_BINARY_INV)
            dark_pixels=cv2.countNonZero(binary_dark)
            total_pixels=gray.shape[0]*gray.shape[1]
            dark_ratio=dark_pixels/total_pixels
            mean_brightness=np.mean(gray)  
            # print(f"""frame_count------------------------------{frame_counter}
            #       len(unique_names) ----------------------------{ len(unique_names)} 
            #       and dark_ratio----------------------------{dark_ratio:.2f} 
            #       and unique_names----------------------------{unique_names} 
            #       and text----------------------------------{text}""")
             
            if "participants" in text.lower() or "share invite" in text.lower():
                # print(f"skipped participants/share invite screen text={text}")
                return True    
            elif  dark_ratio>0.6 and len(unique_names)>=2:
                # print(f"skipped due to dark ration/background {dark_ratio:.2f} and frame_counter={frame_counter}")
                return True
            return False
        
        # cap =   cv2.VideoCapture(video_path)
        try:
            # print('before cv2 start')
            # print(cv2.getBuildInformation())
            # print('after cv2 start')
            cap =   cv2.VideoCapture(video_path,cv2.CAP_ANY)
            print('cap assigned')
            # cap.set(cv2.CAP_PROP_HW_ACCELERATION,cv2.VIDEO_ACCELERATION_NONE)
            print('cap set')
            if not cap.isOpened():
                print("Error while opeing video.")
                exit()
            while True:
                # print('frame read start')
                ret, frame =cap.read()
                # print('frame read start 1')
                if not ret:
                    # print("no more frame to read.")
                    break
                # if frame_count>4400:
                #     break
                if frame_counter % interval==0 :
                    # print('before motion function call start')
                    if not motion(frame,frame_counter):
                        # print('after motion function call start')
                        frame_number=frame_counter
                        filename=os.path.join(image_folder,filename_format.format(frame_number))
                        if os.path.exists(filename):
                                    os.remove(filename)
                        cv2.imwrite(filename,frame)
                    
                        # print('before crop_faces function call start')
                        #  # Crop faces from the saved image
                        cropped_filename = crop_faces(filename,frame,frame_counter)
                        # print('after crop_faces function call start')
                        # print(f"""filename------------------{filename} 
                        #       \n length of cropped_faces {cropped_filename}""")
                        if cropped_filename:
                            image_filenames.append(cropped_filename)
                            # print(f'cropped_filename added in image_filenames={cropped_filename}')
                        else:
                            
                            image_filenames.append(filename)
                            # print(f'filenames added in image_filenames={filename}')
                    
                frame_counter+=1
                if frame_count >0 and frame_counter>=frame_count :
                    break
        
            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f'error in {traceback.format_exc()}')
        print('image capture done')
        if len(image_filenames)>0:
            for i,file in enumerate(image_filenames):
                    print(f'i={i} and file={file}')
        return image_filenames
    except Exception as e:
        print('error extract_image_from_video:',{e})
        return [] 
        
def get_extract_image_from_video(video_path,file_name):
    image_filenames=[]
    print('get_extract_image_from_video start--------------')
    try:
        image_filenames=extract_image_from_video(video_path,file_name)
        print('length from get--------------',len(image_filenames))
        return image_filenames
    except Exception as e:
        print('error extract_image_from_video:',{e})
        return image_filenames