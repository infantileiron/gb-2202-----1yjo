from ..services import study_service
from ..models.study import DelayStudy
from ..models.common import serialize
from .common import listing,require
def list_all(db): return listing(db,DelayStudy)
def detail(db,ident): return serialize(require(db,DelayStudy,ident))
def create(db,body): return serialize(study_service.create(db,body))
