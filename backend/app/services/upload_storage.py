from pathlib import Path
from typing import Optional
from uuid import uuid4

from app.core.config import BASE_DIR, settings


UPLOAD_ROOT = Path(settings.USER_UPLOAD_DIR)
if not UPLOAD_ROOT.is_absolute():
    UPLOAD_ROOT = BASE_DIR / UPLOAD_ROOT


def build_upload_url(relative_path: Optional[str]) -> Optional[str]:
    if not relative_path:
        return None
    return f"/uploads/{relative_path.lstrip('/')}"


def save_user_image(user_id: int, raw: bytes, *, prefix: str, content_type: Optional[str] = None) -> str:
    ext = ".jpg"
    if content_type and "png" in content_type.lower():
        ext = ".png"
    elif content_type and "webp" in content_type.lower():
        ext = ".webp"

    folder = UPLOAD_ROOT / "users" / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}-{uuid4().hex}{ext}"
    target = folder / filename
    target.write_bytes(raw)
    return f"users/{user_id}/{filename}"


def save_product_rights_image(raw: bytes, *, content_type: Optional[str] = None) -> str:
    ext = ".jpg"
    if content_type and "png" in content_type.lower():
        ext = ".png"
    elif content_type and "webp" in content_type.lower():
        ext = ".webp"
    elif content_type and "gif" in content_type.lower():
        ext = ".gif"

    folder = UPLOAD_ROOT / "products" / "rights"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"rights-{uuid4().hex}{ext}"
    target = folder / filename
    target.write_bytes(raw)
    return f"products/rights/{filename}"
