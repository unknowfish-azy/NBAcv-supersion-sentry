"""Conservative basketball trajectory quality checks."""
from __future__ import annotations

import math
from typing import Any, Iterable


def audit_track(rows: Iterable[dict[str, Any]], *, max_speed_px_s: float = 1200,
                max_gap_s: float = 0.5) -> dict[str, Any]:
    rows = sorted(rows, key=lambda r: (str(r.get("track_id", "")), float(r["timestamp"])))
    issues = []
    previous: dict[str, dict[str, Any]] = {}
    for row in rows:
        track_id = str(row.get("track_id", ""))
        if not track_id or row.get("interpolated"):
            issues.append({"timestamp": row["timestamp"], "reason": "unverified_or_interpolated_point"})
            continue
        old = previous.get(track_id)
        previous[track_id] = row
        if old is None:
            continue
        dt = float(row["timestamp"]) - float(old["timestamp"])
        if dt <= 0:
            issues.append({"timestamp": row["timestamp"], "reason": "non_increasing_timestamp"})
            continue
        if dt > max_gap_s:
            issues.append({"timestamp": row["timestamp"], "reason": "track_gap", "gap_s": dt})
            continue
        ox, oy, ow, oh = map(float, old["bbox"])
        x, y, w, h = map(float, row["bbox"])
        speed = math.hypot(x + w / 2 - ox - ow / 2, y + h / 2 - oy - oh / 2) / dt
        if speed > max_speed_px_s:
            issues.append({"timestamp": row["timestamp"], "reason": "excess_speed", "speed_px_s": speed})
    return {"schema": "nba.ball_track_guard.v1", "status": "REVIEW" if issues else "PASS",
            "rows": len(rows), "issues": issues}
