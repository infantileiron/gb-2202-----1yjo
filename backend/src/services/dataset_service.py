from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from ..models.dataset import MilestoneDataset
from .paired_milestones import parse_csv

def create(db,body):
 if db.scalar(select(MilestoneDataset).where(MilestoneDataset.name==body.name)): raise HTTPException(409,"数据批次名称已存在")
 try: events=parse_csv(body.csv_text)
 except ValueError as e: raise HTTPException(422,str(e))
 row=MilestoneDataset(id=str(uuid4()),name=body.name,events=events,description=body.description);db.add(row);db.commit();return row
