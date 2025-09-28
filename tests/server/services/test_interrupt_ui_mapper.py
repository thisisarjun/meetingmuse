"""
Tests for interrupt_ui_mapper module
Tests the mapping of interrupt information to UI elements for WebSocket responses
"""
from meetingmuse.models.interrupts import InterruptOperationApproval, InterruptType
from server.models.message.ui_elements import UIButton, UIButtonActionType, UIElements
from server.services.interrupt_ui_mapper import map_interrupt_to_ui_elements


class TestMapInterruptToUIElements:
    """Test suite for map_interrupt_to_ui_elements function"""

    def test_operation_approval_interrupt_with_retry_and_cancel(self):
        """Test mapping operation approval interrupt with retry and cancel options"""
        # Arrange
        interrupt_info = InterruptOperationApproval(
            type=InterruptType.OPERATION_APPROVAL,
            message="Meeting scheduling failed.",
            question="Would you like to retry this operation?",
            options=["retry", "cancel"],
        )

        # Expected result
        expected_result = UIElements(
            buttons=[
                UIButton(
                    action_type=UIButtonActionType.RETRY,
                    label="Retry",
                    value="retry",
                    variant="primary",
                ),
                UIButton(
                    action_type=UIButtonActionType.CANCEL,
                    label="Cancel",
                    value="cancel",
                    variant="secondary",
                ),
            ]
        )

        # Act
        result = map_interrupt_to_ui_elements(interrupt_info)

        # Assert
        assert result == expected_result

    def test_operation_approval_interrupt_with_only_retry(self):
        """Test mapping operation approval interrupt with only retry option"""
        # Arrange
        interrupt_info = InterruptOperationApproval(
            type=InterruptType.OPERATION_APPROVAL,
            message="Operation failed.",
            question="Would you like to retry?",
            options=["retry"],
        )

        # Act
        result = map_interrupt_to_ui_elements(interrupt_info)

        # Assert
        assert result is not None
        assert isinstance(result, UIElements)
        assert result.buttons is not None
        assert len(result.buttons) == 1

        retry_button = result.buttons[0]
        assert retry_button.action_type == UIButtonActionType.RETRY
        assert retry_button.label == "Retry"
        assert retry_button.value == "retry"
        assert retry_button.variant == "primary"
