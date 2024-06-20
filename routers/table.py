# -*- coding: utf-8 -*-

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO 
from models.OCRModel import *
from models.RestfulModel import *
from paddleocr import PPStructure, save_structure_res
from utils.ImageHelper import base64_to_ndarray, bytes_to_ndarray
import requests
import os
import numpy as np
import cv2
import glob
import zipfile
from urllib.parse import quote
import shutil

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust the origins according to your needs
    allow_credentials=True,
    allow_methods=["*"],  # Or specify just the methods you need: ["GET", "POST", etc.]
    allow_headers=["*"],  # Or specify just the headers you need
)

OCR_LANGUAGE = os.environ.get("OCR_LANGUAGE", "en")

router = APIRouter(prefix="/table", tags=["table"])

model = YOLO('models/yolov8n-layout.onnx', task='detect')
table_engine = PPStructure(lang=OCR_LANGUAGE, layout=False)

def clear_temp_folder(folder_path):
    """
    Clears all files and folders within the specified folder path.
    """
    try:
        if os.path.exists(folder_path):  # Check if the folder exists
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)  # Recreate the temp folder after clearing
    except Exception as e:
        print(f'Failed to clear {folder_path}. Reason: {e}')

def table_detection(image_path, save_folder, base_filename):
    # Load the original image
    img = cv2.imread(image_path)
    
    # Perform object detection
    results = model(image_path, classes=[8])
    boxes = results[0].boxes.xyxy.tolist()

    # Process each detected object sequentially
    for i, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = map(int, box)
        cropped_img = img[y1:y2, x1:x2]
        
        # Recognize table from the cropped image sequentially
        recognize_table_from_image(cropped_img, save_folder, f'{base_filename}')

def recognize_table_from_image(img_array, save_folder, image_name):
    """
    Recognize table from an image array and save the result.
    """
    result = table_engine(img_array)
    save_structure_res(result, save_folder, image_name)

# @router.get('/predict-by-path', response_model=RestfulModel, summary="table recognition with local images by path")
# def predict_by_path(image_path: str):
#     result = table_engine(image_path)
#     restfulModel = RestfulModel(
#         resultcode=200, message="Success", data=result, cls=LayoutModel)
#     return restfulModel


# @router.post('/predict-by-base64', response_model=RestfulModel, summary="table recognition with base64 data")
# def predict_by_base64(base64model: Base64PostModel):
#     img = base64_to_ndarray(base64model.base64_str)
#     result = table_engine(img)
#     restfulModel = RestfulModel(
#         resultcode=200, message="Success", data=result, cls=LayoutModel)
#     return restfulModel


@router.post('/predict-by-file-zip', summary="Zip file of table recognition with uploaded files")
async def predict_by_file_zip(file: UploadFile, background_tasks: BackgroundTasks):
    if not file.filename.endswith((".jpg", ".png")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload images in .jpg or .png format"
        )
    
    save_folder = './temp'
    filename_base = os.path.basename(file.filename).split('.')[0]
    temp_img_path = os.path.join(save_folder, filename_base + '.png')

    with open(temp_img_path, 'wb') as buffer:
        buffer.write(file.file.read())

    # Assuming table_detection function processes the image and saves xlsx files
    table_detection(temp_img_path, save_folder, filename_base)

    specific_folder = os.path.join(save_folder, filename_base)
    xlsx_files = glob.glob(os.path.join(specific_folder, '*.xlsx'))

    zip_file_path = os.path.join(save_folder, filename_base + '.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in xlsx_files:
            zipf.write(file, os.path.basename(file))

    response = FileResponse(
            zip_file_path, 
            media_type="application/zip",
            headers={'Content-Disposition': f'attachment; filename={filename_base}.zip'},
            status_code=status.HTTP_200_OK
        )
    background_tasks.add_task(clear_temp_folder, './temp')
    return response

@router.post('/predict-by-url-zip', summary="Zip file of table recognition with URL")
async def predict_by_url_zip(url: str, background_tasks: BackgroundTasks):
    if not url.endswith((".jpg", ".png")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a URL pointing to an image in .jpg or .png format"
        )
    
    save_folder = './temp'
    filename_base = os.path.basename(url).split('.')[0]
    temp_img_path = os.path.join(save_folder, filename_base + '.png')

    # Download the image from the URL and save it to a temporary location
    urlresponse = requests.get(url)
    if urlresponse.status_code == 200:
        with open(temp_img_path, 'wb') as buffer:
            buffer.write(urlresponse.content)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to download the image from the provided URL"
        )

    # Assuming table_detection function processes the image and saves xlsx files
    table_detection(temp_img_path, save_folder, filename_base)

    specific_folder = os.path.join(save_folder, filename_base)
    xlsx_files = glob.glob(os.path.join(specific_folder, '*.xlsx'))

    zip_file_path = os.path.join(save_folder, filename_base + '.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in xlsx_files:
            zipf.write(file, os.path.basename(file))

    response = FileResponse(
            zip_file_path, 
            media_type="application/zip",
            headers={'Content-Disposition': f'attachment; filename={filename_base}.zip'},
            status_code=status.HTTP_200_OK
        )
    background_tasks.add_task(clear_temp_folder, './temp')
    return response

# @router.get("/xlsx-preview", summary="Returns an XLSX file")
# async def xlsx_preview(filename: str):
#     save_folder = './temp'
#     filename_base = os.path.splitext(filename)[0]
#     specific_folder = os.path.join(save_folder, filename_base)
#     xlsx_file_paths = glob.glob(os.path.join(specific_folder, '*.xlsx'))

#     if not xlsx_file_paths:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="XLSX file not found"
#         )

#     xlsx_file_path = xlsx_file_paths[0]
#     safe_filename = quote(os.path.basename(xlsx_file_path))  # URL encode the filename

#     return FileResponse(
#             xlsx_file_path, 
#             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             headers={'Content-Disposition': f'attachment; filename="{safe_filename}"'},
#             status_code=status.HTTP_200_OK
#         )