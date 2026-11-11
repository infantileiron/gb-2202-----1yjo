from pydantic import BaseModel,Field
class StudyCreate(BaseModel):
 name:str=Field(min_length=2,max_length=180)
 dataset_id:str
 group_id:str
 replicates:int=Field(default=200,ge=30,le=1000)
 seed:int=Field(default=42,ge=0,le=2147483647)
 tail_quantile:float=Field(default=.95,ge=.8,le=.99)
