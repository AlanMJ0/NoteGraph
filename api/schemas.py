from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    question:str
    session_id:Optional[int]=None

class QueryResonse(BaseModel):
    answer:str
    route:str
    extracted_concept:Optional[str]=None
    latency_ms:int
    session_id:int

class DocumentResponse(BaseModel):
    id:int
    filename:str
    chunk_count:int
    uploaded_at:str

