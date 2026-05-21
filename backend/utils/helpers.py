import os
from uuid import uuid4

from werkzeug.utils import secure_filename

from config import Config


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_logo(file) -> str | None:
    if not file or not allowed_file(file.filename):
        return None
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"
    path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(path)
    return f"/uploads/logos/{filename}"
