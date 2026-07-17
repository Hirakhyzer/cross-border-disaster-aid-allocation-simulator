"""Hash-chained transparency ledger for allocation experiments."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def _hash_record(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def append_record(path: str | Path, record: dict[str, Any]) -> dict[str, Any]:
    """Append a hash-linked audit record to a JSONL file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = "GENESIS"
    if destination.exists() and destination.read_text(encoding="utf-8").strip():
        last = destination.read_text(encoding="utf-8").strip().splitlines()[-1]
        previous_hash = json.loads(last)["record_hash"]
    enriched = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "previous_hash": previous_hash,
        **record,
    }
    enriched["record_hash"] = _hash_record(enriched)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(enriched, ensure_ascii=False, default=str) + "\n")
    return enriched


def verify_log(path: str | Path) -> dict[str, Any]:
    """Verify local hash-chain integrity."""
    source = Path(path)
    if not source.exists():
        return {"exists": False, "records": 0, "valid": False}
    previous = "GENESIS"
    records = 0
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        current_hash = record.pop("record_hash")
        if record.get("previous_hash") != previous:
            return {"exists": True, "records": records, "valid": False}
        if _hash_record(record) != current_hash:
            return {"exists": True, "records": records, "valid": False}
        previous = current_hash
        records += 1
    return {"exists": True, "records": records, "valid": True}
