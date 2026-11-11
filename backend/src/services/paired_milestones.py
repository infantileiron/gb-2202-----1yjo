import csv,io,math
from datetime import datetime
import numpy as np
from ..constants.enums import PHASES,MILESTONES

def parse_csv(text):
 rows=list(csv.DictReader(io.StringIO(text)))
 if not rows or len(rows)>10000: raise ValueError("需要1至10000条里程碑事件")
 required={"shipment_id","station","milestone","timestamp"}
 if not required.issubset(rows[0]): raise ValueError("CSV须含shipment_id,station,milestone,timestamp")
 events=[]
 for i,row in enumerate(rows):
  if not row["shipment_id"].strip() or not row["station"].strip(): raise ValueError(f"第{i+2}行缺少票号或站点")
  if row["milestone"] not in MILESTONES: raise ValueError(f"第{i+2}行里程碑未知")
  try:
   dt=datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
   if dt.tzinfo is None: raise ValueError()
   dt.timestamp()
  except Exception: raise ValueError(f"第{i+2}行时间需携带时区")
  events.append({k:row[k].strip() for k in required})
 return events

def parse_supplement_csv(text):
 # 补报批次：与原始CSV相同的校验，额外要求整数修订号 revision>=1。
 rows=list(csv.DictReader(io.StringIO(text)))
 if not rows or len(rows)>10000: raise ValueError("需要1至10000条补报事件")
 required={"shipment_id","station","milestone","timestamp","revision"}
 if not required.issubset(rows[0]): raise ValueError("补报CSV须含shipment_id,station,milestone,timestamp,revision")
 events=[]
 for i,row in enumerate(rows):
  if not row["shipment_id"].strip() or not row["station"].strip(): raise ValueError(f"第{i+2}行缺少票号或站点")
  if row["milestone"] not in MILESTONES: raise ValueError(f"第{i+2}行里程碑未知")
  rev_raw=(row.get("revision") or "").strip()
  if not rev_raw.isdigit() or int(rev_raw)<1: raise ValueError(f"第{i+2}行修订号需为>=1的整数")
  try:
   dt=datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
   if dt.tzinfo is None: raise ValueError()
   dt.timestamp()
  except Exception: raise ValueError(f"第{i+2}行时间需携带时区")
  events.append({"shipment_id":row["shipment_id"].strip(),"station":row["station"].strip(),"milestone":row["milestone"].strip(),"timestamp":row["timestamp"].strip(),"revision":int(rev_raw)})
 return events

def event_key(event): return (event["shipment_id"],event["milestone"])

def pair(events,stations):
 groups={}; rejected=[]
 for event in events:
  if event["station"] in stations: groups.setdefault(event["shipment_id"],[]).append(event)
 for sid,items in groups.items():
  names=[i["milestone"] for i in items]
  if len({i["station"] for i in items})!=1: rejected.append({"shipment_id":sid,"reason":"inconsistent_station"});continue
  if len(names)!=len(set(names)): rejected.append({"shipment_id":sid,"reason":"duplicate_milestone"});continue
  if set(names)!=set(MILESTONES): rejected.append({"shipment_id":sid,"reason":"missing_milestone"});continue
  ordered={i["milestone"]:datetime.fromisoformat(i["timestamp"].replace("Z","+00:00")).timestamp() for i in items}
  durations=[(ordered[b]-ordered[a])/60 for a,b in zip(MILESTONES,MILESTONES[1:])]
  if any(not math.isfinite(x) or x<0 for x in durations): rejected.append({"shipment_id":sid,"reason":"negative_duration"});continue
  yield {"shipment_id":sid,"station":items[0]["station"],"durations":durations,"total":sum(durations)},rejected
 # Rejections are returned independently by summarize to avoid incomplete generator state.

def summarize(events,stations):
 selected={e["shipment_id"] for e in events if e["station"] in stations}
 rows=[x[0] for x in pair(events,stations)]
 accepted={r["shipment_id"] for r in rows}
 rejected=[]
 for sid in sorted(selected-accepted):
  items=[e for e in events if e["shipment_id"]==sid and e["station"] in stations]
  names=[e["milestone"] for e in items]
  reason="inconsistent_station" if len({e["station"] for e in items})!=1 else "duplicate_milestone" if len(names)!=len(set(names)) else "missing_milestone" if set(names)!=set(MILESTONES) else "negative_duration"
  rejected.append({"shipment_id":sid,"reason":reason})
 if len(rows)<8: raise ValueError("完整且有序的配送票数至少8票")
 matrix=np.array([r["durations"] for r in rows],dtype=float)
 quantiles=[.5,.9,.95]
 phase_stats=[{"phase":p,"p50":float(np.quantile(matrix[:,i],.5)),"p90":float(np.quantile(matrix[:,i],.9)),"p95":float(np.quantile(matrix[:,i],.95)),"mean":float(matrix[:,i].mean())} for i,p in enumerate(PHASES)]
 return {"rows":rows,"matrix":matrix,"rejected":rejected,"phases":phase_stats,"total_quantiles":{f"p{int(q*100)}":float(np.quantile(matrix.sum(axis=1),q)) for q in quantiles}}
