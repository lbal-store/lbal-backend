from typing import Any


def translate(key: str, locale: str = "en", **kwargs: Any) -> str:
    return key.format(**kwargs) if kwargs else key
