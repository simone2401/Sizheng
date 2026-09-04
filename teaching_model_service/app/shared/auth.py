from __future__ import annotations

import secrets
from collections.abc import Mapping


def authorized(authorization: str | None, api_keys: frozenset[str], disabled: bool = False) -> bool:
    if disabled:
        return True
    if not api_keys or not authorization:
        return False
    scheme, sep, token = authorization.partition(" ")
    return bool(sep == " " and scheme.lower() == "bearer" and token and any(secrets.compare_digest(token, key) for key in api_keys))


def bearer_headers(api_key: str) -> Mapping[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}
