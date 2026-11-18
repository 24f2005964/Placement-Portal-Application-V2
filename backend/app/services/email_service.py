import os
import smtplib
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import UserNotification, ReminderConfig


def dispatch_email_message(
    recipient_email: str,
    recipient_name: str,
    subject: str,
    message: str,
    user_id: Optional[int] = None,
    trek_name: Optional[str] = None,
    sender: str = "TMA TrekSync Operations"
) -> Dict[str, Any]:
    """
    Unified email dispatcher:
    1. Saves notification directly into in-app UserNotification inbox (guaranteed visibility).
    2. Writes email log file in exports/email_reminders/.
    3. If live SMTP is configured/enabled, attempts delivery to real external inbox (Gmail/Outlook/etc.).
    """
    now = datetime.utcnow()

    # 1. Save to in-app UserNotification inbox
    user_notif = None
    if user_id:
        try:
            user_notif = UserNotification(
                user_id=user_id,
                sender=sender,
                subject=subject,
                message=message,
                trek_name=trek_name or '',
                is_read=False,
                created_at=now
            )
            db.session.add(user_notif)
            db.session.commit()
        except Exception as e:
            current_app.logger.warning(f"Could not save UserNotification: {e}")

    # 2. Write to exports/email_reminders/ disk archive
    logs_dir = current_app.config.get('EXPORT_FOLDER', './exports')
    reminders_dir = os.path.join(logs_dir, 'email_reminders')
    os.makedirs(reminders_dir, exist_ok=True)

    timestamp_str = now.strftime('%Y%m%d_%H%M%S_%f')
    filename = f"email_{user_id or 'ext'}_{timestamp_str}.txt"
    filepath = os.path.join(reminders_dir, filename)

    text_content = (
        f"--- TMA TREKSYNC DISPATCHED EMAIL ---\n"
        f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"From: {sender}\n"
        f"To: {recipient_name} <{recipient_email}>\n"
        f"Trek Route: {trek_name or 'General Notice'}\n"
        f"Subject: {subject}\n"
        f"---------------------------------------------------\n\n"
        f"Dear {recipient_name},\n\n"
        f"{message}\n\n"
        f"---------------------------------------------------\n"
        f"TMA V2 Trekking Operations Team | IITM BS Degree Project\n"
    )

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
    except Exception as e:
        current_app.logger.warning(f"Could not write email file: {e}")

    # 3. Live SMTP dispatch if configured
    smtp_sent = False
    smtp_error = None
    config = ReminderConfig.query.first()

    if config and config.smtp_enabled and config.smtp_host and config.smtp_user and config.smtp_pass:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config.smtp_from or config.smtp_user
            msg['To'] = recipient_email

            # HTML Body
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h2 style="color: #0284c7; margin-top: 0;">🏔️ TMA TrekSync Notification</h2>
                <p style="font-size: 14px; color: #64748b; margin-bottom: 20px;"><strong>Trek:</strong> {trek_name or 'General Notice'}</p>
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 6px; border-left: 4px solid #0284c7; margin-bottom: 20px;">
                    <p style="font-size: 15px; line-height: 1.6; color: #1e293b; margin: 0; white-space: pre-line;">{message}</p>
                </div>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
                <p style="font-size: 12px; color: #94a3b8; text-align: center;">TMA V2 — Trekking Management Application | IITM BS Degree Project</p>
            </div>
            """
            msg.attach(MIMEText(message, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            port = int(config.smtp_port or 587)
            if port == 465:
                server = smtplib.SMTP_SSL(config.smtp_host, port, timeout=10)
            else:
                server = smtplib.SMTP(config.smtp_host, port, timeout=10)
                server.starttls()

            server.login(config.smtp_user, config.smtp_pass)
            server.sendmail(config.smtp_from or config.smtp_user, [recipient_email], msg.as_string())
            server.quit()
            smtp_sent = True
        except Exception as e:
            smtp_error = str(e)
            current_app.logger.warning(f"SMTP delivery error to {recipient_email}: {e}")

    return {
        'in_app_saved': bool(user_notif),
        'file_path': filepath,
        'smtp_sent': smtp_sent,
        'smtp_error': smtp_error
    }
