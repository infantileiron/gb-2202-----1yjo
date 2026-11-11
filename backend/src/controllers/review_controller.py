from ..services import review_service
from ..models.review import ActionReview
from ..models.common import serialize
from .common import listing,require
def list_all(db): return listing(db,ActionReview)
def detail(db,ident): return serialize(require(db,ActionReview,ident))
def create(db,body): return serialize(review_service.create(db,body))
