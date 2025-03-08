import re


class DataSanitizer:
    PATTERNS = [
        r"(?i)(token|key|secret|password)",
        r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # CC-like numbers
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        for pattern in cls.PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text)
        return text
