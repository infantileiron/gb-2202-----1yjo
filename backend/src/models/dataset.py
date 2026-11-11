from sqlalchemy import String,Text,JSON,Integer
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.ext.mutable import MutableList
from .common import RecordMixin
from ..config.database import Base
class MilestoneDataset(RecordMixin,Base):
 __tablename__="datasets"
 name:Mapped[str]=mapped_column(String(180),unique=True)
 events:Mapped[list]=mapped_column(MutableList.as_mutable(JSON))
 description:Mapped[str]=mapped_column(Text,default="")
 # 当前数据版本：原始入库为0，每接受一批补报递增1。运行记录钉住其入队时的版本。
 version:Mapped[int]=mapped_column(Integer,default=0,server_default="0")
 # 补报批次决策摘要（与 dataset_supplements 表同源，便于列表接口直接展示）。
 revisions:Mapped[list]=mapped_column(MutableList.as_mutable(JSON),default=list)
class DatasetSupplement(RecordMixin,Base):
 __tablename__="dataset_supplements"
 dataset_id:Mapped[str]=mapped_column(String(36),index=True)
 seq:Mapped[int]=mapped_column(Integer)
 status:Mapped[str]=mapped_column(String(20),default="accepted")
 note:Mapped[str]=mapped_column(String(300),default="")
 row_count:Mapped[int]=mapped_column(Integer,default=0)
 accepted_count:Mapped[int]=mapped_column(Integer,default=0)
 ignored_count:Mapped[int]=mapped_column(Integer,default=0)
 conflict_count:Mapped[int]=mapped_column(Integer,default=0)
 # 逐行决策：key/revision/decision/reason/detail，冲突批次保留全部冲突明细供页面核对。
 decisions:Mapped[list]=mapped_column(MutableList.as_mutable(JSON),default=list)
