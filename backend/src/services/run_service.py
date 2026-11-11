from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.ext.mutable import MutableList
from ..models.run import DelayRun
from ..models.study import DelayStudy
from ..models.dataset import MilestoneDataset
from ..models.group import RouteGroup
from ..utils.queue import enqueue
from .paired_milestones import summarize
from .tail_attribution import attribute

def create(db,body):
 if not db.get(DelayStudy,body.study_id):raise HTTPException(422,"研究不存在")
 study=db.get(DelayStudy,body.study_id);dataset=db.get(MilestoneDataset,study.dataset_id)
 # 钉住当前数据版本并固化事件快照（深拷贝，独立于后续补报对数据集的原地变更）。
 row=DelayRun(id=str(uuid4()),study_id=body.study_id,status="queued",result={},error="",
  dataset_version=dataset.version or 0,dataset_snapshot=MutableList([dict(e) for e in dataset.events]))
 db.add(row);db.commit()
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
  # 优先使用入队时固化的快照；历史运行无快照时退回当前事件。
  events=row.dataset_snapshot if row.dataset_snapshot else dataset.events
  paired=summarize(events,group.stations);tail=attribute(paired.pop("matrix"),**study.config)
  row.result={**paired,"tail":tail,"dataset_name":dataset.name,"group_name":group.name,
   "valid_count":len(paired["rows"]),"rejected_count":len(paired["rejected"]),
   "dataset_version":row.dataset_version,"current_dataset_version":dataset.version or 0}
  row.status="completed"
 except Exception as e:
  row.status="failed";row.error=str(e)[:1000]
 db.commit()
