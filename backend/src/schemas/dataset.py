from pydantic import BaseModel,Field
class DatasetCreate(BaseModel):
 name:str=Field(min_length=2,max_length=180)
 csv_text:str=Field(min_length=20,max_length=2500000)
 description:str=Field(default="",max_length=2000)
class DatasetEdit(BaseModel):
 description:str=Field(max_length=2000)
class DatasetSupplementCreate(BaseModel):
 # 补报CSV在原四列基础上增加 revision 列：修订号>=1，同票同里程碑取较新修订。
 csv_text:str=Field(min_length=20,max_length=2500000)
 note:str=Field(default="",max_length=300)
