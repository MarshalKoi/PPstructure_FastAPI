# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from models.OCRModel import *
from models.RestfulModel import *
from paddleocr import PPStructure, save_structure_res
from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes, convert_info_docx
from utils.ImageHelper import base64_to_ndarray, bytes_to_ndarray
import requests
import os
import numpy as np
import cv2
from docx import Document

OCR_LANGUAGE = os.environ.get("OCR_LANGUAGE", "en")

router = APIRouter(prefix="/layout", tags=["layout"])

layout = PPStructure(recovery=True, lang=OCR_LANGUAGE)


@router.get('/predict-by-path', response_model=RestfulModel, summary="Layout recognition with local images by path")
def predict_by_path(image_path: str):
    result = layout(image_path)
    restfulModel = RestfulModel(
        resultcode=200, message="Success", data=result, cls=LayoutModel)
    return restfulModel


@router.post('/predict-by-base64', response_model=RestfulModel, summary="Layout recognition with base64 data")
def predict_by_base64(base64model: Base64PostModel):
    img = base64_to_ndarray(base64model.base64_str)
    result = layout(img)
    restfulModel = RestfulModel(
        resultcode=200, message="Success", data=result, cls=LayoutModel)
    return restfulModel


@router.post('/predict-by-file', summary="Layout recognition with uploaded files")
async def predict_by_file(file: UploadFile):
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
    return {
        "file": FileResponse(
            docx_file_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={'Content-Disposition': f'attachment; filename={filename_base}.docx'},
            status_code=status.HTTP_200_OK
        ),
        "filename": f"{filename_base}.docx"
    }


@router.post('/predict-by-url', summary="Layout recognition with URL")
async def predict_by_url(url: str):
    if url.endswith((".jpg", ".png")):  # Only handle common format images
        save_folder = './temp'  # Change the save folder to './temp'
        filename_base = os.path.basename(url).split('.')[0]
        temp_img_path = os.path.join(save_folder, filename_base + '.png')

        # Download the image from the URL and save it to a temporary location
        response = requests.get(url)
        with open(temp_img_path, 'wb') as buffer:
            buffer.write(response.content)

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

        return {
            "file": FileResponse(
            docx_file_path, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={'Content-Disposition': f'attachment; filename={filename_base}.docx'},
            status_code=status.HTTP_200_OK
        ),
            "filename": f"{filename_base}.docx"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL. Only .jpg and .png URLs are supported.",
        )