from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from keep_up_with.core.config import KeepUpWithConfig


@dataclass(frozen=True)
class Event:
    id: str
    integration: str
    kind: str
    summary: str
    refs: dict[str, str]
    data: dict[str, Any]
    high_priority: bool
    created_at: str


@dataclass(frozen=True)
class InboxItem:
    event: Event
    created_at: str
    notified_at: str | None


class EventStore:
    def __init__(self, config: KeepUpWithConfig) -> None:
        self.db_path = config.paths.events_db

    def record(
        self,
        *,
        integration: str,
        kind: str,
        external_id: str,
        summary: str,
        refs: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        high_priority: bool = False,
        pending: bool = True,
    ) -> Event | None:
        event = Event(
            id=event_id(integration, kind, external_id),
            integration=integration,
            kind=kind,
            summary=" ".join(summary.split()),
            refs=_string_refs(refs or {}),
            data=data or {},
            high_priority=high_priority,
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._connect() as db:
            cursor = db.execute(
                """
                insert or ignore into events
                  (id, integration, kind, summary, refs, data, high_priority, created_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.integration,
                    event.kind,
                    event.summary,
                    json.dumps(event.refs, sort_keys=True),
                    json.dumps(event.data, sort_keys=True),
                    int(event.high_priority),
                    event.created_at,
                ),
            )
            if cursor.rowcount == 0:
                return None
            if pending:
                db.execute(
                    "insert or ignore into inbox (event_id, created_at) values (?, ?)",
                    (event.id, event.created_at),
                )
        return event

    def list_events(
        self,
        *,
        limit: int = 100,
        since: str | None = None,
        until: str | None = None,
        query: str | None = None,
    ) -> list[Event]:
        fields = """
            select id, integration, kind, summary, refs, data, high_priority, created_at
            from events
        """
        clauses: list[str] = []
        params: list[Any] = []
        if since:
            clauses.append("created_at >= ?")
            params.append(since)
        if until:
            clauses.append("created_at <= ?")
            params.append(until)
        if query:
            needle = f"%{query}%"
            clauses.append("(summary like ? or refs like ? or data like ?)")
            params.extend([needle, needle, needle])
        where = f" where {' and '.join(clauses)}" if clauses else ""
        sql = f"""
            select *
            from (
              {fields}
              {where}
              order by created_at desc
              limit ?
            )
            order by created_at asc
        """
        params.append(limit)
        with self._connect() as db:
            rows = db.execute(sql, tuple(params)).fetchall()
        return [_event_from_row(row) for row in rows]

    def get_event(self, event_id_or_prefix: str) -> Event | None:
        with self._connect() as db:
            rows = db.execute(
                """
                select id, integration, kind, summary, refs, data, high_priority, created_at
                from events
                where id like ?
                order by created_at asc
                limit 2
                """,
                (f"{event_id_or_prefix}%",),
            ).fetchall()
        if len(rows) != 1:
            return None
        return _event_from_row(rows[0])

    def list_inbox(
        self,
        *,
        only_unnotified: bool = False,
    ) -> list[InboxItem]:
        sql = """
            select
              inbox.created_at as inbox_created_at,
              inbox.notified_at,
              events.id,
              events.integration,
              events.kind,
              events.summary,
              events.refs,
              events.data,
              events.high_priority,
              events.created_at
            from inbox
            join events on events.id = inbox.event_id
        """
        if only_unnotified:
            sql += " where inbox.notified_at is null"
        sql += " order by inbox.created_at asc"
        with self._connect() as db:
            rows = db.execute(sql).fetchall()
        return [_inbox_from_row(row) for row in rows]

    def mark_notified(self, event_ids: list[str]) -> None:
        if not event_ids:
            return
        notified_at = datetime.now(UTC).isoformat()
        with self._connect() as db:
            db.executemany(
                "update inbox set notified_at = ? where event_id = ?",
                [(notified_at, event_id) for event_id in event_ids],
            )

    def dismiss_inbox(self, event_id_or_prefix: str) -> bool:
        with self._connect() as db:
            rows = db.execute(
                """
                select event_id
                from inbox
                where event_id like ?
                order by created_at asc
                limit 2
                """,
                (f"{event_id_or_prefix}%",),
            ).fetchall()
            if len(rows) != 1:
                return False
            cursor = db.execute(
                "delete from inbox where event_id = ?",
                (rows[0]["event_id"],),
            )
        return cursor.rowcount > 0

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.db_path, timeout=30)
        try:
            db.row_factory = sqlite3.Row
            db.execute("pragma busy_timeout = 5000")
            db.execute("pragma foreign_keys = on")
            try:
                db.execute("pragma journal_mode = wal")
            except sqlite3.OperationalError:
                pass
            db.executescript(
                """
                create table if not exists events (
                  id text primary key,
                  integration text not null,
                  kind text not null,
                  summary text not null,
                  refs text not null,
                  data text not null,
                  high_priority integer not null,
                  created_at text not null
                );

                create table if not exists inbox (
                  event_id text primary key references events(id) on delete cascade,
                  created_at text not null,
                  notified_at text
                );
                """
            )
            yield db
            db.commit()
        finally:
            db.close()


def event_id(integration: str, kind: str, external_id: str) -> str:
    if not external_id.strip():
        raise ValueError("external_id is required")
    payload = f"{integration}:{kind}:{external_id}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _event_from_row(row: sqlite3.Row) -> Event:
    return Event(
        id=row["id"],
        integration=row["integration"],
        kind=row["kind"],
        summary=row["summary"],
        refs=json.loads(row["refs"]),
        data=json.loads(row["data"]),
        high_priority=bool(row["high_priority"]),
        created_at=row["created_at"],
    )


def _inbox_from_row(row: sqlite3.Row) -> InboxItem:
    return InboxItem(
        event=_event_from_row(row),
        created_at=row["inbox_created_at"],
        notified_at=row["notified_at"],
    )


def _string_refs(refs: dict[str, Any]) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in refs.items()
        if key and value is not None and value != ""
    }
