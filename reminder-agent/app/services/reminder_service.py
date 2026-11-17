
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models import Reminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate


def create_reminder(db: Session, data: ReminderCreate):
    if data.scheduled_at.tzinfo is None:
        raise ValueError("scheduled_at must include a timezone")

    scheduled_at_utc = data.scheduled_at.astimezone(timezone.utc)

    if scheduled_at_utc <= datetime.now(timezone.utc):
        raise ValueError("scheduled_at must be in the future")

    reminder = Reminder(
        title=data.title,
        description=data.description,
        scheduled_at=scheduled_at_utc,
        status="pending"
    )

    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return reminder


def get_reminders(db: Session):
    return (
        db.query(Reminder)
        .order_by(Reminder.scheduled_at.asc())
        .all()
    )


def get_reminder(db: Session, reminder_id: int):
    return db.query(Reminder).filter(
        Reminder.id == reminder_id
    ).first()


def update_reminder(
    db: Session,
    reminder: Reminder,
    data: ReminderUpdate
):
    if reminder.status != "pending":
        raise ValueError("Only pending reminders can be updated")

    updates = data.model_dump(exclude_unset=True)

    if "scheduled_at" in updates and updates["scheduled_at"] is not None:
        scheduled_at = updates["scheduled_at"]

        if scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must include a timezone")

        scheduled_at = scheduled_at.astimezone(timezone.utc)

        if scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("scheduled_at must be in the future")

        updates["scheduled_at"] = scheduled_at

    for key, value in updates.items():
        setattr(reminder, key, value)

    db.commit()
    db.refresh(reminder)

    return reminder


def cancel_reminder(db: Session, reminder: Reminder):
    if reminder.status != "pending":
        raise ValueError("Only pending reminders can be cancelled")

    reminder.status = "cancelled"

    db.commit()
    db.refresh(reminder)

    return reminder
