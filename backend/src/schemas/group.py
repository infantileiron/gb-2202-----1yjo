from pydantic import BaseModel,Field
class GroupCreate(BaseModel):
 name:str=Field(min_length=2,max_length=100)
 stations:list[str]=Field(min_length=1,max_length=20)
 note:str=Field(default="",max_length=1000)
