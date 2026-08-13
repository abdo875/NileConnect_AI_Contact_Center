from datetime import datetime
from typing import Optional


def format_datetime(dt_str: Optional[str], fmt: str = "%d %b %Y, %H:%M") -> str:
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime(fmt)
    except Exception:
        return dt_str


def format_date(dt_str: Optional[str]) -> str:
    return format_datetime(dt_str, fmt="%d %b %Y")


def format_duration(seconds: Optional[int]) -> str:
    if seconds is None:
        return "—"
    minutes, secs = divmod(seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def format_file_size(size_bytes: Optional[int]) -> str:
    if size_bytes is None:
        return "—"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


STATUS_COLORS = {
    # Case statuses
    "OPEN": "🔵",
    "IN_PROGRESS": "🟡",
    "FOLLOW_UP_PENDING": "🟠",
    "AI_FOLLOW_UP_SCHEDULED": "🟣",
    "AI_FOLLOW_UP_COMPLETED": "🔷",
    "NEEDS_HUMAN": "🔴",
    "RESOLVED": "🟢",
    # Followup statuses
    "SCHEDULED": "🟣",
    "COMPLETED": "🟢",
    "FAILED": "🔴",
    "CANCELLED": "⚫",
    # Document statuses
    "UPLOADING": "⏳",
    "PROCESSING": "🔄",
    "READY": "✅",
    # Priority
    "LOW": "🔵",
    "MEDIUM": "🟡",
    "HIGH": "🟠",
    "URGENT": "🔴",
    "PENDING": "⚪",
    "ESCALATED": "🟠",
    "FOLLOW_UP_REQUIRED": "🟠",
    "NO_ANSWER": "⚫",
}


def status_badge(status: str) -> str:
    icon = STATUS_COLORS.get(status, "⚪")
    label = status.replace("_", " ").title()
    return f"{icon} {label}"
