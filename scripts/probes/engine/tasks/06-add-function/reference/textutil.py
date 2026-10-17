import re


def shout(text):
    return text.upper() + "!"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
