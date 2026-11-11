from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.study import DelayStudy
from ..models.dataset import MilestoneDataset
from ..models.group import RouteGroup

def create(db,body):
 if not db.get(MilestoneDataset,body.dataset_id) or not db.get(RouteGroup,body.group_id):raise HTTPException(422,"数据批次或线路组不存在")
 if db.scalar(select(DelayStudy).where(DelayStudy.name==body.name)):raise HTTPException(409,"研究名称已存在")
 row=DelayStudy(id=str(uuid4()),name=body.name,dataset_id=body.dataset_id,group_id=body.group_id,config={k:getattr(body,k) for k in ["replicates","seed","tail_quantile"]});db.add(row);db.commit();return row
