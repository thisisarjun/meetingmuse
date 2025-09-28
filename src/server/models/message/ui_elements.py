from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field


class UIButtonActionType(StrEnum):
    """UI action type identifier"""

    RETRY = "retry"
    CANCEL = "cancel"
    CONFIRM = "confirm"


class UIButton(BaseModel):
    """UI button configuration"""

    action_type: UIButtonActionType = Field(
        ..., description="Action type for the button"
    )
    label: str = Field(..., description="Button label text")
    value: str = Field(..., description="Value to send when button is clicked")
    variant: Optional[str] = Field(
        default="primary", description="Button variant (primary, secondary, danger)"
    )


class UIElements(BaseModel):
    """UI elements to display with the message"""

    buttons: Optional[List[UIButton]] = Field(
        default=None, description="List of buttons to display"
    )
