# -*- coding: utf-8 -*-

from typing import List, Set, Tuple

from pydantic import BaseModel


class OCRModel(BaseModel):
    coordinate: List  #Image coordinates
    result: Set
class LayoutModel(BaseModel):
    element_type: str
    bbox: List[int]
    res: Tuple[List[List[float]], List[Tuple[str, float]]]
class Base64PostModel(BaseModel):
    base64_str: str  # base64 string
