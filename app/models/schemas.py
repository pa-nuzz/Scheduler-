#defines what  data looks like when it cones into the api
from pydantic import BaseModel, EmailStr
from typing import List, Optional

#Ingestion API
class IngestRequest(BaseModel):
    filename: str
    chunkscount: int
    message: str

# chat ko api 
class ChatRequest(BaseModel):
    message: str
    session_id : str # redis memory 

class ChatResponse(BaseModel):
    answer: str
    session_id: str

# booking logic
class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    date: str
    time: str
    service: str



