import json
from pathlib import Path

from config.settings import *  # noqa: F401,F403
from config.queries import *  # noqa: F401,F403
from config.constants import *  # noqa: F401,F403

try:
    from config.profile import PROFILE as _BASE_PROFILE, SKILL_WEIGHTS, SKILL_CATEGORIES  # noqa: F401
except ImportError:
    raise ImportError(
        "config/profile.py not found. "
        "Copy config/profile.example.py to config/profile.py "
        "and fill in your personal details."
    )

_profile_json = Path(__file__).resolve().parent.parent / "profile.json"
if _profile_json.exists():
    try:
        with open(_profile_json, "r", encoding="utf-8") as _f:
            _data = json.load(_f)
        PROFILE = _data.get("PROFILE", _BASE_PROFILE)
    except (json.JSONDecodeError, KeyError):
        PROFILE = _BASE_PROFILE
else:
    PROFILE = _BASE_PROFILE
