import os
import json
import urllib.request
from datetime import datetime, timedelta
from flask import render_template_string, current_app
from app.extensions import celery_app, db
from app.models import Trek, Booking, User, ReminderConfig, NotificationLog
from app.services.pdf_service import generate_monthly_pdf
from app.services.email_service import dispatch_email_message

def post_to_google_chat(webhook_url: str, text: str) -> dict:
    """
    Sends message payload to Google Chat Webhook and returns status details.
    """
    if not webhook_url or not webhook_url.startswith(('http://', 'https://')):
        return {'success': False, 'error': 'Invalid or missing webhook URL'}
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps({'text': text}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            return {'success': response.status in (200, 204), 'status_code': response.status, 'error': None}
    except urllib.error.HTTPError as e:
        err_msg = f"HTTP {e.code}: {e.reason}"
        current_app.logger.warning(f"Google Chat webhook dispatch HTTPError: {err_msg}")
        return {'success': False, 'status_code': e.code, 'error': err_msg}
    except Exception as e:
        current_app.logger.warning(f"Google Chat webhook dispatch failed: {e}")
        return {'success': False, 'status_code': None, 'error': str(e)}

@celery_app.task(name='tasks.send_daily_reminders')
def send_daily_reminders(custom_days=None, force=False, trigger_source='Celery Beat Scheduler'):
    """
    Scans treks starting within days_before threshold and sends daily reminders
    to registered trekkers via email log and Google Chat webhook (if configured).
    Supports instant on-demand trigger and schedule configuration overrides.
    """
    config = ReminderConfig.query.first()
    days_before = int(custom_days if custom_days is not None else (config.days_before if config else 2))
    webhook_url = config.webhook_url if config else None
    channel = config.channel if config else 'Email'

    now = datetime.utcnow().date()
    reminder_threshold = now + timedelta(days=days_before)

    upcoming_treks = Trek.query.filter(
        Trek.status.in_(['Open', 'Approved']),
        Trek.start_date >= now,
        Trek.start_date <= reminder_threshold
    ).all()

    logs_dir = current_app.config.get('EXPORT_FOLDER', './exports')
    reminders_dir = os.path.join(logs_dir, 'email_reminders')
    os.makedirs(reminders_dir, exist_ok=True)

    sent_count = 0
    results = []
    webhook_results = []

    for trek in upcoming_treks:
        confirmed_bookings = Booking.query.filter_by(trek_id=trek.id, status='Confirmed').all()
        trek_recipients = 0
        for b in confirmed_bookings:
            user = b.user
            if not user or not user.is_active:
                continue

            reminder_text = (
                f"This is a reminder for your upcoming trek '{trek.name}' starting on {trek.start_date}.\n"
                f"Location: {trek.location}\n"
                f"Difficulty: {trek.difficulty}\n"
                f"Duration: {trek.duration_days} days\n"
                f"Seats Booked: {b.seats_booked}\n"
                f"Assigned Guide: {trek.assigned_staff.name if trek.assigned_staff else 'TBA'}\n\n"
                f"Please ensure you carry appropriate gear, identification, and arrive 30 mins before start time."
            )

            dispatch_res = dispatch_email_message(
                recipient_email=user.email,
                recipient_name=user.name,
                subject=f"Upcoming Trek Reminder: {trek.name}",
                message=reminder_text,
                user_id=user.id,
                trek_name=trek.name,
                sender=trigger_source
            )

            sent_count += 1
            trek_recipients += 1
            results.append({
                'user': user.email,
                'trek': trek.name,
                'file': os.path.basename(dispatch_res['file_path']),
                'smtp_sent': dispatch_res.get('smtp_sent', False)
            })

        # Post to Google Chat Webhook if configured
        if webhook_url and trek_recipients > 0:
            msg = (
                f"🏔️ *Upcoming Trek Reminder: {trek.name}*\n"
                f"📅 *Start Date:* {trek.start_date} ({trek.duration_days} days)\n"
                f"📍 *Location:* {trek.location} | Difficulty: {trek.difficulty}\n"
                f"👥 *Reminders Dispatched to:* {trek_recipients} confirmed participant(s)"
            )
            gchat_res = post_to_google_chat(webhook_url, msg)
            webhook_results.append(gchat_res)

        # Log notification dispatch
        if trek_recipients > 0:
            log_entry = NotificationLog(
                trek_id=trek.id,
                trek_name=trek.name,
                recipient_count=trek_recipients,
                subject=f"Upcoming Trek Reminder: {trek.name}",
                message=f"Reminder dispatched for trek starting on {trek.start_date}.",
                channel=channel,
                dispatch_type='Instant' if force else 'Automated Daily',
                status='Sent',
                sent_by=trigger_source
            )
            db.session.add(log_entry)

    if sent_count > 0:
        db.session.commit()

    any_smtp = any(r.get('smtp_sent') for r in results)
    gchat_delivered = any(w.get('success') for w in webhook_results) if webhook_results else False

    gchat_status = "Delivered to Google Chat Space" if gchat_delivered else (
        "Skipped (No Webhook URL configured)" if not webhook_url else "Failed to deliver to Google Chat"
    )
    smtp_status = "Delivered to real external inboxes" if any_smtp else (
        "Skipped (Live SMTP disabled / not configured)" if not (config and config.smtp_enabled) else "Failed to deliver via SMTP"
    )

    return {
        'status': 'completed',
        'reminders_sent': sent_count,
        'details': results,
        'gchat_status': gchat_status,
        'smtp_status': smtp_status,
        'webhook_configured': bool(webhook_url),
        'smtp_configured': bool(config and config.smtp_enabled and config.smtp_user and config.smtp_pass)
    }


def send_custom_notification(
    trek_id=None,
    subject="Important Trekker Update",
    message="",
    channel="Email",
    dispatch_type="Instant",
    scheduled_for=None,
    sent_by="System Admin"
):
    """
    Sends or schedules a custom notification/reminder written by Admin or Staff.
    Supports targeting a specific trek route or broadcasting across all active treks.
    """
    config = ReminderConfig.query.first()
    webhook_url = config.webhook_url if config else None

    # Determine target treks
    if trek_id:
        treks = [Trek.query.get(trek_id)]
        treks = [t for t in treks if t]
    else:
        treks = Trek.query.filter(Trek.status.in_(['Open', 'Approved'])).all()

    if not treks:
        return {'status': 'error', 'message': 'No eligible treks found for notification.'}

    target_name = treks[0].name if len(treks) == 1 else f"All Active Expeditions ({len(treks)} routes)"
    total_recipients = 0

    # Count total confirmed bookings
    for t in treks:
        total_recipients += Booking.query.filter_by(trek_id=t.id, status='Confirmed').count()

    if dispatch_type == 'Scheduled Later':
        # Create scheduled entry for future execution
        log_entry = NotificationLog(
            trek_id=trek_id,
            trek_name=target_name,
            recipient_count=total_recipients,
            subject=subject,
            message=message,
            channel=channel,
            dispatch_type='Scheduled Later',
            scheduled_for=scheduled_for,
            status='Scheduled',
            sent_by=sent_by
        )
        db.session.add(log_entry)
        db.session.commit()
        return {
            'status': 'scheduled',
            'message': f"Notification scheduled for {scheduled_for} to {total_recipients} recipient(s).",
            'log': log_entry.to_dict()
        }

    # Instant Dispatch
    logs_dir = current_app.config.get('EXPORT_FOLDER', './exports')
    reminders_dir = os.path.join(logs_dir, 'email_reminders')
    os.makedirs(reminders_dir, exist_ok=True)

    sent_count = 0
    now = datetime.utcnow()
    email_dispatches = []

    for trek in treks:
        confirmed_bookings = Booking.query.filter_by(trek_id=trek.id, status='Confirmed').all()
        for b in confirmed_bookings:
            user = b.user
            if not user or not user.is_active:
                continue

            full_msg = (
                f"{message}\n\n"
                f"Trek Details:\n"
                f"- Route: {trek.name} ({trek.location})\n"
                f"- Dates: {trek.start_date} to {trek.end_date}\n"
                f"- Reserved Seats: {b.seats_booked}"
            )

            d_res = dispatch_email_message(
                recipient_email=user.email,
                recipient_name=user.name,
                subject=subject,
                message=full_msg,
                user_id=user.id,
                trek_name=trek.name,
                sender=sent_by
            )
            email_dispatches.append(d_res)

            sent_count += 1

    # Post to Google Chat webhook if channel is Webhook or Both
    gchat_res = None
    if webhook_url and ('Webhook' in channel or 'All' in channel):
        gchat_msg = (
            f"📢 *TMA V2 Announcement: {subject}*\n"
            f"🎯 *Target Route:* {target_name}\n"
            f"👤 *Author:* {sent_by}\n\n"
            f"{message}\n\n"
            f"Sent to {sent_count} confirmed participants."
        )
        gchat_res = post_to_google_chat(webhook_url, gchat_msg)

    # Log entry in database
    log_entry = NotificationLog(
        trek_id=trek_id,
        trek_name=target_name,
        recipient_count=sent_count,
        subject=subject,
        message=message,
        channel=channel,
        dispatch_type='Instant',
        status='Sent',
        sent_by=sent_by
    )
    db.session.add(log_entry)
    db.session.commit()

    any_smtp = any(r.get('smtp_sent') for r in email_dispatches)
    gchat_delivered = bool(gchat_res and gchat_res.get('success'))

    gchat_status = "Delivered to Google Chat Space" if gchat_delivered else (
        "Skipped (No Webhook URL configured)" if not webhook_url else f"Failed: {gchat_res.get('error') if gchat_res else 'Not dispatched'}"
    )
    smtp_status = "Delivered to real external inboxes" if any_smtp else (
        "Skipped (Live SMTP disabled / not configured)" if not (config and config.smtp_enabled) else "Failed to deliver via SMTP"
    )

    return {
        'status': 'sent',
        'message': f"Notification processed for {sent_count} recipient(s).",
        'recipients': sent_count,
        'gchat_status': gchat_status,
        'smtp_status': smtp_status,
        'webhook_configured': bool(webhook_url),
        'smtp_configured': bool(config and config.smtp_enabled and config.smtp_user and config.smtp_pass),
        'log': log_entry.to_dict()
    }


@celery_app.task(name='tasks.generate_monthly_report')
def generate_monthly_report():
    """
    Celery Beat task: Generates HTML monthly trekking activity report for Admin.
    """
    now = datetime.utcnow()
    year = now.year
    month = now.month

    total_treks = Trek.query.count()
    open_treks = Trek.query.filter_by(status='Open').count()
    completed_treks = Trek.query.filter_by(status='Completed').count()

    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()

    total_bookings = Booking.query.count()
    confirmed_bookings = Booking.query.filter_by(status='Confirmed').count()
    cancelled_bookings = Booking.query.filter_by(status='Cancelled').count()

    metrics = {
        'total_treks': total_treks,
        'open_treks': open_treks,
        'completed_treks': completed_treks,
        'total_users': total_users,
        'total_staff': total_staff,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
    }

    # Most popular treks by bookings count
    treks = Trek.query.all()
    popular = []
    for t in treks:
        b_count = Booking.query.filter_by(trek_id=t.id, status='Confirmed').count()
        popular.append({
            'name': t.name,
            'location': t.location,
            'difficulty': t.difficulty,
            'bookings': b_count
        })
    popular.sort(key=lambda x: x['bookings'], reverse=True)
    top_treks = popular[:5]

    # Recent reservations for audit
    recent_bookings = [b.to_dict() for b in Booking.query.order_by(Booking.booking_date.desc()).limit(20).all()]

    export_folder = current_app.config.get('EXPORT_FOLDER', './exports')
    os.makedirs(export_folder, exist_ok=True)

    # 1. Generate PDF Report
    pdf_filename = f"monthly_report_{year}_{month:02d}.pdf"
    pdf_path = os.path.join(export_folder, pdf_filename)
    try:
        generate_monthly_pdf(pdf_path, year, month, metrics, top_treks, recent_bookings)
    except Exception as e:
        current_app.logger.error(f"Error generating PDF monthly report: {e}")

    # 2. Generate HTML Report
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>TMA V2 — Monthly Trekking Activity Report ({year}-{month:02d})</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; color: #1e293b; padding: 30px; }}
    .container {{ max-width: 750px; margin: 0 auto; background: white; padding: 35px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.06); }}
    h1 {{ color: #0284c7; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-top: 0; }}
    .meta {{ font-size: 13px; color: #64748b; margin-bottom: 25px; }}
    .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }}
    .metric-card {{ background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 15px; text-align: center; }}
    .metric-value {{ font-size: 28px; font-weight: bold; color: #0369a1; }}
    .metric-label {{ font-size: 12px; text-transform: uppercase; color: #0284c7; font-weight: 600; margin-top: 5px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
    th {{ background: #f8fafc; font-weight: 600; color: #475569; }}
    .badge {{ background: #10b981; color: white; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: bold; }}
    .footer {{ margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px; font-size: 12px; color: #94a3b8; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>🏔️ Trekking Activity Monthly Report</h1>
    <div class="meta">Report Period: {year}-{month:02d} | Generated: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC</div>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-value">{total_treks}</div>
        <div class="metric-label">Total Treks ({open_treks} Open)</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{total_users}</div>
        <div class="metric-label">Registered Trekkers</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{confirmed_bookings}</div>
        <div class="metric-label">Confirmed Bookings</div>
      </div>
    </div>

    <h3>Top Popular Treks</h3>
    <table>
      <thead>
        <tr>
          <th>Trek Name</th>
          <th>Location</th>
          <th>Confirmed Participants</th>
        </tr>
      </thead>
      <tbody>
        {"".join([f"<tr><td><strong>{t['name']}</strong></td><td>{t['location']}</td><td><span class='badge'>{t['bookings']} trekkers</span></td></tr>" for t in top_treks])}
      </tbody>
    </table>

    <div class="footer">
      Generated automatically by TMA V2 Celery Beat Scheduler | IITM BS Degree MAD 2 Project
    </div>
  </div>
</body>
</html>
"""

    report_filename = f"monthly_report_{year}_{month:02d}.html"
    report_path = os.path.join(export_folder, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return {
        'status': 'completed',
        'report_file': report_filename,
        'filepath': report_path,
        'pdf_file': pdf_filename,
        'pdf_path': pdf_path,
        'year': year,
        'month': month
    }

