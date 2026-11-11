from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.group import RouteGroup

def create(db,body):
 if len(set(body.stations))!=len(body.stations): raise HTTPException(422,"站点不能重复")
 if db.scalar(select(RouteGroup).where(RouteGroup.name==body.name)):raise HTTPException(409,"线路组名称已存在")
 row=RouteGroup(id=str(uuid4()),**body.model_dump());db.add(row);db.commit();return row
