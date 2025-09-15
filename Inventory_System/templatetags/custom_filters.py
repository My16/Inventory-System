import os
from django import template

register = template.Library()

@register.filter
def filename(value, max_length=None):
    """
    Return only the base filename (no path).
    Supports both FileField and plain string paths.
    Optionally truncate if max_length is given, keeping the extension.
    """
    # Get the base name
    if hasattr(value, "name"):
        name = os.path.basename(value.name)
    else:
        name = os.path.basename(str(value))

    if max_length and len(name) > int(max_length):
        # Split name and extension
        base, ext = os.path.splitext(name)
        # Leave room for "..." and extension
        truncated_length = int(max_length) - len(ext) - 3
        if truncated_length > 0:
            return base[:truncated_length] + "..." + ext
        else:
            # If max_length is too small, just return "..." + ext
            return "..." + ext
    return name

@register.filter
def filetype(value):
    """Return a simple file type category based on extension."""
    if hasattr(value, "name"):
        ext = os.path.splitext(value.name)[1].lower()
    else:
        ext = os.path.splitext(str(value))[1].lower()

    if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"]:
        return "image"
    elif ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
        return "video"
    elif ext == ".pdf":
        return "pdf"
    elif ext in [".doc", ".docx"]:
        return "word"
    elif ext in [".xls", ".xlsx"]:
        return "excel"
    else:
        return "other"
