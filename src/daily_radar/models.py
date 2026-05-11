from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class RadarItem:
    source: str
    category: str
    title: str
    url: str = ""
    summary: str = ""
    published_at: str = ""
    fetched_at: str = ""
    score: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.fetched_at:
            self.fetched_at = datetime.now(timezone.utc).isoformat()

    @property
    def id(self) -> str:
        base = (self.url or self.title).strip().lower()
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Any) -> "RadarItem":
        raw = row[8] if len(row) > 8 else "{}"
        return cls(
            source=row[1],
            category=row[2],
            title=row[3],
            url=row[4] or "",
            summary=row[5] or "",
            published_at=row[6] or "",
            fetched_at=row[7] or "",
            score=float(row[9] if len(row) > 9 else 0),
            raw=json.loads(raw or "{}"),
        )
