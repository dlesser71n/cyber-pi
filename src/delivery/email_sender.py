"""
Email Delivery System for cyber-pi
Supports SMTP and SendGrid for automated report delivery
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Send threat intelligence reports via email"""
    
    def __init__(self, method: str = 'smtp'):
        """
        Initialize email sender
        
        Args:
            method: 'smtp' or 'sendgrid'
        """
        self.method = method
        
        if method == 'smtp':
            self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
            self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
            self.smtp_user = os.getenv('SMTP_USER', '')
            self.smtp_pass = os.getenv('SMTP_PASS', '')
            self.from_email = os.getenv('FROM_EMAIL', 'cyberpi@nexum.com')
        elif method == 'sendgrid':
            self.sendgrid_key = os.getenv('SENDGRID_API_KEY', '')
            self.from_email = os.getenv('FROM_EMAIL', 'cyberpi@nexum.com')
        
        logger.info(f"✅ Email sender initialized ({method})")
    
    def send_report(self, to_emails: List[str], subject: str, 
                   html_body: str, attachments: List[str] = None) -> bool:
        """
        Send email report
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            attachments: List of file paths to attach
        
        Returns:
            True if sent successfully
        """
        if self.method == 'smtp':
            return self._send_smtp(to_emails, subject, html_body, attachments)
        elif self.method == 'sendgrid':
            return self._send_sendgrid(to_emails, subject, html_body, attachments)
        else:
            logger.error(f"Unknown email method: {self.method}")
            return False
    
    def _send_smtp(self, to_emails: List[str], subject: str,
                   html_body: str, attachments: List[str] = None) -> bool:
        """Send via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                            msg.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_pass:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                
                server.sendmail(self.from_email, to_emails, msg.as_string())
            
            logger.info(f"✅ Email sent to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return False
    
    def _send_sendgrid(self, to_emails: List[str], subject: str,
                      html_body: str, attachments: List[str] = None) -> bool:
        """Send via SendGrid API"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
            import base64
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_key)
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_emails,
                subject=subject,
                html_content=html_body
            )
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            data = f.read()
                            encoded = base64.b64encode(data).decode()
                        
                        attachment = Attachment(
                            FileContent(encoded),
                            FileName(os.path.basename(filepath)),
                            FileType('application/pdf'),
                            Disposition('attachment')
                        )
                        message.attachment = attachment
            
            response = sg.send(message)
            
            if response.status_code in [200, 202]:
                logger.info(f"✅ Email sent via SendGrid to {len(to_emails)} recipients")
                return True
            else:
                logger.error(f"❌ SendGrid error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send via SendGrid: {str(e)}")
            return False
    
    def send_alert(self, to_emails: List[str], threat: Dict) -> bool:
        """
        Send critical threat alert
        
        Args:
            to_emails: List of recipient emails
            threat: Threat item dict
        
        Returns:
            True if sent successfully
        """
        subject = f"🚨 CRITICAL THREAT ALERT: {threat.get('title', 'Unknown')[:50]}"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ background: #ff4444; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .threat-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .threat-desc {{ margin-bottom: 20px; }}
                .button {{ background: #0066cc; color: white; padding: 10px 20px; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <h2>🚨 CRITICAL THREAT ALERT</h2>
            </div>
            <div class="content">
                <div class="threat-title">{threat.get('title', 'Unknown Threat')}</div>
                <div class="threat-desc">{threat.get('description', '')[:500]}</div>
                
                <p><strong>Relevance Score:</strong> {threat.get('relevance_score', 0)}</p>
                <p><strong>Match Reasons:</strong></p>
                <ul>
                    {''.join(f"<li>{reason}</li>" for reason in threat.get('match_reasons', [])[:5])}
                </ul>
                
                <p>
                    <a href="{threat.get('link', '#')}" class="button">View Full Details</a>
                </p>
                
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Automated alert from cyber-pi Threat Intelligence Platform<br>
                    Powered by Nexum
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_report(to_emails, subject, html_body)


if __name__ == "__main__":
    # Test email sender
    logging.basicConfig(level=logging.INFO)
    
    sender = EmailSender(method='smtp')
    
    test_html = """
    <html>
    <body>
        <h1>Test Email from cyber-pi</h1>
        <p>This is a test of the email delivery system.</p>
    </body>
    </html>
    """
    
    # Note: Update with real email for testing
    # sender.send_report(['test@example.com'], 'Test Report', test_html)
    
    print("Email sender ready. Configure SMTP settings in .env to test.")
