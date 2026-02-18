"""
SMTP client for sending emails.
Supports HTML emails with retry logic and delivery tracking.
"""

import time
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from src.config import settings
from src.utils.logger import logger


class SMTPClient:
    """
    Client for SMTP email sending.
    Handles HTML emails with attachments and retry logic.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        """
        Initialize SMTP client.

        Args:
            host: SMTP server host (defaults to settings)
            port: SMTP server port (defaults to settings)
            user: SMTP username (defaults to settings)
            password: SMTP password (defaults to settings)
            from_email: From email address (defaults to settings)
            from_name: From name (defaults to settings)
        """
        self.host = host or settings.smtp_host
        self.port = port or settings.smtp_port
        self.user = user or settings.smtp_user
        self.password = password or settings.smtp_password
        self.from_email = from_email or settings.smtp_from_email
        self.from_name = from_name or settings.smtp_from_name

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        max_retries: int = 3
    ) -> dict:
        """
        Send HTML email to recipients.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text email body (fallback)
            max_retries: Maximum retry attempts on failure

        Returns:
            Dictionary containing:
                - success: True if sent successfully
                - message: Success/error message
                - recipients: List of recipients
                - sent_at: Timestamp when sent

        Raises:
            Exception: If all retry attempts fail
        """
        logger.info(
            "email_send_started",
            recipients=to_emails,
            subject=subject,
            recipient_count=len(to_emails)
        )

        start_time = time.time()
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"{self.from_name} <{self.from_email}>"
                msg['To'] = ', '.join(to_emails)

                # Add plain text part (fallback)
                if text_body:
                    part1 = MIMEText(text_body, 'plain')
                    msg.attach(part1)

                # Add HTML part
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)

                # Connect to SMTP server
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()  # Enable TLS
                    server.login(self.user, self.password)
                    server.send_message(msg)

                duration = time.time() - start_time

                logger.info(
                    "email_sent_successfully",
                    recipients=to_emails,
                    subject=subject,
                    duration_seconds=duration,
                    attempt=attempt
                )

                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "recipients": to_emails,
                    "sent_at": time.time()
                }

            except smtplib.SMTPAuthenticationError as e:
                # Authentication failed - don't retry
                logger.error(
                    "email_authentication_failed",
                    error=str(e),
                    host=self.host,
                    user=self.user
                )
                raise Exception(f"SMTP authentication failed: {str(e)}")

            except Exception as e:
                last_error = e
                logger.warning(
                    "email_send_retry",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e),
                    recipients=to_emails
                )

                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(
                        "email_retry_wait",
                        wait_seconds=wait_time,
                        next_attempt=attempt + 1
                    )
                    time.sleep(wait_time)
                else:
                    # All retries exhausted
                    logger.error(
                        "email_send_failed",
                        attempts=max_retries,
                        error=str(e),
                        recipients=to_emails,
                        exc_info=True
                    )
                    raise

        # Should never reach here, but for type safety
        raise last_error or Exception("Email sending failed")

    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify SMTP configuration.

        Args:
            to_email: Test recipient email address

        Returns:
            True if test email sent successfully, False otherwise
        """
        try:
            html_body = """
            <html>
                <body>
                    <h2>SkyNet SMTP Test Email</h2>
                    <p>This is a test email to verify your SMTP configuration.</p>
                    <p>If you received this, your email setup is working correctly!</p>
                </body>
            </html>
            """

            self.send_email(
                to_emails=[to_email],
                subject="SkyNet SMTP Test Email",
                html_body=html_body,
                text_body="This is a test email from SkyNet."
            )

            logger.info("test_email_sent_successfully", recipient=to_email)
            return True

        except Exception as e:
            logger.error(
                "test_email_failed",
                recipient=to_email,
                error=str(e)
            )
            return False

    def health_check(self) -> bool:
        """
        Check if SMTP server is accessible.

        Returns:
            True if SMTP connection successful, False otherwise
        """
        try:
            with smtplib.SMTP(self.host, self.port, timeout=5) as server:
                server.starttls()
                server.login(self.user, self.password)

            logger.info("smtp_health_check_passed")
            return True

        except Exception as e:
            logger.error(
                "smtp_health_check_failed",
                error=str(e),
                host=self.host,
                port=self.port
            )
            return False
