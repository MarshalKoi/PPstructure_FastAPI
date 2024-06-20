# -*- coding: utf-8 -*-

# import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# import uvicorn

from models.RestfulModel import *
from routers import ocr, layout, table
from utils.ImageHelper import *

app = FastAPI(title="PaddleOCR and PPstructure API",
              description="Self-use interface based on Paddle OCR and FastAPI")


# Cross-domain settings
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(table.router)
app.include_router(layout.router)
app.include_router(ocr.router)

# uvicorn.run(app=app, host="0.0.0.0", port=8000)
