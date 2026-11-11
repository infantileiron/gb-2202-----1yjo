from sqlalchemy import String,Text,JSON,ForeignKey,Integer
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.ext.mutable import MutableList
from .common import RecordMixin
from ..config.database import Base
class DelayRun(RecordMixin,Base):
 __tablename__="runs"
 study_id:Mapped[str]=mapped_column(ForeignKey("studies.id"))
 status:Mapped[str]=mapped_column(String(20),default="queued")
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str]=mapped_column(Text,default="")
 # 入队时钉住的数据集版本；之后补报产生的新版本不影响本运行口径。
 dataset_version:Mapped[int]=mapped_column(Integer,default=0,server_default="0")
 # 入队时刻的事件不可变快照，保证排队/历史运行可按原口径复算。
 dataset_snapshot:Mapped[list]=mapped_column(MutableList.as_mutable(JSON),default=list)
