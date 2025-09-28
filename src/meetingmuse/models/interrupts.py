from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class InterruptType(StrEnum):
    OPERATION_APPROVAL = "operation_approval"
    SEEK_MORE_INFO = "seek_more_info"


class InterruptInfo(BaseModel):
    type: InterruptType
    message: str
    question: str
    options: Optional[list[str]] = None


class InterruptOperationApproval(InterruptInfo):
    type: InterruptType = InterruptType.OPERATION_APPROVAL
    options: list[str] = ["retry", "cancel"]
