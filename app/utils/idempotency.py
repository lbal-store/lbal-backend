import uuid


def generate_key() -> str:
    return uuid.uuid4().hex
