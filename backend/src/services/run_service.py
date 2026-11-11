from uuid import uuid4
from fastapi import HTTPException
from ..models.run import DelayRun
from ..models.study import DelayStudy
from ..models.dataset import MilestoneDataset
from ..models.group import RouteGroup
from ..utils.queue import enqueue
from .paired_milestones import summarize
from .tail_attribution import attribute

def create(db,body):
 if not db.get(DelayStudy,body.study_id):raise HTTPException(422,"研究不存在")
 row=DelayRun(id=str(uuid4()),study_id=body.study_id,status="queued",result={},error="");db.add(row);db.commit()
 try: enqueue(row.id)
 except Exception:
  row.status="failed";row.error="Redis队列不可用，请稍后重试";db.commit();raise HTTPException(503,row.error)
 return row

def compute(db,run_id):
 row=db.get(DelayRun,run_id)
 if row is None or row.status not in ("queued","running"):return
 row.status="running";db.commit()
 try:
  study=db.get(DelayStudy,row.study_id);dataset=db.get(MilestoneDataset,study.dataset_id);group=db.get(RouteGroup,study.group_id)
  paired=summarize(dataset.events,group.stations);tail=attribute(paired.pop("matrix"),**study.config)
  row.result={**paired,"tail":tail,"dataset_name":dataset.name,"group_name":group.name,"valid_count":len(paired["rows"]),"rejected_count":len(paired["rejected"])};row.status="completed"
 except Exception as e:row.status="failed";row.error=str(e)[:1000]
 db.commit()
