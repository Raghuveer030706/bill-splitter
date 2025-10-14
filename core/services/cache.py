# Purpose of imports:
# - json: serialize/deserialize our app state to a local file (store.json)
# - pathlib.Path: robust file paths across OSes (create dirs, read/write files)
# - typing: type hints for clarity and editor tooling
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil
from datetime import datetime


class CacheService:
    """
    Manages the application state in-memory and persists it as JSON.
    State shape (minimal to start):
      {
        "users": [ { "username": str, "name": str, "password": str } ],
        "groups": [ { "id": str, "name": str } ],
        "expenses": [ { ...serialized Expense... } ],
        "settlements": [ { ...serialized Settlement... } ]
      }
    """

    def __init__(self, path: str = "data/store.json") -> None:
        # Where JSON snapshot lives (and ensure folder exists)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Default empty state
        self.state: Dict[str, Any] = {
            "users": [],
            "groups": [],
            "expenses": [],
            "settlements": [],
        }

        # Load from disk if present
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text())
                # Shallow merge to keep expected keys even if file is partial
                for k in self.state:
                    if k in loaded:
                        self.state[k] = loaded[k]
            except json.JSONDecodeError:
                # Corrupt or empty file → keep defaults; caller may choose to overwrite
                pass

    # ---------- persistence ----------
    def save(self, backup: bool = True) -> None:
        """
        Atomic write: write to temp then replace. Optional timestamped backup in data/backups/.
        """
        tmp = self.path.with_suffix(".tmp")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(self.state, indent=2))
        if backup:
            bdir = self.path.parent / "backups"
            bdir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(self.path, bdir / f"store-{stamp}.json") if self.path.exists() else None
        tmp.replace(self.path)

    # ---- users (dedupe) ----
    def add_user(self, username: str, name: str, password: str) -> None:
        if not any(u["username"] == username for u in self.state["users"]):
            self.state["users"].append({"username": username, "name": name, "password": password})

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Return user dict or None."""
        for u in self.state["users"]:
            if u["username"] == username:
                return u
        return None

    # ---------- groups ----------
    # ---- groups (dedupe) ----
    def add_group(self, gid: str, name: str) -> None:
        if not any(g["id"] == gid for g in self.state["groups"]):
            self.state["groups"].append({"id": gid, "name": name})

    def get_group(self, gid: str) -> Optional[Dict[str, Any]]:
        """Fetch a group by id."""
        for g in self.state["groups"]:
            if g["id"] == gid:
                return g
        return None

    # ---------- expenses ----------
    def add_expense(self, data: Dict[str, Any]) -> None:
        """
        Add a serialized expense dict.
        (Serialization from model → dict will be handled by ExpenseManager.)
        """
        self.state["expenses"].append(data)

    def list_expenses(self) -> List[Dict[str, Any]]:
        """Return all expense dicts."""
        return list(self.state["expenses"])

    # ---------- settlements ----------
    def add_settlement(self, data: Dict[str, Any]) -> None:
        """Add a serialized settlement dict."""
        self.state["settlements"].append(data)

    def list_settlements(self) -> List[Dict[str, Any]]:
        """Return all settlement dicts."""
        return list(self.state["settlements"])
