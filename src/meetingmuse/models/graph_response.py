"""
Graph Response Models
Data structures for graph message processor responses
"""

from typing import Optional

from pydantic import BaseModel

from meetingmuse.models.interrupts import InterruptInfo


class GraphResponse(BaseModel):
    """Response from graph message processing"""

    content: str
    interrupt_info: Optional[InterruptInfo] = None
