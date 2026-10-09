"""Geometry helpers for court-aware filtering; boxes use [x,y,w,h]."""
from __future__ import annotations

from typing import Any, Iterable


def point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    if len(polygon) < 3:
        return False
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def footpoint_in_polygon(bbox: list[float], polygon: list[tuple[float, float]]) -> bool:
    x, y, w, h = map(float, bbox)
    return point_in_polygon(x + w / 2, y + h, polygon)


def filter_detections_by_court(detections: Iterable[dict[str, Any]], polygon: list[tuple[float, float]]):
    kept, rejected = [], []
    for det in detections:
        if footpoint_in_polygon(det["bbox"], polygon):
            kept.append(det)
        else:
            rejected.append({**det, "reason": "footpoint_outside_court"})
    return kept, rejected
