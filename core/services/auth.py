# typing.Optional: clarify when a method may return no value
from typing import Optional, Dict


class AuthService:
    """
    Minimal, local-only auth. In a real app, you'd hash passwords and never store plain text.
    For our demo: a small user registry plus login & forgot-password stubs.
    """
    def __init__(self, seed_users: Optional[Dict[str, Dict[str, str]]] = None) -> None:
        # Structure: { "user@example.com": {"password": "...", "name": "You"} }
        self._users: Dict[str, Dict[str, str]] = seed_users or {
            "you@example.com": {"password": "pass123", "name": "You"},
            "sam@example.com": {"password": "pass123", "name": "Sam"},
        }

    def login(self, username: str, password: str) -> bool:
        """Return True if credentials match."""
        rec = self._users.get(username)
        return bool(rec and rec.get("password") == password)

    def forgot_password(self, username: str) -> str:
        """Always return a friendly stub message (no real email)."""
        return "If the account exists, a reset link has been sent (demo)."

    def get_profile(self, username: str) -> Optional[Dict[str, str]]:
        """Return profile dict for UI personalization."""
        return self._users.get(username)
