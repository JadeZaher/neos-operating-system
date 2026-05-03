"""Version fingerprint generation for governance entities."""
import hashlib
from datetime import datetime


def generate_fingerprint(
    title: str,
    text: str | None,
    version: str,
    status: str,
    updated_at: datetime | None = None,
) -> str:
    """Generate SHA-256 fingerprint from entity fields."""
    parts = [
        title or "",
        text or "",
        version or "",
        status or "",
        updated_at.isoformat() if updated_at else "",
    ]
    content = "|".join(parts)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
