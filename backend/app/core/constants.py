from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CALL_CENTER = "CALL_CENTER"


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    FOLLOW_UP_PENDING = "FOLLOW_UP_PENDING"
    AI_FOLLOW_UP_SCHEDULED = "AI_FOLLOW_UP_SCHEDULED"
    AI_FOLLOW_UP_COMPLETED = "AI_FOLLOW_UP_COMPLETED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    RESOLVED = "RESOLVED"


class CasePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class CaseCategory(str, Enum):
    CONNECTIVITY = "CONNECTIVITY"
    SPEED = "SPEED"
    BILLING = "BILLING"
    EQUIPMENT = "EQUIPMENT"
    OUTAGE = "OUTAGE"
    INSTALLATION = "INSTALLATION"
    OTHER = "OTHER"


class CallType(str, Enum):
    INBOUND_HUMAN = "INBOUND_HUMAN"
    OUTBOUND_HUMAN = "OUTBOUND_HUMAN"
    OUTBOUND_AI = "OUTBOUND_AI"


class CallOutcome(str, Enum):
    RESOLVED = "RESOLVED"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"
    NO_ANSWER = "NO_ANSWER"
    ESCALATED = "ESCALATED"
    PENDING = "PENDING"


class DocumentStatus(str, Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class FollowupStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FollowupResult(str, Enum):
    YES = "YES"
    NO = "NO"
    NO_ANSWER = "NO_ANSWER"
    UNKNOWN = "UNKNOWN"
