# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import FileResponse
from models.OCRModel import *
from models.RestfulModel import *
from ultralytics import YOLO 
from paddleocr import PPStructure, save_structure_res
from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes, convert_info_docx
from utils.ImageHelper import base64_to_ndarray, bytes_to_ndarray
import requests
import os
import numpy as np
import cv2
from docx import Document
import shutil

OCR_LANGUAGE = os.environ.get("OCR_LANGUAGE", "en")

router = APIRouter(prefix="/layout", tags=["layout"])

model = YOLO('models/yolov8n-layout.onnx', task='detect')
layout = PPStructure(recovery=True, lang=OCR_LANGUAGE)

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

def text_detection(image_path):
    # Perform object detection
    results = model(image_path, classes=[8, 9])  # Assuming classes 8 and 9 are for tables and text
    boxes = results[0].boxes.xyxy.tolist()

    if not boxes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Table or text found in image"
        )
    
    return boxes

# @router.get('/predict-by-path', response_model=RestfulModel, summary="Layout recognition with local images by path")
# def predict_by_path(image_path: str):
#     result = layout(image_path)
#     restfulModel = RestfulModel(
#         resultcode=200, message="Success", data=result, cls=LayoutModel)
#     return restfulModel


# @router.post('/predict-by-base64', response_model=RestfulModel, summary="Layout recognition with base64 data")
# def predict_by_base64(base64model: Base64PostModel):
#     img = base64_to_ndarray(base64model.base64_str)
#     result = layout(img)
#     restfulModel = RestfulModel(
#         resultcode=200, message="Success", data=result, cls=LayoutModel)
#     return restfulModel


@router.post('/predict-by-file', summary="Layout recognition with uploaded files")
async def predict_by_file(file: UploadFile, background_tasks: BackgroundTasks):
    if file.filename.endswith((".jpg", ".png")):  # Only handle common format images
        save_folder = './temp'  # Change the save folder to './temp'
        filename_base = os.path.basename(file.filename).split('.')[0]
        temp_img_path = os.path.join(save_folder, filename_base + '.png')

        # Write the uploaded file to a temporary location
        with open(temp_img_path, 'wb') as buffer:
            buffer.write(file.file.read())

        img = cv2.imread(temp_img_path)  # Read the image from the temporary location
        result = layout(img)

        save_structure_res(result, save_folder, os.path.basename(temp_img_path).split('.')[0])  # Pass the path of the temporary image file to save_structure_res
        h, w, _ = img.shape
        res = sorted_layout_boxes(result, w)
        convert_info_docx(img, res, save_folder, os.path.basename(temp_img_path).split('.')[0])  # This function saves the .docx file

        docx_file_path = os.path.join(save_folder, filename_base + '_ocr.docx')
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload images in .jpg or .png format"
        )
    response = FileResponse(
            docx_file_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={'Content-Disposition': f'attachment; filename={filename_base}.docx'},
            status_code=status.HTTP_200_OK
        )
    background_tasks.add_task(clear_temp_folder, './temp')
    return response


@router.post('/predict-by-url', summary="Layout recognition with URL")
async def predict_by_url(url: str, background_tasks: BackgroundTasks):
    if url.endswith((".jpg", ".png")):  # Only handle common format images
        save_folder = './temp'  # Change the save folder to './temp'
        filename_base = os.path.basename(url).split('.')[0]
        temp_img_path = os.path.join(save_folder, filename_base + '.png')

        # Download the image from the URL and save it to a temporary location
        urlresponse = requests.get(url)
        with open(temp_img_path, 'wb') as buffer:
            buffer.write(urlresponse.content)

        # Apply text detection
        text_detection(temp_img_path)
        
        img = cv2.imread(temp_img_path)  # Read the image from the temporary location
        result = layout(img)

        save_structure_res(result, save_folder, os.path.basename(temp_img_path).split('.')[0])  # Pass the path of the temporary image file to save_structure_res
        h, w, _ = img.shape
        res = sorted_layout_boxes(result, w)
        convert_info_docx(img, res, save_folder, os.path.basename(temp_img_path).split('.')[0])  # This function saves the .docx file

        docx_file_path = os.path.join(save_folder, filename_base + '_ocr.docx')

        if not os.path.exists(docx_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create .docx file"
            )

        response = FileResponse(
            docx_file_path, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={'Content-Disposition': f'attachment; filename={filename_base}.docx'},
            status_code=status.HTTP_200_OK
        )
        background_tasks.add_task(clear_temp_folder, './temp')
        return response
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL. Only .jpg and .png URLs are supported.",
        )