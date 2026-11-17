
from datetime import timezone
from zoneinfo import ZoneInfo

from winotify import Notification


USER_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def show_reminder_notification(reminder):
    scheduled_at = reminder.scheduled_at

    # SQLite có thể trả về datetime không có timezone.
    # Trong project này, datetime lưu trong database luôn là UTC.
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

    local_time = scheduled_at.astimezone(USER_TIMEZONE)

    description = reminder.description or "Đã đến giờ thực hiện công việc."

    message = (
        f"{description}\n\n"
        f"Thời gian: {local_time.strftime('%H:%M %d/%m/%Y')}"
    )

    toast = Notification(
        app_id="Reminder Agent",
        title=reminder.title,
        msg=message,
        duration="long"
    )

    toast.show()
