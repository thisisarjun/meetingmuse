"""
Interrupt to UI Elements Mapper
Maps interrupt information to appropriate UI elements for WebSocket responses
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from meetingmuse.models.interrupts import (
    InterruptInfo,
    InterruptOperationApproval,
    InterruptType,
)
from server.models.message.ui_elements import UIButton, UIButtonActionType, UIElements


class BaseInterruptUIMapper(ABC):
    """Base class for interrupt-specific UI mappers"""

    @abstractmethod
    def map_to_ui_elements(self, interrupt_info: InterruptInfo) -> UIElements:
        """Map interrupt info to UI elements"""


class OperationApprovalUIMapper(BaseInterruptUIMapper):
    """Maps operation approval interrupts to retry/cancel UI elements"""

    def map_to_ui_elements(self, interrupt_info: InterruptInfo) -> UIElements:
        assert isinstance(interrupt_info, InterruptOperationApproval)
        """Create retry/cancel buttons for operation approval"""
        buttons: List[UIButton] = []

        for option in interrupt_info.options:
            if option.lower() == "retry":
                buttons.append(
                    UIButton(
                        action_type=UIButtonActionType.RETRY,
                        label="Retry",
                        value="retry",
                        variant="primary",
                    )
                )
            elif option.lower() == "cancel":
                buttons.append(
                    UIButton(
                        action_type=UIButtonActionType.CANCEL,
                        label="Cancel",
                        value="cancel",
                        variant="secondary",
                    )
                )

        return UIElements(buttons=buttons)


_MAPPERS: Dict[InterruptType, BaseInterruptUIMapper] = {
    InterruptType.OPERATION_APPROVAL: OperationApprovalUIMapper(),
}


def map_interrupt_to_ui_elements(interrupt_info: InterruptInfo) -> Optional[UIElements]:
    """
    Convert InterruptInfo to UIElements using appropriate mapper

    Args:
        interrupt_info: Interrupt information from the graph

    Returns:
        UIElements with appropriate buttons for the interrupt type
    """
    mapper = _MAPPERS.get(interrupt_info.type)
    if not mapper:
        return None

    return mapper.map_to_ui_elements(interrupt_info)
