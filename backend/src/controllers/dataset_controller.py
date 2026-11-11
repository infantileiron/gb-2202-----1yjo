from ..services import dataset_service
from ..models.dataset import MilestoneDataset
from ..models.common import serialize
from .common import listing,require
def list_all(db): return listing(db,MilestoneDataset)
def detail(db,ident): return serialize(require(db,MilestoneDataset,ident))
def create(db,body): return serialize(dataset_service.create(db,body))
