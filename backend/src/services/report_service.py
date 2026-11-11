import csv,io
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from ..models.review import ActionReview
from ..models.run import DelayRun
from ..models.report import Report

def create(db,body):
 review=db.get(ActionReview,body.review_id)
 if review is None or review.state!="approved":raise HTTPException(409,"报告必须关联已批准的复核")
 existing=db.scalar(select(Report).where(Report.review_id==body.review_id))
 if existing:return existing
 run=db.get(DelayRun,review.run_id);row=Report(id=str(uuid4()),review_id=review.id,title=body.title,snapshot={"result":run.result,"action":review.action,"reviewer":review.reviewer});db.add(row);db.commit();return row

def export(row):
 out=io.StringIO();writer=csv.writer(out);writer.writerow(["phase","p50_minutes","p90_minutes","p95_minutes","tail_reduction_minutes","share","bootstrap_low","bootstrap_high"])
 result=row.snapshot["result"];contrib={c["phase"]:c for c in result["tail"]["contributions"]}
 for p in result["phases"]:
  c=contrib[p["phase"]];writer.writerow([p["phase"],p["p50"],p["p90"],p["p95"],c["reduction"],c["share"],c["low"],c["high"]])
 return "\ufeff"+out.getvalue()
