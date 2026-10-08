"""Resolve a credential bundle only when a connection is opened."""

import json
from typing import cast

import keyring


def credentials(reference: str) -> dict[str, str]:
    if not reference.startswith("qmx/"):
        raise ValueError("Use a qmx/* Credential Manager reference")
    secret = keyring.get_password(reference, reference.removeprefix("qmx/"))
    if secret is None:
        raise ValueError(
            f"Missing Credential Manager entry {reference}; configure it before connecting"
        )
    try:
        value: object = json.loads(secret)
        if (
            not isinstance(value, dict)
            or not value
            or any(
                not isinstance(key, str) or not isinstance(item, str) or not item
                for key, item in cast("dict[object, object]", value).items()
            )
        ):
            raise ValueError
    except (ValueError, TypeError) as error:
        raise ValueError(
            "Credential Manager entry must be a JSON object of nonempty strings"
        ) from error
    return cast("dict[str, str]", value)
