from sqlalchemy import String,Text,JSON,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class RouteGroup(RecordMixin,Base):
 __tablename__="route_groups"
 name:Mapped[str]=mapped_column(String(100),unique=True)
 stations:Mapped[list]=mapped_column(JSON)
 note:Mapped[str]=mapped_column(Text,default="")
