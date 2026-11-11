from ..services import group_service
from ..models.group import RouteGroup
from ..models.common import serialize
from .common import listing,require
def list_all(db): return listing(db,RouteGroup)
def detail(db,ident): return serialize(require(db,RouteGroup,ident))
def create(db,body): return serialize(group_service.create(db,body))
