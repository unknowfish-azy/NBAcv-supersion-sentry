"""NBA roster/schedule adapter and conservative data sentinel."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _position_group(position: str) -> str:
    p = position.upper()
    if "G" in p:
        return "guard"
    if "F" in p:
        return "forward"
    if "C" in p:
        return "center"
    return "unknown"


def normalize_players(players: Iterable[dict[str, Any]], source: str = "") -> list[dict[str, Any]]:
    result = []
    for item in players:
        team = _text(item.get("team")).upper()
        position = _text(item.get("position")).upper()
        jersey = _text(item.get("jersey_number", item.get("jersey")))
        row = {
            "team": team,
            "team_name": _text(item.get("team_name")),
            "player_id": _text(item.get("player_id")),
            "name": _text(item.get("name")),
            "jersey_number": jersey,
            "position": position,
            "height_in": _float(item.get("height_in")),
            "weight_lbs": _float(item.get("weight_lbs")),
            "hand": _text(item.get("hand")).upper(),
            "slug": _text(item.get("slug")),
            "source": source or _text(item.get("source")),
            "as_of": _text(item.get("as_of")),
        }
        row["identity_features"] = {
            "position_group": _position_group(position),
            "height_band": (
                "short" if row["height_in"] is not None and row["height_in"] < 76
                else "tall" if row["height_in"] is not None and row["height_in"] >= 81
                else "middle" if row["height_in"] is not None else "unknown"
            ),
            "weight_band": (
                "light" if row["weight_lbs"] is not None and row["weight_lbs"] < 205
                else "heavy" if row["weight_lbs"] is not None and row["weight_lbs"] >= 240
                else "middle" if row["weight_lbs"] is not None else "unknown"
            ),
        }
        result.append(row)
    return result


def _read_records(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh)), {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data, {}
    if "players" in data:
        return data["players"], data
    if "games" in data:
        return data["games"], data
    return [data], data if isinstance(data, dict) else {}


def _parse_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(value[:10])
        except (ValueError, TypeError):
            return None


def resolve_schedule_context(
    games: Iterable[dict[str, Any]], timestamp: str, teams: set[str]
) -> dict[str, Any]:
    """Attach a frame timestamp to one game only when date and teams agree."""
    observed_date = _parse_date(timestamp)
    wanted = {x.upper() for x in teams if x}
    if observed_date is None or len(wanted) != 2:
        return {"status": "context_unknown", "reason": "invalid_timestamp_or_teams"}
    matches = []
    for game in games:
        game_date = _parse_date(_text(game.get("date_utc")))
        game_teams = {_text(game.get("home")).upper(), _text(game.get("away")).upper()}
        if game_date == observed_date and wanted == game_teams:
            matches.append(game)
    if len(matches) != 1:
        return {
            "status": "context_unknown",
            "reason": "no_unique_game_match",
            "candidate_count": len(matches),
        }
    game = matches[0]
    return {
        "status": "matched",
        "game_id": _text(game.get("game_id")),
        "date_utc": _text(game.get("date_utc")),
        "home": _text(game.get("home")).upper(),
        "away": _text(game.get("away")).upper(),
    }


def build_sentinel_report(
    players: list[dict[str, Any]],
    games: list[dict[str, Any]],
    roster_as_of: str = "",
    expected_teams: set[str] | None = None,
    now: date | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    now = now or datetime.now(timezone.utc).date()
    expected_teams = expected_teams or {"HOU", "DAL"}

    seen: dict[tuple[str, str], list[str]] = {}
    for p in players:
        key = (_text(p.get("team")).upper(), _text(p.get("jersey_number", p.get("jersey"))))
        if key[0] and key[1]:
            seen.setdefault(key, []).append(_text(p.get("player_id")) or _text(p.get("name")))
    for (team, jersey), ids in seen.items():
        if len(ids) > 1:
            issues.append({"severity": "BLOCK", "code": "duplicate_team_jersey",
                           "team": team, "jersey_number": jersey, "players": ids})

    as_of = _parse_date(roster_as_of)
    if as_of and (now - as_of).days > 180:
        issues.append({"severity": "WARN", "code": "roster_stale",
                       "as_of": roster_as_of, "age_days": (now - as_of).days})

    game_teams = set()
    for game in games:
        game_teams.update({_text(game.get("home")).upper(), _text(game.get("away")).upper()})
    game_teams.discard("")
    if not expected_teams.issubset(game_teams):
        issues.append({"severity": "WARN", "code": "schedule_team_mismatch",
                       "expected_teams": sorted(expected_teams),
                       "observed_teams": sorted(game_teams)})

    status = "BLOCK" if any(i["severity"] == "BLOCK" for i in issues) else "WARN" if issues else "PASS"
    return {
        "schema": "nba.data_sentinel.v1",
        "status": status,
        "counts": {"players": len(players), "games": len(games), "issues": len(issues)},
        "issues": issues,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--players", required=True)
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expected-teams", default="HOU,DAL")
    args = ap.parse_args()
    player_rows, player_meta = _read_records(Path(args.players))
    game_rows, _ = _read_records(Path(args.schedule))
    players = normalize_players(player_rows, source=str(Path(args.players)))
    report = build_sentinel_report(
        players, game_rows, player_meta.get("as_of", ""),
        expected_teams={x.strip().upper() for x in args.expected_teams.split(",") if x.strip()},
    )
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "schema": "nba.player_profile.v2",
        "players": players,
        "sentinel": report,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] != "BLOCK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
