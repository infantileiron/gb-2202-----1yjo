import json,random
from datetime import datetime,timedelta,timezone
from sqlalchemy import select,func
from src.config.database import initialize,Session
from src.models import MilestoneDataset,RouteGroup,DelayStudy,DelayRun,ActionReview,Report,User
from src.utils.security import hash_password
from src.services.run_service import compute
from src.constants.enums import MILESTONES

def make_events():
 rng=random.Random(20261112);events=[]
 for i in range(600):
  station=["城北","河西","临港","城南"][i%4];t=datetime(2026,11,9,6,0,tzinfo=timezone.utc)+timedelta(minutes=i*2)
  durations=[rng.uniform(10,35),rng.uniform(20,60),rng.uniform(50,110),rng.expovariate(1/50)+20]
  if station=="临港" and i%9==2:durations[2]+=160
  for j,milestone in enumerate(MILESTONES):
   if j:t+=timedelta(minutes=durations[j-1])
   events.append({"shipment_id":f"CY{i+1:05}","station":station,"milestone":milestone,"timestamp":t.isoformat()})
 # Three deliberately invalid shipments: missing, duplicate, and reversed timestamps.
 for suffix,kind in [("M","missing"),("D","duplicate"),("N","negative")]:
  for j,milestone in enumerate(MILESTONES):
   if kind=="missing" and j==2:continue
   minute=j*30 if kind!="negative" or j!=3 else 10
   events.append({"shipment_id":"BAD"+suffix,"station":"城北","milestone":milestone,"timestamp":(datetime(2026,11,9,tzinfo=timezone.utc)+timedelta(minutes=minute)).isoformat()})
   if kind=="duplicate" and j==1:events.append(events[-1].copy())
 return events

def seed():
 initialize()
 with Session() as db:
  for role in ["admin","analyst","viewer"]:
   email=role+"@delay.demo"
   if not db.scalar(select(User).where(User.email==email)):db.add(User(id="user-"+role,email=email,role=role,password_hash=hash_password("DelayDemo2026!")))
  if not db.get(MilestoneDataset,"demo-dataset"):db.add(MilestoneDataset(id="demo-dataset",name="城配里程碑 2026-11-09",events=make_events(),description="600票完整观测与3票质量反例 · UTC原始时间"))
  if not db.get(RouteGroup,"demo-group"):db.add(RouteGroup(id="demo-group",name="四站联运",stations=["城北","河西","临港","城南"],note="四站共同口径；分钟为单位"))
  db.commit()
  if not db.get(DelayStudy,"demo-study"):db.add(DelayStudy(id="demo-study",name="四站 P95 尾延迟复核",dataset_id="demo-dataset",group_id="demo-group",config={"replicates":200,"seed":42,"tail_quantile":.95}))
  db.commit()
  if not db.get(DelayRun,"demo-run"):db.add(DelayRun(id="demo-run",study_id="demo-study",status="queued",result={},error=""));db.commit();compute(db,"demo-run")
  if not db.get(ActionReview,"demo-review"):db.add(ActionReview(id="demo-review",run_id="demo-run",action="先复核临港交接与末端离散度，再做分线路分层分析；不直接据此归责。",state="approved",reviewer="admin@delay.demo"))
  db.commit()
  if not db.get(Report,"demo-report"):db.add(Report(id="demo-report",review_id="demo-review",title="四站履约时延基线",snapshot={"result":db.get(DelayRun,"demo-run").result,"action":db.get(ActionReview,"demo-review").action,"reviewer":"admin@delay.demo"}))
  db.commit()
  return {cls.__tablename__:db.scalar(select(func.count()).select_from(cls)) for cls in [User,MilestoneDataset,RouteGroup,DelayStudy,DelayRun,ActionReview,Report]}
if __name__=="__main__":print(json.dumps(seed(),ensure_ascii=False))
