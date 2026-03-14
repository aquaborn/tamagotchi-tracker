from __future__ import annotations

import hmac
import hashlib
import time
import urllib.parse
from dataclasses import dataclass


@dataclass(frozen=True)
class TmaUser:
    id: int
    first_name: str | None = None
    username: str | None = None


@dataclass(frozen=True)
class TmaInitData:
    auth_date: int
    user: TmaUser


class TmaAuthError(Exception):
    pass


def _parse_qs(init_data_raw: str) -> dict[str, str]:
    pairs = urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True)
    return {k: v for k, v in pairs}


def _calc_check_string(data: dict[str, str]) -> str:
    items = [(k, v) for k, v in data.items() if k != "hash"]
    items.sort(key=lambda x: x[0])
    return "\n".join(f"{k}={v}" for k, v in items)


def validate_and_parse_init_data(init_data_raw: str, bot_token: str, expires_in_sec: int = 3600) -> TmaInitData:
    data = _parse_qs(init_data_raw)
    got_hash = data.get("hash")
    if not got_hash:
        raise TmaAuthError("No hash in initData")

    auth_date_s = data.get("auth_date")
    if not auth_date_s or not auth_date_s.isdigit():
        raise TmaAuthError("Bad auth_date")
    auth_date = int(auth_date_s)

    now = int(time.time())
    if now - auth_date > expires_in_sec:
        raise TmaAuthError("initData expired")

    check_string = _calc_check_string(data)

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, got_hash):
        raise TmaAuthError("Bad initData signature")

    # user is JSON string inside the query
    import json
    user_raw = data.get("user")
    if not user_raw:
        raise TmaAuthError("No user")
    user_obj = json.loads(user_raw)

    return TmaInitData(
        auth_date=auth_date,
        user=TmaUser(
            id=int(user_obj["id"]),
            first_name=user_obj.get("first_name"),
            username=user_obj.get("username"),
        ),
    )