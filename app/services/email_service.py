"""
Email Service - Gmail Integration
Sends emails to property managers and users
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from db import fetch_query
from typing import List, Optional


class EmailService:
    """Service class for sending emails via Gmail SMTP"""

    def __init__(self):
        self._load_credentials()

    def _load_credentials(self):
        """Load Gmail credentials from api_keys table or environment variables"""
        # Try environment variables first (fallback)
        self.gmail_address = os.getenv("GMAIL_ADDRESS", "")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")

        # Override with database values if available
        query = """
            SELECT key_name, key_value
            FROM api_keys
            WHERE key_name IN ('gmail_address', 'gmail_app_password')
            AND user_id IS NULL
        """
        result = fetch_query(query)

        if result:
            for row in result:
                if row['key_name'] == 'gmail_address' and row['key_value']:
                    self.gmail_address = row['key_value']
                elif row['key_name'] == 'gmail_app_password' and row['key_value']:
                    self.gmail_app_password = row['key_value']

    def is_configured(self) -> bool:
        """Check if Gmail credentials are configured"""
        return bool(self.gmail_address and self.gmail_app_password)

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None
    ) -> bool:
        """
        Send an email via Gmail SMTP

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML version of email body
            cc_emails: Optional list of CC recipients
            bcc_emails: Optional list of BCC recipients
            attachments: Optional list of (filename, content) tuples

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_configured():
            raise Exception("Gmail not configured. Please add Gmail Address and App Password in API Settings.")

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.gmail_address
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # Add body
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            # Add attachments if any
            if attachments:
                for filename, content in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(part)

            # Combine all recipients
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)

            # Connect to Gmail SMTP server
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_address, self.gmail_app_password)
                server.send_message(msg, to_addrs=all_recipients)

            print(f"Email sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            raise Exception(f"Failed to send email: {str(e)}")

    def send_weather_alert(self, property_managers: List[dict], forecast_data: dict) -> bool:
        """
        Send weather alert to property managers

        Args:
            property_managers: List of dicts with 'email' and 'name' keys
            forecast_data: Weather forecast information

        Returns:
            bool: True if sent successfully
        """
        emails = [pm['email'] for pm in property_managers if pm.get('email')]

        if not emails:
            return False

        subject = f"⚠️ Weather Alert: {forecast_data.get('summary', 'Snow Expected')}"

        body = f"""
Weather Alert - Snow Contractor Portal

Hello,

A winter weather event is forecasted for your properties:

Summary: {forecast_data.get('summary', 'Snow expected')}
Expected Start: {forecast_data.get('start_time', 'See forecast')}
Snow Accumulation: {forecast_data.get('accumulation', 'TBD')}
Temperature: {forecast_data.get('temperature', 'TBD')}

Please ensure your crews are prepared and properties are serviced according to contract requirements.

Login to view details: https://snow-contractor.com

---
This is an automated alert from Snow Contractor Portal
        """.strip()

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">⚠️ Weather Alert</h2>
            <p>A winter weather event is forecasted for your properties:</p>

            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Summary:</td>
                    <td style="padding: 8px;">{forecast_data.get('summary', 'Snow expected')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Expected Start:</td>
                    <td style="padding: 8px;">{forecast_data.get('start_time', 'See forecast')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Snow Accumulation:</td>
                    <td style="padding: 8px;">{forecast_data.get('accumulation', 'TBD')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Temperature:</td>
                    <td style="padding: 8px;">{forecast_data.get('temperature', 'TBD')}</td>
                </tr>
            </table>

            <p>Please ensure your crews are prepared and properties are serviced according to contract requirements.</p>

            <p><a href="https://snow-contractor.com" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Login to View Details</a></p>

            <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
            <p style="color: #7f8c8d; font-size: 12px;">This is an automated alert from Snow Contractor Portal</p>
        </body>
        </html>
        """

        return self.send_email(emails, subject, body, html_body)

    def send_work_log_notification(self, manager_email: str, property_name: str, contractor_name: str, log_details: dict) -> bool:
        """
        Send notification when a work log is submitted

        Args:
            manager_email: Property manager's email
            property_name: Name of the property
            contractor_name: Name of the contractor
            log_details: Dict with log information

        Returns:
            bool: True if sent successfully
        """
        subject = f"Work Log Submitted: {property_name}"

        body = f"""
Work Log Notification - Snow Contractor Portal

A new work log has been submitted:

Property: {property_name}
Contractor: {contractor_name}
Date: {log_details.get('date', 'N/A')}
Time In: {log_details.get('time_in', 'N/A')}
Time Out: {log_details.get('time_out', 'N/A')}
Hours: {log_details.get('hours', 'N/A')}
Equipment: {log_details.get('equipment', 'N/A')}

Notes: {log_details.get('notes', 'None')}

Login to review: https://snow-contractor.com/static/ViewWinterLogs.html

---
Snow Contractor Portal
        """.strip()

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">Work Log Submitted</h2>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0;">
                <p><strong>Property:</strong> {property_name}</p>
                <p><strong>Contractor:</strong> {contractor_name}</p>
                <p><strong>Date:</strong> {log_details.get('date', 'N/A')}</p>
                <p><strong>Time In:</strong> {log_details.get('time_in', 'N/A')}</p>
                <p><strong>Time Out:</strong> {log_details.get('time_out', 'N/A')}</p>
                <p><strong>Hours:</strong> {log_details.get('hours', 'N/A')}</p>
                <p><strong>Equipment:</strong> {log_details.get('equipment', 'N/A')}</p>
            </div>

            {f'<p><strong>Notes:</strong> {log_details.get("notes", "None")}</p>' if log_details.get('notes') else ''}

            <p><a href="https://snow-contractor.com/static/ViewWinterLogs.html" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Review Work Log</a></p>

            <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
            <p style="color: #7f8c8d; font-size: 12px;">Snow Contractor Portal</p>
        </body>
        </html>
        """

        return self.send_email([manager_email], subject, body, html_body)

    def send_invoice_created_notification(self, customer_email: str, invoice_details: dict) -> bool:
        """
        Send notification when QuickBooks invoice is created

        Args:
            customer_email: Customer's email address
            invoice_details: Dict with invoice information

        Returns:
            bool: True if sent successfully
        """
        subject = f"Invoice #{invoice_details.get('invoice_number', 'N/A')} - {invoice_details.get('property_name', '')}"

        body = f"""
Invoice Created - Snow Contractor Portal

A new invoice has been created for your property:

Invoice Number: {invoice_details.get('invoice_number', 'N/A')}
Property: {invoice_details.get('property_name', 'N/A')}
Event: {invoice_details.get('event_name', 'N/A')}
Amount: ${invoice_details.get('amount', '0.00')}
Date: {invoice_details.get('date', 'N/A')}

This invoice has been created in QuickBooks Online. You will receive a separate invoice from QuickBooks.

If you have any questions, please contact your area manager.

---
Snow Contractor Portal
        """.strip()

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">Invoice Created</h2>

            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 4px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Invoice #{invoice_details.get('invoice_number', 'N/A')}</h3>
                <p><strong>Property:</strong> {invoice_details.get('property_name', 'N/A')}</p>
                <p><strong>Event:</strong> {invoice_details.get('event_name', 'N/A')}</p>
                <p><strong>Date:</strong> {invoice_details.get('date', 'N/A')}</p>
                <p style="font-size: 24px; color: #27ae60; margin: 10px 0;">
                    <strong>Amount: ${invoice_details.get('amount', '0.00')}</strong>
                </p>
            </div>

            <p>This invoice has been created in QuickBooks Online. You will receive a separate invoice from QuickBooks with payment details.</p>

            <p style="color: #7f8c8d;">If you have any questions, please contact your area manager.</p>

            <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
            <p style="color: #7f8c8d; font-size: 12px;">Snow Contractor Portal</p>
        </body>
        </html>
        """

        return self.send_email([customer_email], subject, body, html_body)
