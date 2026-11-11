from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from ..models.dataset import MilestoneDataset,DatasetSupplement
from ..models.common import now,serialize
from .paired_milestones import parse_supplement_csv,event_key

# 决策原因：adopted=采纳并覆盖/补入；ignored_stale=迟到旧修订不覆盖；
# ignored_duplicate=重复投递不新增事件；conflict=同修订号内容冲突（整批拒收）。

def _group_incoming(incoming):
 # 按（票号,里程碑）归组，保留行号，便于逐行给出决策与冲突明细。
 groups={}
 for line,event in enumerate(incoming,start=2):
  groups.setdefault(event_key(event),[]).append((line,event))
 return groups

def supplement(db,ident,body):
 row=db.get(MilestoneDataset,ident)
 if row is None:raise HTTPException(404,"数据批次不存在")
 try: incoming=parse_supplement_csv(body.csv_text)
 except ValueError as e:raise HTTPException(422,str(e))

 grouped=_group_incoming(incoming)
 # 现行事件修订号缺省为0，按键归组。
 current={}
 for event in row.events:
  current.setdefault(event_key(event),[]).append(event)

 # 第一阶段：批次内同（票号,里程碑,修订号）出现多份不同内容即冲突，整批拒收。
 # 与现行事件同修订号但内容不同的，视为迟到同修订记录，第二阶段忽略，不触发拒收。
 conflicts=[]
 for key,items in grouped.items():
  by_rev={}
  for line,event in items:
   by_rev.setdefault(event["revision"],set()).add((event["station"],event["timestamp"]))
  for rev,payloads in by_rev.items():
   if len(payloads)>1:
    lines=[line for line,e in items if e["revision"]==rev]
    conflicts.append({"shipment_id":key[0],"milestone":key[1],"revision":rev,
     "reason":"补报批次内同修订号内容冲突","lines":lines,
     "detail":[f"第{line}行 station={e['station']}, timestamp={e['timestamp']}" for line,e in items if e["revision"]==rev]})
 # 与现行事件同修订号但内容不同属于迟到的同修订旧记录，在第二阶段记 ignored_stale 不覆盖；
 # 只有批次内部同（键,修订号）出现多份不同内容才构成整批拒收的冲突。
 if conflicts:
  record=DatasetSupplement(id=str(uuid4()),dataset_id=row.id,seq=len(row.revisions)+1,status="rejected",
   note=body.note,row_count=len(incoming),accepted_count=0,ignored_count=0,conflict_count=len(conflicts),
   decisions=[{"decision":"conflict",**c} for c in conflicts])
  db.add(record);db.commit()
  raise HTTPException(409,{"message":"补报批次存在同修订号内容冲突，整批拒收，原批次事件未做任何改动",
   "supplement_id":record.id,"conflicts":conflicts})

 # 第二阶段：无冲突，逐键逐行决策。每个键只采纳本批次最高修订的一条事件。
 decisions=[]; adopted_by_key={}; adopted=ignored=0
 for key,items in grouped.items():
  existing=current.get(key,[])
  max_existing=max((e.get("revision",0) for e in existing),default=0)
  batch_max=max(e["revision"] for _,e in items)
  winner=next(e for _,e in items if e["revision"]==batch_max)
  for line,event in items:
   rev=event["revision"]
   if rev<batch_max:
    decisions.append({"decision":"ignored_stale","shipment_id":key[0],"milestone":key[1],"revision":rev,
     "reason":f"本批次已含更新修订{batch_max}，修订{rev}不采纳","line":line})
    ignored+=1;continue
   if rev<max_existing:
    decisions.append({"decision":"ignored_stale","shipment_id":key[0],"milestone":key[1],"revision":rev,
     "reason":f"迟到旧记录：现行修订号已为{max_existing}，修订{rev}不覆盖","line":line,
     "detail":{"current_revision":max_existing}})
    ignored+=1;continue
   if rev==max_existing and existing:
    identical=any(e.get("revision",0)==rev and e["station"]==event["station"] and e["timestamp"]==event["timestamp"] for e in existing)
    if identical:
     decisions.append({"decision":"ignored_duplicate","shipment_id":key[0],"milestone":key[1],"revision":rev,
      "reason":"重复投递，与现行事件完全一致，不新增事件","line":line})
    else:
     decisions.append({"decision":"ignored_stale","shipment_id":key[0],"milestone":key[1],"revision":rev,
      "reason":f"迟到旧记录：现行修订{rev}内容已确定，不同内容不覆盖","line":line,
      "detail":{"current":[{"revision":e.get("revision",0),"station":e["station"],"timestamp":e["timestamp"]} for e in existing]}})
    ignored+=1;continue
   # rev>max_existing：同内容重复行只采纳一次，其余记重复投递。
   if key in adopted_by_key:
    decisions.append({"decision":"ignored_duplicate","shipment_id":key[0],"milestone":key[1],"revision":rev,
     "reason":"重复投递，与本批次采纳记录一致，不新增事件","line":line})
    ignored+=1;continue
   decisions.append({"decision":"adopted","shipment_id":key[0],"milestone":key[1],"revision":rev,
    "reason":("补入缺失里程碑，救回缺节点票" if not existing else f"修订{rev}覆盖修订{max_existing}"),
    "line":line,"detail":{"previous_revision":max_existing,
     "previous":[{"revision":e.get("revision",0),"station":e["station"],"timestamp":e["timestamp"]} for e in existing]}})
   adopted+=1;adopted_by_key[key]=winner

 # 第三阶段：落地。被采纳键的旧事件整体替换，其余原事件原样保留。
 final_events=[];replaced=set()
 for event in row.events:
  key=event_key(event)
  if key in adopted_by_key:
   if key not in replaced:final_events.append(adopted_by_key[key]);replaced.add(key)
   continue
  final_events.append(event)
 for key,event in adopted_by_key.items():
  if key not in replaced:final_events.append(event)

 row.events=final_events;row.version=(row.version or 0)+1
 record=DatasetSupplement(id=str(uuid4()),dataset_id=row.id,seq=row.version,status="accepted",
  note=body.note,row_count=len(incoming),accepted_count=adopted,ignored_count=ignored,
  conflict_count=0,decisions=decisions)
 summary={"id":record.id,"seq":row.version,"status":"accepted","note":body.note,
  "row_count":len(incoming),"accepted_count":adopted,"ignored_count":ignored,"conflict_count":0,
  "created_at":now().isoformat()+"Z"}
 row.revisions=list(row.revisions)+[summary]
 db.add(record);db.commit()
 return {"dataset":serialize(row),"supplement":serialize(record)}

def list_supplements(db,ident):
 row=db.get(MilestoneDataset,ident)
 if row is None:raise HTTPException(404,"数据批次不存在")
 records=db.scalars(select(DatasetSupplement).where(DatasetSupplement.dataset_id==ident).order_by(DatasetSupplement.seq.asc())).all()
 return [serialize(r) for r in records]
