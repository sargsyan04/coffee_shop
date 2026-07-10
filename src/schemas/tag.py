from pydantic import BaseModel, ConfigDict

class TagCreate(BaseModel):
    name: str

class TagResponse(TagCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
