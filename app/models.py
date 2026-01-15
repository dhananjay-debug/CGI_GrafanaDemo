from pydantic import BaseModel
from typing import List, Optional, Any

class NlQueryRequest(BaseModel):
    query: str

class DataPoint(BaseModel):
    _time: str
    value: Optional[Any]
    field: str
    measurement: str

class NlQueryResponse(BaseModel):
    query: str
    summary: str
    sample_points: List[DataPoint]
