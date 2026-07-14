import bleach
from zoneinfo import ZoneInfo


def localtime_filter(dt, tz_name="Asia/Yakutsk"):
    if dt is None:
        return ""
    return (dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz_name)).strftime("%d-%m-%Y %H:%M"))


ALLOWED_HTML_TAGS = [
    "br", "p",
    "b", "i", "u", "em", "strong",
    "ul", "ol", "li",
    "a",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "code", "pre",
]

ALLOWED_HTML_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
}


def sanitize_and_nl2br(text: str) -> str:
    """Заменяет переводы строк на <br> и санитайзит HTML через bleach."""
    if not text:
        return ""
    # Сначала заменяем переводы строк на <br>
    text = text.replace("\n", "<br>")
    # Санитайзим: разрешаем безопасные теги, всё остальное вырезаем
    return bleach.clean(
        text,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True,
    )
