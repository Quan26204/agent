
import logging

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.database.models import Reminder
from app.services.notification_service import show_reminder_notification


logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone=timezone.utc)


def deliver_reminder(reminder_id: int):
    db: Session = SessionLocal()

    try:
        reminder = db.query(Reminder).filter(
            Reminder.id == reminder_id
        ).first()

        if reminder is None:
            logger.warning("Reminder %s not found", reminder_id)
            return

        if reminder.status != "pending":
            logger.info("Reminder %s is no longer pending", reminder_id)
            return

        try:
            show_reminder_notification(reminder)

            reminder.status = "completed"
            db.commit()

            logger.info("Reminder %s delivered successfully", reminder_id)

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to deliver reminder %s. Retrying in 60 seconds.",
                reminder_id
            )

            scheduler.add_job(
                deliver_reminder,
                trigger="date",
                run_date=datetime.now(timezone.utc) + timedelta(seconds=60),
                args=[reminder_id],
                id=f"reminder_{reminder_id}",
                replace_existing=True,
                misfire_grace_time=None
            )

    finally:
        db.close()


def schedule_reminder(reminder: Reminder):
    scheduled_at = reminder.scheduled_at

    # Database lưu thời gian UTC dưới dạng naive datetime.
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    # Nếu reminder đã quá hạn, gửi thông báo ngay sau khi khôi phục.
    if scheduled_at <= now:
        run_date = now + timedelta(seconds=2)
    else:
        run_date = scheduled_at

    scheduler.add_job(
        deliver_reminder,
        trigger="date",
        run_date=run_date,
        args=[reminder.id],
        id=f"reminder_{reminder.id}",
        replace_existing=True,
        misfire_grace_time=None
    )

    logger.info(
        "Scheduled reminder %s at %s",
        reminder.id,
        run_date.isoformat()
    )


def start_scheduler():
    if scheduler.running:
        return

    scheduler.start()

    db: Session = SessionLocal()

    try:
        pending_reminders = db.query(Reminder).filter(
            Reminder.status == "pending"
        ).all()

        for reminder in pending_reminders:
            schedule_reminder(reminder)

        logger.info(
            "Scheduler started. Restored %s pending reminders.",
            len(pending_reminders)
        )

    finally:
        db.close()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
