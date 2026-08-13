"""Inventory repositories with a hard demo/local persistence boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import sqlite3
from typing import Iterable

from .models import AISystem, AssessmentHistoryRecord


class InventoryRepository(ABC):
    """Small persistence port used by the UI and tests."""

    @abstractmethod
    def list_systems(self) -> list[AISystem]: ...

    @abstractmethod
    def get_system(self, system_id: str) -> AISystem | None: ...

    @abstractmethod
    def save_system(self, system: AISystem) -> None: ...

    @abstractmethod
    def add_history(self, record: AssessmentHistoryRecord) -> None: ...

    @abstractmethod
    def list_history(self, system_id: str) -> list[AssessmentHistoryRecord]: ...


class SessionInventoryRepository(InventoryRepository):
    """Process/session-only repository. It never opens a database or writes files."""

    def __init__(self, systems: Iterable[AISystem] = ()):
        self._systems = {item.system_id: item.model_copy(deep=True) for item in systems}
        self._history: dict[str, list[AssessmentHistoryRecord]] = {}

    def list_systems(self) -> list[AISystem]:
        return sorted((item.model_copy(deep=True) for item in self._systems.values()), key=lambda x: x.name)

    def get_system(self, system_id: str) -> AISystem | None:
        item = self._systems.get(system_id)
        return item.model_copy(deep=True) if item else None

    def save_system(self, system: AISystem) -> None:
        self._systems[system.system_id] = system.model_copy(deep=True)

    def add_history(self, record: AssessmentHistoryRecord) -> None:
        self._history.setdefault(record.system_id, []).append(record.model_copy(deep=True))

    def list_history(self, system_id: str) -> list[AssessmentHistoryRecord]:
        return [item.model_copy(deep=True) for item in self._history.get(system_id, [])]


class SQLiteInventoryRepository(InventoryRepository):
    """Local developer/testing persistence. Not suitable for a public anonymous demo."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS ai_systems (
                    system_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS assessment_history (
                    history_id TEXT PRIMARY KEY,
                    system_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(system_id) REFERENCES ai_systems(system_id)
                );
                CREATE INDEX IF NOT EXISTS idx_history_system_created
                    ON assessment_history(system_id, created_at);
                """
            )

    def list_systems(self) -> list[AISystem]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM ai_systems ORDER BY json_extract(payload, '$.name')").fetchall()
        return [AISystem.model_validate_json(row["payload"]) for row in rows]

    def get_system(self, system_id: str) -> AISystem | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM ai_systems WHERE system_id = ?", (system_id,)).fetchone()
        return AISystem.model_validate_json(row["payload"]) if row else None

    def save_system(self, system: AISystem) -> None:
        payload = system.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO ai_systems(system_id, payload, created_at, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(system_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
                (system.system_id, payload, system.created_at.isoformat(), system.updated_at.isoformat()),
            )

    def add_history(self, record: AssessmentHistoryRecord) -> None:
        if self.get_system(record.system_id) is None:
            raise ValueError(f"Unknown AI system: {record.system_id}")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO assessment_history(history_id, system_id, payload, created_at) VALUES (?, ?, ?, ?)",
                (record.history_id, record.system_id, record.model_dump_json(), record.created_at.isoformat()),
            )

    def list_history(self, system_id: str) -> list[AssessmentHistoryRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM assessment_history WHERE system_id = ? ORDER BY created_at", (system_id,)
            ).fetchall()
        return [AssessmentHistoryRecord.model_validate_json(row["payload"]) for row in rows]


def load_seed_systems(path: str | Path) -> list[AISystem]:
    return [AISystem.model_validate(item) for item in json.loads(Path(path).read_text(encoding="utf-8"))["systems"]]


def add_seed_history(
    repository: InventoryRepository, records: Iterable[AssessmentHistoryRecord]
) -> None:
    """Add deterministic synthetic history once without replacing user-created history."""
    for record in records:
        existing_ids = {item.history_id for item in repository.list_history(record.system_id)}
        if record.history_id not in existing_ids:
            repository.add_history(record)


def repository_for_mode(
    mode: str | None,
    seeds: Iterable[AISystem],
    database_path: str | Path | None = None,
) -> InventoryRepository:
    """Construct the repository without permitting demo mode to touch SQLite."""
    selected = (mode or os.environ.get("CONTROL_PLANE_DATA_MODE", "demo")).lower()
    if selected == "demo":
        return SessionInventoryRepository(seeds)
    if selected != "local":
        raise ValueError("CONTROL_PLANE_DATA_MODE must be 'demo' or 'local'")
    path = database_path or os.environ.get("CONTROL_PLANE_DATABASE", ".local/control-plane.db")
    repository = SQLiteInventoryRepository(path)
    if not repository.list_systems():
        for system in seeds:
            repository.save_system(system)
    return repository


def find_potential_duplicates(candidate: AISystem, existing: Iterable[AISystem]) -> list[AISystem]:
    """Flag likely duplicates using transparent matching signals; never merge automatically."""
    matches: list[AISystem] = []
    for item in existing:
        if item.system_id == candidate.system_id:
            continue
        name_similarity = SequenceMatcher(None, candidate.name.casefold(), item.name.casefold()).ratio()
        purpose_similarity = SequenceMatcher(None, candidate.purpose.casefold(), item.purpose.casefold()).ratio()
        provider_model_match = (
            candidate.provider.casefold() == item.provider.casefold()
            and (candidate.model or "").casefold() == (item.model or "").casefold()
        )
        if name_similarity >= 0.75 or purpose_similarity >= 0.82 or provider_model_match:
            matches.append(item.model_copy(deep=True))
    return matches
