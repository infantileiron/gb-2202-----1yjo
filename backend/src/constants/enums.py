from enum import StrEnum
class Role(StrEnum):
 ADMIN="admin"
 ANALYST="analyst"
 VIEWER="viewer"
class RunStatus(StrEnum):
 QUEUED="queued"
 RUNNING="running"
 COMPLETED="completed"
 FAILED="failed"
PHASES=["collection","sorting","linehaul","lastmile"]
MILESTONES=["accepted","collected","sorted","arrived","delivered"]
