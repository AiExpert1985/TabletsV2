"""
Notification abstraction for email and SMS.

Phase 1: Interface defined, implementation deferred.
Future: Implement EmailNotificationService and SMSNotificationService.
"""
from abc import ABC, abstractmethod
from typing import Protocol


class INotificationService(Protocol):
    """Interface for notification services (email, SMS, etc.)."""

    async def send(self, recipient: str, message: str, subject: str | None = None) -> bool:
        """
        Send notification.

        Args:
            recipient: Email address or phone number
            message: Message content
            subject: Optional subject (for email)

        Returns:
            True if sent successfully, False otherwise
        """
        ...


class EmailNotificationService:
    """
    Email notification service.

    TODO Phase 2: Implement using SMTP or email service (SendGrid, AWS SES, etc.)
    """

    async def send(self, recipient: str, message: str, subject: str | None = None) -> bool:
        """Send email notification."""
        # TODO: Implement email sending
        # For now: Log to console (development only)
        print(f"[EMAIL] To: {recipient}")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Message: {message}")
        print("-" * 50)
        return True


class SMSNotificationService:
    """
    SMS notification service.

    TODO Phase 2: Implement using SMS provider (Twilio, AWS SNS, local Iraqi provider)
    """

    async def send(self, recipient: str, message: str, subject: str | None = None) -> bool:
        """Send SMS notification."""
        # TODO: Implement SMS sending
        # For now: Log to console (development only)
        print(f"[SMS] To: {recipient}")
        print(f"[SMS] Message: {message}")
        print("-" * 50)
        return True


# Factory function for future use
def get_notification_service(notification_type: str) -> INotificationService:
    """
    Get notification service by type.

    Args:
        notification_type: 'email' or 'sms'

    Returns:
        Notification service instance

    Raises:
        ValueError: If notification type is invalid
    """
    if notification_type == "email":
        return EmailNotificationService()
    elif notification_type == "sms":
        return SMSNotificationService()
    else:
        raise ValueError(f"Invalid notification type: {notification_type}")
