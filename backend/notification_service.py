import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os
from typing import Optional

class NotificationService:
    def __init__(self):
        # Email configuration - you can set these via environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@support.com")
        self.from_name = os.getenv("FROM_NAME", "Customer Support")
        
        print(f"DEBUG: SMTP_USERNAME={self.smtp_username}, SMTP_PASSWORD={'SET' if self.smtp_password else 'NOT SET'}")
        
    async def send_ticket_resolved_notification(self, user_email: str, user_name: str, ticket_id: str, resolution_notes: str = ""):
        """Send email notification when a ticket is resolved"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = user_email
            msg['Subject'] = f"Ticket #{ticket_id} - Resolved"
            
            # Email template
            template = Template("""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Ticket Resolved</h2>
                    
                    <p>Dear {{ user_name }},</p>
                    
                    <p>We're pleased to inform you that your support ticket has been resolved.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <strong>Ticket ID:</strong> {{ ticket_id }}<br>
                        <strong>Status:</strong> <span style="color: #28a745;">Resolved</span>
                    </div>
                    
                    {% if resolution_notes %}
                    <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Resolution Notes:</strong><br>
                        {{ resolution_notes }}
                    </div>
                    {% endif %}
                    
                    <p>If you have any further questions or concerns, please don't hesitate to create a new support ticket.</p>
                    
                    <p>Thank you for your patience and for choosing our services.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message. Please do not reply to this email.
                    </p>
                </div>
            </body>
            </html>
            """)
            
            # Render template
            html_content = template.render(
                user_name=user_name,
                ticket_id=ticket_id,
                resolution_notes=resolution_notes
            )
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            if self.smtp_username and self.smtp_password:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    start_tls=True,
                    username=self.smtp_username,
                    password=self.smtp_password
                )
                print(f"✅ Resolution notification sent to {user_email}")
                return True
            else:
                print(f"⚠ Email not configured - would send to {user_email}: Ticket #{ticket_id} resolved")
                return True
                
        except Exception as e:
            print(f"❌ Failed to send notification to {user_email}: {str(e)}")
            return False
    
    async def send_ticket_breach_notification(self, user_email: str, user_name: str, ticket_id: str):
        """Send email notification when a ticket SLA is breached"""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = user_email
            msg['Subject'] = f"Ticket #{ticket_id} - SLA Breach Alert"
            
            template = Template("""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545;">SLA Breach Alert</h2>
                    
                    <p>Dear {{ user_name }},</p>
                    
                    <p>We apologize, but your support ticket has exceeded our service level agreement response time.</p>
                    
                    <div style="background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
                        <strong>Ticket ID:</strong> {{ ticket_id }}<br>
                        <strong>Status:</strong> <span style="color: #dc3545;">SLA Breached</span>
                    </div>
                    
                    <p>Our team is working to resolve this issue as quickly as possible. We will provide you with an update shortly.</p>
                    
                    <p>We sincerely apologize for any inconvenience this may cause.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message. Please do not reply to this email.
                    </p>
                </div>
            </body>
            </html>
            """)
            
            html_content = template.render(
                user_name=user_name,
                ticket_id=ticket_id
            )
            
            msg.attach(MIMEText(html_content, 'html'))
            
            if self.smtp_username and self.smtp_password:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    start_tls=True,
                    username=self.smtp_username,
                    password=self.smtp_password
                )
                print(f"✅ Breach notification sent to {user_email}")
                return True
            else:
                print(f"⚠ Email not configured - would send breach alert to {user_email}: Ticket #{ticket_id}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to send breach notification to {user_email}: {str(e)}")
            return False

# Global notification service instance
notification_service = NotificationService()
