
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.scheduler import schedule_reminder

from app.database.database import get_db
from app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse
)
from app.services import reminder_service

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.post("", response_model=ReminderResponse, status_code=201)
def create(data: ReminderCreate, db: Session = Depends(get_db)):
    try:
        reminder = reminder_service.create_reminder(db, data)
        schedule_reminder(reminder)
        return reminder
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ReminderResponse])
def list_all(db: Session = Depends(get_db)):
    return reminder_service.get_reminders(db)


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_one(reminder_id: int, db: Session = Depends(get_db)):
    reminder = reminder_service.get_reminder(db, reminder_id)

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return reminder


@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update(
    reminder_id: int,
    data: ReminderUpdate,
    db: Session = Depends(get_db)
):
    reminder = reminder_service.get_reminder(db, reminder_id)

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    try:
        return reminder_service.update_reminder(db, reminder, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{reminder_id}", response_model=ReminderResponse)
def cancel(reminder_id: int, db: Session = Depends(get_db)):
    reminder = reminder_service.get_reminder(db, reminder_id)

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    try:
        return reminder_service.cancel_reminder(db, reminder)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
